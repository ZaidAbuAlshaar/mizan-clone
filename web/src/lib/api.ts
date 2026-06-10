/**
 * طبقة البيانات — نمط fallback (فلسفة سلّم الخروج: الديمو لا يسقط أبداً)
 * 1) تجرّب API الحي (NEXT_PUBLIC_API_URL) بمهلة قصيرة
 * 2) تسقط على الملفات الساكنة /data/*.json (نسخة من data/demo)
 * تحديثات الحالة في الوضع الساكن تُحفظ في localStorage (موسومة محلية).
 */
import type {
  AlertItem, BasinsFC, ClimateData, FieldFeature, FieldsFC, FieldStatus, Forecast,
  GwsSeries, ImpactData, LedgerData, MetaData, NasaManifest, TimeMachineData, TwsSeries, ValidationData,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";
const API_TIMEOUT_MS = 1800;

export type DataSource = "api" | "static";
let lastSource: DataSource = "static";
export function getLastSource(): DataSource {
  return lastSource;
}

async function tryApi<T>(path: string): Promise<T | null> {
  if (!API_URL) return null;
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), API_TIMEOUT_MS);
    const res = await fetch(`${API_URL}${path}`, { signal: ctrl.signal, cache: "no-store" });
    clearTimeout(t);
    if (!res.ok) return null;
    lastSource = "api";
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

async function staticJson<T>(file: string): Promise<T> {
  // no-cache: يُعيد التحقق دائماً حتى تظهر البيانات المحدَّثة (لوحة بيانات لا أصول ثابتة)
  const res = await fetch(`/data/${file}`, { cache: "no-cache" });
  if (!res.ok) throw new Error(`static data missing: ${file}`);
  lastSource = "static";
  return (await res.json()) as T;
}

/** تراكب حالات الحقول المحلي (وضع static فقط) */
const LS_KEY = "mizan_status_overrides";
function readOverrides(): Record<string, FieldStatus> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) || "{}");
  } catch {
    return {};
  }
}
function writeOverride(id: string, status: FieldStatus) {
  const o = readOverrides();
  o[id] = status;
  localStorage.setItem(LS_KEY, JSON.stringify(o));
}

function applyOverrides(fc: FieldsFC): FieldsFC {
  const o = readOverrides();
  if (!Object.keys(o).length) return fc;
  return {
    ...fc,
    features: fc.features.map((f) =>
      o[f.properties.id]
        ? { ...f, properties: { ...f.properties, status: o[f.properties.id] } }
        : f,
    ),
  };
}

// ---------------------------------------------------------------- fetchers

export async function getFields(params?: {
  basin?: string; min_score?: number; status?: string; flag?: string;
}): Promise<FieldsFC> {
  const qs = new URLSearchParams();
  if (params?.basin) qs.set("basin", params.basin);
  if (params?.min_score != null) qs.set("min_score", String(params.min_score));
  if (params?.status) qs.set("status", params.status);
  if (params?.flag) qs.set("flag", params.flag);
  const fromApi = await tryApi<FieldsFC>(`/fields${qs.toString() ? `?${qs}` : ""}`);
  if (fromApi) return fromApi;
  let fc = await staticJson<FieldsFC>("fields.geojson");
  fc = applyOverrides(fc);
  let feats = fc.features;
  if (params?.basin) feats = feats.filter((f) => f.properties.basin_id === params.basin);
  if (params?.min_score != null) feats = feats.filter((f) => f.properties.score >= params.min_score!);
  if (params?.status) feats = feats.filter((f) => f.properties.status === params.status);
  if (params?.flag) feats = feats.filter((f) => f.properties.flag === params.flag);
  return { ...fc, features: feats };
}

export async function getField(id: string): Promise<FieldFeature | null> {
  const fromApi = await tryApi<FieldFeature>(`/fields/${id}`);
  if (fromApi) return fromApi;
  const fc = await getFields();
  return fc.features.find((f) => f.properties.id === id) || null;
}

