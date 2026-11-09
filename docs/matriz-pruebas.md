# Matriz de casos de prueba — LabTrack

**Curso:** Calidad y Pruebas de Software · **Docente:** Mark Anthony Arribasplata Palomino  
**Sistema:** LabTrack — Gestión de préstamos de laboratorio  
**Versión evaluada:** 1.0.0 · **Fecha de ejecución:** 09/11/2026  
**Alcance:** HU-01 Autenticación · HU-02 Catálogo · HU-03 Reservas · HU-04 Aprobación/Rechazo · HU-05 Devolución y penalización

## Convenciones

| Campo | Valores |
|---|---|
| Origen | **H** = diseñado por el equipo · **IA** = sugerido por IA y validado por el equipo |
| Prioridad | **P1** crítica · **P2** alta · **P3** media |
| Nivel | **API** (Vitest + Supertest) · **UI** (Vitest + RTL) · **E2E** (Selenium) · **Carga** (JMeter) |
| Estado | **Aprobado** = ejecutado y conforme · **Fallido** = defecto abierto |

## Resumen de ejecución

| HU | Casos | H | IA | Aprobados | Fallidos | Automatización |
|---|---:|---:|---:|---:|---:|---|
| HU-01 Autenticación segura | 12 | 8 | 4 | 12 | 0 | API + UI + E2E |
| HU-02 Catálogo y filtrado | 11 | 7 | 4 | 11 | 0 | API + UI + E2E |
| HU-03 Reserva de equipos | 18 | 11 | 7 | 18 | 0 | API + UI + E2E |
| HU-04 Aprobación y rechazo | 12 | 7 | 5 | 12 | 0 | API + UI + E2E |
| HU-05 Devolución y penalización | 8 | 5 | 3 | 8 | 0 | API + UI + E2E |
| **Total funcional** | **61** | **38** | **23** | **61** | **0** | — |
| Rendimiento (JMeter) | 5 | 3 | 2 | 5 | 0 | Carga |

---

## HU-01 · Autenticación segura

| ID | Caso de prueba | Origen | Prio. | Precondición | Entrada / pasos | Resultado esperado | Nivel · Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| CP-01 | Inicio de sesión válido de estudiante | H | P1 | Usuario `20240001` activo | Código y contraseña correctos; clic en Ingresar | HTTP 200, JWT y usuario sin `passwordHash`; redirección a `/catalogo` | API `auth.spec.ts` · E2E `03-catalogo-estudiante.png` | Aprobado |
| CP-02 | Inicio de sesión válido de administrador | H | P1 | Usuario `ADMIN01` activo | Credenciales de administrador | HTTP 200 y acceso al panel administrativo | API `auth.spec.ts` | Aprobado |
| CP-03 | Credenciales inválidas muestran el mensaje exigido | H | P1 | Usuario existente | Contraseña incorrecta | HTTP 401 y texto exacto **“Credenciales inválidas.”** en login | API `auth.spec.ts` · E2E `01-login-credenciales-invalidas.png` | Aprobado |
| CP-04 | Usuario inexistente no revela su existencia | IA | P2 | — | Código `99999999` | Mismo mensaje “Credenciales inválidas.”, sin distinguir del caso anterior | API `auth.spec.ts` | Aprobado |
| CP-05 | Bloqueo tras 3 intentos fallidos consecutivos | H | P1 | Usuario activo | Tres contraseñas incorrectas seguidas | Los dos primeros intentos: 401; el tercero: 423 `ACCOUNT_LOCKED` con alerta de bloqueo temporal | API `auth.spec.ts` · E2E `02-login-cuenta-bloqueada.png` | Aprobado |
| CP-06 | Cuenta bloqueada rechaza incluso la contraseña correcta | H | P1 | Cuenta bloqueada por CP-05 | Credenciales correctas | HTTP 423; `lockedUntil` persistido en base de datos | API `auth.spec.ts` | Aprobado |
| CP-07 | Validación de campos obligatorios | IA | P2 | — | Código y contraseña vacíos | HTTP 400 con arreglo de mensajes de validación | API `auth.spec.ts` | Aprobado |
| CP-08 | Normalización del código de usuario | IA | P3 | Usuario activo | Código con espacios y minúsculas: `  20240001  ` | Inicio de sesión exitoso y código normalizado | API `auth.spec.ts` | Aprobado |
| CP-09 | Cierre de sesión | H | P2 | Sesión iniciada | `POST /api/auth/logout` y clic en Cerrar sesión | HTTP 200 y retorno a `/login`; token eliminado del cliente | API `auth.spec.ts` · UI `AuthContext` | Aprobado |
| CP-10 | Estudiante no accede al panel administrativo | H | P1 | Sesión de estudiante | `GET /api/admin/reservations` y `/api/admin/stats` | HTTP 403 en ambos endpoints | API `auth.spec.ts` y `admin.spec.ts` | Aprobado |
| CP-11 | Ruta protegida sin sesión redirige al login | H | P1 | Sin token en almacenamiento | Abrir `/catalogo` directamente | Redirección a `/login` | UI `ProtectedRoute` | Aprobado |
| CP-12 | Petición sin token es rechazada | IA | P2 | — | `GET /api/auth/me` sin cabecera Authorization | HTTP 401 | API `auth.spec.ts` | Aprobado |

