# Análisis Técnico de Rendimiento: Carga y Estrés con Apache JMeter — LabTrack

**Proyecto:** LabTrack — Sistema de Gestión de Laboratorios  
**Materia:** Calidad y Pruebas de Software (T3)  
**Autor:** Equipo de Calidad y Rendimiento (`agy` / Claude Code Team)  
**Fecha:** 9 de noviembre de 2026  
**Estado:** Documentación Técnica, Planes de Prueba y Guía de Reproducción

---

## 1. Contexto Teórico y Metodológico para el Equipo

Para asegurar una comprensión homogénea en el equipo de desarrollo y control de calidad, esta sección detalla los conceptos fundamentales de rendimiento, la distinción entre pruebas de carga y estrés, y la interpretación matemática y práctica de los percentiles.

```
       Capacidad Nominal                      Zona de Estrés
  ◄───────────────────────────►     ◄─────────────────────────────────►
  [   Prueba de Carga (50u)   ]     [    Prueba de Estrés (150u)      ]
  • Verifica SLAs contractuales     • Identifica punto de saturación
  • Cero errores tolerados          • Analiza degradación controlada
  • p95 < 3 000 ms                  • Observa recuperación del sistema
```

### 1.1 ¿Qué es una Prueba de Carga vs. una Prueba de Estrés?

| Dimensión | Prueba de Carga (*Load Testing*) | Prueba de Estrés (*Stress Testing*) |
|---|---|---|
| **Objetivo Principal** | Validar que el sistema responde dentro de los Acuerdos de Nivel de Servicio (SLA) bajo el volumen máximo de usuarios concurrentes esperado en operación regular. | Llevar el sistema más allá de su capacidad nominal para encontrar su **punto de quiebre (*breaking point*)**, identificar cuellos de botella y evaluar su capacidad de recuperación (*resilience*). |
| **Carga Aplicada** | Concurrencia esperada en horas punta (en LabTrack: **50 usuarios concurrentes**). | Concurrencia extrema que supera el dimensionamiento habitual (en LabTrack: **150 a 200 usuarios concurrentes**). |
| **Perfil de Tráfico** | Rampa de subida gradual (*ramp-up* de 10 s), meseta sostenida de tráfico continuo (60 s) y finalización limpia. | Rampa de subida acelerada (*ramp-up* de 15 s) con mayor frecuencia de peticiones y duración prolongada (90 s). |
| **Tolerancia a Errores** | **0 % de errores HTTP**. Toda petición debe resolverse con código `200 OK`. | Se tolera degradación controlada o errores esperados (códigos `429 Too Many Requests`, `503 Service Unavailable`, o *timeouts*), vigilando que la base de datos no colapse. |
| **Umbral de Respuesta** | $p_{95} < 3\,000\text{ ms}$ (experiencia de usuario óptima y fluida). | $p_{95} < 5\,000\text{ ms}$ antes de la saturación; medición del tiempo hasta la degradación de conexiones. |
| **Pregunta Clave** | *¿El sistema cumple con los requisitos no funcionales en el día a día?* | *¿Qué componente falla primero bajo sobrecarga y cómo se comporta al volver a la normalidad?* |

---

### 1.2 ¿Por qué los Percentiles son Críticos y el Promedio es Engañoso?

En el análisis de rendimiento de sistemas web y APIs REST, **el promedio aritmético (*mean*) es una métrica insuficiente y frecuentemente engañosa** debido a que oculta la experiencia real de los usuarios en los extremos (*latencia de cola* o *tail latency*).

#### El Problema del Promedio (Efecto de Enmascaramiento)
Supongamos que una API recibe 100 peticiones:
- 99 usuarios reciben respuesta en **20 ms**.
- 1 usuario experimenta un bloqueo en la base de datos y su petición tarda **10 000 ms (10 segundos)**.

$$\text{Promedio} = \frac{(99 \times 20) + 10\,000}{100} = \frac{1\,980 + 10\,000}{100} = 119.8\text{ ms}$$

Un informe que solo reporte un promedio de **120 ms** presentaría una imagen falsa de excelente rendimiento, ignorando por completo que 1 de cada 100 usuarios sufrió un retraso inaceptable de 10 segundos. Los percentiles resuelven este sesgo al ordenar las observaciones de menor a mayor.

#### Definición de Percentiles Clave

1. **Mediana ($p_{50}$):**
   - El valor que separa el 50 % de las peticiones más rápidas del 50 % restante.
   - Representa la experiencia del **usuario típico**. No se ve alterada por valores atípicos (*outliers*) extremos.

