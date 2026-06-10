# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/p7_validate.py  (P7 — سلاح المصداقية، بالإصلاح الكامل)
يقرأ مواقع الإنفاذ من data/demo/validation.json + مضلعات القناع (fields.geojson) ويحسب:

  • تطابق حالات (case-study concordance) — **لا precision/recall** على عيّنة إخبارية منحازة.
  • عتبة معلَنة سلفاً: الموقع "تطابق" إذا وقع ضمن ≤5كم من مضلع 🔴.
  • مواقع الغور (الكفرين/سويمة…) تُستبعد **بشفافية** مع سبب الاستبعاد —
    غور مروي بمياه سطحية، منطق «أخضر+صفر مطر» لا ينطبق.
  • lift/enrichment (null model): (نسبة الالتقاط) ÷ (نسبة المساحة الحمراء من AOI)
    — الجواب على تهمة «لوّنتم كل الخريطة».
  • precision@20 للطابور (proxy بالقرب من مواقع الإنفاذ — يُستبدل برقم التفتيش الفعلي).
  • خيار --mini-aois: يولّد bboxes حول المواقع داخل المنهجية لتشغيل p2_mask عليها
    (mini-AOIs داخل المنهجية — أو التشغيل الوطني 100م كخيار أقوى).

يعمل محلياً بلا GEE. الإخراج: geo/outputs/validation.json (بنية CONTRACTS §2.5).

أمثلة:
  python p7_validate.py --fields ../data/demo/fields.geojson
  python p7_validate.py --fields outputs/fields.geojson --mini-aois
