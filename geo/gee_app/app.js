/**
 * ميزان MIZAN — GEE App (خطة B لبوابة H20: رابط يعمل بلا أي بنية تحتية)
 * يُلصق كاملاً في GEE Code Editor ثم: Apps → Publish → New App.
 *
 * الطبقات: قناع الريّ v1 (P2) + مضلعات الدرجات (P4 إن توفر الـ Asset) + legend ثنائي اللغة.
 * قاعدة GRACE: هذا التطبيق يعرض كشف الحقول من Sentinel-2 حصراً — لا ادعاء حقلي من الجاذبية.
 */

// ------------------------- إعدادات -------------------------
var YEAR = 2025;                                   // سنة القناع
var NDVI_T = 0.35;                                 // عتبة P2 (بدائل H6: 0.30/0.40)
var RAIN_MM = 10;                                  // sum(CHIRPS, حزيران-آب) < 10مم
var AOI = ee.Geometry.Rectangle([36.45, 31.55, 37.30, 32.25]);  // bbox الأزرق
// Asset مضلعات P4 (حدّثه بعد تصدير p3/p4 — إن تُرك فارغاً تُعرض طبقة القناع فقط)
var FIELDS_ASSET = '';   // مثال: 'projects/mizan-vcoders/assets/mizan/p3/mizan_p3_fields_azraq_2025'

// ------------------------- قناع الريّ v1 (P2) -------------------------
// S2 SR مقنّع سحابياً عبر s2cloudless
function s2Masked(start, end) {
  var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(AOI).filterDate(start, end);
  var prob = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
      .filterBounds(AOI).filterDate(start, end);
  var joined = ee.Join.saveFirst('cp').apply(s2, prob,
      ee.Filter.equals({leftField: 'system:index', rightField: 'system:index'}));
  return ee.ImageCollection(joined).map(function (img) {
    img = ee.Image(img);
    var cp = ee.Image(img.get('cp')).select('probability');
    var scl = img.select('SCL');
    var good = cp.lt(40).and(scl.neq(3)).and(scl.neq(8))
        .and(scl.neq(9)).and(scl.neq(10));
    return img.select(['B2', 'B3', 'B4', 'B8', 'B11'])
        .divide(10000).updateMask(good)
        .copyProperties(img, ['system:time_start']);
  });
}

var summer = s2Masked(YEAR + '-06-01', YEAR + '-09-01');
var ndvi = summer.map(function (i) {
  return ee.Image(i).normalizedDifference(['B8', 'B4']).rename('NDVI');
}).mean();

var rain = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
    .filterDate(YEAR + '-06-01', YEAR + '-09-01').sum();

// WorldCover — الفلتر الموسَّع {شجري 10، شجيري 20، محاصيل 40، جرداء 60} (الزيتون)
var wc = ee.Image(ee.ImageCollection('ESA/WorldCover/v200').first()).select('Map');
var wcOk = wc.remap([10, 20, 40, 60], [1, 1, 1, 1], 0);

// خارج أي امتداد مائي تاريخي
var jrc = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('max_extent');

var mask = ndvi.gte(NDVI_T)
    .and(rain.lt(RAIN_MM))
    .and(wcOk)
    .and(jrc.unmask(0).eq(0))
    .selfMask();

// ------------------------- الخريطة -------------------------
Map.setOptions('SATELLITE');
Map.centerObject(AOI, 10);
Map.addLayer(ndvi.clip(AOI), {min: 0, max: 0.6, palette: ['#3b2f1e', '#e6edf7', '#10B981']},
    'NDVI صيفي · Summer NDVI', false);
Map.addLayer(mask.clip(AOI), {palette: ['#2DD4BF']},
    'قناع الريّ v1 · Irrigation mask v1', true, 0.75);
Map.addLayer(ee.Image().paint(ee.FeatureCollection([ee.Feature(AOI)]), 0, 2),
    {palette: ['#38BDF8']}, 'حدود الدراسة · AOI');

// مضلعات الدرجات (إن صُدّر Asset من p3/p4)
if (FIELDS_ASSET !== '') {
  var fields = ee.FeatureCollection(FIELDS_ASSET);
  var styled = fields.map(function (f) {
    var score = ee.Number(f.get('score'));
    var color = ee.String(ee.Algorithms.If(score.gte(70), '#F43F5E',
        ee.Algorithms.If(score.gte(40), '#F59E0B', '#10B981')));
    return f.set('style', {color: color, fillColor: color.cat('33'), width: 2});
  });
  Map.addLayer(styled.style({styleProperty: 'style'}),
      {}, 'درجات الاشتباه · Suspicion scores');
}

// ------------------------- Legend ثنائي اللغة -------------------------
var panel = ui.Panel({
  style: {position: 'bottom-left', padding: '10px 14px',
          backgroundColor: '#0B1422', width: '280px'}
});
function label(txt, color, size, bold) {
  return ui.Label(txt, {color: color || '#E6EDF7', fontSize: size || '12px',
                        fontWeight: bold ? 'bold' : 'normal',
                        backgroundColor: '#0B1422', margin: '2px 0'});
}
function legendRow(color, txt) {
  var box = ui.Label('', {backgroundColor: color, padding: '6px',
                          margin: '3px 8px 3px 0'});
  return ui.Panel([box, label(txt)], ui.Panel.Layout.flow('horizontal'),
                  {backgroundColor: '#0B1422'});
}
panel.add(label('ميزان MIZAN — كشف الريّ المشبوه', '#2DD4BF', '15px', true));
panel.add(label('MIZAN — Suspicious irrigation detection', '#8FA3BF', '11px'));
panel.add(label('حوض الأزرق (مغلق قانونياً 1992) · Azraq basin', '#E6EDF7', '12px'));
panel.add(legendRow('#2DD4BF', 'قناع الريّ v1 · Irrigation mask v1'));
panel.add(legendRow('#F43F5E', 'اشتباه مرتفع ≥70 · High suspicion'));
panel.add(legendRow('#F59E0B', 'متوسط 40–69 · Medium'));
panel.add(legendRow('#10B981', 'منخفض <40 · Low'));
panel.add(label('القاعدة: أخضر في صيف بلا مطر (CHIRPS<10مم) = ضخّ جوفي',
                '#8FA3BF', '11px'));
panel.add(label('Green in a rainless summer = groundwater pumping', '#8FA3BF', '10px'));
panel.add(label('التحديد من Sentinel-2 حصراً — GRACE إشارة إقليمية ~300كم',
                '#8FA3BF', '10px'));
panel.add(label('Fields from Sentinel-2 only — GRACE is ~300km regional', '#8FA3BF', '9px'));
panel.add(label('مرشّحات لا اتهامات — المفتّش يقرر · Filters, not accusations',
                '#F59E0B', '10px'));
Map.add(panel);
