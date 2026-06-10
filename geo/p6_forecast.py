# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/p6_forecast.py  (P6 — التنبّؤ)
يعمل **محلياً** على سلسلة CSV/JSON (ناتج p6_grace.py أو data/demo/tws_series.json):

  • النموذج: Prophet إن كان مثبّتاً، وإلا fallback موثَّق:
    انحدار خطي + توافقيات سنوية (numpy lstsq) بفترات ثقة من تغاير المعاملات.
  • Backtest بحجب آخر 24 شهراً → MAE (مراجعة — يُعرض بجانب المنحنى).
  • استقراء مناسيب الآبار (الأزرق −20م منذ 2000، ~−1.1م/سنة — ملحق أ) بفترة ثقة
    → **نطاق سنوات حرج لا نقطة** (مراجعة #15: العتبة الحرجة على الآبار لا على TWS).

قاعدة الصياغة: تنبّؤ GRACE مؤشر **إقليمي مساند** — العتبة الفعلية على مناسيب الآبار.
الإخراج: geo/outputs/forecast.json — مطابق لبنية data/demo/forecast.json.

أمثلة:
  python p6_forecast.py --input ../data/demo/tws_series.json     # اختبار على الديمو
  python p6_forecast.py --input outputs/tws_series.json          # السلسلة الحقيقية
"""

import argparse
import csv
import json
import math

import numpy as np

import config as C


# ---------------------------------------------------------------------------
# تحميل السلسلة
# ---------------------------------------------------------------------------

def _ym_to_index(ym):
    """'YYYY-MM' → عدد الأشهر منذ 2000-01 (محور زمني تقويمي يحترم الفجوات)."""
    return (int(ym[:4]) - 2000) * 12 + int(ym[5:7]) - 1


def _index_to_ym(idx):
    return f"{2000 + idx // 12:04d}-{idx % 12 + 1:02d}"


def load_series(path, column="auto"):
    """يقرأ JSON (بنية tws_series.json) أو CSV → (months_idx, values, label, is_demo)."""
    if path.lower().endswith(".csv"):
        with open(path, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        is_demo = False
    else:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        rows = doc["series"]
        is_demo = bool(doc.get("is_demo", False))

    col = column
    if col == "auto":
        # نفضّل GWS (التفكيك TWS−SM) إن كانت متاحة لمعظم السلسلة
        n_gws = sum(1 for r in rows if r.get("gws_cm") not in (None, ""))
        col = "gws_cm" if n_gws >= 0.6 * len(rows) else "tws_cm"

    t, y = [], []
    for r in sorted(rows, key=lambda x: x["month"]):
        v = r.get(col)
        if v in (None, ""):
            continue
        t.append(_ym_to_index(r["month"]))
        y.append(float(v))
    return np.array(t, dtype=float), np.array(y, dtype=float), col, is_demo


# ---------------------------------------------------------------------------
# النموذج الاحتياطي: خطي + توافقيات سنوية (numpy)
# ---------------------------------------------------------------------------

def _design(t):
    """مصفوفة التصميم: ثابت + اتجاه + توافقيتان سنويتان."""
    w = 2.0 * math.pi / 12.0
    return np.column_stack([
        np.ones_like(t), t,
        np.sin(w * t), np.cos(w * t),
        np.sin(2 * w * t), np.cos(2 * w * t),
    ])


class HarmonicTrendModel:
    """انحدار OLS بفترات تنبّؤ من تغاير المعاملات — fallback موثَّق لـ Prophet."""

    name = "linear_trend_plus_annual_harmonics (numpy OLS fallback)"

    def fit(self, t, y):
        X = _design(t)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        dof = max(len(y) - X.shape[1], 1)
        sigma2 = float(resid @ resid) / dof
        self.beta = beta
        self.sigma2 = sigma2
        self.xtx_inv = np.linalg.pinv(X.T @ X)
        return self

    def predict(self, t_new):
        X = _design(np.asarray(t_new, dtype=float))
        yhat = X @ self.beta
        # تباين التنبّؤ = ضوضاء + ارتياب المعاملات (يتسع مع البعد عن العينة)
        var = self.sigma2 * (1.0 + np.einsum("ij,jk,ik->i", X, self.xtx_inv, X))
        half = 1.96 * np.sqrt(var)
        return yhat, yhat - half, yhat + half


def _try_prophet():
    try:
        from prophet import Prophet  # noqa: F401
        return Prophet
    except Exception:
        return None


class ProphetModel:
    """غلاف Prophet بواجهة fit/predict نفسها."""

    name = "prophet"

    def __init__(self, prophet_cls):
        self._cls = prophet_cls

    def fit(self, t, y):
        import pandas as pd
        df = pd.DataFrame({
            "ds": [f"{_index_to_ym(int(i))}-01" for i in t],
            "y": y,
        })
        df["ds"] = pd.to_datetime(df["ds"])
        self.model = self._cls(yearly_seasonality=True,
                               weekly_seasonality=False,
                               daily_seasonality=False)
        self.model.fit(df)
        return self

    def predict(self, t_new):
        import pandas as pd
        df = pd.DataFrame({"ds": pd.to_datetime(
            [f"{_index_to_ym(int(i))}-01" for i in t_new])})
        out = self.model.predict(df)
        return (out["yhat"].to_numpy(),
                out["yhat_lower"].to_numpy(),
                out["yhat_upper"].to_numpy())


def make_model():
    prophet_cls = _try_prophet()
    if prophet_cls is not None:
        return ProphetModel(prophet_cls)
    print("Prophet غير مثبّت — استخدام fallback الموثَّق (اتجاه خطي + توافقيات سنوية).")
    return HarmonicTrendModel()


# ---------------------------------------------------------------------------
# Backtest + التنبّؤ + استقراء الآبار
# ---------------------------------------------------------------------------

def backtest(t, y, holdout=C.BACKTEST_HOLDOUT_MONTHS):
    """حجب آخر `holdout` شهراً → MAE على المحجوب."""
    if len(y) <= holdout + 24:
        return None
    model = make_model().fit(t[:-holdout], y[:-holdout])
    yhat, _, _ = model.predict(t[-holdout:])
    return float(np.mean(np.abs(yhat - y[-holdout:])))


def forecast_series(t, y, horizon=C.FORECAST_HORIZON_MONTHS):
    model = make_model().fit(t, y)
    last = int(t[-1])
    t_new = np.arange(last + 1, last + 1 + horizon, dtype=float)
    yhat, lo, hi = model.predict(t_new)
    series = [{
        "month": _index_to_ym(int(i)),
        "yhat": round(float(v), 2),
        "lo": round(float(l), 2),
        "hi": round(float(h), 2),
    } for i, v, l, h in zip(t_new, yhat, lo, hi)]
    return series, model.name


def well_level_extrapolation():
    """العتبة الحرجة الفعلية على مناسيب الآبار (ملحق أ) — نطاق سنوات بفترة ثقة."""
    rate = abs(C.WELL_RATE_M_PER_YR)
    unc = C.WELL_RATE_UNCERT
    extra = abs(C.WELL_THRESHOLD_EXTRA_M)
    # معدل أسرع → يبلغ العتبة أبكر (حد النطاق الأدنى)
    year_low = C.WELL_BASE_YEAR + extra / (rate + unc)
    year_high = C.WELL_BASE_YEAR + extra / max(rate - unc, 1e-6)
    return {
        "drop_2000_2017_m": C.WELL_DROP_2000_2017_M,
        "rate_m_per_yr": C.WELL_RATE_M_PER_YR,
        "critical_year_low": int(round(year_low)),
        "critical_year_high": int(round(year_high)),
        "threshold_note_ar": "عتبة توضيحية: عمق ضخ اقتصادي إضافي −15م من منسوب 2017",
        "threshold_note_en": "Illustrative threshold: additional -15m economic pumping depth from 2017 level",
        "source_note_ar": ("المنسوب والاتجاه من قياسات آبار الوزارة (ملحق أ)؛ "
                           f"النطاق من ارتياب المعدل ±{unc} م/سنة"),
    }


def main():
    ap = argparse.ArgumentParser(description="P6 — Prophet/fallback + العتبة الحرجة")
    ap.add_argument("--input", type=str, default=C.DEMO_TWS_JSON,
                    help="tws_series.json أو CSV من p6_grace")
    ap.add_argument("--column", choices=["auto", "tws_cm", "gws_cm"], default="auto")
    ap.add_argument("--horizon", type=int, default=C.FORECAST_HORIZON_MONTHS)
    ap.add_argument("--out", type=str, default=C.OUT_FORECAST)
    args = ap.parse_args()

    C.ensure_out_dirs()
    t, y, col, src_is_demo = load_series(args.input, args.column)
    print(f"السلسلة: {len(y)} شهراً ({_index_to_ym(int(t[0]))} → {_index_to_ym(int(t[-1]))}) · العمود: {col}"
          + (" · المصدر بيانات تجريبية (is_demo)" if src_is_demo else ""))

    mae = backtest(t, y)
    series, model_name = forecast_series(t, y, args.horizon)

    doc = {
        "basin_id": "azraq",
        "grace_forecast": {
            "label_ar": "تنبّؤ على منحنى GRACE للمنطقة الشرقية/الأردن — مؤشر إقليمي مساند",
            "model": model_name,
            "column": col,
            "series": series,
            "backtest_mae_cm": round(mae, 2) if mae is not None else None,
            "backtest_note_ar": f"MAE بحجب آخر {C.BACKTEST_HOLDOUT_MONTHS} شهراً من السلسلة",
        },
        "well_level": well_level_extrapolation(),
        # إن كان المصدر demo فالناتج demo — لا mock كحقيقي أبداً
        "is_demo": bool(src_is_demo),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)

    wl = doc["well_level"]
    print(f"كُتب {args.out}")
    print(f"Backtest MAE: {doc['grace_forecast']['backtest_mae_cm']} سم · النموذج: {model_name}")
    print(f"النطاق الحرج (مناسيب الآبار): {wl['critical_year_low']}–{wl['critical_year_high']}")


if __name__ == "__main__":
    main()
