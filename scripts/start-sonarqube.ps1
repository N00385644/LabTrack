param(
    [int]$Port = 9000
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$instance = Join-Path $root 'instance'
$sonarHome = Join-Path $root 'tools\sonarqube-26.10.0.133078'
$startScript = Join-Path $sonarHome 'bin\windows-x86-64\StartSonar.bat'

if (-not (Test-Path $startScript)) {
    throw "No se encontró SonarQube en $sonarHome. Extrae el paquete en tools\\sonarqube-26.10.0.133078."
}

Write-Host '== LabTrack · SonarQube ==' -ForegroundColor Cyan

# PostgreSQL debe estar activo en el puerto 55432.
$pg = Get-NetTCPConnection -LocalPort 55432 -State Listen -ErrorAction SilentlyContinue
if (-not $pg) {
    throw 'PostgreSQL no está escuchando en el puerto 55432. Ejecuta scripts\\start.ps1 primero.'
}

# La base "sonar" debe existir.
$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$exists = & $psql -h 127.0.0.1 -p 55432 -U labtrack -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='sonar';"
if ($exists.Trim() -ne '1') {
    & 'C:\Program Files\PostgreSQL\18\bin\createdb.exe' -h 127.0.0.1 -p 55432 -U labtrack sonar
    Write-Host 'Base de datos "sonar" creada.' -ForegroundColor Green
}

# Configuración de conexión (idempotente).
$conf = Join-Path $sonarHome 'conf\sonar.properties'
$content = Get-Content $conf -Raw
$content = $content -replace '(?m)^#?\s*sonar.jdbc.url=.*$', 'sonar.jdbc.url=jdbc:postgresql://127.0.0.1:55432/sonar'
$content = $content -replace '(?m)^#?\s*sonar.jdbc.username=.*$', 'sonar.jdbc.username=labtrack'
$content = $content -replace '(?m)^#?\s*sonar.jdbc.password=.*$', 'sonar.jdbc.password='
$content = $content -replace '(?m)^#?\s*sonar.web.port=.*$', "sonar.web.port=$Port"

# Los datos de Elasticsearch se guardan en D: para no superar el umbral de disco de C:.
$dataRoot = 'D:\LabTrackSonar'
$dataDir = Join-Path $dataRoot 'data'
$tempDir = Join-Path $dataRoot 'temp'
New-Item -ItemType Directory -Force $dataDir, $tempDir | Out-Null
$dataPath = $dataDir.Replace('\', '/')
$tempPath = $tempDir.Replace('\', '/')
if ($content -match '(?m)^#?\s*sonar.path.data=.*$') {
    $content = $content -replace '(?m)^#?\s*sonar.path.data=.*$', "sonar.path.data=$dataPath"
} else {
    $content += "`nsonar.path.data=$dataPath`n"
}
if ($content -match '(?m)^#?\s*sonar.path.temp=.*$') {
    $content = $content -replace '(?m)^#?\s*sonar.path.temp=.*$', "sonar.path.temp=$tempPath"
} else {
    $content += "sonar.path.temp=$tempPath`n"
}
Set-Content -Path $conf -Value $content -Encoding UTF8

$already = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($already) {
    Write-Host "SonarQube ya está escuchando en el puerto $Port." -ForegroundColor Green
    exit 0
}

Write-Host "Iniciando SonarQube en el puerto $Port (puede tardar 1-2 minutos)…" -ForegroundColor Yellow
$process = Start-Process -FilePath $startScript `
    -WorkingDirectory $sonarHome `
    -RedirectStandardOutput (Join-Path $instance 'sonar.out.log') `
    -RedirectStandardError (Join-Path $instance 'sonar.err.log') `
    -WindowStyle Hidden -PassThru
Set-Content (Join-Path $instance 'sonar.pid') $process.Id

$deadline = (Get-Date).AddMinutes(5)
while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest "http://localhost:$Port/api/system/status" -UseBasicParsing -TimeoutSec 5
        $status = ($response.Content | ConvertFrom-Json).status
        if ($status -eq 'UP') {
            Write-Host "SonarQube listo en http://localhost:$Port (admin/admin)." -ForegroundColor Green
            exit 0
        }
    } catch { }
    Start-Sleep -Seconds 5
}

throw 'SonarQube no alcanzó el estado UP. Revisa instance/sonar.out.log y instance/sonar.err.log.'
