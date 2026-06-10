# -*- coding: utf-8 -*-
"""
ميزان MIZAN — anomaly scoring (تنفيذ بند «AI/analytics method» المعلن في plan.md §371)
=======================================================================================
Isolation Forest (scikit-learn) على القياسات الحقيقية للحقول الـ141 → مؤشر شذوذ 0..1.

**مؤشر مساند (supporting indicator) حصراً:**
  - لا يدخل في درجة P4 ولا يغيّر ترتيب الطابور (الصيغة الشفافة 35/25/15/12.5/12.5 تبقى القانون)
  - دوره: «هذا الحقل غريب عن أقرانه» — عين ثانية للمفتش فوق الدرجة القاعدية
  - حتمي بالكامل (random_state=42) — يعاد إنتاجه بالبايت

الميزات: المساحة · التوسّع · الاستمرارية · بصمة الريّ · سنة الظهور · إحصاءات NDVI الموسمية.
المخرج: data/real/fields.geojson (خاصية ml_anomaly مضافة) + data/real/ml_meta.json

تشغيل:  python tools/ml_anomaly.py
"""
import json
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

import numpy as np
from sklearn.ensemble import IsolationForest

HERE = os.path.dirname(__file__)
FIELDS = os.path.join(HERE, "..", "data", "real", "fields.geojson")
META_OUT = os.path.join(HERE, "..", "data", "real", "ml_meta.json")

FEATURE_NAMES = [
    "area_ha", "expansion_rate", "persistence_months", "anti_phase_score",
    "years_since_first_seen", "ndvi_mean", "ndvi_max", "ndvi_summer_mean", "ndvi_std",
]


def field_features(p):
    nd = [pt["ndvi"] for pt in p.get("ndvi_series", [])]
    summer = [pt["ndvi"] for pt in p.get("ndvi_series", []) if pt["month"][5:7] in ("06", "07", "08")]
    nd = nd or [0.0]
    summer = summer or nd
    return [
        float(p["area_ha"]),
        float(p["expansion_rate"]),
        float(p["persistence_months"]),
        float(p["anti_phase_score"]),
        float(2026 - p["first_seen_year"]),
        float(np.mean(nd)), float(np.max(nd)), float(np.mean(summer)), float(np.std(nd)),
    ]


def main():
    with open(FIELDS, encoding="utf-8") as f:
        fc = json.load(f)
    feats = fc["features"]
    X = np.array([field_features(ft["properties"]) for ft in feats])
    # توحيد مقاييس بسيط (z-score) كي لا تطغى المساحة على الميزات الصغيرة
    mu, sigma = X.mean(axis=0), X.std(axis=0)
    sigma[sigma == 0] = 1.0
    Xz = (X - mu) / sigma

    model = IsolationForest(n_estimators=300, contamination="auto", random_state=42)
    model.fit(Xz)
    raw = -model.score_samples(Xz)            # أعلى = أكثر شذوذاً
    a, b = float(raw.min()), float(raw.max())
    anomaly = (raw - a) / (b - a) if b > a else np.zeros_like(raw)

    for ft, s in zip(feats, anomaly):
        ft["properties"]["ml_anomaly"] = round(float(s), 3)

    with open(FIELDS, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, separators=(",", ":"))

    top = sorted(feats, key=lambda ft: -ft["properties"]["ml_anomaly"])[:5]
    meta = {
        "model": "IsolationForest (scikit-learn)",
        "n_estimators": 300,
        "random_state": 42,
        "features": FEATURE_NAMES,
        "n_fields": len(feats),
        "role_ar": "مؤشر مساند — لا يدخل في درجة P4 (plan.md §371: anomaly scoring)",
        "role_en": "Supporting indicator — does NOT affect the P4 score",
        "top_anomalies": [
            {"id": ft["properties"]["id"], "ml_anomaly": ft["properties"]["ml_anomaly"],
             "score": ft["properties"]["score"]} for ft in top
        ],
        "is_real": True,
    }
    with open(META_OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    print(f"  ✅ ml_anomaly أُضيف لـ{len(feats)} حقلاً (IsolationForest، حتمي)")
    print("  أعلى 5 شذوذاً:", ", ".join(f"{m['id']}={m['ml_anomaly']}" for m in meta["top_anomalies"]))


if __name__ == "__main__":
    main()
