# Matriz de Casos de Prueba y Trazabilidad de Calidad — LabTrack

**Curso:** Calidad y Pruebas de Software · **Caso de Estudio T3:** Sistema de Gestión de Laboratorios "LabTrack"  
**Docente:** Mark Anthony Arribasplata Palomino  
**Versión evaluada:** 1.0.0 · **Fecha:** 09/11/2026  
**Alcance funcional:** HU-01 Autenticación Segura · HU-02 Catálogo y Filtrado · HU-03 Reserva de Equipos · HU-04 Aprobación y Rechazo Administrativo · HU-05 Devolución y Penalización Automática  
**Alcance no funcional:** Rendimiento bajo Carga (50 usuarios) y Estrés (150 usuarios) con Apache JMeter 5.6.3.

---

## 1. Convenciones y Definiciones de la Matriz

| Atributo | Significado y Criterios |
|---|---|
| **Origen** | **H** = Caso diseñado directamente por el equipo humano.<br>**IA** = Caso de borde propuesto mediante asistencia de IA (**Validación humana PENDIENTE** en los casos no consolidados). |
| **Prioridad** | **P1 (Crítica)**: Afecta reglas de negocio nucleares, seguridad o transacciones financieras/académicas.<br>**P2 (Alta)**: Validación de restricciones, bordes de entrada y flujos alternativos importantes.<br>**P3 (Media)**: Mejoras de usabilidad, normalización de datos e interfaces cosméticas. |
| **Nivel / Capa** | **API**: Pruebas de integración HTTP contra NestJS usando Vitest + Supertest.<br>**UI**: Pruebas de componentes web usando Vitest + React Testing Library sobre jsdom.<br>**E2E**: Pruebas de recorrido completo con Selenium WebDriver 4.51 en Google Chrome headless (*evidencias de corrida previa*).<br>**Carga / Estrés**: Simulación de concurrencia masiva con Apache JMeter 5.6.3. |
| **Estado** | **Aprobado**: Ejecutado y conforme con los criterios de aceptación.<br>**Pendiente**: Caso sugerido por IA a la espera de validación humana formal. |

---

## 2. Resumen Ejecutivo de Ejecución de Pruebas

| Historia de Usuario / Dimensión | Casos Totales | Diseñados por Equipo (H) | Sugeridos por IA | Aprobados | Pendientes de Validación Humana | Estrategia de Automatización |
|---|---:|---:|---:|---:|---:|---|
| **HU-01: Autenticación Segura** | 12 | 8 | 4 | 12 | 0 | API + UI + E2E (Selenium) |
| **HU-02: Catálogo y Filtrado** | 11 | 7 | 4 | 11 | 0 | API + UI + E2E (Selenium) |
| **HU-03: Reserva de Equipos** | 18 | 11 | 7 | 18 | 0 | API + UI + E2E (Selenium) |
| **HU-04: Aprobación y Rechazo** | 12 | 7 | 5 | 12 | 0 | API + UI + E2E (Selenium) |
| **HU-05: Devolución y Penalización** | 8 | 5 | 3 | 8 | 0 | API + UI + E2E (Selenium) |
| **Casos IA Complementarios (Borde)** | 5 | 0 | 5 | 0 | **5 (Pendientes)** | Propuesta Backend / Frontend |
| **Subtotal Funcional** | **66** | **38** | **28** | **61** | **5** | — |
| **Rendimiento Carga (50 usuarios)** | 5 | 3 | 2 | 5 | 0 | Apache JMeter 5.6.3 |
| **Rendimiento Estrés (150 usuarios)** | 5 | 3 | 2 | 5 | 0 | Apache JMeter 5.6.3 |
| **Total General** | **76** | **44** | **32** | **71** | **5** | **Suites Vitest (101) + Selenium (7) + JMeter** |