## HU-02 · Catálogo y filtrado de equipos

| ID | Caso de prueba | Origen | Prio. | Precondición | Entrada / pasos | Resultado esperado | Nivel · Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| CP-13 | Catálogo muestra nombre, código, categoría y estado | H | P1 | Sesión de estudiante | Abrir `/catalogo` | Cada tarjeta muestra nombre, código de inventario, categoría y estado Disponible/Prestado | API `equipment.spec.ts` · UI `CatalogPage.test.tsx` · E2E `03-catalogo-estudiante.png` | Aprobado |
| CP-14 | Filtro exacto “Cómputo” | H | P1 | Catálogo cargado | Clic en filtro Cómputo | Solo equipos de categoría `Cómputo` | API `equipment.spec.ts` · UI `CatalogPage.test.tsx` | Aprobado |
| CP-15 | Filtro exacto “Electrónica” | H | P1 | Catálogo cargado | Clic en filtro Electrónica | Solo equipos de categoría `Electrónica` | API `equipment.spec.ts` · E2E `04-filtro-electronica.png` | Aprobado |
| CP-16 | Filtro exacto “Redes” | H | P1 | Catálogo cargado | Clic en filtro Redes | Solo equipos de categoría `Redes` | API `equipment.spec.ts` · UI `CatalogPage.test.tsx` | Aprobado |
| CP-17 | Mensaje vacío exacto por categoría sin equipos | H | P1 | Categoría sin resultados | Filtrar una categoría vacía | Texto exacto **“No hay equipos disponibles en esta categoría”** | UI `CatalogPage.test.tsx` | Aprobado |
| CP-18 | Categoría desconocida no rompe el catálogo | IA | P3 | Catálogo cargado | `GET /api/equipment?category=Inexistente` | HTTP 200 y catálogo completo sin error | API `equipment.spec.ts` | Aprobado |
| CP-19 | Endpoint de equipos disponibles | H | P2 | Inventario con equipos prestados | `GET /api/equipment/available` | Solo equipos `AVAILABLE`; excluye `BORROWED` | API `equipment.spec.ts` | Aprobado |
| CP-20 | Búsqueda por nombre o código de inventario | IA | P2 | Catálogo cargado | Escribir “router” en el buscador | Se muestran solo coincidencias; se ocultan las demás tarjetas | UI `CatalogPage.test.tsx` | Aprobado |
| CP-21 | Indicadores del catálogo | IA | P3 | Datos sembrados | `GET /api/equipment/stats` | Totales de equipos, disponibles, prestados, pendientes y estudiantes correctos | API `equipment.spec.ts` · UI `CatalogPage.test.tsx` | Aprobado |
| CP-22 | Detalle de equipo inexistente | IA | P3 | Sesión activa | `GET /api/equipment/no-existe` | HTTP 404 | API `equipment.spec.ts` | Aprobado |
| CP-23 | Catálogo exige autenticación | H | P2 | Sin token | `GET /api/equipment` | HTTP 401 | API `equipment.spec.ts` | Aprobado |

## HU-03 · Reserva de equipos

