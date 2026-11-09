# LabTrack · Evidencias de Pruebas de Rendimiento (JMeter)

Este directorio contiene la documentación técnica, especificaciones de planes de prueba, scripts de automatización y plantillas de resultados para las **Pruebas de Carga** y **Pruebas de Estrés** del sistema LabTrack.

---

## 📌 Estado del Entorno de Ejecución

> [!WARNING]
> **Apache JMeter 5.6.3 no se encuentra preinstalado** en el sistema ni en el `PATH` del entorno host.
> Siguiendo estrictamente las directivas de calidad del proyecto (*"si JMeter no está instalado, repórtalo y deja los comandos exactos; no inventes resultados"*), se documenta el diagnóstico técnico completo, la búsqueda realizada en el sistema y los **comandos exactos paso a paso** para instalar JMeter y ejecutar las pruebas de manera 100 % reproducible.

---

## 📂 Contenido del Directorio

1. **[`analisis-carga-estres.md`](file:///docs/evidencias-jmeter/analisis-carga-estres.md)**:
   - Sección formativa para el equipo: Diferencias metodológicas y conceptuales entre **Carga vs Estrés**.
   - Interpretación estadística y práctica de los **Percentiles** ($p_{50}$, $p_{90}$, $p_{95}$, $p_{99}$) y por qué superan al promedio en la medición de SLAs.
   - Auditoría de búsqueda de JMeter en Windows (PATH, registro, carpetas estándar).
   - Detección de Java y resolución automática en scripts PowerShell.
   - Comandos exactos de instalación, ejecución, análisis y captura con Playwright.
   - Matriz de umbrales SLA y resultados esperados.

2. **[`plantilla-resultados.csv`](file:///docs/evidencias-jmeter/plantilla-resultados.csv)**:
   - Estructura CSV estandarizada de métricas por transacción (`Muestras`, `Promedio_ms`, `p50_ms`, `p90_ms`, `p95_ms`, `p99_ms`, `Throughput_rps`, `Errores`, `Error_pct`).

3. **[`plantilla-resultados.md`](file:///docs/evidencias-jmeter/plantilla-resultados.md)**:
   - Tablas en formato Markdown listas para incorporación en el informe final y la presentación ejecutiva.

4. **[`capture_report.js`](file:///docs/evidencias-jmeter/capture_report.js)**:
   - Script automatizado con **Playwright** para renderizar y tomar capturas PNG de alta resolución del Dashboard interactivo generado por Apache JMeter (`index.html`).

---

## 🚀 Flujo de Reproducción Rápida

```powershell
# 1. Descargar y extraer Apache JMeter portable (una sola vez)
Invoke-WebRequest -Uri "https://dlcdn.apache.org/jmeter/binaries/apache-jmeter-5.6.3.zip" -OutFile "..\tools\jmeter.zip"
Expand-Archive -Path "..\tools\jmeter.zip" -DestinationPath "..\tools\" -Force

# 2. Iniciar el backend con base de datos de prueba
$env:DATABASE_URL="postgresql://labtrack@127.0.0.1:55432/labtrack_test?schema=public"
$env:PORT="3000"
$env:JWT_SECRET="jmeter-secret-testing-key-1234567890"
Start-Process node -ArgumentList "backend\dist\main.js"

# 3. Ejecutar prueba de Carga (50 usuarios · 60 s)
powershell -ExecutionPolicy Bypass -File .\jmeter\run-load-test.ps1 -Threads 50 -Duration 60 -RampUp 10

# 4. Ejecutar prueba de Estrés (150 usuarios · 90 s)
powershell -ExecutionPolicy Bypass -File .\jmeter\run-stress-test.ps1 -Threads 150 -Duration 90 -RampUp 15

# 5. Capturar dashboard HTML con Playwright
node docs/evidencias-jmeter/capture_report.js
```
