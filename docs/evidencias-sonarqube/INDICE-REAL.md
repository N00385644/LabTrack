# Índice de evidencias REALES (SonarQube ejecutado en localhost:9000)

**Contexto para compañeros:** SonarQube es una herramienta de análisis estático: lee el código sin ejecutarlo y reporta
errores (bugs), fallas de seguridad (vulnerabilidades) y problemas de mantenimiento (code smells).
Se analizaron dos proyectos: `labtrack-antes` y `labtrack-despues`.

## Qué es real y qué es reproducido

| Elemento | Naturaleza |
|---|---|
| Capturas en `antes/capturas-reales/` y `despues/capturas-reales/` | **Reales**: interfaz de SonarQube 26.10 mostrando un escaneo ejecutado en esta máquina |
| JSON en `*/api-real/` | **Reales**: respuestas de la API de SonarQube |
| Logs `*/logs/scan-*-real.log` | **Reales**: salida de `sonar-scanner` (sin token) |
| Código del ANTES (`antes/src/`) | **Reproducido**: el repositorio solo tiene un commit, no existe la versión previa a las correcciones. Se reinyectaron los defectos de `docs/sonar-baseline.json` (ver `antes/README-reproduccion.md`) |
| PNG sueltos en `antes/*.png` y `despues/*.png` (paneles) | **Reconstruidos** desde los JSON históricos, con banner; NO son capturas de SonarQube. Quedan solo como referencia |

## Configuración común de ambos escaneos

* SonarQube Community Build 26.10.0.133078, `sonar-scanner` 8.3.1.16491, JDK 21.
* Perfil de calidad **Sonar way comprehensive** (TypeScript/JavaScript) en ambos proyectos.
* Mismas exclusiones: `node_modules`, `dist`, `coverage`, `*.d.ts` y `frontend/src/test`. Las pruebas (`backend/test`, `frontend/e2e`) no forman parte de `src`.
* Quality Gate por defecto ("Sonar way"): evalúa código nuevo, por eso aprueba en el primer análisis de cada proyecto.

## Capturas (en cada carpeta `capturas-reales/`)

| Archivo | Qué demuestra |
|---|---|
| `01-dashboard.png` | Resumen "Overall Code": calidad de seguridad, confiabilidad y mantenibilidad, cobertura, duplicación, Quality Gate, versión y fecha del análisis |
| `02-issues-todas.png` | Lista de issues con regla, archivo y línea |
| `03-seguridad.png` | Issues de calidad Seguridad (S2068 contraseña embebida, S2245 `Math.random()`) |
| `04-confiabilidad.png` | Issues de calidad Confiabilidad (p. ej. S1082 accesibilidad con teclado) |
| `05-mantenibilidad.png` | Issues de Mantenibilidad (S3358 ternarios anidados, S6819, S7718, etc.) |
| `06-medidas.png` | Medidas numéricas del proyecto |
| `07-actividad-fecha-version.png` | Fecha del análisis y versión (`antes-reproducido-<commit>` / `despues-<commit>`) |

## Comparación

`comparacion/real/tabla-comparativa-real.md` y `comparacion/real/grafico-comparativo-real.png`.

## Resultado real

Ver `comparacion/real/tabla-comparativa-real.md`. Los valores reales difieren de la línea base histórica (2 bugs, 2 vulnerabilidades,
40 code smells) por la versión de SonarQube, su perfil de reglas y por ser un ANTES reproducido; ambos conjuntos de datos se conservan y se explican.