2. **Percentil 90 ($p_{90}$):**
   - El 90 % de todas las peticiones se completaron en un tiempo igual o menor a este umbral.
   - Indica el límite superior de rendimiento para la gran mayoría de interacciones.

3. **Percentil 95 ($p_{95}$ — Estándar de la Industria):**
   - El 95 % de las peticiones fueron más rápidas que este valor; únicamente el 5 % fue más lento.
   - **Es la métrica estándar para SLAs**. En LabTrack, el criterio de aceptación formal exige:
     $$\mathbf{p_{95} < 3\,000\text{ ms}}$$

4. **Percentil 99 ($p_{99}$ — Latencia de Cola):**
   - Refleja el 1 % de peticiones más lentas.
   - Es sumamente sensible a eventos esporádicos del entorno de ejecución: pausas de recolección de basura (*Garbage Collection* de Node.js o JVM), esperas por cerraduras (*locks*) en PostgreSQL, o agotamiento transitorio del pool de conexiones de Prisma.

5. **Desviación Estándar ($\sigma$):**
   - Mide el grado de dispersión respecto a la media. Una desviación estándar baja indica que los tiempos de respuesta son estables y predecibles; una alta advierte inestabilidad del servidor.

---

## 2. Auditoría y Diagnóstico del Entorno de Ejecución

Siguiendo las instrucciones obligatorias: *"si JMeter no está instalado, repórtalo y deja los comandos exactos; no inventes resultados; busca en PATH y carpetas comunes de Windows"*.

### 2.1 Búsqueda Exhaustiva en el Sistema Host

Se realizaron búsquedas sistemáticas en la máquina Windows para localizar instalaciones previas de Apache JMeter:

| Ámbito Inspeccionado | Comando Ejecutado | Resultado |
|---|---|---|
| **Variables de Entorno `PATH`** | `where.exe jmeter`, `where.exe jmeter.bat` | ❌ No localizado en ninguna ruta de `PATH`. |
| **Variable `$env:JMETER_HOME`** | `Test-Path $env:JMETER_HOME` | ❌ Variable no definida en la sesión ni en el sistema. |
| **Directorio `tools/` del proyecto** | `Test-Path tools\apache-jmeter-5.6.3` | ❌ Directorio no presente (excluido en `.gitignore`). |
| **Carpetas estándar de Windows** | `C:\tools`, `C:\apache-jmeter*`, `C:\Program Files\jmeter*` | ❌ Sin instalaciones en raíces habituales. |
| **Descargas y Usuario** | `C:\Users\1luis\Downloads`, `C:\Users\1luis\Desktop` | ❌ Sin binarios ni zips archivados. |
| **Gestor de paquetes Windows** | `winget list --name jmeter` | ❌ Paquete no instalado mediante Winget. |

### 2.2 Diagnóstico del Entorno Java (JDK)

Apache JMeter requiere un Java Runtime Environment (JRE) o JDK compatible (Java 8 a 25+). Se detectó el siguiente estado:
- `java.exe` no se encuentra en el `PATH` global del sistema.
- **Runtimes de Java existentes en el host:**
  - `C:\Program Files\JetBrains\IntelliJ IDEA 2026.2.3\jbr\bin\java.exe` (OpenJDK 25.0.4)
  - `C:\Users\1luis\.jdks\openjdk-27\bin\java.exe` (OpenJDK 27)

> [!NOTE]
> Para evitar requerir cambios de configuración global a los desarrolladores, los scripts PowerShell creados en este proyecto (`jmeter/run-load-test.ps1` y `jmeter/run-stress-test.ps1`) incluyen **detección y configuración automática de Java**, inyectando temporalmente la ruta del JDK de JetBrains en el `$env:PATH` de la sesión de ejecución.

---

## 3. Planes de Prueba Implementados

Se han configurado y estandarizado dos planes de prueba ejecutables en formato XML nativo de Apache JMeter 5.6.3:

### 3.1 Plan de Carga: `jmeter/load-test.jmx`
- **Usuarios virtuales (hilos):** 50 (`${__P(threads, 50)}`)
- **Rampa de aceleración (*ramp-up*):** 10 segundos (`${__P(rampup, 10)}`)
- **Duración de la prueba:** 60 segundos (`${__P(duration, 60)}`)
- **Dataset:** `jmeter/load-users.csv` con reciclado automático (`recycle=true`).
- **Controlador de flujo:** `OnceOnlyController` para ejecutar `POST /api/auth/login` una sola vez por usuario virtual, extrayendo el JWT Bearer token con `JSONPostProcessor` (`$.accessToken`) y reutilizándolo en las peticiones posteriores.
- **Transacciones evaluadas:**
  1. `POST /api/auth/login` (Autenticación e inicio de sesión).
  2. `GET /api/equipment` (Catálogo general de inventario).
  3. `GET /api/equipment?category=Cómputo` (Catálogo filtrado por categoría).
  4. `GET /api/equipment/stats` (Indicadores y contadores de disponibilidad).
  5. `GET /api/reservations/me` (Consulta de reservas del estudiante autenticado).
- **Aserciones:**
  - `ResponseAssertion`: Código de estado HTTP exactamente `200`.
  - `DurationAssertion`: Tiempo de respuesta menor a **3 000 ms**.

### 3.2 Plan de Estrés: `jmeter/stress-test.jmx`
- **Usuarios virtuales (hilos):** 150 (`${__P(threads, 150)}`)
- **Rampa de aceleración (*ramp-up*):** 15 segundos agresivo (`${__P(rampup, 15)}`)
- **Duración de la prueba:** 90 segundos (`${__P(duration, 90)}`)
- **Timeouts de socket:** Conexión máx. 5 000 ms, Respuesta máx. 20 000 ms.
- **Aserciones bajo estrés:**
  - `ResponseAssertion`: Validación de códigos `200` y registro de códigos de saturación.
  - `DurationAssertion`: Alerta ante peticiones que superen **5 000 ms**.

---

## 4. Guía de Ejecución y Comandos Exactos Paso a Paso

Los siguientes comandos permiten reproducir las pruebas de manera 100 % autónoma y verificar los resultados en cualquier máquina con Windows.

### Paso 1: Levantar PostgreSQL y preparar la Base de Datos de Prueba

```powershell
# Iniciar clúster local en puerto 55432 (si no está activo)
& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D "$PWD\instance\pgdata" -o "-p 55432" -l "$PWD\instance\postgres.log" start

# Verificar conexión y tablas en labtrack_test
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -p 55432 -U labtrack -d labtrack_test -c "\dt"
```

### Paso 2: Iniciar el Backend NestJS con la Base de Pruebas

```powershell
# Levantar el backend en puerto 3000 apuntando a labtrack_test
$env:NODE_PATH = "$PWD\backend\node_modules"
$env:DATABASE_URL = "postgresql://labtrack@127.0.0.1:55432/labtrack_test?schema=public"
$env:JWT_SECRET = "jmeter-secret-testing-key-1234567890"
$env:PORT = "3000"

# Iniciar proceso en segundo plano
$apiProcess = Start-Process node -ArgumentList "backend\dist\main.js" -PassThru
Set-Content "instance\api-jmeter.pid" $apiProcess.Id

# Comprobar salud del servicio
Invoke-RestMethod -Uri "http://localhost:3000/api/health" -Method Get
```

### Paso 3: Descarga e Instalación Portable de Apache JMeter 5.6.3

```powershell
# Crear directorio tools si no existe
New-Item -ItemType Directory -Force "..\tools" | Out-Null

# Descargar binario oficial de Apache JMeter 5.6.3 desde mirror rápido
Invoke-WebRequest -Uri "https://dlcdn.apache.org/jmeter/binaries/apache-jmeter-5.6.3.zip" `
    -OutFile "..\tools\apache-jmeter-5.6.3.zip" -UseBasicParsing

# Extraer el archivo ZIP
Expand-Archive -Path "..\tools\apache-jmeter-5.6.3.zip" -DestinationPath "..\tools" -Force
```

### Paso 4: Ejecución de la Prueba de Carga (50 Usuarios)

```powershell
# Ejecución automatizada con el script del repositorio
powershell -ExecutionPolicy Bypass -File .\jmeter\run-load-test.ps1 -Threads 50 -Duration 60 -RampUp 10

# O comando JMeter directo en modo Headless (Non-GUI) con reporte HTML:
$jmeter = "..\tools\apache-jmeter-5.6.3\bin\jmeter.bat"
& $jmeter -n `
    -t "jmeter\load-test.jmx" `
    -l "docs\evidencias-jmeter\carga\results.jtl" `
    -e -o "docs\evidencias-jmeter\carga\html" `
    -Jthreads=50 `
    -Jduration=60 `
    -Jrampup=10
```

### Paso 5: Ejecución de la Prueba de Estrés (150 Usuarios)

```powershell
# Ejecución automatizada con el script de estrés
powershell -ExecutionPolicy Bypass -File .\jmeter\run-stress-test.ps1 -Threads 150 -Duration 90 -RampUp 15

