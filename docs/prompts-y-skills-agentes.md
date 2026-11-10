# Uso de agentes de IA: prompts, skills y herramientas

**Contexto para compañeros:** este trabajo se desarrolló con un "equipo" de agentes de IA coordinados desde la línea de
comandos. Un agente líder (Claude Code) divide el trabajo en tareas con alcance de archivos que no se solapan; cada agente
trabaja en su propia copia aislada del repositorio (git worktree y rama `team/<id>`), sin hacer commit ni merge. El líder revisa
el reporte y el diff de cada tarea y recién entonces las integra una por una. Este documento deja constancia de **qué se le pidió a cada agente**.

## Skills utilizadas

| Skill / mecanismo | Quién la usó | Para qué |
|---|---|---|
| `multi-cli-team` (invocada con `/team`) | Agente líder (Claude Code) | Orquestar el equipo: `doctor`, `plan`, `spawn`, `wait`, `collect`, `merge`, `cleanup` mediante `team.ps1` |
| Herramientas MCP de Playwright | Agente líder | Capturas reales de la interfaz de SonarQube y de los reportes de JMeter; ejecución de axe-core (accesibilidad) |
| `sonar-scanner`, SonarQube Community Build 26.10, Apache JMeter 5.6.3, Vitest, Selenium WebDriver | Líder y agentes | Análisis estático, pruebas de carga/estrés, pruebas unitarias y funcionales |

Los agentes de trabajo pueden cargar sus propias skills y servidores MCP; **no se registró cuáles usó cada uno**, por lo que no se afirma nada al respecto.

## Reparto de agentes

| Tarea | Agente | Alcance (archivos que podía tocar) | Resultado |
|---|---|---|---|
| `sonar-antes-despues` | `opencode` | `docs/evidencias-sonarqube/**` | Reprodujo el ANTES, generó paneles de apoyo y JSON. No había SonarQube instalado: lo instaló y ejecutó el líder para obtener capturas reales |
| `pruebas-unitarias` | `copilot` | `docs/evidencias-pruebas/**`, `backend/test/*.extra.spec.ts`, `frontend/src/test/*.extra.test.ts`, `frontend/src/test/*.extra.test.tsx` | Ejecutó y documentó pruebas unitarias; agregó 2 archivos de pruebas nuevos (+8 casos) y la matriz de casos |
| `jmeter-carga-estres` | `agy` | `jmeter/**`, `docs/evidencias-jmeter/**` | Dejó plan de estrés, scripts y análisis; JMeter no estaba instalado, la ejecución real la hizo el líder tras instalarlo |
| `informe-presentacion-backlog` | `agy` | `docs/*.py`, `docs/*.docx`, `docs/*.pdf`, `docs/*.pptx`, `docs/*.md`, `docs/assets/**` | Informe, presentación y backlog (primer intento con `claude`, descartado a pedido del usuario; rehecho con `agy`) |
| `historias-usuario` | `copilot` | `docs/generate_report.py`, `docs/generate_presentation.py`, `docs/trazabilidad-historias-usuario.md`, `docs/*.md`, `docs/*.docx`, `docs/*.pdf`, `docs/*.pptx`, `docs/assets/**` | Verificó cada historia de usuario contra el código y actualizó informe, presentación y backlog |

> Decisión del usuario: la redacción del informe y la presentación **no** debía hacerla Claude; se asignó a `agy` (y luego las historias de usuario a `copilot`).
> `dsh` (DeepSeek Harness) no estaba instalado y no se usó.

## Prompts enviados a cada agente (texto original)

Los prompts se transcriben tal como están en `.team/tasks.json`. En el primer envío se pedía además evidencias con capturas del ANTES y el DESPUÉS.

### `sonar-antes-despues` — agente `opencode`

**Título:** SonarQube ANTES/DESPUES con evidencias reales  
**Depende de:** ninguna  
**Verificación:** `powershell -NoProfile -Command "if (-not (Test-Path docs/evidencias-sonarqube/INDICE.md)) { exit 1 }"`