> [!NOTE]
> **Evolución de las pruebas unitarias:** La suite de pruebas automatizadas aumentó de **93 a 101 pruebas** (+8 pruebas nuevas de límites y bordes: 53 en backend y 48 en frontend). Todas finalizaron con código de salida 0. La cobertura real de código medida con Istanbul/V8 alcanzó **95.71 % en el backend** y **90.26 % en el frontend**.
> 
> **Herramientas de gestión y pruebas E2E:**
> - Las capturas de flujos E2E (`frontend/e2e/screenshots/`) provienen de una **corrida previa documentada**, no habiéndose re-ejecutado en este ciclo.
> - **Katalon Studio y Testomat.io / TestLink NO fueron ejecutados** en esta auditoría: se incluyen las plantillas formales y el archivo de interoperabilidad `docs/evidencias-pruebas/testomatio-import.csv` para exportación/importación sin fabricar capturas ficticias.

---

## 3. Casos Sugeridos por Inteligencia Artificial (Validación Humana PENDIENTE)

De acuerdo con el procedimiento de aseguramiento de calidad, los casos exploratorios propuestos por algoritmos de IA requieren validación formal de un analista antes de ser promovidos a la suite oficial:

| ID | Caso Sugerido por IA | Prioridad | Nivel Propuesto | Comportamiento Esperado | Validación Humana |
|---|---|:---:|---|---|:---:|
| **IA-01** | Dos reservas contiguas deben ser válidas | P1 | Backend + Frontend | Si un estudiante o equipo tiene reserva 08:00–10:00, una nueva solicitud 10:00–12:00 debe aceptarse porque los extremos contiguos no se solapan. | **PENDIENTE de validación humana** |
| **IA-02** | Duración cero debe rechazarse antes del envío | P1 | Frontend (UI) | Formulario de reserva con `startTime == endTime` debe bloquear el botón de confirmación y advertir duración inválida en el cliente. | **PENDIENTE de validación humana** |
| **IA-03** | Límites exactos de atención (07:00 y 22:00) | P2 | Backend + Frontend | Petición que inicie exactamente a las 07:00 o culmine exactamente a las 22:00 debe ser admitida; reservas a las 06:59 o 22:01 deben rechazarse con HTTP 400. | **PENDIENTE de validación humana** |
| **IA-04** | Normalización de código con espacios y minúsculas | P2 | Backend (API) | Si el usuario ingresa `"  20240001  "`, el sistema debe aplicar `trim()` y reconocer el código sin arrojar error 401 indebido. | **PENDIENTE de validación humana** |
| **IA-05** | Reintento automático con token JWT expirado | P1 | Frontend + E2E | Si la sesión caduca mientras el usuario navega el catálogo, el cliente debe limpiar el almacenamiento local y redirigir limpiamente a `/login`. | **PENDIENTE de validación humana** |

---

## 4. Matriz Detallada de Pruebas Funcionales por Historia de Usuario

### HU-01 · Autenticación Segura
*Como estudiante universitario, quiero iniciar sesión en la plataforma utilizando mi código y contraseña, para acceder a mi panel personal de préstamos.*

