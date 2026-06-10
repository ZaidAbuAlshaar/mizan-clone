# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/export_thumbs.py
قرار معمارية الـ raster (مراجعة #7): سحّاب قبل/بعد وآلة الزمن يستهلكان **صوراً PNG ثابتة**
عبر getThumbURL — لا tiles ولا بنية تحتية:

  1) لكل مضلع في fields.geojson: صورة "قبل" (صيف سنة الظهور−1) و"بعد" (آخر صيف)
     → geo/outputs/thumbs/{id}_before.png / {id}_after.png + manifest بحقلي
     thumb_before_url / thumb_after_url (تُدمج في GeoJSON للواجهة).
  2) 10 صور سنوية للأزرق (2016–2026) لآلة الزمن — سنة 2016 من TOA (لا L2A قبل 2017).

أمثلة:
  python export_thumbs.py --fields outputs/fields.geojson --limit 20
  python export_thumbs.py --timemachine
"""

import argparse
import json
import os
import urllib.request

import ee

import config as C
from p1_composites import s2_cloudmasked, toa_2016_composite

# تمديد بصري للـ RGB (انعكاسية 0..1)
_VIS_RGB = {"bands": ["B4", "B3", "B2"], "min": 0.0, "max": 0.30}
_AFTER_YEAR = 2025          # "بعد" = آخر صيف مكتمل
_BUFFER_M = 400             # هامش حول المضلع
_DIM = 512                  # أبعاد PNG للمضلعات
_DIM_TM = 1024              # أبعاد PNG لآلة الزمن


def _summer_rgb(aoi, year):
    """مركّب RGB صيفي مقنّع سحابياً لسنة معينة (TOA لـ2016)."""
    if year <= 2016:
        img = toa_2016_composite(aoi, "s2")
        return img.select(["B4", "B3", "B2"])
    col = s2_cloudmasked(aoi, f"{year}-06-01", f"{year}-09-01")
    return col.median().select(["B4", "B3", "B2"])


def _download(url, path):
    urllib.request.urlretrieve(url, path)


def thumbs_for_fields(fields_path, limit=None):
    """صور قبل/بعد لكل مضلع + كتابة manifest."""
    with open(fields_path, encoding="utf-8") as fh:
        feats = json.load(fh)["features"]
    if limit:
        feats = sorted(feats, key=lambda f: -(f["properties"].get("score") or 0))[:limit]

    manifest = {}
    for f in feats:
        props = f["properties"]
        fid = props["id"]
        geom = ee.Geometry(f["geometry"])
        region = geom.buffer(_BUFFER_M).bounds()
        first_seen = int(props.get("first_seen_year") or 2018)
        before_year = max(first_seen - 1, 2016)

        entry = {}
        for tag, year in (("before", before_year), ("after", _AFTER_YEAR)):
            img = _summer_rgb(region, year)
            url = img.getThumbURL({
                "region": region, "dimensions": _DIM,
                "format": "png", **_VIS_RGB})
            fname = f"{fid}_{tag}.png"
            fpath = os.path.join(C.THUMBS_DIR, fname)
            try:
                _download(url, fpath)
                entry[f"thumb_{tag}_url"] = f"thumbs/{fname}"
                entry[f"{tag}_year"] = year
                print(f"  {fid} {tag} ({year}) ✓")
            except Exception as exc:
                entry[f"thumb_{tag}_url"] = None
                print(f"  {fid} {tag} ({year}) فشل: {exc}")
        manifest[fid] = entry

    with open(C.OUT_THUMBS_MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(f"كُتب {C.OUT_THUMBS_MANIFEST} — ادمج الحقلين في GeoJSON الواجهة.")


def timemachine_thumbs():
    """10+ صور سنوية للأزرق (آلة الزمن) — 2016 من TOA بشفافية."""
    aoi = ee.Geometry.Rectangle(C.AOI_AZRAQ_BBOX)
    index = []
    for year in C.TIMEMACHINE_YEARS:
        img = _summer_rgb(aoi, year)
        url = img.getThumbURL({
            "region": aoi, "dimensions": _DIM_TM,
            "format": "png", **_VIS_RGB})
        fname = f"azraq_{year}.png"
        fpath = os.path.join(C.THUMBS_DIR, fname)
        try:
            _download(url, fpath)
            index.append({"year": year, "file": f"thumbs/{fname}",
                          "source": "S2 L1C TOA" if year <= 2016 else "S2 SR"})
            print(f"  آلة الزمن {year} ✓" + (" (TOA)" if year <= 2016 else ""))
        except Exception as exc:
            print(f"  آلة الزمن {year} فشل: {exc}")

    with open(os.path.join(C.THUMBS_DIR, "timemachine_index.json"),
              "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)
    print("كُتب timemachine_index.json")


def main():
    ap = argparse.ArgumentParser(description="صور PNG ثابتة: قبل/بعد + آلة الزمن")
    ap.add_argument("--fields", type=str, default=C.OUT_FIELDS)
    ap.add_argument("--limit", type=int, default=None,
                    help="أعلى N مضلعاً بالدرجة فقط (وفّر زمن الديمو: 20)")
    ap.add_argument("--timemachine", action="store_true")
    args = ap.parse_args()

    ee.Initialize(project=C.EE_PROJECT)
    C.ensure_out_dirs()

    if args.timemachine:
        timemachine_thumbs()
    else:
        thumbs_for_fields(args.fields, args.limit)


if __name__ == "__main__":
    main()
