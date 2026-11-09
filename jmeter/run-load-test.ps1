param(
    [int]$Threads = 50,
    [int]$Duration = 60,
    [int]$RampUp = 10,
    [string]$OutputDir = '',
    [string]$JMeterPath = ''
)

$ErrorActionPreference = 'Stop'

function Find-Java {
    if (Get-Command java.exe -ErrorAction SilentlyContinue) {
        return (Get-Command java.exe).Source
    }
    $candidates = @(
        "$env:JAVA_HOME\bin\java.exe",
        "C:\Program Files\JetBrains\IntelliJ IDEA 2026.2.3\jbr\bin\java.exe",
        "$env:USERPROFILE\.jdks\openjdk-27\bin\java.exe",
        "C:\Program Files\Android\Android Studio\jbr\bin\java.exe",
        "C:\Program Files\Java\jdk*\bin\java.exe"
    )
    foreach ($cand in $candidates) {
        $resolved = Resolve-Path $cand -ErrorAction SilentlyContinue
        if ($resolved) {
            $binDir = Split-Path -Parent $resolved[0].Path
            $env:JAVA_HOME = Split-Path -Parent $binDir
            $env:PATH = "$binDir;$env:PATH"
            Write-Host "Java configurado automáticamente desde: $binDir" -ForegroundColor DarkGray
            return $resolved[0].Path
        }
    }
    return $null
}

function Find-JMeter {
    param([string]$explicitPath)
    if ($explicitPath -and (Test-Path $explicitPath)) {
        return (Resolve-Path $explicitPath).Path
    }
    if (Get-Command jmeter.bat -ErrorAction SilentlyContinue) {
        return (Get-Command jmeter.bat).Source
    }
    if ($env:JMETER_HOME -and (Test-Path (Join-Path $env:JMETER_HOME 'bin\jmeter.bat'))) {
        return (Join-Path $env:JMETER_HOME 'bin\jmeter.bat')
    }
    $candidates = @(
        (Join-Path $PSScriptRoot '..\tools\apache-jmeter-5.6.3\bin\jmeter.bat'),
        (Join-Path $PSScriptRoot '..\..\tools\apache-jmeter-5.6.3\bin\jmeter.bat'),
        (Join-Path $PSScriptRoot '..\..\..\tools\apache-jmeter-5.6.3\bin\jmeter.bat'),
        'C:\tools\apache-jmeter-5.6.3\bin\jmeter.bat',
        'C:\apache-jmeter-5.6.3\bin\jmeter.bat',
        'C:\Program Files\apache-jmeter-5.6.3\bin\jmeter.bat',
        (Join-Path $env:USERPROFILE 'tools\apache-jmeter-5.6.3\bin\jmeter.bat')
    )
    foreach ($cand in $candidates) {
        if (Test-Path $cand) {
            return (Resolve-Path $cand).Path
        }
    }
    return $null
}

$javaExe = Find-Java
$jmeter = Find-JMeter -explicitPath $JMeterPath

if (-not $jmeter) {
    Write-Host '==========================================================================' -ForegroundColor Red
    Write-Host '[ALERTA] Apache JMeter no está instalado ni en PATH ni en rutas estándar.' -ForegroundColor Red
    Write-Host '==========================================================================' -ForegroundColor Red
    Write-Host 'Rutas examinadas:' -ForegroundColor Yellow
    Write-Host '  - PATH (jmeter.bat)' -ForegroundColor DarkGray
    Write-Host '  - $env:JMETER_HOME' -ForegroundColor DarkGray
    Write-Host '  - tools\apache-jmeter-5.6.3\bin\jmeter.bat' -ForegroundColor DarkGray
    Write-Host '  - ..\tools\apache-jmeter-5.6.3\bin\jmeter.bat' -ForegroundColor DarkGray
    Write-Host '  - ..\..\..\tools\apache-jmeter-5.6.3\bin\jmeter.bat' -ForegroundColor DarkGray
    Write-Host '  - C:\tools\apache-jmeter-5.6.3\bin\jmeter.bat' -ForegroundColor DarkGray
    Write-Host '  - C:\apache-jmeter-5.6.3\bin\jmeter.bat' -ForegroundColor DarkGray
    Write-Host ''
    Write-Host 'Comandos para instalar y ejecutar:' -ForegroundColor Cyan
    Write-Host '  1. Descargar Apache JMeter 5.6.3: https://dlcdn.apache.org/jmeter/binaries/apache-jmeter-5.6.3.zip' -ForegroundColor White
    Write-Host '  2. Extraer en tools\apache-jmeter-5.6.3 o en C:\tools\apache-jmeter-5.6.3' -ForegroundColor White
    Write-Host "  3. Reejecutar este script: .\run-load-test.ps1 -Threads $Threads -Duration $Duration -RampUp $RampUp" -ForegroundColor White
    throw 'Apache JMeter no disponible. Revisa las instrucciones en docs/evidencias-jmeter/analisis-carga-estres.md'
}

$reports = if ($OutputDir) { $OutputDir } else { Join-Path $PSScriptRoot 'reports' }
if (Test-Path $reports) {
    Remove-Item $reports -Recurse -Force
}
New-Item -ItemType Directory -Force $reports | Out-Null

$testPlan = Join-Path $PSScriptRoot 'load-test.jmx'
$jtlFile = Join-Path $reports 'results.jtl'
$htmlDir = Join-Path $reports 'html'

Write-Host '==========================================================================' -ForegroundColor Cyan
Write-Host ' Ejecutando Prueba de CARGA — LabTrack' -ForegroundColor Cyan
Write-Host " Hilos: $Threads | Ramp-up: $RampUp s | Duración: $Duration s" -ForegroundColor Cyan
Write-Host " JMeter: $jmeter" -ForegroundColor Cyan
Write-Host " Plan: $testPlan" -ForegroundColor Cyan
Write-Host " Salida: $reports" -ForegroundColor Cyan
Write-Host '==========================================================================' -ForegroundColor Cyan

& $jmeter -n `
    -t $testPlan `
    -l $jtlFile `
    -e -o $htmlDir `
    "-Jthreads=$Threads" `
    "-Jduration=$Duration" `
    "-Jrampup=$RampUp"

if ($LASTEXITCODE -ne 0) {
    throw "JMeter terminó con código de error $LASTEXITCODE"
}

$analyzer = Join-Path $PSScriptRoot 'analyze_results.py'
python $analyzer --jtl $jtlFile --output $reports --title 'Prueba de Carga (50 usuarios)' --threshold-p95 3000

Write-Host ''
Write-Host 'Prueba de carga completada con éxito.' -ForegroundColor Green
Write-Host "Reporte HTML JMeter: $(Join-Path $htmlDir 'index.html')" -ForegroundColor Green
Write-Host "Resumen Markdown:    $(Join-Path $reports 'summary.md')" -ForegroundColor Green
Write-Host "Tabla CSV:           $(Join-Path $reports 'resultados_tabla.csv')" -ForegroundColor Green
Write-Host "Gráficas generadas:  $(Join-Path $reports 'charts')" -ForegroundColor Green
