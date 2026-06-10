# -*- coding: utf-8 -*-
"""
ميزان MIZAN — آلة الزمن عالية الدقة (Sentinel-2/Landsat true-color)
====================================================================
يستبدل صور MODIS (250م — مغبشة) بمركّبات صيفية حقيقية حادّة:
  • 2016  → Landsat 8 Collection-2 L2 (30م) عبر Planetary Computer (بلا مفتاح)
  • 2018–2025 → Sentinel-2 L2A (10م، شبكة العرض 20م) عبر Planetary Computer

المخرجات:
  web/public/nasa/tm_azraq_{year}.jpg      — مسرح آلة الزمن (نفس الأسماء = لا تغيير بالواجهة)
  web/public/nasa/fields/{id}_before.jpg   — قصاصة 2016 الحقيقية لكل حقل (Landsat 30م)
  web/public/nasa/fields/{id}_after.jpg    — قصاصة أحدث صيف لكل حقل (Sentinel-2 10م)
  web/public/nasa/tm_meta.json             — بيان الدقة/المصادر/السنوات (يقرؤه المولّد)

تشغيل:  python tools/fetch_s2_timemachine.py
        python tools/fetch_s2_timemachine.py --res 25 --skip-thumbs   (أسرع)
"""
import argparse
import json
import os
import sys
import warnings

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
warnings.filterwarnings("ignore")

import numpy as np
import planetary_computer as pc
from pystac_client import Client
import odc.stac
from PIL import Image
from pyproj import Transformer

HERE = os.path.dirname(__file__)
REAL_DIR = os.path.join(HERE, "..", "data", "real")
NASA_DIR = os.path.join(HERE, "..", "web", "public", "nasa")
FIELDS_DIR = os.path.join(NASA_DIR, "fields")
UTM = "EPSG:32637"
SUMMER = ("07-01", "08-31")
S2_YEARS = [2018, 2020, 2022, 2024, 2025]
BEFORE_YEAR = 2016
THEATER_W = 2200          # عرض JPEG النهائي للمسرح
THUMB_PX = 320            # حجم قصاصة الحقل
THUMB_WIN_M = 700         # نصف عرض نافذة القصاصة (م)

# امتداد ثابت للستريتش عبر كل السنوات — ألوان متسقة للمقارنة العادلة
VMAX = 0.40
GAMMA = 1.35

CAT = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)


def fields_bbox(pad_frac=0.12):
    """bbox مسرح العرض من حدود الحقول الحقيقية المكتشفة + هامش."""
    with open(os.path.join(REAL_DIR, "fields.geojson"), encoding="utf-8") as f:
        fc = json.load(f)
    xs, ys = [], []
    for ft in fc["features"]:
        cx, cy = ft["properties"]["centroid"]
        xs.append(cx); ys.append(cy)
    lon0, lon1, lat0, lat1 = min(xs), max(xs), min(ys), max(ys)
    padx, pady = (lon1 - lon0) * pad_frac, (lat1 - lat0) * pad_frac
    bbox = [lon0 - padx, lat0 - pady, lon1 + padx, lat1 + pady]
    return bbox, fc


def stretch(rgb):
    """reflectance 0..VMAX → 0..255 مع غاما — ثابت لكل السنوات."""
    x = np.clip(rgb / VMAX, 0, 1) ** (1 / GAMMA)
    return (x * 255).astype("uint8")


def load_s2_rgb(year, bbox, res_m, max_scenes=12):
    # 12 مشهداً: bbox الأزرق يمتد على مدارين (R078/R121) — أقل من ذلك = فجوات سوداء
    """median true-color حقيقي من Sentinel-2 L2A. يرجع (rgb HxWx3 reflectance, geobox)."""
    for cloud in (5, 15, 30):
        items = list(CAT.search(
            collections=["sentinel-2-l2a"], bbox=bbox,
            datetime=f"{year}-{SUMMER[0]}/{year}-{SUMMER[1]}",
            query={"eo:cloud_cover": {"lt": cloud}},
        ).items())
        if items:
            break
    if not items:
        return None, None
    items = sorted(items, key=lambda i: i.properties.get("eo:cloud_cover", 100))[:max_scenes]
    ds = odc.stac.load(items, bands=["B04", "B03", "B02"], bbox=bbox,
                       resolution=res_m, crs=UTM, chunks={}, groupby="solar_day")
    med = ds.median(dim="time")
    rgb = np.dstack([med["B04"].values, med["B03"].values, med["B02"].values]).astype("float32") / 10000.0
    return rgb, ds.odc.geobox