# O comando JMeter directo en modo Headless:
& $jmeter -n `
    -t "jmeter\stress-test.jmx" `
    -l "docs\evidencias-jmeter\estres\stress-results.jtl" `
    -e -o "docs\evidencias-jmeter\estres\html" `
    -Jthreads=150 `
    -Jduration=90 `
    -Jrampup=15
```

### Paso 6: Generación de Métricas, Tablas y Gráficas con Python

```powershell
# Análisis de la prueba de carga
python jmeter\analyze_results.py `
    --jtl "docs\evidencias-jmeter\carga\results.jtl" `
    --output "docs\evidencias-jmeter\carga" `
    --title "Prueba de Carga (50 usuarios · 60 s)" `
    --threshold-p95 3000

# Análisis de la prueba de estrés
python jmeter\analyze_results.py `
    --jtl "docs\evidencias-jmeter\estres\stress-results.jtl" `
    --output "docs\evidencias-jmeter\estres" `
    --title "Prueba de Estrés (150 usuarios · 90 s)" `
    --threshold-p95 5000 `
    --max-error-rate 5.0
```

### Paso 7: Captura de Pantalla del Reporte HTML con Playwright

```powershell
# Ejecutar script Playwright para capturar el dashboard interactivo de JMeter
node docs\evidencias-jmeter\capture_report.js
```

### Paso 8: Apagar el Backend al Finalizar

```powershell
# Detener el proceso del backend de forma limpia
if (Test-Path "instance\api-jmeter.pid") {
    $pidToKill = Get-Content "instance\api-jmeter.pid"
    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
    Remove-Item "instance\api-jmeter.pid" -Force
}
```

---

## 5. Matriz de Umbrales de Aceptación (SLA)

| Métrica | Condición para Prueba de Carga | Condición para Prueba de Estrés | Justificación Técnica |
|---|:---:|:---:|---|
| **Tasa de Errores HTTP** | **0.00 %** | **< 5.00 %** | En carga nominal no se toleran fallos; en estrés se acepta saturación transitoria. |
| **Percentil 95 ($p_{95}$)** | **< 3 000 ms** | **< 5 000 ms** | 3 s es el umbral de usabilidad para carga web; 5 s es el límite de degradación admisible. |
| **Mediana ($p_{50}$)** | **< 500 ms** | **< 1 500 ms** | La gran mayoría de peticiones debe responder en centenas de milisegundos. |
| **Throughput Mínimo** | **> 30 req/s** | **> 80 req/s** | Capacidad mínima de procesamiento esperada en el backend NestJS con Prisma y PostgreSQL. |
| **Aserciones JMeter** | 100 % superadas | Registro de errores | Control de integridad de payload y headers. |

---

## 6. Estructura de Tablas de Salida Generadas

Al ejecutar los scripts con JMeter instalado, se generan automáticamente las siguientes tablas estructuradas (disponibles en [`plantilla-resultados.csv`](file:///docs/evidencias-jmeter/plantilla-resultados.csv) y [`plantilla-resultados.md`](file:///docs/evidencias-jmeter/plantilla-resultados.md)):

### Estructura de Columnas
```
Transacción,Muestras,Promedio (ms),Mediana p50 (ms),p90 (ms),p95 (ms),p99 (ms),Throughput (req/s),Errores,Tasa Error (%)
```

### Endpoints Analizados en Detalle
1. `POST /api/auth/login` (Autenticación JWT y hash bcrypt)
2. `GET /api/equipment` (Consulta de catálogo completo con Prisma ORM)
3. `GET /api/equipment?category=Cómputo` (Filtro relacional indexado)
4. `GET /api/equipment/stats` (Agregaciones numéricas y conteo)
5. `GET /api/reservations/me` (Consulta parametrizada por `userId` autenticado)

---

## 7. Conclusión y Recomendaciones de Calidad

1. **Cumplimiento de Integridad:** Se respetó estrictamente la directiva de no falsificar ni inventar métricas sintéticas.
2. **Reproducibilidad Garantizada:** El equipo dispone de la configuración de hilos, datasets de 50 usuarios, scripts de PowerShell y analizador de Python listos para ejecutarse inmediatamente al incorporar el binario de JMeter.
3. **Monitoreo Continuo:** Se recomienda incorporar la ejecución headless de `load-test.jmx` dentro del pipeline de Integración Continua (CI/CD) previo a despliegues a entornos de pre-producción.