| ID | Caso de Prueba | Origen | Prio. | Precondición | Entrada / Pasos | Resultado Esperado | Nivel · Evidencia | Estado |
|---|---|:---:|:---:|---|---|---|---|:---:|
| CP-01 | Inicio de sesión válido de estudiante | H | P1 | Usuario `20240001` activo | Código `20240001` y clave correcta; clic en "Ingresar" | HTTP 200, JWT emitido, usuario sin `passwordHash`; redirección a `/catalogo` | API `auth.spec.ts` · E2E `03-catalogo-estudiante.png` | Aprobado |
| CP-02 | Inicio de sesión válido de administrador | H | P1 | Usuario `ADMIN01` activo | Credenciales correctas de administrador | HTTP 200, rol `ADMIN`, acceso habilitado al panel de administración | API `auth.spec.ts` | Aprobado |
| CP-03 | Credenciales inválidas muestran mensaje exigido | H | P1 | Usuario existente | Contraseña errónea | HTTP 401 y mensaje exacto: **“Credenciales inválidas.”** en la interfaz | API `auth.spec.ts` · E2E `01-login-credenciales-invalidas.png` | Aprobado |
| CP-04 | Usuario inexistente no revela existencia | IA | P2 | — | Código `99999999` y contraseña cualquiera | HTTP 401 y mismo mensaje: **“Credenciales inválidas.”** (previene enumeración) | API `auth.spec.ts` | Aprobado |
| CP-05 | Bloqueo temporal tras 3 intentos fallidos | H | P1 | Usuario activo | Tres contraseñas incorrectas consecutivas | Primeros 2 intentos: 401; tercer intento: HTTP 423 `ACCOUNT_LOCKED` y alerta en pantalla | API `auth.spec.ts` · E2E `02-login-cuenta-bloqueada.png` | Aprobado |
| CP-06 | Cuenta bloqueada rechaza incluso clave correcta | H | P1 | Cuenta bloqueada por CP-05 | Credenciales válidas del usuario | HTTP 423; se mantiene `lockedUntil` en base de datos hasta cumplir el tiempo | API `auth.spec.ts` | Aprobado |
| CP-07 | Validación de campos requeridos | IA | P2 | Formulario en blanco | Clic en ingresar sin rellenar campos | HTTP 400 en API; validación visual de campos obligatorios en el cliente | API `auth.spec.ts` · UI `LoginPage.test.tsx` | Aprobado |
| CP-08 | Normalización de espacios en código | IA | P3 | Usuario activo | Código `"  20240001  "` | Código saneado por DTO; autenticación exitosa sin errores | API `auth.spec.ts` | Aprobado |
| CP-09 | Cierre de sesión (Logout) | H | P2 | Sesión activa | Clic en botón "Cerrar sesión" | Token removido de localStorage; redirección inmediata a `/login` | API `auth.spec.ts` · UI `AuthContext` | Aprobado |
| CP-10 | Estudiante restringido de rutas de administrador | H | P1 | Sesión de estudiante | Petición a `GET /api/admin/reservations` | HTTP 403 Forbidden devuelto por los Guards de NestJS | API `auth.spec.ts` y `admin.spec.ts` | Aprobado |
| CP-11 | Redirección de ruta protegida sin token | H | P1 | Sin sesión iniciada | Abrir directamente URL `/catalogo` | Redirección automática hacia `/login` por `ProtectedRoute` | UI `ProtectedRoute.test.tsx` | Aprobado |
| CP-12 | Petición API sin cabecera Bearer es denegada | IA | P2 | — | Petición HTTP sin Authorization header | HTTP 401 Unauthorized inmediato | API `auth.spec.ts` | Aprobado |

---

### HU-02 · Catálogo y Filtrado de Equipos
*Como estudiante, quiero visualizar el catálogo de equipos del laboratorio y filtrar por categorías, para encontrar rápidamente el material para mi clase.*