```text
Lee docs/sonar-baseline.json, docs/sonar-data.json, docs/refactoring-backlog.md, docs/collect_sonar.py y sonar-project.properties. Objetivo: evidencias visuales de SonarQube (http://localhost:9000) del ANTES y DESPUES de LabTrack. No existe version ANTES en Git (solo 1 commit). Crea en docs/evidencias-sonarqube/antes/src/ una COPIA de backend/src y frontend/src y REINTRODUCE los defectos listados en sonar-baseline.json (S3358, S1082, S6819, S6847, S2068, S2245, S6759 y el resto registrado), usando los mismos archivos/lineas de la baseline; si hace falta, agrega defectos sembrados extra y marcalos con el comentario '// DEFECTO SEMBRADO (demostracion)'. REGLA OBLIGATORIA: todo lo reconstruido o sembrado debe etiquetarse como ANTES REPRODUCIDO, nunca como captura historica; crea docs/evidencias-sonarqube/antes/README-reproduccion.md explicando que es reconstruido, que fragmentos y por que. NO modifiques backend/src ni frontend/src reales. Para el DESPUES analiza el codigo actual con projectKey labtrack-despues pasando -D por linea de comandos, sin editar sonar-project.properties. Proyectos: labtrack-antes y labtrack-despues (sonar-scanner; token SOLO via variable de entorno SONAR_TOKEN, jamas escribirlo en archivos ni logs; si no hay SonarQube o token, escribe el bloqueo en el reporte y usa los JSON historicos dejando claro que NO es un escaneo nuevo). Espera a que cada tarea del Compute Engine termine. Con playwright captura PNG legibles de: dashboard, bugs, vulnerabilidades, code smells, ratings, quality gate, listado de issues (regla+archivo), fecha y commit. Guarda en docs/evidencias-sonarqube/{antes,despues,comparacion}/: PNG, JSON de la API (api/issues/search, api/measures/component), logs de escaneo (sin tokens), tabla comparativa Metrica|Antes|Despues|Mejora (Bugs, Vulnerabilidades, Code Smells, Confiabilidad, Seguridad, Mantenibilidad, Quality Gate), un grafico comparativo PNG y INDICE.md explicando que demuestra cada evidencia. Ademas escribe docs/evidencias-sonarqube/hallazgos.md con, por cada regla representativa: id de regla, archivo, clasificacion original (BUG/VULNERABILITY/CODE_SMELL, no asumas bug), descripcion, codigo ANTES, codigo DESPUES, explicacion tecnica, referencia a captura. Todo en espanol, con una seccion de contexto para companeros que no conocen el proyecto. No hagas commit.
```

### `pruebas-unitarias` — agente `copilot`

**Título:** Pruebas unitarias y automatizadas antes/despues  
**Depende de:** ninguna  
**Verificación:** `powershell -NoProfile -Command "if (-not (Test-Path docs/evidencias-pruebas/matriz-casos.md)) { exit 1 }"`

```text
Contexto: proyecto LabTrack (backend NestJS + vitest en backend/test, frontend React + vitest en frontend/src/test). Lee docs/matriz-pruebas.md y README.md. Tareas: (1) ejecuta las pruebas unitarias y de cobertura del backend y frontend (npm ci si hace falta; revisa package.json por los scripts) y guarda la salida completa en docs/evidencias-pruebas/unitarias/ (logs .txt, resumen de aprobadas/falladas, cobertura, y capturas PNG del reporte HTML de cobertura usando playwright si es posible). (2) ANTES/DESPUES: en docs/evidencias-pruebas/antes-despues/ documenta el estado de las pruebas antes de agregar casos (conteo actual) y despues de agregar casos nuevos; agrega pruebas unitarias nuevas SOLO como archivos NUEVOS en backend/test/ y frontend/src/test/ (nombres terminados en .extra.spec.ts o .extra.test.ts/.extra.test.tsx) cubriendo casos limite sugeridos. Incluye al menos 2 pruebas que demuestren una falla ante un defecto simulado en un mock local del propio test (nunca editando backend/src ni frontend/src) para tener evidencia de falladas y aprobadas. (3) Escribe docs/evidencias-pruebas/matriz-casos.md con: pruebas unitarias, funcionales automatizadas (frontend/e2e), carga y estres (solo referencia a docs/evidencias-jmeter, no la rellenes), y casos sugeridos por IA con columna de validacion humana (marcala como pendiente de revision, no como validada). Agrega plantillas claras para Katalon y Testomat.io/TestLink (pasos de exportacion y CSV importable docs/evidencias-pruebas/testomatio-import.csv) sin inventar capturas de herramientas que no se ejecutaron. Cada documento con seccion de contexto en espanol para companeros que no conocen el proyecto. NO modifiques backend/src ni frontend/src. No hagas commit.
```

### `jmeter-carga-estres` — agente `agy`

**Título:** Pruebas JMeter de carga y estres  
**Depende de:** ninguna  
**Verificación:** `powershell -NoProfile -Command "if (-not (Test-Path docs/evidencias-jmeter)) { exit 1 }"`

