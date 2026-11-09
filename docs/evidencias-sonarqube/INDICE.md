# Índice de evidencias SonarQube — LabTrack ANTES / DESPUÉS

**Fecha de la evidencia:** 2026-11-09
**Commit analizado:** `840052e769ac7386f458d9cac2332d6a4dd2d50d` — «Initial commit» (2026-11-09 13:15:16 -0500)
**Proyectos previstos:** `labtrack-antes` y `labtrack-despues`
**Herramienta de referencia:** SonarQube Community Build 26.10 · SonarScanner CLI 8.3.1

---

## Declaración de estado (leer primero)

**No se ejecutó ningún escaneo nuevo.** El 2026-11-09 se comprobó que:

| Comprobación | Resultado |
|---|---|
| `http://localhost:9000/api/system/status` | **No disponible** («No es posible conectar con el servidor remoto»). |
| Variable `SONAR_TOKEN` | **No definida**. |
| `instance/sonar-token.txt` | **No existe**. |
| `tools/sonar-scanner-…/sonar-scanner.bat` | **No existe**; `sonar-scanner` tampoco está en `PATH`. |
| `tools/sonarqube-26.10.0.133078` | **No existe** en este worktree. |

Consecuencia: no hubo análisis enviado al Compute Engine ni capturas de la interfaz de
SonarQube. Las métricas provienen de las instantáneas históricas del repositorio:

- **ANTES:** [`docs/sonar-baseline.json`](../sonar-baseline.json) → **ANTES REPRODUCIDO**.
- **DESPUÉS:** [`docs/sonar-data.json`](../sonar-data.json), bloque `final` → instantánea histórica.

Los **PNG** son capturas de Playwright sobre paneles HTML generados localmente a partir de
esos JSON. **No son capturas de la UI de SonarQube.** Cada imagen lleva un aviso visible
que lo indica.

No se modificó `sonar-project.properties`. El escaneo del DESPUÉS, cuando sea posible, se
hará con `-Dsonar.projectKey=labtrack-despues` y `-Dsonar.sources` por línea de comandos.

---

## Resumen de resultados

| Métrica | ANTES (reproducido) | DESPUÉS (histórico) | Mejora |
|---|---:|---:|---|
| Bugs | 2 | 0 | −2 (−100 %) |
| Vulnerabilidades | 2 | 0 | −2 (−100 %) |
| Code Smells | 40 | 0 | −40 (−100 %) |
| Confiabilidad | B | A | B → A |
| Seguridad | C | A | C → A |
| Mantenibilidad | A | A | A (sin deuda abierta) |
| Quality Gate | OK | OK | OK → OK con 0 issues abiertos |
| Issues abiertos | 44 | 0 | −44 (−100 %) |

---

## Mapa de carpetas

```
docs/evidencias-sonarqube/
├── INDICE.md                     este documento
├── README.md                     metodología y limitaciones
├── antes/
│   ├── README-reproduccion.md    qué se reconstruyó y por qué
│   ├── src/                      COPIA de backend/src y frontend/src con los 44 defectos
│   ├── api/                      JSON con forma de API (reconstruidos)
│   ├── logs/scan-antes.log       intento de escaneo y bloqueo
│   ├── defectos-sembrados.json   inventario máquina-legible de las 44 marcas
│   ├── sonar-antes.properties    propiedades para el escaneo futuro
│   └── *.png                     8 evidencias visuales
├── despues/
│   ├── api/, logs/, *.png        8 evidencias visuales + JSON + log
├── comparacion/
│   ├── tabla-comparativa.md      tabla Métrica | Antes | Después | Mejora
│   ├── tabla-comparativa.png     la misma tabla como imagen
│   ├── grafico-comparativo.png   gráfico de barras de hallazgos
│   ├── dashboard-comparativo.png resumen visual comparado
│   └── comparacion.json          datos completos de la comparación
├── render/                       HTML fuente de cada PNG (reproducible)
└── scripts/
    ├── reconstruir-antes.py      reconstruye el árbol ANTES
    └── generar-evidencias.py     regenera JSON, tabla y HTML
```

---

## Qué demuestra cada evidencia

### `antes/` — ANTES REPRODUCIDO

| Archivo | Qué muestra | Qué demuestra |
|---|---|---|
| `dashboard.png` | KPIs y ratings del estado ANTES. | Existían 2 bugs, 2 vulnerabilidades y 40 code smells; ratings B/C/A. |
| `bugs.png` | Los 2 bugs, regla `S1082`, archivo y línea. | Ambos bugs provienen del modal no accesible de `ui.tsx` (líneas 218 y 222). |
| `vulnerabilidades.png` | Las 2 vulnerabilidades (`S2245`, `S2068`). | `Math.random()` en toasts y contraseña embebida en el login. |
| `code-smells.png` | Los 40 code smells agrupados por regla y por archivo. | La deuda se concentra en `S6759` (14), `S7718` (11) y `S3358` (8). |
| `ratings.png` | Calificaciones B (confiabilidad), C (seguridad) y A (mantenibilidad). | El estado ANTES no llegaba a A en confiabilidad ni seguridad. |
| `quality-gate.png` | Quality Gate `OK` y ausencia de condiciones registradas. | La instantánea histórica aprobaba el gate pese a los 44 issues; no había condiciones guardadas. |
| `issues-lista.png` | Las 44 incidencias con regla, archivo:línea, severidad y mensaje. | Trazabilidad completa hallazgo → archivo → línea del estado ANTES. |
| `fecha-commit.png` | Fecha de captura, commit, fuente y estado del escaneo. | La evidencia está anclada al commit `840052e` y declara que el escaneo no se ejecutó. |
| `api/measures-component.json` | Medidas con forma de `api/measures/component`. | Valores numéricos usados en la tabla y el gráfico. |
| `api/issues-search.json` | 44 issues con forma de `api/issues/search`. | Listado completo y reutilizable de hallazgos ANTES. |
| `api/qualitygates-project-status.json` | Estado del gate con forma de `api/qualitygates/project_status`. | Gate `OK` y condiciones (vacías) del histórico. |
| `logs/scan-antes.log` | Comprobaciones de servidor, token y scanner; comando previsto. | El escaneo quedó **bloqueado** y no se envió nada al Compute Engine. |
| `README-reproduccion.md` | Metodología, tabla baseline → reproducible y límites. | El árbol es una reconstrucción, no una captura histórica. |
| `defectos-sembrados.json` | Archivo, línea y regla de cada marca `DEFECTO SEMBRADO`. | Verificación automática de que se sembraron las 44 reglas. |
| `sonar-antes.properties` | Configuración lista para el escaneo futuro. | Reproducibilidad cuando SonarQube esté disponible. |

