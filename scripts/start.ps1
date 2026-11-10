param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$instance = Join-Path $root 'instance'
New-Item -ItemType Directory -Force $instance | Out-Null

function Test-Port([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Http([string]$Url, [int]$Seconds = 45) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return $true }
        } catch {
            Start-Sleep -Milliseconds 800
        }
    }
    return $false
}

Write-Host '== LabTrack · arranque ==' -ForegroundColor Cyan

# 1. PostgreSQL
if (-not (Test-Port 55432)) {
    Write-Host 'Iniciando PostgreSQL en el puerto 55432…' -ForegroundColor Yellow
    $pgCtl = 'C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe'
    if (-not (Test-Path $pgCtl)) { throw "No se encontró pg_ctl en $pgCtl" }
    & $pgCtl -D (Join-Path $instance 'pgdata') -o '-p 55432' -l (Join-Path $instance 'postgres.log') start | Out-Null
    Start-Sleep -Seconds 3
} else {
    Write-Host 'PostgreSQL ya está en ejecución (55432).' -ForegroundColor Green
}

# 2. Backend
$apiHealthy = $false
try {
    $health = Invoke-WebRequest 'http://localhost:3000/api/health' -UseBasicParsing -TimeoutSec 3
    $apiHealthy = $health.StatusCode -eq 200
} catch { }

if (-not $apiHealthy) {
    $backend = Join-Path $root 'backend'
    if (-not $SkipBuild -and -not (Test-Path (Join-Path $backend 'dist\main.js'))) {
        Write-Host 'Compilando backend…' -ForegroundColor Yellow
        Push-Location $backend
        npm run build
        Pop-Location
    }
    Write-Host 'Iniciando API NestJS en el puerto 3000…' -ForegroundColor Yellow
    $api = Start-Process -FilePath 'node.exe' `
        -ArgumentList 'dist\main.js' `
        -WorkingDirectory $backend `
        -RedirectStandardOutput (Join-Path $instance 'api.out.log') `
        -RedirectStandardError (Join-Path $instance 'api.err.log') `
        -WindowStyle Hidden -PassThru
    Set-Content (Join-Path $instance 'api.pid') $api.Id
    if (-not (Wait-Http 'http://localhost:3000/api/health')) {
        throw 'La API no respondió. Revisa instance/api.err.log'
    }
    Write-Host 'API lista.' -ForegroundColor Green
} else {
    Write-Host 'La API ya está en ejecución (3000).' -ForegroundColor Green
}

# 3. Frontend
$webHealthy = $false
try {
    $web = Invoke-WebRequest 'http://localhost:4173/' -UseBasicParsing -TimeoutSec 3
    $webHealthy = $web.StatusCode -eq 200
} catch { }

if (-not $webHealthy) {
    $frontend = Join-Path $root 'frontend'
    if (-not $SkipBuild -and -not (Test-Path (Join-Path $frontend 'dist\index.html'))) {
        Write-Host 'Compilando frontend…' -ForegroundColor Yellow
        Push-Location $frontend
        npm run build
        Pop-Location
    }
    Write-Host 'Iniciando vista previa del frontend en el puerto 4173…' -ForegroundColor Yellow
    $webProcess = Start-Process -FilePath 'node.exe' `
        -ArgumentList 'node_modules\vite\bin\vite.js', 'preview', '--port', '4173', '--strictPort' `
        -WorkingDirectory $frontend `
        -RedirectStandardOutput (Join-Path $instance 'web.out.log') `
        -RedirectStandardError (Join-Path $instance 'web.err.log') `
        -WindowStyle Hidden -PassThru
    Set-Content (Join-Path $instance 'web.pid') $webProcess.Id
    if (-not (Wait-Http 'http://localhost:4173/')) {
        throw 'El frontend no respondió. Revisa instance/web.err.log'
    }
    Write-Host 'Frontend listo.' -ForegroundColor Green
} else {
    Write-Host 'El frontend ya está en ejecución (4173).' -ForegroundColor Green
}

Write-Host ''
Write-Host 'LabTrack disponible en:' -ForegroundColor Cyan
Write-Host '  Aplicación : http://localhost:4173'
Write-Host '  API        : http://localhost:3000/api'
Write-Host '  Swagger    : http://localhost:3000/api/docs'
Write-Host ''
Write-Host 'Estudiante N00385644 / Estudiante2026!  ·  Admin ADMIN01 / Admin2026!' -ForegroundColor DarkGray