```text
Contexto: LabTrack tiene jmeter/load-test.jmx, jmeter/load-users.csv, jmeter/run-load-test.ps1 y jmeter/analyze_results.py. Lee README.md y esos archivos. Tareas: levanta el backend en un puerto local (revisa backend/package.json y prisma; usa base de datos de prueba, no datos reales), ejecuta una prueba de CARGA y una de ESTRES con JMeter (si JMeter no esta instalado, reportalo y deja los comandos exactos; no inventes resultados; busca en PATH y carpetas comunes de Windows). Guarda en docs/evidencias-jmeter/: .jtl crudos, reporte HTML de JMeter, tablas CSV/MD de resultados (muestras, promedio, p90/p95/p99, throughput, % error), graficas PNG de tiempos de respuesta y errores (jmeter/analyze_results.py o matplotlib), capturas PNG del reporte HTML con playwright, y un analisis en espanol de tiempos de respuesta y porcentaje de errores con una seccion de contexto para companeros (que es carga vs estres, que significan los percentiles). Puedes crear/ajustar archivos en jmeter/** (p.ej. jmeter/stress-test.jmx) pero no toques backend/src ni frontend/src. Apaga el backend al terminar. No hagas commit.
```

### `informe-presentacion-backlog` — agente `agy`

**Título:** Informe Word, presentacion y backlog finales  
**Depende de:** sonar-antes-despues, pruebas-unitarias, jmeter-carga-estres  
**Verificación:** `powershell -NoProfile -Command "if (-not (Test-Path docs/informe-tecnico-labtrack.docx)) { exit 1 }"`

```text
Eres el redactor de documentacion academica. Lee ../Desarrollo de Caso T3 -LabTrack.docx y ../calidad t3.png (la imagen, para ver los requisitos del entregable) y ../Historias Usuario-LabTrack.docx. En la rama YA estan las EVIDENCIAS REALES; lee los archivos y usa SOLO cifras que salgan de ellos: (1) docs/evidencias-sonarqube/INDICE-REAL.md, comparacion/real/tabla-comparativa-real.md y grafico-comparativo-real.png, antes|despues/capturas-reales/*.png (capturas REALES de la interfaz de SonarQube), */api-real/*.json, antes/README-reproduccion.md, antes/src (codigo ANTES reproducido); (2) docs/evidencias-pruebas/: capturas/*.png (salida real de pruebas antes/despues y fallidas), unitarias/*.log y *cobertura*.txt, matriz-casos.md, antes-despues/comparativo.md, testomatio-import.csv; (3) docs/evidencias-jmeter/carga/ y estres/ (summary.md, resultados_tabla.csv, charts/*.png, captura-*.png del dashboard de JMeter) y analisis-carga-estres.md (las plantillas plantilla-resultados.* ya NO aplican, hay resultados reales).
HECHOS A RESPETAR: SonarQube real ANTES = 44 issues abiertos (1 bug, 2 vulnerabilidades, 41 code smells; reliability B, security C, maintainability A) vs DESPUES 0/0/0 (A/A/A), Quality Gate Passed en ambos (solo evalua codigo nuevo). Total 44 coincide con la linea base historica docs/sonar-baseline.json (2/2/40); la clasificacion por tipo difiere levemente por la version de SonarQube (explicalo). El codigo ANTES es REPRODUCIDO, no historico (el repo tiene un solo commit); dilo con claridad en informe y presentacion. Los paneles sueltos antes/*.png y despues/*.png (en la raiz de cada carpeta) son reconstruidos: NUNCA los uses como capturas reales; usa capturas-reales/. Cobertura en SonarQube = 0.0% porque no se importo LCOV (registralo como defecto de configuracion); cobertura real de Vitest: backend 95.71%, frontend 90.26%. JMeter: carga 50 usuarios y estres 150 usuarios (confirma cifras leyendo los archivos). Pruebas unitarias 93 -> 101. Katalon y Testomat.io/TestLink NO se ejecutaron: dejalo dicho y deja plantilla y CSV; no inventes capturas de esas herramientas. Casos sugeridos por IA: validacion humana PENDIENTE. Las capturas E2E (frontend/e2e/screenshots) son de una corrida previa, no re-ejecutada; dilo. docs/evidencias-sonarqube/hallazgos.md no existe: arma los hallazgos (regla, archivo, clasificacion original, codigo ANTES de antes/src, codigo DESPUES de backend/src y frontend/src, explicacion tecnica) desde antes/api-real/issues.json. Cubre S3358, S1082, S6819, S6847, S2068, S2245, S6759, S7718, S9379, S3776. Integrantes de la portada: dejalos como marcadores [Integrante N].
TAREAS: (A) actualiza docs/generate_report.py y regenera docs/informe-tecnico-labtrack.docx (y el PDF si el flujo actual lo hace) INCRUSTANDO las capturas reales con pie de figura, secciones: introduccion, metodologia de analisis estatico, estado inicial, evidencias del ANTES, problemas detectados con codigo antes/despues, correcciones, evidencias del DESPUES, tabla y grafico comparativo, resultados de pruebas unitarias antes/despues, matriz de casos, evidencias de automatizacion, JMeter carga y estres (tablas y graficas, tiempos y % de error), SonarQube, backlog de refactorizacion, conclusiones; cada seccion con un parrafo de contexto para companeros que no conocen el proyecto. (B) actualiza docs/generate_presentation.py y regenera docs/presentacion-labtrack.pptx/.pdf con MAXIMO 5 diapositivas y un antes/despues visual con capturas reales de SonarQube. (C) actualiza docs/refactoring-backlog.md y docs/matriz-pruebas.md (defecto, prioridad, archivos/modulos, solucion, estado, evidencia de validacion). Instala con pip lo que falte (python-docx, python-pptx, matplotlib). NO modifiques backend/src, frontend/src ni docs/evidencias-*. Ejecuta los generadores y verifica que se producen los archivos, que el docx contiene las imagenes y que el pptx tiene 5 diapositivas. No hagas commit.
```

