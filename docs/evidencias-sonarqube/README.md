# Evidencias SonarQube — LabTrack ANTES / DESPUÉS

Este directorio reúne la evidencia visual y de datos del contraste de calidad estática
de LabTrack entre el estado **ANTES** y el estado **DESPUÉS**.

- **Índice completo y qué demuestra cada archivo:** [`INDICE.md`](INDICE.md)
- **Cómo se reconstruyó el ANTES:** [`antes/README-reproduccion.md`](antes/README-reproduccion.md)
- **Tabla comparativa:** [`comparacion/tabla-comparativa.md`](comparacion/tabla-comparativa.md)

## Estado del escaneo

El 2026-11-09 **no fue posible ejecutar un escaneo nuevo**:

- `http://localhost:9000` no responde (no hay SonarQube levantado en este entorno).
- `SONAR_TOKEN` no está definido y `instance/sonar-token.txt` no existe.
- No hay `sonar-scanner` en `tools/` ni en `PATH`.

Por eso las cifras provienen de las instantáneas históricas del repositorio:

| Estado | Fuente | Etiqueta |
|---|---|---|
| ANTES | `docs/sonar-baseline.json` | **ANTES REPRODUCIDO** |
| DESPUÉS | `docs/sonar-data.json` (`final`) | Instantánea histórica |

Ningún PNG es una captura de la interfaz de SonarQube: son capturas de Playwright sobre
paneles HTML generados localmente a partir de esos JSON, con un aviso visible que lo
declara. Los logs documentan el bloqueo y el comando que se habría ejecutado.

## Resultado en una línea

44 hallazgos abiertos (2 bugs, 2 vulnerabilidades, 40 code smells; ratings B/C/A) →
0 hallazgos abiertos (ratings A/A/A; quality gate OK con 3 condiciones).

## Reglas de integridad aplicadas

1. El árbol ANTES se etiqueta siempre como **ANTES REPRODUCIDO**, nunca como captura
   histórica.
2. `backend/src` y `frontend/src` reales **no se tocaron**; la reconstrucción vive en
   `antes/src`.
3. El token de SonarQube **nunca** se escribe en archivos ni en logs; se pasa solo por la
   variable de entorno `SONAR_TOKEN`.
4. No se editó `sonar-project.properties`; los `projectKey` se pasan con `-D` en la línea
   de comandos.
5. Los JSON de API son reconstrucciones con forma de API, marcadas con
   `"reconstruido": true` y su `fuente`.

## Reproducibilidad

```powershell
python docs/evidencias-sonarqube/scripts/reconstruir-antes.py
python docs/evidencias-sonarqube/scripts/generar-evidencias.py
```

Los paneles HTML quedan en `render/`; los PNG se capturan desde ahí con Playwright.