| ID | Caso de Prueba | Origen | Prio. | Precondición | Entrada / Pasos | Resultado Esperado | Nivel · Evidencia | Estado |
|---|---|:---:|:---:|---|---|---|---|:---:|
| CP-13 | Catálogo muestra nombre, código, categoría y estado | H | P1 | Sesión de estudiante | Acceder a `/catalogo` | Cada tarjeta muestra: nombre, código inventario, categoría y badge Disponible/Prestado | API `equipment.spec.ts` · UI `CatalogPage.test.tsx` · E2E | Aprobado |
| CP-14 | Filtro exacto por categoría "Cómputo" | H | P1 | Catálogo cargado | Clic en botón filtro "Cómputo" | Se despliegan exclusivamente equipos clasificados como `Cómputo` | API `equipment.spec.ts` · UI `CatalogPage.test.tsx` | Aprobado |
| CP-15 | Filtro exacto por categoría "Electrónica" | H | P1 | Catálogo cargado | Clic en botón filtro "Electrónica" | Se despliegan exclusivamente equipos clasificados como `Electrónica` | API `equipment.spec.ts` · E2E `04-filtro-electronica.png` | Aprobado |
| CP-16 | Filtro exacto por categoría "Redes" | H | P1 | Catálogo cargado | Clic en botón filtro "Redes" | Se despliegan exclusivamente equipos clasificados como `Redes` | API `equipment.spec.ts` · UI `CatalogPage.test.tsx` | Aprobado |
| CP-17 | Mensaje exacto cuando categoría no tiene equipos | H | P1 | Filtro sin resultados | Filtrar categoría sin inventario | Mensaje exacto: **“No hay equipos disponibles en esta categoría”** | UI `CatalogPage.test.tsx` | Aprobado |
| CP-18 | Categoría desconocida devuelve lista completa | IA | P3 | Catálogo cargado | `GET /api/equipment?category=Inexistente` | HTTP 200 y catálogo completo tolerante a fallos sin errores 500 | API `equipment.spec.ts` | Aprobado |
| CP-19 | Filtrado exclusivo de equipos disponibles | H | P2 | Inventario mixto | `GET /api/equipment/available` | Solo equipos en estado `AVAILABLE`; omite los que están `BORROWED` | API `equipment.spec.ts` | Aprobado |
| CP-20 | Búsqueda por texto en tiempo real | IA | P2 | Catálogo cargado | Escribir término de búsqueda | Filtrado reactivo de tarjetas en el cliente coincidiendo por nombre o código | UI `CatalogPage.test.tsx` | Aprobado |
| CP-21 | Métricas numéricas del catálogo | IA | P3 | Datos sembrados | `GET /api/equipment/stats` | Conteo exacto de total, disponibles, prestados y en mantenimiento | API `equipment.spec.ts` · UI `CatalogPage.test.tsx` | Aprobado |
| CP-22 | Consulta de equipo inexistente arroja 404 | IA | P3 | Sesión iniciada | `GET /api/equipment/id-inexistente` | HTTP 404 con mensaje descriptivo de no encontrado | API `equipment.spec.ts` | Aprobado |
| CP-23 | Catálogo requiere autenticación obligatoria | H | P2 | Sin credenciales | `GET /api/equipment` | HTTP 401 rechazando el acceso no autenticado | API `equipment.spec.ts` | Aprobado |

---

### HU-03 · Reserva de Equipos (Flujo Crítico)
*Como estudiante, quiero solicitar la reserva de un equipo indicando fecha y horario exacto de uso, para asegurar su disponibilidad durante mi práctica.*