const VALID_TRANSITIONS: Record<FieldStatus, FieldStatus[]> = {
  new: ["inspected"],
  inspected: ["confirmed", "cleared"],
  confirmed: [],
  cleared: [],
};

export function canTransition(from: FieldStatus, to: FieldStatus): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}

export async function patchFieldStatus(
  id: string, current: FieldStatus, next: FieldStatus,
): Promise<{ ok: boolean; source: DataSource }> {
  if (!canTransition(current, next)) return { ok: false, source: lastSource };
  if (API_URL) {
    try {
      const res = await fetch(`${API_URL}/fields/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: next }),
      });
      if (res.ok) return { ok: true, source: "api" };
    } catch {
      /* يسقط على المحلي */
    }
  }
  writeOverride(id, next);
  return { ok: true, source: "static" };
}

export async function getAlerts(): Promise<AlertItem[]> {
  const fromApi = await tryApi<{ alerts: AlertItem[] }>("/alerts");
  if (fromApi) return fromApi.alerts;
  const data = await staticJson<{ alerts: AlertItem[] }>("alerts.json");
  return data.alerts;
}

export async function getBasins(): Promise<BasinsFC> {
  return (await tryApi<BasinsFC>("/basins")) ?? staticJson<BasinsFC>("basins.geojson");
}

export async function getTws(): Promise<TwsSeries> {
  return (
    (await tryApi<TwsSeries>("/basins/azraq/tws")) ?? staticJson<TwsSeries>("tws_series.json")
  );
}

export async function getForecast(basin = "azraq"): Promise<Forecast> {
  return (
    (await tryApi<Forecast>(`/basins/${basin}/forecast`)) ?? staticJson<Forecast>("forecast.json")
  );
}

export async function getLedger(basin = "azraq"): Promise<LedgerData> {
  return (
    (await tryApi<LedgerData>(`/basins/${basin}/ledger`)) ?? staticJson<LedgerData>("ledger.json")
  );
}

export async function getValidation(): Promise<ValidationData> {
  return (await tryApi<ValidationData>("/validation")) ?? staticJson<ValidationData>("validation.json");
}

export async function getImpact(): Promise<ImpactData> {
  return (await tryApi<ImpactData>("/impact")) ?? staticJson<ImpactData>("impact.json");
}

export async function getTimeMachine(): Promise<TimeMachineData> {
  return (await tryApi<TimeMachineData>("/timemachine")) ?? staticJson<TimeMachineData>("timemachine.json");
}

export async function getMeta(): Promise<MetaData> {
  return (await tryApi<MetaData>("/meta")) ?? staticJson<MetaData>("meta.json");
}

/** meta مخزّنة (طلب واحد مشترك لكل الشارات) */
let _metaCache: Promise<MetaData> | null = null;
export function getMetaCached(): Promise<MetaData> {
  if (!_metaCache) _metaCache = getMeta();
  return _metaCache;
}

export async function getExclusions(): Promise<GeoJSON.FeatureCollection> {
  return staticJson<GeoJSON.FeatureCollection>("exclusions.geojson");
}

/** بيانات NASA الحقيقية — ملفات ساكنة (تُولّد من tools/fetch_nasa_data.py) */
export async function getClimate(): Promise<ClimateData | null> {
  try {
    return (await tryApi<ClimateData>("/climate")) ?? (await staticJson<ClimateData>("climate.json"));
  } catch {
    return null;
  }
}

export async function getNasa(): Promise<NasaManifest | null> {
  try {
    return (await tryApi<NasaManifest>("/nasa")) ?? (await staticJson<NasaManifest>("nasa.json"));
  } catch {
    return null;
  }
}

/** مخزون GLDAS الجوفي (Google Earth Engine) — ملف ساكن من geo/fetch_gldas_gws.py */
export async function getGws(): Promise<GwsSeries | null> {
  try {
    return await staticJson<GwsSeries>("gws_series.json");
  } catch {
    return null;
  }
}
