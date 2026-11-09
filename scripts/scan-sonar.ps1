param(
    [string]$Token = $env:SONAR_TOKEN,
    [string]$ProjectKey = 'labtrack'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$scanner = Join-Path $root 'tools\sonar-scanner-8.3.1.16491-windows-x64\bin\sonar-scanner.bat'

if (-not (Test-Path $scanner)) {
    throw "No se encontró SonarScanner en $scanner. Descarga y extrae sonar-scanner-cli-8.3.1.16491-windows-x64.zip en tools."
}

if (-not $Token) {
    $tokenFile = Join-Path $root 'instance\sonar-token.txt'
    if (Test-Path $tokenFile) {
        $Token = (Get-Content $tokenFile -Raw).Trim()
    }
}

if (-not $Token) {
    throw 'No hay token de SonarQube. Genera uno en http://localhost:9000/account/security y guárdalo en instance\\sonar-token.txt o define SONAR_TOKEN.'
}

Write-Host '== LabTrack · escaneo SonarQube ==' -ForegroundColor Cyan
Write-Host "Escaneando el proyecto $ProjectKey…" -ForegroundColor Yellow

Push-Location $root
try {
    & $scanner `
        "-Dsonar.host.url=http://localhost:9000" `
        "-Dsonar.token=$Token" `
        "-Dsonar.projectKey=$ProjectKey"
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($code -ne 0) {
    throw "SonarScanner finalizó con código $code."
}

$taskUrl = 'http://localhost:9000/api/ce/activity?component=labtrack&ps=1'
Write-Host "Escaneo enviado. Consulta el estado en $taskUrl" -ForegroundColor Green
Write-Host 'Métricas: http://localhost:9000/dashboard?id=labtrack' -ForegroundColor Green