### `historias-usuario` — agente `copilot`

**Título:** Incorporar historias de usuario a informe, presentacion y backlog  
**Depende de:** informe-presentacion-backlog  
**Verificación:** `powershell -NoProfile -Command "if (-not (Test-Path docs/trazabilidad-historias-usuario.md)) { exit 1 }"`

```text
Contexto: LabTrack (backend NestJS en backend/src, frontend React en frontend/src). El informe docs/informe-tecnico-labtrack.docx (generado por docs/generate_report.py) y docs/matriz-pruebas.md, docs/refactoring-backlog.md y la presentacion (docs/generate_presentation.py) ya fueron actualizados por otro agente con evidencias reales, pero solo cubren HU-01 a HU-05. El equipo declaro como implementadas las HU-01, 02, 03, 04, 05, 06, 07, 08, 11, 13, 14 y 15: el texto exacto esta en docs/historias-usuario-implementadas.md. Lee tambien ../Historias Usuario-LabTrack.docx (historias originales) y ../Desarrollo de Caso T3 -LabTrack.docx.
TAREA: (1) Para CADA HU declarada, verifica en backend/src, frontend/src, backend/test y frontend/src/test si existe codigo y pruebas (busca controladores, servicios, paginas, pruebas por nombre/ruta) y clasificala: 'implementada con pruebas', 'implementada sin pruebas' o 'declarada, sin evidencia verificable en el repositorio'. No afirmes implementacion ni pruebas que no encuentres en el codigo. (2) Crea docs/trazabilidad-historias-usuario.md: tabla HU | descripcion | criterios de aceptacion | archivos (backend/frontend) | pruebas que la cubren | estado de evidencia. (3) Actualiza docs/generate_report.py para agregar una seccion 'Historias de usuario implementadas y trazabilidad' (con la tabla anterior, contexto para companeros que no conocen el proyecto, y los criterios de aceptacion de cada HU) y menciona las HU donde ya se hable del alcance (ya no solo HU-01..HU-05); ajusta la matriz de casos de prueba y el backlog (docs/matriz-pruebas.md, docs/refactoring-backlog.md) para referenciar las HU, y agrega a la presentacion (docs/generate_presentation.py) una mencion breve de las HU SIN pasar de 5 diapositivas. Regenera docs/informe-tecnico-labtrack.docx/.pdf y docs/presentacion-labtrack.pptx/.pdf ejecutando los generadores y verifica que se producen, que el docx contiene la seccion nueva y que el pptx sigue con 5 diapositivas. Si una HU no tiene pruebas, anotalo como brecha en el backlog (defecto, prioridad, solucion propuesta, estado 'pendiente'). NO modifiques backend/src, frontend/src ni docs/evidencias-*. No hagas commit.
```

## Pedido original del usuario (resumen)

1. Reconstruir y documentar el ANTES y DESPUÉS de SonarQube con evidencias reales (capturas), sin presentar reconstrucciones como históricas.
2. Documentar pruebas unitarias, funcionales, de carga y estrés, casos sugeridos por IA y backlog de refactorización, con contexto para los compañeros.
3. Usar la plantilla institucional de la UPN para el informe, incluir las historias de usuario implementadas y reunir todas las evidencias en `Evidencias_T3`.

## Intervenciones del líder (lo que NO hicieron los agentes de trabajo)

* Instaló y ejecutó SonarQube, `sonar-scanner`, JDK 21 portable y JMeter (los agentes no tenían estas herramientas disponibles).
* Detectó y corrigió falsos positivos del ANTES (faltaban `tsconfig.json`, `package.json` y dependencias en la copia) y un escaneo del DESPUÉS contaminado por `tsconfig` de carpetas de trabajo.
* Ejecutó realmente Selenium y encontró la regresión causada por la refactorización S6819 (selectores `[role="status"]` / `[role="dialog"]`).
* Ejecutó axe-core para accesibilidad.
* Resolvió el fallo de merge (faltaba identidad de Git local) y verificó que no se filtraran tokens al repositorio.
