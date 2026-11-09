param(
    [int]$Threads = 50,
    [int]$Duration = 60,
    [int]$RampUp = 10
)

$ErrorActionPreference = 'Stop'

$jmeterHome = Join-Path $PSScriptRoot '..\tools\apache-jmeter-5.6.3'
$jmeter = Join-Path $jmeterHome 'bin\jmeter.bat'
if (-not (Test-Path $jmeter)) {
    throw "JMeter no está instalado en $jmeterHome. Descarga Apache JMeter 5.6.3 en tools/."
}

$reports = Join-Path $PSScriptRoot 'reports'
if (Test-Path $reports) {
    Remove-Item $reports -Recurse -Force
}
New-Item -ItemType Directory -Force $reports | Out-Null

Write-Host "Ejecutando JMeter: $Threads usuarios, ramp-up $RampUp s, duración $Duration s..." -ForegroundColor Cyan
& $jmeter -n `
    -t (Join-Path $PSScriptRoot 'load-test.jmx') `
    -l (Join-Path $reports 'results.jtl') `
    -e -o (Join-Path $reports 'html') `
    "-Jthreads=$Threads" `
    "-Jduration=$Duration" `
    "-Jrampup=$RampUp"

if ($LASTEXITCODE -ne 0) {
    throw "JMeter terminó con código $LASTEXITCODE"
}

python (Join-Path $PSScriptRoot 'analyze_results.py')
Write-Host "Reporte HTML: $reports\html\index.html" -ForegroundColor Green
Write-Host "Resumen: $reports\summary.md" -ForegroundColor Green