| ID | Caso de prueba | Origen | Prio. | Precondición | Entrada / pasos | Resultado esperado | Nivel · Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| CP-24 | Registrar reserva pendiente | H | P1 | Equipo disponible y estudiante activo | Equipo + fecha futura + 08:00–10:00 | HTTP 201, estado `PENDING`, sin penalización | API `reservations.spec.ts` · E2E `05-reserva-registrada.png` | Aprobado |
| CP-25 | Bloquear cruce con reserva aprobada del mismo equipo | H | P1 | Reserva aprobada 09:00–11:00 | Solicitar 08:00–10:00 para el mismo equipo y fecha | HTTP 400 indicando cruce con reserva aprobada | API `reservations.spec.ts` | Aprobado |
| CP-26 | Una sola reserva activa simultánea por estudiante | H | P1 | Reserva pendiente 08:00–10:00 | Segunda reserva 09:00–11:00 en otro equipo | HTTP 400: el estudiante ya tiene una reserva activa | API `reservations.spec.ts` | Aprobado |
| CP-27 | Reservas contiguas sin cruce son válidas | IA | P2 | Reserva aprobada 08:00–10:00 | Solicitar 10:00–12:00 | HTTP 201; los extremos contiguos no se consideran cruce | API `reservations.spec.ts` | Aprobado |
| CP-28 | Equipo no disponible es rechazado | H | P1 | Equipo en estado `BORROWED` | Intentar reservarlo | HTTP 400 “no está disponible” | API `reservations.spec.ts` | Aprobado |
| CP-29 | Fecha pasada es rechazada | IA | P2 | Sesión activa | Fecha `2020-01-01` | HTTP 400 por fechas pasadas | API `reservations.spec.ts` | Aprobado |
| CP-30 | Hora de inicio posterior a la de fin | H | P1 | Formulario abierto | Inicio 12:00, fin 10:00 | HTTP 400; la UI muestra “anterior a la hora de fin” | API `reservations.spec.ts` · UI `NewReservationPage.test.tsx` | Aprobado |
| CP-31 | Máximo 4 horas continuas | H | P1 | Formulario abierto | 08:00–13:00 | HTTP 400; la UI muestra límite de 4 horas | API `reservations.spec.ts` · UI `NewReservationPage.test.tsx` | Aprobado |
| CP-32 | Horario fuera de atención | IA | P2 | Formulario abierto | 06:00–08:00 | HTTP 400; atención 07:00–22:00 | API `reservations.spec.ts` | Aprobado |
| CP-33 | Formato de hora inválido | IA | P2 | Petición directa | `startTime: "8:00"` | HTTP 400 con errores de validación del DTO | API `reservations.spec.ts` | Aprobado |
| CP-34 | Estudiante penalizado no puede reservar | H | P1 | Usuario `PENALIZED` | Intentar crear reserva | HTTP 400 indicando cuenta penalizada | API `reservations.spec.ts` | Aprobado |
| CP-35 | Administrador no puede crear reservas | H | P2 | Sesión de administrador | `POST /api/reservations` | HTTP 403 | API `reservations.spec.ts` | Aprobado |
| CP-36 | Equipo inexistente | IA | P2 | Sesión de estudiante | `equipmentId` inválido | HTTP 404 “no existe” | API `reservations.spec.ts` | Aprobado |
| CP-37 | Estudiante solo ve sus propias reservas | H | P1 | Reservas de dos estudiantes | `GET /api/reservations/me` | Solo las reservas del estudiante autenticado | API `reservations.spec.ts` | Aprobado |
| CP-38 | Reserva exige autenticación | H | P2 | Sin token | `POST /api/reservations` | HTTP 401 | API `reservations.spec.ts` | Aprobado |
| CP-39 | Preselección del equipo desde el catálogo | IA | P2 | Sesión activa | Abrir `/reservar?equipo=<id>` | El selector y el panel de detalle muestran el equipo elegido | UI `NewReservationPage.test.tsx` | Aprobado |
| CP-40 | Confirmación de solicitud registrada | H | P2 | Equipo preseleccionado | Enviar formulario válido | Mensaje “Reserva registrada. Queda pendiente de aprobación.” y redirección a Mis reservas | UI `NewReservationPage.test.tsx` · E2E `05-reserva-registrada.png` | Aprobado |
| CP-41 | Duración rápida de 1 a 4 horas | IA | P3 | Formulario abierto | Clic en “2 h” | Hora de fin ajustada a inicio + 2 horas sin exceder 22:00 | UI `NewReservationPage.tsx` (validación local) | Aprobado |