"""

import argparse
import json
import math

import config as C

KM_PER_DEG_LAT = 110.574


def _km_xy(lon, lat, lon0, lat0):
    """إسقاط متساوي المستطيلات محلي → كم (دقيق كفاية لمسافات ≤ عشرات الكم)."""
    kx = 111.320 * math.cos(math.radians(lat0))
    return (lon - lon0) * kx, (lat - lat0) * KM_PER_DEG_LAT


def _pt_seg_dist(px, py, ax, ay, bx, by):
    """مسافة نقطة عن قطعة مستقيمة (كم)."""
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _point_in_ring(lon, lat, ring):
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


def dist_to_polygon_km(lon, lat, geom):
    """مسافة نقطة عن مضلع بالكم (0 إن كانت داخله) — Polygon/MultiPolygon."""
    rings = []
    if geom["type"] == "Polygon":
        rings = [geom["coordinates"][0]]
        if _point_in_ring(lon, lat, geom["coordinates"][0]):
            return 0.0
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            rings.append(poly[0])
            if _point_in_ring(lon, lat, poly[0]):
                return 0.0
    best = float("inf")
    for ring in rings:
        for i in range(len(ring) - 1):
            ax, ay = _km_xy(ring[i][0], ring[i][1], lon, lat)
            bx, by = _km_xy(ring[i + 1][0], ring[i + 1][1], lon, lat)
            best = min(best, _pt_seg_dist(0.0, 0.0, ax, ay, bx, by))
    return best


def aoi_area_ha(bbox):
    """مساحة bbox بالهكتار (تقريب متساوي المستطيلات)."""
    lat_mid = (bbox[1] + bbox[3]) / 2.0
    w_km = (bbox[2] - bbox[0]) * 111.320 * math.cos(math.radians(lat_mid))
    h_km = (bbox[3] - bbox[1]) * KM_PER_DEG_LAT
    return w_km * h_km * 100.0


def main():
    ap = argparse.ArgumentParser(description="P7 — التحقّق (تطابق حالات + lift)")
    ap.add_argument("--fields", type=str, default=C.DEMO_FIELDS_GEOJSON,
                    help="GeoJSON المضلعات (ناتج P4 أو demo)")
    ap.add_argument("--validation", type=str, default=C.VALIDATION_JSON)
    ap.add_argument("--threshold-km", type=float, default=C.P7_THRESHOLD_KM)
    ap.add_argument("--national", action="store_true",
                    help="حساب نسبة المساحة الحمراء على bbox وطني (تشغيل وطني)")
    ap.add_argument("--mini-aois", action="store_true",
                    help="توليد bboxes حول المواقع داخل المنهجية لتشغيل p2_mask")
    ap.add_argument("--out", type=str, default=C.OUT_VALIDATION)
    args = ap.parse_args()

    C.ensure_out_dirs()

    with open(args.validation, encoding="utf-8") as fh:
        vdoc = json.load(fh)
    with open(args.fields, encoding="utf-8") as fh:
        fdoc = json.load(fh)

    feats = fdoc["features"]
    fields_demo = any(f["properties"].get("is_demo") for f in feats)
    reds = [f for f in feats if f["properties"].get("tier") == "red"]

    print("=" * 72)
    print(f"P7 — التحقّق · عتبة معلَنة سلفاً: ≤{args.threshold_km:.0f} كم من مضلع 🔴")
    print(f"المضلعات: {len(feats)} (منها {len(reds)} 🔴)"
          + ("  [بيانات تجريبية — demo]" if fields_demo else ""))
    print("=" * 72)

    sites_out, in_scope, hits = [], 0, 0
    mini_aois = []
    for site in vdoc["sites"]:
        s = dict(site)
        if s.get("scope") == "out_of_methodology":
            # استبعاد شفاف — يُعرض السبب لا يُخفى الموقع
            s["hit"] = None
            print(f"  [خارج المنهجية] {s['name_ar']}: {s.get('out_reason_ar', '—')}")
        else:
            in_scope += 1
            dmin = min((dist_to_polygon_km(s["lon"], s["lat"], f["geometry"])
                        for f in reds), default=float("inf"))
            s["nearest_red_km"] = round(dmin, 1) if dmin != float("inf") else None
            s["hit"] = bool(dmin <= args.threshold_km)
            hits += 1 if s["hit"] else 0
            mark = "تطابق ✓" if s["hit"] else "لا تطابق ✗"
            print(f"  [داخل المنهجية] {s['name_ar']}: أقرب 🔴 على بعد "
                  f"{s['nearest_red_km']} كم → {mark}")
            if args.mini_aois:
                d = C.P7_MINI_AOI_DEG
                mini_aois.append({
                    "site_id": s["id"],
                    "bbox": [round(s["lon"] - d, 3), round(s["lat"] - d, 3),
                             round(s["lon"] + d, 3), round(s["lat"] + d, 3)],
                })
        sites_out.append(s)

    # null model: نسبة الالتقاط ÷ نسبة المساحة الحمراء من الـ AOI
    bbox = C.AOI_JORDAN_BBOX if args.national else C.AOI_AZRAQ_BBOX
    red_ha = sum(f["properties"].get("area_ha") or 0.0 for f in reds)
    red_area_pct = 100.0 * red_ha / aoi_area_ha(bbox)
    capture = hits / in_scope if in_scope else 0.0
    lift = (capture / (red_area_pct / 100.0)) if red_area_pct > 0 else None

    # precision@20 — proxy بالقرب من مواقع الإنفاذ داخل المنهجية
    # (الرقم الحقيقي = نسبة المؤكَّد من أعلى 20 بعد التفتيش — يُستبدل يوم الحدث)
    in_sites = [s for s in sites_out if s.get("scope") == "in_methodology"]
    top = sorted(feats, key=lambda f: -(f["properties"].get("score") or 0))[:C.P7_TOP_K]
    p_at_20 = None
    if in_sites and top:
        supported = 0
        for f in top:
            d = min(dist_to_polygon_km(s["lon"], s["lat"], f["geometry"])
                    for s in in_sites)
            supported += 1 if d <= args.threshold_km else 0
        p_at_20 = round(supported / len(top), 2)

    out = {
        "threshold_km": args.threshold_km,
        "threshold_note_ar": f"الموقع يُحتسب تطابقاً إذا وقع ضمن ≤{args.threshold_km:.0f}كم من مضلع 🔴 — عتبة معلَنة سلفاً",
        "threshold_note_en": f"A site counts as a hit if within <={args.threshold_km:.0f}km of a red polygon — pre-declared threshold",
        "sites": sites_out,
        "stats": {
            "in_scope": in_scope,
            "hits": hits,
            "red_area_pct": round(red_area_pct, 2),
            "lift": round(lift, 1) if lift is not None else None,
            "lift_note_ar": "(نسبة الالتقاط ÷ نسبة المساحة الحمراء) — null model ضد تهمة «لوّنتم كل الخريطة»",
            "precision_at_20": p_at_20,
            "precision_note_ar": "proxy بقرب مواقع الإنفاذ — يُستبدل بنسبة المؤكَّد من التفتيش يوم الحدث",
            "framing_ar": "تطابق حالات (case-study concordance) — لا precision/recall إحصائي على عيّنة إخبارية منحازة",
            "framing_en": "Case-study concordance — not statistical precision/recall on a biased news sample",
            "mini_aoi_note_ar": "المواقع داخل المنهجية تُفحص بقناع mini-AOI حول كل موقع (التشغيل الوطني 100م الخيار الأقوى)",
        },
        # demo يبقى demo — لا mock كحقيقي أبداً
        "is_demo": bool(fields_demo or vdoc.get("is_demo", False)),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    print("-" * 72)
    print(f"النتيجة: {hits} من {in_scope} داخل المنهجية ضمن ≤{args.threshold_km:.0f}كم من 🔴 · "
          f"مساحة حمراء {red_area_pct:.2f}% · lift = {out['stats']['lift']} · "
          f"precision@20 (proxy) = {p_at_20}")
    print(f"كُتب {args.out}")

    if args.mini_aois and mini_aois:
        with open(C.OUT_MINI_AOIS, "w", encoding="utf-8") as fh:
            json.dump(mini_aois, fh, ensure_ascii=False, indent=2)
        print(f"كُتب {C.OUT_MINI_AOIS} — شغّل لكل bbox:")
        for m in mini_aois:
            b = m["bbox"]
            print(f"  python p2_mask.py --year 2025 --bbox {b[0]},{b[1]},{b[2]},{b[3]}  # {m['site_id']}")


if __name__ == "__main__":
    main()
