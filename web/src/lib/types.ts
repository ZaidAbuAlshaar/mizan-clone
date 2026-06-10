/** الأنواع المشتركة — مطابقة لعقود CONTRACTS.md §2 حرفياً */

export type Tier = "red" | "orange" | "green";
export type FieldStatus = "new" | "inspected" | "confirmed" | "cleared";
export type FieldFlag = "NEW" | "EXPANDING" | "STABLE";

export interface NdviPoint {
  month: string;
  ndvi: number;
  chirps_mm: number;
}

export interface ScoreBreakdown {
  inside_protected_basin: number;
  new_after_closure: number;
  persistence: number;
  area: number;
  expansion: number;
}

export interface FieldProps {
  id: string;
  basin_id: string;
  area_ha: number;
  first_seen_year: number;
  flag: FieldFlag;
  expansion_rate: number;
  persistence_months: number;
  anti_phase_score: number;
  /** مؤشر شذوذ AI (IsolationForest) 0..1 — مساند، لا يدخل في درجة P4 */
  ml_anomaly?: number;
  score: number;
  score_breakdown: ScoreBreakdown;
  tier: Tier;
  est_m3_low: number;
  est_m3_high: number;
  status: FieldStatus;
  centroid: [number, number];
  rank: number;
  cluster?: string;
  ndvi_series: NdviPoint[];
  sm_rootzone: number[];
  is_demo: boolean;
}

export interface FieldFeature {
  type: "Feature";
  geometry: GeoJSON.Polygon;
  properties: FieldProps;
}

export interface FieldsFC {
  type: "FeatureCollection";
  name?: string;
  features: FieldFeature[];
}

export interface BasinProps {
  id: string;
  name_ar: string;
  name_en: string;
  exploitation_pct: number | null;
  exploitation_source: string | null;
  closure_year: number | null;
  well_level_drop_m: number | null;
  status: "modeled" | "secondary" | "context";
  is_demo_geometry: boolean;
}

export interface BasinsFC {
  type: "FeatureCollection";
  features: { type: "Feature"; geometry: GeoJSON.Polygon; properties: BasinProps }[];
}

export interface TwsSeries {
  scope: string;
  label_ar: string;
  label_en: string;
  unit: string;
  resolution_note_ar: string;
  gap: [string, string];
  ends_at: string;
  series: { month: string; tws_cm: number | null; gws_cm: number | null }[];
  source?: string;
  is_real?: boolean;
  is_demo: boolean;
}

export interface Forecast {
  basin_id: string;
  grace_forecast: {
    label_ar: string;
    series: { month: string; yhat: number; lo: number; hi: number }[];
    backtest_mae_cm: number;
    backtest_note_ar: string;
  };
  well_level: {
    drop_2000_2017_m: number;
    rate_m_per_yr: number;
    critical_year_low: number;
    critical_year_high: number;
    threshold_note_ar: string;
    threshold_note_en: string;
    source_note_ar: string;
  };
  is_demo: boolean;
}

export interface ValidationSite {
  id: string;
  name_ar: string;
  name_en: string;
  lon: number;
  lat: number;
  date: string;
  detail_ar: string;
  detail_en: string;
  source: string;
  coords_note: string;
  scope: "in_methodology" | "out_of_methodology";
  out_reason_ar?: string | null;
  out_reason_en?: string | null;
  hit: boolean | null;
}

export interface ValidationData {
  threshold_km: number;
  threshold_note_ar: string;
  threshold_note_en: string;
  sites: ValidationSite[];
  stats: {
    in_scope: number;
    hits: number;
    red_area_pct: number;
    lift: number;
    lift_note_ar: string;
    precision_at_20: number;
    precision_note_ar: string;
    framing_ar: string;
    framing_en: string;
    mini_aoi_note_ar: string;
  };
  is_demo: boolean;
}

export interface ImpactData {
  detected_fields: number;
  detected_total_ha: number;
  detected_total_m3_low: number;
  detected_total_m3_mid: number;
  detected_total_m3_high: number;
  scenarios: { conservative: number; expected: number };
  scenario_note_ar: string;
  constants: {
    people_per_mcm: number;
    people_equation_note_ar: string;
    desal_usd_low: number;
    desal_usd_high: number;
    carrier_mcm: number;
    carrier_cost_usd_bn: number;
    overdraft_mcm: number;
    overdraft_vs_carrier_pct: number;
    manual_2023_24: { wells: number; mcm: number; usd_m_low: number; usd_m_high: number };
    wells_sealed_since_2013: number;
    avg_sealed_well_m3: number;
    avg_sealed_well_note_ar: string;
    scarcity_m3_capita: number;
    national_abstraction_pct: number;
    azraq_pct: number;
    amman_zarqa_pct: number;
  };
  is_demo: boolean;
}

export interface LedgerData {
  basin_id: string;
  title_ar: string;
  title_en: string;
  explain_ar: string;
  explain_en: string;
  left_scale: {
    label_ar: string;
    grace_regional_loss_mcm: number;
    recharge_mcm: number;
    total_demand_mcm: number;
  };
  right_scale: {
    label_ar: string;
    documented_abstraction_mcm: number;
    detected_fields_et_mcm: number;
  };
  unknown_deficit_mcm: number;
  method_note_ar: string;
  is_demo: boolean;
}

export interface TimeMachineData {
  years: Record<string, { fields_visible: number; total_ha: number; est_m3_mid: number }>;
  note_ar: string;
  is_demo: boolean;
}

export interface AlertItem {
  id: string;
  rank: number;
  score: number;
  tier: Tier;
  area_ha: number;
  first_seen_year: number;
  flag: FieldFlag;
  est_m3_low: number;
  est_m3_high: number;
  status: FieldStatus;
  centroid: [number, number];
}

export interface MetaData {
  data_mode: string;
  generated_at: string;
  generator_version: string;
  real_layers?: string[];
  demo_layers?: string[];
  note_ar: string;
  note_en: string;
}

export interface ClimateData {
  source: string;
  title_ar: string;
  title_en: string;
  note_ar: string;
  rain_proof: {
    mean_summer_mm: number;
    max_summer_mm: number;
    years: number;
    headline_ar: string;
    headline_en: string;
    implication_ar: string;
    implication_en: string;
  };
  annual_rain: Record<string, number>;
  series: { month: string; precip_mm: number; et_ref_mm: number; balance_mm: number; cum_deficit_mm: number }[];
  is_real: boolean;
  is_demo: boolean;
}

/** مخزون المياه الجوفية GLDAS (CLSM GRACE-DA) — عبر Google Earth Engine */
export interface GwsSeries {
  label_ar: string;
  label_en: string;
  region_note_ar: string;
  unit: string;
  series: { month: string; gws_mm: number }[];
  trend_mm_per_yr: number;
  months: number;
  source: string;
  is_real: boolean;
}

export interface NasaManifest {
  provider: string;
  basemap: { jordan: string; layer: string; bbox: [number, number, number, number]; date: string };
  time_machine: {
    years: Record<string, string>;
    layer: string;
    bbox: [number, number, number, number];
    /** ملصق المصدر للواجهة (مثل «Sentinel-2 · 20م») */
    label?: string;
  };
  ndvi: { "2016": string; "2024": string; layer: string };
  pivots: { disi: string; note_ar: string };
  /** قصاصات قبل/بعد الحقيقية لكل حقل (من fetch_s2_timemachine.py) */
  fields_thumbs?: { before_year: number; after_year: number; count: number };
  is_real: boolean;
}