## HU-04 · Aprobación y rechazo de solicitudes

| ID | Caso de prueba | Origen | Prio. | Precondición | Entrada / pasos | Resultado esperado | Nivel · Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| CP-42 | Listar solicitudes pendientes por defecto | H | P1 | Solicitudes en `PENDING` | `GET /api/admin/reservations` | Solo pendientes con datos de estudiante y equipo | API `admin.spec.ts` · UI `AdminPendingPage.test.tsx` | Aprobado |
| CP-43 | Filtro por estado y opción ALL | IA | P2 | Reservas en varios estados | `?status=APPROVED` y `?status=ALL` | Filtrado correcto y listado completo respectivamente | API `admin.spec.ts` | Aprobado |
| CP-44 | Aprobar reserva y marcar equipo como prestado | H | P1 | Solicitud pendiente | Clic en Aprobar | Estado `APPROVED`, revisor y fecha; equipo pasa a `BORROWED`; evento de auditoría | API `admin.spec.ts` · E2E `06-solicitud-aprobada.png` | Aprobado |
| CP-45 | No aprobar una reserva que cruza otra aprobada | H | P1 | Reserva aprobada 09:00–11:00 | Aprobar pendiente 10:00–12:00 | HTTP 400 por cruce con otra reserva aprobada | API `admin.spec.ts` | Aprobado |
| CP-46 | Solo se aprueban reservas pendientes | IA | P2 | Reserva ya aprobada | Volver a aprobar | HTTP 400 indicando que solo aplica a pendientes | API `admin.spec.ts` | Aprobado |
| CP-47 | Rechazo exige motivo obligatorio | H | P1 | Solicitud pendiente | Abrir modal y confirmar sin motivo | Error “al menos 5 caracteres”; no se llama al API | API `admin.spec.ts` · UI `AdminPendingPage.test.tsx` | Aprobado |
| CP-48 | Motivo de rechazo demasiado corto | IA | P2 | Solicitud pendiente | Motivo `abc` | HTTP 400 y la reserva permanece `PENDING` | API `admin.spec.ts` | Aprobado |
| CP-49 | Rechazo guarda el motivo visible al estudiante | H | P1 | Solicitud pendiente | Motivo “Equipo en mantenimiento preventivo” | Estado `REJECTED`, motivo y revisor persistidos; visible en Mis reservas | API `admin.spec.ts` · UI `MyReservationsPage.test.tsx` | Aprobado |
| CP-50 | Estudiante sin acceso al panel administrativo | H | P1 | Sesión de estudiante | Consultar reservas y métricas administrativas | HTTP 403 en todos los endpoints | API `admin.spec.ts` | Aprobado |
| CP-51 | Métricas administrativas | IA | P2 | Datos sembrados | `GET /api/admin/stats` | Pendientes, aprobadas, devoluciones de hoy, penalizados e inventario correctos | API `admin.spec.ts` · UI `AdminPendingPage.test.tsx` | Aprobado |
| CP-52 | Bitácora de auditoría disponible | H | P2 | Eventos registrados | `GET /api/admin/audit?limit=10` | Eventos con tipo, actor, fecha e IP | API `admin.spec.ts` | Aprobado |
| CP-53 | Aprobar reserva inexistente | IA | P3 | Sesión de administrador | `PATCH /api/admin/reservations/no-existe/approve` | HTTP 404 | API `admin.spec.ts` | Aprobado |

## HU-05 · Devolución y penalización automática

