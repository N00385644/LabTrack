# Evidencia antes/después de pruebas unitarias

## Contexto

LabTrack es una aplicación de préstamos de laboratorio con backend NestJS y frontend React. Esta comparación registra el estado de las suites antes y después de agregar casos límite, sin modificar código de producción.

## Conteo

| Capa | Antes | Después | Incremento | Resultado |
|---|---:|---:|---:|---|
| Backend | 49 pruebas, 4 archivos | 53 pruebas, 5 archivos | +4 | 53 aprobadas |
| Frontend | 44 pruebas, 12 archivos | 48 pruebas, 13 archivos | +4 | 48 aprobadas |
| Total | 93 | 101 | +8 | Todas las suites terminan con código 0 |

Las pruebas nuevas incluyen casos aprobados para ventanas de reserva, límites de atención y duración cero. Tres casos usan `it.fails` contra funciones defectuosas definidas dentro del propio test; Vitest los reporta como aprobados porque documentan la falla esperada del mock simulado. No se modificaron `backend/src` ni `frontend/src`.

La evidencia de fallas reales contra dos mocks locales está en `../unitarias/simulated-defects-failed.txt`; el archivo temporal utilizado para producirla fue eliminado.

## Evidencias completas

- Antes backend: `backend-antes.log`
- Antes frontend: `frontend-antes.log`
- Después backend y cobertura: `../unitarias/backend-cobertura.txt`
- Después frontend y cobertura: `../unitarias/frontend-cobertura.txt`
- Pruebas nuevas: `backend/test/reservation-boundaries.extra.spec.ts` y `frontend/src/test/reservation-boundaries.extra.test.ts`
