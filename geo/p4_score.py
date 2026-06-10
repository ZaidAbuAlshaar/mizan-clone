# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/p4_score.py  (P4)
درجة الاشتباه 0–100 — الصيغة المعتمدة في CONTRACTS §3 (بلا طبقة تراخيص):

  score = 35·inside_protected_basin + 25·is_new_after_closure
        + 15·(persistence_months/12) + 12.5·norm(area_ha) + 12.5·norm(expansion_rate)

  norm(area) = clip(area/p95, 0, 1) · norm(exp) = clip(exp/0.5, 0, 1)
  🔴 ≥70 · 🟠 40–69 · 🟢 <40

إضافات المراجعة:
  • بصمة الريّ الزمنية anti_phase: ارتباط Pearson بين NDVI الشهري وCHIRPS الشهري
    على 36 شهراً لكل مضلع → anti_phase_score = clip((1−r)/2, 0, 1)
    (أخضر في أشهر الصفر-مطر → ارتباط سالب → درجة قرب 1 — جواب "شو الفرق عنكم؟")
  • sm_rootzone من SMAP SPL4SMGP/008 — 12 قيمة شهرية كتوكيد مستقل في بانل الدليل.

الإخراج: geo/outputs/fields.geojson — مطابق **حرفياً** لمخطط CONTRACTS §2.1
(يستبدل data/demo/fields.geojson مع is_demo=false).

أمثلة:
  python p4_score.py --fields-geojson downloads/mizan_p3_fields_azraq_2025.geojson
  python p4_score.py --fields-asset projects/.../p3/mizan_p3_fields_azraq_2025