| ID | Caso de prueba | Origen | Prio. | Precondición | Entrada / pasos | Resultado esperado | Nivel · Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| CP-54 | Devolución puntual sin penalización | H | P1 | Reserva aprobada vigente | Registrar devolución antes del fin | `late=false`, `penaltyApplied=false`; estudiante sigue `ACTIVE` | API `admin.spec.ts` | Aprobado |
| CP-55 | Devolución tardía penaliza automáticamente | H | P1 | Reserva aprobada con fecha vencida | Registrar devolución | `late=true`, `penaltyApplied=true`; estudiante pasa a `PENALIZED` | API `admin.spec.ts` · E2E `07-devolucion-penalizada.png` | Aprobado |
| CP-56 | El equipo vuelve a estar disponible | H | P1 | Cualquier devolución | Confirmar devolución | Equipo en estado `AVAILABLE` | API `admin.spec.ts` | Aprobado |
| CP-57 | Solo se devuelven reservas aprobadas | IA | P2 | Reserva pendiente | Intentar devolución | HTTP 400 indicando que solo aplica a aprobadas | API `admin.spec.ts` | Aprobado |
| CP-58 | Evento de penalización en la bitácora | H | P1 | Devolución tardía registrada | Consultar bitácora | Evento `PENALTY_APPLIED` con el código del estudiante | API `admin.spec.ts` · E2E `08-bitacora-penalizacion.png` | Aprobado |
| CP-59 | Aviso de cuenta penalizada al estudiante | IA | P2 | Usuario `PENALIZED` | Abrir Mis reservas | Banner “Tu cuenta está penalizada” visible | UI `MyReservationsPage.test.tsx` | Aprobado |
| CP-60 | Advertencia previa a confirmar devolución tardía | IA | P2 | Préstamo vencido | Abrir modal de devolución | Mensaje que anuncia el cambio automático a Penalizado | UI `AdminReturnsPage.test.tsx` · E2E | Aprobado |
| CP-61 | Indicador de puntualidad del préstamo | H | P3 | Préstamo con fecha vencida | Abrir panel de devoluciones | Etiqueta “Vencida hace X h Y min” | UI `AdminReturnsPage.test.tsx` | Aprobado |

---

## Pruebas de rendimiento (JMeter)

Escenario: 50 usuarios concurrentes, ramp-up 10 s, duración 60 s, umbral de aceptación p95 < 3 000 ms y 0 % de errores.

| ID | Transacción | Origen | Prio. | Umbral | Resultado medido | Estado |
|---|---|---|---|---|---|---|
| PC-01 | `POST /api/auth/login` (JWT) | H | P1 | p95 < 3 000 ms | 90 ms p95 · 76.1 ms promedio · 0 errores | Aprobado |
| PC-02 | `GET /api/equipment` | H | P1 | p95 < 3 000 ms | 18 ms p95 · 14.1 ms promedio · 0 errores | Aprobado |
| PC-03 | `GET /api/equipment?category=Cómputo` | H | P2 | p95 < 3 000 ms | 18 ms p95 · 14.1 ms promedio · 0 errores | Aprobado |
| PC-04 | `GET /api/equipment/stats` | IA | P2 | p95 < 3 000 ms | 18 ms p95 · 14.2 ms promedio · 0 errores | Aprobado |
| PC-05 | `GET /api/reservations/me` | IA | P2 | p95 < 3 000 ms | 18 ms p95 · 14.0 ms promedio · 0 errores | Aprobado |

**Resultado global:** 194,629 peticiones · 0 errores (0.00 %) · 3,248.69 req/s · p95 18 ms · máximo 186 ms.  
**Veredicto:** APROBADA — capacidad muy superior al mínimo requerido para la operación del laboratorio.

## Trazabilidad de la automatización

| Suite | Herramienta | Archivos | Casos |
|---|---|---|---:|
| API backend | Vitest + Supertest + SWC | `backend/test/auth.spec.ts`, `equipment.spec.ts`, `reservations.spec.ts`, `admin.spec.ts` | 49 |
| Interfaz web | Vitest + React Testing Library | `frontend/src/test/*.test.tsx` y `format.test.ts` | 44 |
| E2E navegador real | Selenium WebDriver 4.51 + Chrome headless | `frontend/e2e/critical-flows.e2e.test.ts` | 7 flujos |
| Carga y estrés | Apache JMeter 5.6.3 | `jmeter/load-test.jmx` | 5 transacciones |
| **Total automatizado** | — | — | **100 ejecuciones + 5 transacciones de carga** |

## Defectos abiertos

Ninguno. Todas las pruebas planificadas finalizaron conformes tras la corrección de los hallazgos descritos en el informe técnico (sección Análisis estático y refactorización).
