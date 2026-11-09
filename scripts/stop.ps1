param(
    [switch]$StopDatabase
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$instance = Join-Path $root 'instance'

Write-Host '== LabTrack · parada ==' -ForegroundColor Cyan

foreach ($name in @('api', 'web')) {
    $pidFile = Join-Path $instance "$name.pid"
    if (Test-Path $pidFile) {
        $processId = Get-Content $pidFile | Select-Object -First 1
        try {
            Stop-Process -Id ([int]$processId) -Force -ErrorAction Stop
            Write-Host "Proceso $name detenido (PID $processId)." -ForegroundColor Green
        } catch {
            Write-Host "El proceso $name ya no estaba activo." -ForegroundColor DarkGray
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}

if ($StopDatabase) {
    $pgCtl = 'C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe'
    if (Test-Path $pgCtl) {
        & $pgCtl -D (Join-Path $instance 'pgdata') stop -m fast | Out-Null
        Write-Host 'PostgreSQL detenido.' -ForegroundColor Green
    }
} else {
    Write-Host 'PostgreSQL se mantiene en ejecución (usa -StopDatabase para detenerlo).' -ForegroundColor DarkGray
}