### `despues/` — estado final histórico

| Archivo | Qué muestra | Qué demuestra |
|---|---|---|
| `dashboard.png` | 0 bugs, 0 vulnerabilidades y 0 code smells; ratings A/A/A. | El código actual ya no tiene hallazgos abiertos en la instantánea final. |
| `bugs.png` | Listado vacío. | No quedan bugs abiertos. |
| `vulnerabilidades.png` | Listado vacío. | No quedan vulnerabilidades abiertas. |
| `code-smells.png` | Sin code smells; resumen de archivos vacío. | La deuda registrada quedó cerrada. |
| `ratings.png` | A en confiabilidad, seguridad y mantenibilidad. | El estado final alcanza la máxima calificación en las tres dimensiones. |
| `quality-gate.png` | Gate `OK` con 3 condiciones: `new_coverage` 87.1 ≥ 80, `new_duplicated_lines_density` 0.0 ≤ 3, `new_violations` 0 ≤ 0. | El gate del estado final sí tiene condiciones medibles y todas pasan. |
| `issues-lista.png` | «Sin issues abiertos». | El listado final está vacío. |
| `fecha-commit.png` | Fecha, commit y fuente del estado final. | Trazabilidad del DESPUÉS y declaración de que no es un escaneo nuevo. |
| `api/measures-component.json` | Medidas finales. | Valores de la comparación. |
| `api/issues-search.json` | `total: 0`. | Cierre total de incidencias en la instantánea. |
| `api/qualitygates-project-status.json` | Gate con sus 3 condiciones. | Evidencia de las condiciones del estado final. |
| `logs/scan-despues.log` | Comando previsto con `-Dsonar.projectKey=labtrack-despues` y el bloqueo. | Se respetó la regla de no editar `sonar-project.properties`. |

### `comparacion/` — ANTES vs DESPUÉS

| Archivo | Qué muestra | Qué demuestra |
|---|---|---|
| `tabla-comparativa.md` | Tabla Métrica \| Antes \| Después \| Mejora y métricas secundarias. | La reducción cuantitativa de los 44 hallazgos a 0. |
| `tabla-comparativa.png` | La misma tabla como imagen legible. | Evidencia visual lista para el informe o la presentación. |
| `grafico-comparativo.png` | Barras ANTES vs DESPUÉS para bugs, vulnerabilidades y code smells. | Impacto visual de la refactorización (100 % de reducción). |
| `dashboard-comparativo.png` | Tarjetas de deltas, ratings finales y detalle. | Lectura ejecutiva de la mejora. |
| `comparacion.json` | Métricas principales y secundarias + instantáneas completas. | Fuente de datos para regenerar tabla y gráfico. |

---

## Cómo se regeneró todo

```powershell
# 1. Reconstruir el árbol ANTES (copia + 44 defectos sembrados)
python docs/evidencias-sonarqube/scripts/reconstruir-antes.py

# 2. Regenerar JSON con forma de API, tabla comparativa y HTML
python docs/evidencias-sonarqube/scripts/generar-evidencias.py

# 3. Capturar los PNG (requiere servir render/ y Playwright)
python -m http.server 8899 --bind 127.0.0.1 --directory docs/evidencias-sonarqube/render
#    y capturar cada render/*.html a su PNG correspondiente
```

---

## Limitaciones

1. **No hay escaneo nuevo.** Ni el ANTES ni el DESPUÉS fueron analizados por un
   SonarQube en ejecución. Todas las cifras son históricas.
2. **El ANTES es reconstruido.** No existe en Git; se sembraron las 44 reglas en una
   copia del código actual. La fidelidad es de regla, archivo y línea aproximada
   (33/44 exactas y 38/44 a una línea o menos); ver `antes/README-reproduccion.md`.
3. **Los PNG no son capturas de SonarQube.** Son paneles locales con los datos de los
   JSON, etiquetados como tales.
4. **El quality gate ANTES figura como OK** porque así lo registró la instantánea
   histórica; el valor probatorio está en la caída de 44 issues a 0.
5. Cuando haya servidor y token, repetir los escaneos con:

```powershell
$env:SONAR_TOKEN = '<token>'   # solo en memoria; jamás en archivos ni logs
sonar-scanner -Dsonar.host.url=http://localhost:9000 `
  -Dsonar.projectKey=labtrack-antes `
  -Dsonar.sources=docs/evidencias-sonarqube/antes/src

sonar-scanner -Dsonar.host.url=http://localhost:9000 `
  -Dsonar.projectKey=labtrack-despues `
  -Dsonar.sources=backend/src,frontend/src
```

Después, volver a ejecutar `generar-evidencias.py` sustituyendo las instantáneas por las
respuestas reales de `/api/issues/search` y `/api/measures/component`.
