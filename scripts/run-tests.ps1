param(
    [switch]$SkipE2E
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$results = @()

Write-Host '== LabTrack · ejecución completa de pruebas ==' -ForegroundColor Cyan

function Invoke-Suite([string]$Name, [string]$Directory, [string]$Command) {
    Write-Host ''
    Write-Host "» $Name" -ForegroundColor Yellow
    Push-Location $Directory
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -Command $Command
        $code = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    $script:results += [pscustomobject]@{ Suite = $Name; Codigo = $code }
}

Invoke-Suite 'API · Vitest + Supertest' (Join-Path $root 'backend') 'npm run test:cov'

Invoke-Suite 'UI · Vitest + RTL' (Join-Path $root 'frontend') 'npm run test:cov'

if (-not $SkipE2E) {
    try {
        $null = Invoke-WebRequest 'http://localhost:3000/api/health' -UseBasicParsing -TimeoutSec 3
        $null = Invoke-WebRequest 'http://localhost:4173/' -UseBasicParsing -TimeoutSec 3
        Invoke-Suite 'E2E · Selenium' (Join-Path $root 'frontend') 'npm run test:e2e'
    } catch {
        Write-Host 'E2E omitido: inicia la aplicación con scripts\start.ps1 antes de ejecutarlo.' -ForegroundColor DarkYellow
    }
}

Write-Host ''
Write-Host '== Resumen ==' -ForegroundColor Cyan
$results | Format-Table -AutoSize
if ($results.Codigo -contains 0 -and ($results | Where-Object Codigo -ne 0).Count -eq 0) {
    Write-Host 'Todas las suites finalizaron correctamente.' -ForegroundColor Green
} else {
    Write-Host 'Revisa las suites con código distinto de cero.' -ForegroundColor Red
    exit 1
}
