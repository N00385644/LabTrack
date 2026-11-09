# Historias de Usuario Implementadas (fuente: equipo, texto proporcionado por el estudiante)

**HU-01: Autenticación Segura y Control de Bloqueos**
- Login con código de estudiante en formato estricto: `N0` seguido de 8 dígitos (`^N0\d{8}$`).
- Mensaje de credenciales inválidas: "Credenciales inválidas".
- Bloqueo temporal por 15 minutos al acumular 3 intentos fallidos consecutivos.

**HU-02: Catálogo y Filtrado de Equipos**
- Filtros exactos por categorías: "Cómputo", "Electrónica" y "Redes".
- Mensaje exacto cuando no hay equipos disponibles: "No hay equipos disponibles en esta categoría".

**HU-03: Reserva de Equipos (Flujo Crítico)**
- Validación transaccional contra cruce de horarios para el mismo equipo.
- Regla de negocio: máximo un (1) equipo reservado o prestado de forma simultánea por estudiante.
- Bloqueo inmediato si el estudiante se encuentra penalizado.

**HU-04: Gestión de Solicitudes (Panel de Administrador)**
- Aprobación y rechazo con motivo obligatorio.

**HU-05: Devolución y Penalización Automática**
- Al marcar devolución el equipo pasa a Disponible.
- Si la hora de devolución física supera la hora fin acordada, el sistema cambia automáticamente el estado del alumno a "Penalizado" (7 días de suspensión).

**HU-06: Carnet Digital QR del Estudiante**
- Credencial digital para escaneo ágil en ventanilla.

**HU-07: Gestión Integral de Equipos (CRUD Admin)**
- Registro de equipos con fotos, especificaciones, ubicación y generación de código QR.

**HU-08: Gestión de Penalizaciones y Levantamiento**
- Panel administrativo para levantar sanciones con justificación médica o académica.

**HU-11: Dashboard y Métricas de Uso**
- Gráficos de distribución de inventario y tasa de puntualidad.

**HU-13: Administración y Creación de Usuarios (CRUD Admin)**
- Creación de alumnos (`N0XXXXXXXX`) o administradores, reseteo de claves y botón para desbloquear cuentas bloqueadas tras 3 intentos.

**HU-14: Escaneo Rápido con Cámara / Lector QR**
- Despacho y devolución rápida en ventanilla sin teclear manualmente.

**HU-15: Acta Oficial de Préstamo en PDF**
- Descarga en 1 clic de constancia formal con cláusula de responsabilidad del estudiante.

> Nota para quien documente: esta lista es el alcance declarado por el equipo. No toda HU tiene necesariamente
> código, pruebas o evidencia en este repositorio. Verifica en `backend/src` y `frontend/src` qué HU están realmente
> implementadas y cuáles tienen pruebas; donde no haya evidencia, indícalo como "declarada, sin evidencia verificable en el repositorio".
