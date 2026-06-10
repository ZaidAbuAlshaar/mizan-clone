# ميزان MIZAN — جالب صور NASA GIBS الحقيقية (real NASA imagery)
# صور أقمار حقيقية بلا مصادقة عبر WMS → web/public/nasa/
# تشغيل:  powershell -File tools/fetch_nasa_imagery.ps1

$ErrorActionPreference = "Stop"
$dir = Join-Path $PSScriptRoot "..\web\public\nasa"
New-Item -ItemType Directory -Force $dir | Out-Null
$wms = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"

function Get-Gibs($layer, $bbox, $w, $h, $time, $fmt, $out) {
  $ext = if ($fmt -eq "image/png") { "png" } else { "jpg" }
  $url = "$wms`?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=$layer&CRS=EPSG:4326&BBOX=$bbox&WIDTH=$w&HEIGHT=$h&FORMAT=$fmt&TIME=$time"
  try {
    Invoke-WebRequest $url -OutFile (Join-Path $dir $out) -TimeoutSec 60
    $kb = [math]::Round((Get-Item (Join-Path $dir $out)).Length / 1KB, 1)
    Write-Output ("  OK  {0,-28} {1,7} KB  ({2})" -f $out, $kb, $time)
  } catch {
    Write-Output ("  ERR {0,-28} {1}" -f $out, $_.Exception.Message)
  }
}

$TC = "VIIRS_SNPP_CorrectedReflectance_TrueColor"
$MODIS = "MODIS_Terra_CorrectedReflectance_TrueColor"
$NDVI = "MODIS_Terra_L3_NDVI_Monthly"

# 1) خلفية الأردن الكاملة (VIIRS TrueColor) — قاعدة الخريطة السينمائية
Write-Output "== خلفية الأردن (VIIRS TrueColor) =="
Get-Gibs $TC "29,34.6,33.5,39.4" 1400 1280 "2024-08-12" "image/jpeg" "jordan_truecolor.jpg"

# 2) آلة الزمن — حزام مزارع الأزرق، عدة سنوات صيفية (MODIS TrueColor، يعود إلى 2000)
Write-Output "== آلة الزمن الأزرق (MODIS TrueColor صيفاً) =="
$azBox = "31.55,36.50,32.20,37.30"
foreach ($yr in 2016,2018,2020,2022,2024) {
  Get-Gibs $MODIS $azBox 900 720 "$yr-08-12" "image/jpeg" "tm_azraq_$yr.jpg"
}

# 3) NDVI الشهري للأزرق (مؤشر الخضرة الحقيقي) — قبل/بعد
Write-Output "== NDVI الأزرق (MODIS الشهري) =="
Get-Gibs $NDVI $azBox 900 720 "2016-08-01" "image/png" "ndvi_azraq_2016.png"
Get-Gibs $NDVI $azBox 900 720 "2024-08-01" "image/png" "ndvi_azraq_2024.png"

# 4) دوائر الري المحوري في صحراء الديسي/المدوّرة (لحظة الإبهار — مرئية في صورة الأردن)
Write-Output "== دوائر الري المحوري (الجنوب الشرقي) =="
Get-Gibs $TC "29.0,36.6,30.2,38.2" 1000 760 "2024-08-12" "image/jpeg" "pivots_disi.jpg"

Write-Output "تم. الصور في web/public/nasa/"