"""

import argparse
import json
import math
import os

import ee

import config as C
from p1_composites import monthly_indices

# بادئات المعرفات حسب الحوض
_ID_PREFIX = {"azraq": "AZQ", "amman_zarqa": "AMZ"}


# ---------------------------------------------------------------------------
# أدوات هندسية محلية (بلا اعتماديات)
# ---------------------------------------------------------------------------

def _point_in_ring(lon, lat, ring):
    """ray casting — هل النقطة داخل حلقة مضلع."""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and \
           (lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def _point_in_geom(lon, lat, geom):
    """دعم Polygon وMultiPolygon (الحلقة الخارجية فقط — كافٍ لأحواض تقريبية)."""
    if geom["type"] == "Polygon":
        return _point_in_ring(lon, lat, geom["coordinates"][0])
    if geom["type"] == "MultiPolygon":
        return any(_point_in_ring(lon, lat, poly[0]) for poly in geom["coordinates"])
    return False


def _pearson(xs, ys):
    """ارتباط Pearson — يتجاهل الأزواج الناقصة."""
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 6:
        return 0.0
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pairs)
    sxx = sum((p[0] - mx) ** 2 for p in pairs)
    syy = sum((p[1] - my) ** 2 for p in pairs)
    if sxx <= 0 or syy <= 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def _centroid(geom):
    """مركز تقريبي (متوسط رؤوس الحلقة الخارجية) — كافٍ للعرض."""
    ring = geom["coordinates"][0] if geom["type"] == "Polygon" \
        else geom["coordinates"][0][0]
    lon = sum(p[0] for p in ring) / len(ring)
    lat = sum(p[1] for p in ring) / len(ring)
    return [round(lon, 5), round(lat, 5)]


def _months_range(start_ym, n):
    y, m = int(start_ym[:4]), int(start_ym[5:7])
    out = []
    for i in range(n):
        yy, mm = y + (m - 1 + i) // 12, (m - 1 + i) % 12 + 1
        out.append(f"{yy:04d}-{mm:02d}")
    return out


# ---------------------------------------------------------------------------
# جلب السلاسل الشهرية من GEE (NDVI + CHIRPS + SMAP)
# ---------------------------------------------------------------------------

def fetch_monthly_series(features, aoi):
    """لكل مضلع: 36 شهراً NDVI+CHIRPS، وآخر 12 شهراً SMAP sm_rootzone.

    يرجع dict: fid → {"ndvi_series": [...], "sm_rootzone": [...]}
    """
    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"fid": i})
        for i, f in enumerate(features)])

    months = _months_range(C.NDVI_SERIES_START, C.NDVI_SERIES_MONTHS)
    smap_months = set(months[-C.SMAP_MONTHS:])
    series = {i: {"ndvi_series": [], "sm_rootzone": []} for i in range(len(features))}

    for ym in months:
        y, m = int(ym[:4]), int(ym[5:7])
        start = ee.Date.fromYMD(y, m, 1)
        end = start.advance(1, "month")

        ndvi = monthly_indices(aoi, y, m).select("NDVI")
        chirps = (ee.ImageCollection(C.CHIRPS_DAILY)
                  .filterDate(start, end).sum().rename("chirps_mm"))
        img = ndvi.addBands(chirps)
        if ym in smap_months:
            smap = (ee.ImageCollection(C.SMAP).select(C.SMAP_BAND)
                    .filterDate(start, end).mean().rename("smap_rz"))
            img = img.addBands(smap)

        rr = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=20)
        info = rr.getInfo()
        for feat in info["features"]:
            p = feat["properties"]
            fid = p["fid"]
            ndvi_v = p.get("NDVI")
            rain_v = p.get("chirps_mm")
            series[fid]["ndvi_series"].append({
                "month": ym,
                "ndvi": round(ndvi_v, 3) if ndvi_v is not None else None,
                "chirps_mm": round(rain_v, 1) if rain_v is not None else 0.0,
            })
            if ym in smap_months:
                sm = p.get("smap_rz")
                series[fid]["sm_rootzone"].append(
                    round(sm, 3) if sm is not None else None)
        print(f"  جُلبت سلاسل شهر {ym}")

    return series


# ---------------------------------------------------------------------------
# الدرجة
# ---------------------------------------------------------------------------

def _percentile(values, pct):
    if not values:
        return 1.0
    vs = sorted(values)
    k = (len(vs) - 1) * pct / 100.0
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return vs[lo]
    return vs[lo] + (vs[hi] - vs[lo]) * (k - lo)


def score_feature(props, persistence_months, anti_phase, inside_basin, area_p95):
    """يطبق صيغة CONTRACTS §3 ويرجع (score, breakdown, tier)."""
    ipb = 1.0 if inside_basin else 0.0
    new = 1.0 if (props.get("first_seen_year") or 0) >= C.FLAG_NEW_YEAR else 0.0
    pers = max(0.0, min(1.0, persistence_months / 12.0))
    area = max(0.0, min(1.0, (props.get("area_ha") or 0.0) / max(area_p95, 1e-9)))
    exp = max(0.0, min(1.0, (props.get("expansion_rate") or 0.0) / C.P4_EXP_NORM_CAP))

    breakdown = {
        "inside_protected_basin": round(C.P4_W_BASIN * ipb, 1),
        "new_after_closure": round(C.P4_W_NEW * new, 1),
        "persistence": round(C.P4_W_PERSISTENCE * pers, 1),
        "area": round(C.P4_W_AREA * area, 1),
        "expansion": round(C.P4_W_EXPANSION * exp, 1),
    }
    score = int(round(sum(breakdown.values())))
    tier = "red" if score >= C.TIER_RED else ("orange" if score >= C.TIER_ORANGE else "green")
    return score, breakdown, tier, anti_phase


# ---------------------------------------------------------------------------
# التدفق الرئيسي
# ---------------------------------------------------------------------------

def load_fields(args):
    """يقرأ مضلعات P3 من ملف GeoJSON محلي أو من Asset."""
    if args.fields_geojson:
        with open(args.fields_geojson, encoding="utf-8") as fh:
            return json.load(fh)["features"]
    info = ee.FeatureCollection(args.fields_asset).getInfo()
    return info["features"]


def load_basin_geom(basin_id="azraq"):
    """مضلع الحوض من data/demo/basins.geojson (لخاصية inside_protected_basin)."""
    if not os.path.exists(C.BASINS_GEOJSON):
        return None
    with open(C.BASINS_GEOJSON, encoding="utf-8") as fh:
        gj = json.load(fh)
    for f in gj.get("features", []):
        if f.get("properties", {}).get("id") == basin_id:
            return f["geometry"]
    return None


def main():
    ap = argparse.ArgumentParser(description="P4 — درجات الاشتباه + GeoJSON نهائي")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--fields-geojson", type=str, help="ناتج P3 المنزَّل من Drive")
    src.add_argument("--fields-asset", type=str, help="ناتج P3 كـ Asset")
    ap.add_argument("--basin", type=str, default="azraq")
    ap.add_argument("--national", action="store_true")
    ap.add_argument("--out", type=str, default=C.OUT_FIELDS)
    args = ap.parse_args()

    ee.Initialize(project=C.EE_PROJECT)
    C.ensure_out_dirs()

    bbox = C.AOI_JORDAN_BBOX if args.national else C.AOI_AZRAQ_BBOX
    aoi = ee.Geometry.Rectangle(bbox)

    features = load_fields(args)
    print(f"عدد المضلعات: {len(features)}")
    if not features:
        raise SystemExit("لا مضلعات — تأكد من ناتج P3.")

    basin_geom = load_basin_geom(args.basin)
    if basin_geom is None:
        print("تحذير: مضلع الحوض غير متاح — يُستخدم bbox الأزرق كبديل لـ inside_protected_basin.")

    # سلاسل NDVI/CHIRPS/SMAP لكل مضلع (المكوّن الأبطأ — 36 نداء)
    series = fetch_monthly_series(features, aoi)

    areas = [f["properties"].get("area_ha") or 0.0 for f in features]
    area_p95 = _percentile(areas, 95)
    prefix = _ID_PREFIX.get(args.basin, "JOR")

    out_features = []
    for i, f in enumerate(features):
        props = f["properties"]
        s = series[i]
        ndvi_vals = [pt["ndvi"] for pt in s["ndvi_series"]]
        rain_vals = [pt["chirps_mm"] for pt in s["ndvi_series"]]

        # persistence: أشهر النشاط (NDVI ≥ عتبة) في آخر 12 شهراً
        last12 = [v for v in ndvi_vals[-12:] if v is not None]
        persistence = sum(1 for v in last12 if v >= C.PERSIST_NDVI_T)

        # بصمة الريّ الزمنية: r سالب (أخضر بلا مطر) → درجة قرب 1
        r = _pearson(ndvi_vals, rain_vals)
        anti_phase = round(max(0.0, min(1.0, (1.0 - r) / 2.0)), 2)

        cen = _centroid(f["geometry"])
        inside = (_point_in_geom(cen[0], cen[1], basin_geom)
                  if basin_geom is not None else
                  (C.AOI_AZRAQ_BBOX[0] <= cen[0] <= C.AOI_AZRAQ_BBOX[2]
                   and C.AOI_AZRAQ_BBOX[1] <= cen[1] <= C.AOI_AZRAQ_BBOX[3]))

        score, breakdown, tier, anti_phase = score_feature(
            props, persistence, anti_phase, inside, area_p95)

        area_ha = round(props.get("area_ha") or 0.0, 1)
        out_features.append({
            "type": "Feature",
            "geometry": f["geometry"],
            "properties": {
                # مطابق حرفياً لمخطط CONTRACTS §2.1
                "id": f"{prefix}-{i:04d}",
                "basin_id": args.basin if inside else "out_of_basin",
                "area_ha": area_ha,
                "first_seen_year": int(props.get("first_seen_year") or 0),
                "flag": props.get("flag") or "STABLE",
                "expansion_rate": round(props.get("expansion_rate") or 0.0, 3),
                "persistence_months": persistence,
                "anti_phase_score": anti_phase,
                "score": score,
                "score_breakdown": breakdown,
                "tier": tier,
                "est_m3_low": int(round(area_ha * C.METHOD_A_M3_PER_HA[0])),   # Method A
                "est_m3_high": int(round(area_ha * C.METHOD_A_M3_PER_HA[1])),
                "status": "new",
                "centroid": cen,
                "ndvi_series": s["ndvi_series"],
                "sm_rootzone": s["sm_rootzone"],
                "is_demo": False,   # ناتج pipeline حقيقي — يستبدل ملف demo
            },
        })

    # الترتيب بالدرجة + rank (يستهلكه طابور التفتيش وprecision@20)
    out_features.sort(key=lambda x: -x["properties"]["score"])
    for rank, feat in enumerate(out_features, start=1):
        feat["properties"]["rank"] = rank

    collection = {"type": "FeatureCollection",
                  "name": "mizan_suspect_fields",
                  "features": out_features}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(collection, fh, ensure_ascii=False)

    reds = sum(1 for f in out_features if f["properties"]["tier"] == "red")
    print(f"كُتب {args.out}: {len(out_features)} مضلعاً ({reds} 🔴) — "
          f"p95(area)={area_p95:.1f} هكتار.")
    print("يستبدل data/demo/fields.geojson (انسخه إلى web/public/data/ بعد المراجعة).")


if __name__ == "__main__":
    main()