def load_l8_rgb(year, bbox, res_m=30, max_scenes=4):
    """median true-color حقيقي من Landsat 8 C2 L2 (لسنة 2016 قبل أرشيف S2 فوق الأردن)."""
    items = [i for i in CAT.search(
        collections=["landsat-c2-l2"], bbox=bbox,
        datetime=f"{year}-06-01/{year}-{SUMMER[1]}",
        query={"eo:cloud_cover": {"lt": 10}, "platform": {"eq": "landsat-8"}},
    ).items()]
    if not items:
        return None, None
    items = sorted(items, key=lambda i: i.properties.get("eo:cloud_cover", 100))[:max_scenes]
    ds = odc.stac.load(items, bands=["red", "green", "blue"], bbox=bbox,
                       resolution=res_m, crs=UTM, chunks={}, groupby="solar_day")
    med = ds.median(dim="time")
    rgb = np.dstack([med["red"].values, med["green"].values, med["blue"].values]).astype("float32")
    rgb = rgb * 0.0000275 - 0.2          # معامل Collection-2 L2 الرسمي
    return np.clip(rgb, 0, 1), ds.odc.geobox


def load_s2_filled(year, bbox, res_m, max_scenes=12):
    """Sentinel-2 مع ملء الفجوات المدارية من Landsat نفس السنة (أرشيف S2 فوق الأردن
    ناقص التغطية غرباً في السنوات المبكرة — الأسود ممنوع في مسرح العرض)."""
    rgb, gb = load_s2_rgb(year, bbox, res_m, max_scenes)
    if rgb is None:
        return None, None
    nan_frac = float(np.isnan(rgb).any(axis=2).mean())
    if nan_frac > 0.02:
        print(f"      ⚠ فجوة تغطية {nan_frac:.0%} — تُملأ من Landsat {year}", flush=True)
        l8, _ = load_l8_rgb(year, bbox, res_m=res_m)
        if l8 is not None and l8.shape == rgb.shape:
            rgb = np.where(np.isnan(rgb), l8, rgb)
        else:
            print("      ⚠ تعذّر ملء الفجوة (لا Landsat مطابق)")
        rgb = np.nan_to_num(rgb, nan=0.0)
    else:
        rgb = np.nan_to_num(rgb, nan=0.0)
    return rgb, gb


def save_jpeg(rgb8, path, width=THEATER_W, quality=85):
    img = Image.fromarray(rgb8)
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    img.save(path, "JPEG", quality=quality, optimize=True)
    return os.path.getsize(path) / 1024