| ID | Caso de Prueba | Origen | Prio. | Precondición | Entrada / Pasos | Resultado Esperado | Nivel · Evidencia | Estado |
|---|---|:---:|:---:|---|---|---|---|:---:|
| CP-24 | Registrar solicitud de reserva conforme | H | P1 | Equipo disponible | Fecha futura, horario 08:00 a 10:00 | HTTP 201 Created, estado `PENDING`, sin penalización | API `reservations.spec.ts` · E2E `05-reserva-registrada.png` | Aprobado |
| CP-25 | Bloquear solapamiento con reserva aprobada | H | P1 | Reserva aprobada 09:00–11:00 | Solicitar mismo equipo de 08:00 a 10:00 | HTTP 400 indicando cruce con reserva aprobada existente | API `reservations.spec.ts` | Aprobado |
| CP-26 | Bloquear más de una reserva activa por estudiante | H | P1 | Reserva pendiente activa | Solicitar segundo equipo en mismo horario | HTTP 400: el estudiante ya mantiene una reserva activa | API `reservations.spec.ts` | Aprobado |
| CP-27 | Reservas contiguas son admitidas sin cruce | IA | P2 | Reserva aprobada 08:00–10:00 | Solicitar mismo equipo de 10:00 a 12:00 | HTTP 201 Created; los extremos iguales no se consideran cruce | API `reservations.spec.ts` | Aprobado |
| CP-28 | Rechazar reserva sobre equipo prestado | H | P1 | Equipo en `BORROWED` | Intentar crear reserva | HTTP 400 advirtiendo que el equipo no está disponible | API `reservations.spec.ts` | Aprobado |
| CP-29 | Rechazar solicitud con fecha pasada | IA | P2 | Sesión activa | Seleccionar fecha anterior a hoy | HTTP 400 por validación de fecha retroactiva | API `reservations.spec.ts` | Aprobado |
| CP-30 | Hora de inicio posterior o igual a fin | H | P1 | Formulario abierto | Inicio 12:00 y Fin 10:00 | HTTP 400; la interfaz alerta que el inicio debe ser anterior al fin | API `reservations.spec.ts` · UI `NewReservationPage.test.tsx` | Aprobado |
| CP-31 | Restricción de duración máxima (4 horas) | H | P1 | Formulario abierto | Rango horario de 5 horas continuas | HTTP 400; bloqueo por regla de negocio de máximo 4 horas | API `reservations.spec.ts` · UI `NewReservationPage.test.tsx` | Aprobado |
| CP-32 | Horario fuera de atención del laboratorio | IA | P2 | Formulario abierto | Solicitar de 06:00 a 07:00 | HTTP 400; horario de atención permitido: 07:00 a 22:00 | API `reservations.spec.ts` | Aprobado |
| CP-33 | Formato de hora malformado en payload | IA | P2 | Petición API directa | Enviar `startTime: "8:00"` | HTTP 400 por validación de formato `HH:mm` de class-validator | API `reservations.spec.ts` | Aprobado |
| CP-34 | Estudiante penalizado no puede reservar | H | P1 | Cuenta `PENALIZED` | Intentar solicitar préstamo | HTTP 400 denegando transacción por estado de cuenta sancionado | API `reservations.spec.ts` | Aprobado |
| CP-35 | Administrador no puede solicitar préstamos | H | P2 | Sesión `ADMIN` | Petición a `POST /api/reservations` | HTTP 403; la funcionalidad de reserva es exclusiva de estudiantes | API `reservations.spec.ts` | Aprobado |
| CP-36 | Reserva con ID de equipo inexistente | IA | P2 | Sesión activa | Enviar `equipmentId` inválido | HTTP 404 indicando que el equipo no existe en catálogo | API `reservations.spec.ts` | Aprobado |
| CP-37 | Estudiante únicamente visualiza sus propias reservas | H | P1 | Reservas de varios usuarios | `GET /api/reservations/me` | Retorna estrictamente las reservas del estudiante en sesión | API `reservations.spec.ts` | Aprobado |
| CP-38 | Petición de reserva sin JWT es rechazada | H | P2 | Sin sesión | `POST /api/reservations` | HTTP 401 Unauthorized | API `reservations.spec.ts` | Aprobado |
| CP-39 | Preselección de equipo desde parámetro URL | IA | P2 | Catálogo | Navegar a `/reservar?equipo=<id>` | El formulario precarga el equipo seleccionado en el catálogo | UI `NewReservationPage.test.tsx` | Aprobado |
| CP-40 | Notificación de confirmación de solicitud | H | P2 | Formulario completo | Clic en confirmar | Mensaje de éxito visible y redirección a "Mis Reservas" | UI `NewReservationPage.test.tsx` · E2E | Aprobado |
| CP-41 | Selector de duración rápida (1h a 4h) | IA | P3 | Formulario abierto | Clic en atajo "2 horas" | Calcula automáticamente hora de fin sumando 2 horas al inicio | UI `NewReservationPage.tsx` | Aprobado |

---

### HU-04 · Gestión de Solicitudes (Panel de Administrador)
*Como encargado de laboratorio, quiero visualizar un listado con las reservas pendientes, para aprobar o rechazar las solicitudes de los estudiantes.*

