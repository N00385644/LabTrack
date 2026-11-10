# Evidencias de Testomat.io para LabTrack T3

- Proyecto: https://app.testomat.io/projects/labtrack-t3/
- Corrida: https://app.testomat.io/projects/labtrack-t3/runs/d1058425
- Nombre: Corrida T3 - automatizada. Tipo de registro de la plataforma: manual.
- Importación principal: CP-01 a CP-61, 61 casos con Status Aprobado en el CSV original.
- Importación complementaria: IA-01 a IA-04, 4 casos sin ejecutar con Validacion humana: pendiente.
- Resultado registrado: 61 passed, 0 failed, 0 skipped y 4 pending. Los estados provienen del CSV y no certifican una nueva ejecución de Selenium o Vitest.
- Suites: H = 38, IA = 23, Casos sugeridos por IA = 4. Las suites H e IA proceden de la columna Suite del primer CSV.
- La matriz documental propone IA-01 a IA-05. IA-05 no está en el CSV suministrado y no fue importado ni ejecutado.
- La corrida permanece abierta: Testomat.io advierte que finalizarla convertiría los pendientes en skipped.
- Cuenta con prueba gratuita Enterprise. La importación en el plan gratuito permanente no quedó verificada.

## Importación y campos

El primer intento del CSV original falló con `Runtime error Page[Tests] require columns[Folder]`. El importador nativo no ofreció mapeo libre de columnas. Se prepararon las copias compatibles conservadas aquí; las importaciones finales aceptaron 61 y 4 casos, sin filas rechazadas.

Los identificadores originales están en títulos, tags y descripción. Folder representa Suite; Priority se mapea P1=high, P2=normal y P3=low, conservando la prioridad original como campo. La descripción contiene precondiciones, pasos y resultado esperado. Automation y Status originales se conservan como campos personalizados. Status nativo indica tipo manual y no resultado de ejecución. El campo Validacion humana contiene pendiente en los cuatro casos complementarios y su suite. No se marcaron como validados.

Fuentes originales del repositorio: `docs/evidencias-pruebas/testomatio-import-completo.csv` y `docs/evidencias-pruebas/testomatio-import.csv`. No se modificaron.

## Capturas

| Archivo | Contenido |
|---|---|
| 01-suites.png | Suites y conteos del proyecto |
| 02-detalle-caso.png | CP-01 con precondiciones, pasos y resultado esperado |
| 03-run-resumen.png | Resumen de 61 passed y 4 pending |
| 04-reporte.png | Estadísticas de la corrida por suite |
| 05-casos-ia.png | Cuatro casos de IA con validación pendiente |

Las PNG se capturaron de Testomat.io y se conservaron sin alterar su contenido. El navegador produjo JPEG y se convirtió únicamente el formato de archivo a PNG. Copia de entrega: `Evidencias_T3/06-Testomatio/` junto al repositorio. No se registraron credenciales.