def crop_thumb(rgb8, geobox, lon, lat, win_m=THUMB_WIN_M):
    """قصاصة مربعة حول centroid الحقل من مصفوفة جاهزة (بلا تحميل إضافي)."""
    tr = geobox.transform
    to_utm = Transformer.from_crs("EPSG:4326", UTM, always_xy=True)
    x, y = to_utm.transform(lon, lat)
    inv = ~tr
    col, row = inv * (x, y)
    res = abs(tr.a)
    half = max(int(win_m / res), 8)
    r0, r1 = int(row) - half, int(row) + half
    c0, c1 = int(col) - half, int(col) + half
    h, w = rgb8.shape[:2]
    r0, r1 = max(0, r0), min(h, r1)
    c0, c1 = max(0, c0), min(w, c1)
    if r1 - r0 < 4 or c1 - c0 < 4:
        return None
    img = Image.fromarray(rgb8[r0:r1, c0:c1])
    return img.resize((THUMB_PX, THUMB_PX), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", type=int, default=20, help="دقة شبكة المسرح (م)")
    ap.add_argument("--skip-thumbs", action="store_true")
    args = ap.parse_args()
    os.makedirs(NASA_DIR, exist_ok=True)
    os.makedirs(FIELDS_DIR, exist_ok=True)

    bbox, fc = fields_bbox()
    print(f"== آلة الزمن عالية الدقة · Sentinel-2 {args.res}م + Landsat 2016 ==")
    print(f"  مسرح العرض من حدود الحقول الحقيقية: {[round(v,3) for v in bbox]}")

    meta = {"source": "Sentinel-2 L2A (Microsoft Planetary Computer، بلا مفتاح)",
            "before_source": "Landsat 8 Collection-2 L2 (2016)",
            "resolution_m": {"theater": args.res, "thumbs": 10, "before": 30},
            "bbox": [round(v, 4) for v in bbox], "years": {}, "fields_thumbs": False}

    # ---- 2016 (Landsat 8) — «قبل»
    print(f"  [{BEFORE_YEAR}] Landsat 8 30م ...", flush=True)
    rgb16, gb16 = load_l8_rgb(BEFORE_YEAR, bbox)
    if rgb16 is not None:
        rgb16_8 = stretch(rgb16)
        kb = save_jpeg(rgb16_8, os.path.join(NASA_DIR, f"tm_azraq_{BEFORE_YEAR}.jpg"))
        meta["years"][str(BEFORE_YEAR)] = {"file": f"/nasa/tm_azraq_{BEFORE_YEAR}.jpg",
                                           "sat": "Landsat 8", "res_m": 30}
        print(f"      ✅ tm_azraq_{BEFORE_YEAR}.jpg ({kb:.0f} KB)")
    else:
        print("      ✗ لا مشاهد Landsat — تُترك صورة MODIS القديمة")

    # ---- 2018–2025 (Sentinel-2)
    latest_rgb8, latest_gb, latest_year = None, None, None
    for y in S2_YEARS:
        print(f"  [{y}] Sentinel-2 {args.res}م ...", flush=True)
        rgb, gb = load_s2_filled(y, bbox, args.res)
        if rgb is None:
            print(f"      ✗ لا مشاهد لصيف {y}")
            continue
        rgb8 = stretch(rgb)
        kb = save_jpeg(rgb8, os.path.join(NASA_DIR, f"tm_azraq_{y}.jpg"))
        meta["years"][str(y)] = {"file": f"/nasa/tm_azraq_{y}.jpg", "sat": "Sentinel-2", "res_m": args.res}
        print(f"      ✅ tm_azraq_{y}.jpg ({kb:.0f} KB)")
        latest_rgb8, latest_gb, latest_year = rgb8, gb, y

    # ---- قصاصات قبل/بعد الحقيقية لكل حقل (الدليل البصري — مراجعة #7)
    if not args.skip_thumbs and latest_year is not None:
        print(f"  [قصاصات الحقول] «بعد» من Sentinel-2 10م (صيف {latest_year}) ...", flush=True)
        rgb_hi, gb_hi = load_s2_filled(latest_year, bbox, 10, max_scenes=8)
        if rgb_hi is None:        # fallback على شبكة المسرح
            rgb_hi8, gb_hi = latest_rgb8, latest_gb
        else:
            rgb_hi8 = stretch(rgb_hi)
        n_ok = 0
        for ft in fc["features"]:
            fid = ft["properties"]["id"]
            lon, lat = ft["properties"]["centroid"]
            after = crop_thumb(rgb_hi8, gb_hi, lon, lat)
            before = crop_thumb(rgb16_8, gb16, lon, lat) if rgb16 is not None else None
            if after is not None:
                after.save(os.path.join(FIELDS_DIR, f"{fid}_after.jpg"), "JPEG", quality=82)
                n_ok += 1
            if before is not None:
                before.save(os.path.join(FIELDS_DIR, f"{fid}_before.jpg"), "JPEG", quality=82)
        meta["fields_thumbs"] = True
        meta["thumbs"] = {"before_year": BEFORE_YEAR, "after_year": latest_year,
                          "count": n_ok, "path": "/nasa/fields/{id}_before|after.jpg"}
        print(f"      ✅ {n_ok} حقلاً × قبل/بعد → web/public/nasa/fields/")

    with open(os.path.join(NASA_DIR, "tm_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("  ✅ كُتب tm_meta.json — شغّل generate_demo_data.py لتحديث المانيفست")


if __name__ == "__main__":
    main()