| ID | Caso de Prueba | Origen | Prio. | Precondición | Entrada / Pasos | Resultado Esperado | Nivel · Evidencia | Estado |
|---|---|:---:|:---:|---|---|---|---|:---:|
| CP-42 | Listar solicitudes pendientes por defecto | H | P1 | Reservas en `PENDING` | `GET /api/admin/reservations` | Retorna lista de solicitudes pendientes con datos de estudiante y equipo | API `admin.spec.ts` · UI `AdminPendingPage.test.tsx` | Aprobado |
| CP-43 | Filtrado por estado administrativo | IA | P2 | Múltiples estados | `?status=APPROVED` o `?status=ALL` | Filtrado correcto de registros según el parámetro enviado | API `admin.spec.ts` | Aprobado |
| CP-44 | Aprobar reserva y marcar equipo como prestado | H | P1 | Solicitud pendiente | Clic en botón "Aprobar" | Estado `APPROVED`, equipo pasa a `BORROWED`, evento en auditoría | API `admin.spec.ts` · E2E `06-solicitud-aprobada.png` | Aprobado |
| CP-45 | Impedir aprobar si se genera cruce con otra aprobada | H | P1 | Conflicto de horario | Intentar aprobar solicitud en cruce | HTTP 400 por cruce de horario con otra reserva previamente aprobada | API `admin.spec.ts` | Aprobado |
| CP-46 | Solo es posible aprobar solicitudes pendientes | IA | P2 | Reserva ya aprobada | Reintentar aprobación | HTTP 400 indicando que la reserva ya no está en estado pendiente | API `admin.spec.ts` | Aprobado |
| CP-47 | Rechazo exige motivo obligatorio (mínimo 5 letras) | H | P1 | Solicitud pendiente | Confirmar rechazo sin justificación | La interfaz bloquea el envío y alerta campo requerido | API `admin.spec.ts` · UI `AdminPendingPage.test.tsx` | Aprobado |
| CP-48 | Motivo de rechazo demasiado corto | IA | P2 | Solicitud pendiente | Enviar justificación `"abc"` | HTTP 400 de validación; la solicitud permanece en `PENDING` | API `admin.spec.ts` | Aprobado |
| CP-49 | Rechazo persiste motivo visible para el estudiante | H | P1 | Solicitud pendiente | Justificar: `"Equipo en mantenimiento"` | Estado `REJECTED`, motivo guardado y visible en "Mis Reservas" | API `admin.spec.ts` · UI `MyReservationsPage.test.tsx` | Aprobado |
| CP-50 | Bloqueo de acceso de estudiantes a administración | H | P1 | Sesión estudiante | `GET /api/admin/stats` | HTTP 403 Forbidden | API `admin.spec.ts` | Aprobado |
| CP-51 | Indicadores administrativos de laboratorio | IA | P2 | Base poblada | `GET /api/admin/stats` | Conteo exacto de reservas activas, préstamos y usuarios sancionados | API `admin.spec.ts` · UI `AdminPendingPage.test.tsx` | Aprobado |
| CP-52 | Bitácora inmutable de auditoría | H | P2 | Eventos previos | `GET /api/admin/audit?limit=10` | Registro de tipo de evento, código de actor, fecha e IP | API `admin.spec.ts` | Aprobado |
| CP-53 | Manejo de aprobación sobre reserva inexistente | IA | P3 | Sesión admin | `PATCH /api/admin/reservations/9999/approve` | HTTP 404 Not Found con mensaje claro | API `admin.spec.ts` | Aprobado |

---

### HU-05 · Devolución y Penalización Automática
*Como encargado de laboratorio, quiero registrar la devolución física de un equipo en el sistema, para que vuelva a estar disponible y se penalice a los infractores.*

