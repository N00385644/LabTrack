# Evidencia de automatización con Selenium (ejecución real)

**Contexto:** Selenium WebDriver controla un navegador Chrome real y recorre los flujos críticos de LabTrack
(login, catálogo, reserva, aprobación y devolución con penalización). Son 7 pruebas en
`frontend/e2e/critical-flows.e2e.test.ts`. Entorno: backend NestJS en `localhost:3000` con la base de pruebas
`labtrack_test` (seed con 60 usuarios de carga y reservas demo) y frontend compilado servido en `localhost:4173`.

## Qué pasó (resumen honesto)

| Corrida | Selectores del E2E | Resultado | Carpeta |
|---|---|---|---|
| 1 | Originales (`[role="status"]`, `[role="dialog"]`) sobre el código ya refactorizado | **4 aprobadas / 3 fallidas** (HU-03, HU-04, HU-05) | `corrida-1-regresion-detectada/` |
| Final | Corregidos (`output, [role="status"]` y `dialog, [role="dialog"]`) | **7 aprobadas / 0 fallidas** | `corrida-3-final-aprobada/` |

## Hallazgo: regresión causada por la refactorización S6819

La corrección de la regla SonarQube **S6819** cambió `<div role="status">` por `<output>` y `<div role="dialog">` por `<dialog>`.
Estos elementos HTML ya tienen ese rol de forma *implícita* (accesibilidad correcta), pero el selector CSS `[role="status"]` solo
detecta el atributo escrito, por lo que los tests dejaron de encontrar el aviso (toast) y el cuadro de confirmación.
El comportamiento del sistema era correcto (la reserva sí se creaba); fallaba la prueba. Se corrigió únicamente el código de
**pruebas** (`frontend/e2e/helpers/e2e.ts` y `critical-flows.e2e.test.ts`); el código de producción no se modificó.
Lección para el backlog: toda refactorización de accesibilidad debe volver a ejecutar la suite E2E.

## Capturas

* Capturas del navegador (Selenium, corrida final): `corrida-3-final-aprobada/screenshots/01..08*.png`.
* Reporte JUnit: `corrida-3-final-aprobada/junit.xml` (y `corrida-1-regresion-detectada/junit.xml`).
* Salida de consola renderizada: `../capturas/10-selenium-corrida-1-regresion.png` y `../capturas/11-selenium-corrida-3-final.png`.

## Lo que NO se ejecutó

Testomat.io y TestLink no se ejecutaron (requieren cuenta/servidor). Quedan la plantilla y el CSV `../testomatio-import.csv`
para importarlos y capturar el reporte desde la herramienta.