| ID | Caso de Prueba | Origen | Prio. | Precondición | Entrada / Pasos | Resultado Esperado | Nivel · Evidencia | Estado |
|---|---|:---:|:---:|---|---|---|---|:---:|
| CP-54 | Devolución puntual sin penalización | H | P1 | Préstamo vigente | Clic en "Marcar Devolución" a tiempo | `penaltyApplied = false`, estudiante continúa `ACTIVE`, equipo `AVAILABLE` | API `admin.spec.ts` | Aprobado |
| CP-55 | Devolución tardía penaliza automáticamente | H | P1 | Préstamo vencido | Clic en "Marcar Devolución" con retraso | `penaltyApplied = true`, estudiante cambia a `PENALIZED` automáticamente | API `admin.spec.ts` · E2E `07-devolucion-penalizada.png` | Aprobado |
| CP-56 | Equipo devuelto retorna a estado Disponible | H | P1 | Cualquier devolución | Confirmar recepción de equipo | El equipo cambia inmediatamente su estado de `BORROWED` a `AVAILABLE` | API `admin.spec.ts` | Aprobado |
| CP-57 | Solo se procesan devoluciones de reservas aprobadas | IA | P2 | Reserva en `PENDING` | Intentar devolver préstamo | HTTP 400 advirtiendo que solo aplica a reservas aprobadas | API `admin.spec.ts` | Aprobado |
| CP-58 | Registro de evento de penalización en bitácora | H | P1 | Devolución tardía | Consultar auditoría tras CP-55 | Evento `PENALTY_APPLIED` registrado con código de infractor | API `admin.spec.ts` · E2E `08-bitacora-penalizacion.png` | Aprobado |
| CP-59 | Banner de advertencia de penalización al estudiante | IA | P2 | Cuenta penalizada | Estudiante abre "Mis Reservas" | Banner visible: **"Tu cuenta está penalizada por entrega tardía"** | UI `MyReservationsPage.test.tsx` | Aprobado |
| CP-60 | Alerta previa al encargado antes de sancionar | IA | P2 | Préstamo con retraso | Abrir modal de devolución | Mensaje modal informa que la acción penalizará al estudiante | UI `AdminReturnsPage.test.tsx` | Aprobado |
| CP-61 | Indicador de tiempo transcurrido desde vencimiento | H | P3 | Préstamo vencido | Revisar panel de devoluciones | Etiqueta dinámica: `"Vencida hace X h Y min"` para priorizar | UI `AdminReturnsPage.test.tsx` | Aprobado |

---

## 5. Pruebas de Rendimiento con Apache JMeter 5.6.3

### 5.1 Escenario de Carga Nominal (50 Usuarios Concurrentes · 60 s)
* **Objetivo:** Validar cumplimiento de SLAs contractuales bajo tráfico pico regular.
* **Criterio de Aceptación:** Tasa de error HTTP ≤ 1.0 % y Percentil 95 ($p_{95}$) ≤ 3 000 ms.
* **Resultado Global:** 79,424 peticiones procesadas · **0 errores (0.00 %)** · Throughput: **1,334.07 req/s** · **$p_{95}$: 48.0 ms** · Tiempo promedio: 34.4 ms · Máximo: 230.0 ms. **Estado: APROBADA**.

| ID | Transacción | Muestras | Promedio | Mediana ($p_{50}$) | $p_{90}$ | $p_{95}$ | $p_{99}$ | Máximo | Error % | Estado |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| **PC-01** | `POST /api/auth/login` | 50 | 113.5 ms | 104.5 ms | 153.2 ms | 160.8 ms | 204.5 ms | 230.0 ms | 0.00 % | **Aprobado** |
| **PC-02** | `GET /api/equipment` | 19,865 | 34.5 ms | 34.0 ms | 43.0 ms | 49.0 ms | 89.0 ms | 215.0 ms | 0.00 % | **Aprobado** |
| **PC-03** | `GET /api/equipment?category=Cómputo` | 19,848 | 34.3 ms | 34.0 ms | 42.0 ms | 48.0 ms | 88.5 ms | 208.0 ms | 0.00 % | **Aprobado** |
| **PC-04** | `GET /api/equipment/stats` | 19,836 | 34.4 ms | 34.0 ms | 42.0 ms | 48.0 ms | 88.0 ms | 210.0 ms | 0.00 % | **Aprobado** |
| **PC-05** | `GET /api/reservations/me` | 19,825 | 34.3 ms | 33.0 ms | 42.0 ms | 48.0 ms | 88.0 ms | 195.0 ms | 0.00 % | **Aprobado** |

---

### 5.2 Escenario de Estrés y Saturación (150 Usuarios Concurrentes · 90 s)
* **Objetivo:** Evaluar estabilidad y degradación controlada bajo una demanda 3 veces superior a la nominal.
* **Criterio de Aceptación:** Tasa de error HTTP ≤ 5.0 % y Percentil 95 ($p_{95}$) ≤ 5 000 ms.
* **Resultado Global:** 113,600 peticiones procesadas · **0 errores (0.00 %)** · Throughput: **1,265.24 req/s** · **$p_{95}$: 151.0 ms** · Tiempo promedio: 108.9 ms · Máximo: 1,072.0 ms. **Estado: APROBADA**.

| ID | Transacción | Muestras | Promedio | Mediana ($p_{50}$) | $p_{90}$ | $p_{95}$ | $p_{99}$ | Máximo | Error % | Estado |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| **PE-01** | `POST /api/auth/login` | 150 | 461.2 ms | 402.5 ms | 891.7 ms | 963.3 ms | 1,033.4 ms | 1,072.0 ms | 0.00 % | **Aprobado** |
| **PE-02** | `GET /api/equipment` | 28,421 | 108.9 ms | 101.0 ms | 133.0 ms | 152.0 ms | 380.0 ms | 895.0 ms | 0.00 % | **Aprobado** |
| **PE-03** | `GET /api/equipment?category=Cómputo` | 28,377 | 108.4 ms | 101.0 ms | 132.0 ms | 150.0 ms | 380.2 ms | 910.0 ms | 0.00 % | **Aprobado** |
| **PE-04** | `GET /api/equipment/stats` | 28,345 | 108.3 ms | 101.0 ms | 131.0 ms | 150.0 ms | 374.0 ms | 880.0 ms | 0.00 % | **Aprobado** |
| **PE-05** | `GET /api/reservations/me` | 28,307 | 108.1 ms | 101.0 ms | 132.0 ms | 150.0 ms | 369.0 ms | 890.0 ms | 0.00 % | **Aprobado** |

---

## 6. Formatos de Interoperabilidad con Herramientas de Gestión de Pruebas

### 6.1 Plantilla para Katalon Studio
Para integrar estos casos en Katalon Studio sin ejecutar capturas ficticias, se provee la siguiente estructura estandarizada:

```
Test Case ID: KAT-CP-[ID]
Name: [Nombre del caso de prueba]
Description: [Propósito y regla de negocio asociada de la HU]
Pre-conditions: [Estado de base de datos y token de autenticación]
Test Steps:
  1. Set endpoint URL y cabecera Authorization (Bearer JWT).
  2. Inyectar payload JSON con datos normalizados.
  3. Ejecutar solicitud REST mediante WS.sendRequest.
Expected Result: WS.verifyResponseStatusCode(response, [Código HTTP esperado])
Actual Result: [Registrar al ejecutar en Katalon]
Status: Not Run (Plantilla lista para ejecución desatendida)
```

### 6.2 Plantilla para Testomat.io / TestLink
Se dispone del archivo exportable `docs/evidencias-pruebas/testomatio-import.csv` conteniendo los campos:
* `Suite`, `Title`, `Description`, `Preconditions`, `Steps`, `Expected Result`, `Priority`, `Status`.
* Todos los casos sugeridos por IA conservan la etiqueta `Pending human review` garantizando integridad metodológica.
