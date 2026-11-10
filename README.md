# LabTrack · Sistema de gestión de laboratorios

Aplicación web para el préstamo de equipos de laboratorio de la **Universidad Privada del Norte**, desarrollada como caso de estudio del curso **Calidad y Pruebas de Software (T3)**.

El sistema cubre las cinco historias de usuario del caso:

| HU | Funcionalidad | Criterio clave |
|---|---|---|
| HU-01 | Autenticación segura | Mensaje exacto “Credenciales inválidas.” y bloqueo tras 3 intentos fallidos |
| HU-02 | Catálogo y filtrado | Filtros exactos “Cómputo”, “Electrónica” y “Redes”; mensaje vacío “No hay equipos disponibles en esta categoría” |
| HU-03 | Reserva de equipos | Sin cruces de horario y una sola reserva activa simultánea por estudiante |
| HU-04 | Aprobación / rechazo | Solo administradores; motivo de rechazo obligatorio |
| HU-05 | Devolución | Penalización automática por devolución tardía |

## Arquitectura

```
React 18 + Vite + Tailwind  ──HTTP/JSON (JWT)──  NestJS + TypeScript
                                                     │
                                              Prisma ORM
                                                     │
                                              PostgreSQL 18
```

- **Backend:** NestJS 11, Prisma 6, JWT (Bearer), bcrypt, Swagger, validación global, cabeceras de seguridad y bitácora de auditoría.
- **Frontend:** React 18, Vite 6, React Router 6, Tailwind CSS 3, Lucide, contextos de autenticación y notificaciones.
- **Pruebas:** Vitest + Supertest + SWC (API), Vitest + React Testing Library (UI), Selenium WebDriver + Chrome headless (E2E), Apache JMeter (carga), SonarQube Community Build + SonarScanner (análisis estático).

## Estructura del repositorio

```
LabTrack/
├── backend/                 API NestJS, Prisma, pruebas de integración
│   ├── prisma/              esquema, seed y reset determinista
│   ├── src/                 módulos auth, equipment, reservations, admin
│   └── test/                suites Vitest + Supertest
├── frontend/                SPA React
│   ├── src/                 páginas, componentes, contextos y utilidades
│   └── e2e/                 flujos Selenium, capturas y reporte JUnit
├── jmeter/                  plan de carga, CSV de usuarios, análisis y reportes
├── docs/                    matriz de pruebas, informe y presentación
├── scripts/                 arranque, parada y ejecución de pruebas
├── tools/                   binarios portables (JMeter, SonarQube, escáner)
└── instance/                clúster PostgreSQL local y registros
```

## Requisitos

- Node.js 22 o superior
- PostgreSQL 16 o superior (el proyecto usa un clúster local en el puerto **55432**)
- Java 21 o superior (JMeter y SonarScanner)
- Google Chrome (Selenium)
- Python 3.11+ con `matplotlib` (gráficas de JMeter) y `python-docx` / `python-pptx` (documentos)

## Puesta en marcha

### 1. Base de datos

El clúster local se encuentra en `instance/pgdata` y escucha en el puerto `55432` con autenticación `trust` para el usuario `labtrack`.

```powershell
# Iniciar el clúster (si no está en ejecución)
& "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" -D "$PWD\instance\pgdata" -o "-p 55432" -l "$PWD\instance\postgres.log" start

# Crear las bases si no existen
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -h 127.0.0.1 -p 55432 -U labtrack labtrack
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -h 127.0.0.1 -p 55432 -U labtrack labtrack_test
```

### 2. Backend

```powershell
cd backend
npm install
copy .env.example .env      # ajustar DATABASE_URL y JWT_SECRET
npm run db:setup            # genera Prisma, crea el esquema y siembra los datos
npm run build
npm start                   # API en http://localhost:3000/api
```

Documentación Swagger: <http://localhost:3000/api/docs>

### 3. Frontend

```powershell
cd frontend
npm install
npm run build
npm run preview             # http://localhost:4173
```

También puede ejecutarse en modo desarrollo con `npm run dev`.

### Arranque automatizado

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

## Credenciales de demostración

| Rol | Código | Contraseña |
|---|---|---|
| Estudiante | `N00385644` | `Estudiante2026!` |
| Administrador | `ADMIN01` | `Admin2026!` |
| Estudiantes adicionales | `N00385645`, `N00385646` | `Estudiante2026!` |
| Usuarios de carga (JMeter) | `N00401001` … `N00401050` | `Carga2026!` |

> El seed incluye una reserva aprobada vencida del equipo `ELEC-003` para demostrar la penalización automática de HU-05.

## Pruebas

```powershell
# API: 49 pruebas, cobertura aproximada de 96 % en sentencias
cd backend
npm run test:cov

# UI: 44 pruebas de componentes, rutas y utilidades
cd frontend
npm run test:cov

# E2E: 7 flujos críticos con Selenium + Chrome headless
# Requiere API en :3000 y frontend en :4173, y una base recién sembrada
cd frontend
npm run test:e2e
```

Evidencias:

- Cobertura backend: `backend/coverage/` (HTML e informe `lcov`)
- Cobertura frontend: `frontend/coverage/`
- Capturas E2E: `frontend/e2e/screenshots/`
- Reporte JUnit E2E: `frontend/e2e/reports/junit.xml`

### Prueba de carga

```powershell
cd jmeter
powershell -ExecutionPolicy Bypass -File .\run-load-test.ps1 -Threads 50 -Duration 60 -RampUp 10
```

Salidas: `jmeter/reports/results.jtl`, `reports/html/index.html`, `reports/summary.md`, `reports/charts/*.png`.

### Análisis estático

```powershell
# Servidor SonarQube local en http://localhost:9000
powershell -ExecutionPolicy Bypass -File .\scripts\start-sonarqube.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\scan-sonar.ps1
```

## Documentación entregable

| Documento | Ruta |
|---|---|
| Matriz de pruebas (61 casos funcionales + 5 de carga) | `docs/matriz-pruebas.md` |
| Informe técnico | `docs/informe-tecnico-labtrack.pdf` / `.docx` |
| Presentación ejecutiva (5 diapositivas) | `docs/presentacion-labtrack.pptx` |
| Backlog de refactorización | `docs/refactoring-backlog.md` |
| Resumen de rendimiento | `jmeter/reports/summary.md` |

## Seguridad implementada

- Contraseñas con bcrypt (12 rondas) y nunca expuestas en las respuestas.
- JWT firmado con expiración configurable; el frontend lo envía como `Bearer`.
- Bloqueo temporal tras tres intentos fallidos y bitácora de eventos (`LOGIN_FAILED`, `LOGIN_LOCKED`, `PENALTY_APPLIED`, etc.).
- Guards de rol: los estudiantes no acceden a endpoints administrativos.
- Validación global con `whitelist` y `forbidNonWhitelisted`.
- Cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y CSP básica.
- Consultas parametrizadas mediante Prisma (sin SQL concatenado).

## Notas

- La carpeta `tools/` contiene binarios portables que no deben versionarse; se excluyen en `.gitignore`.
- La base `labtrack_test` se recrea en cada ejecución de las pruebas de API.
- Tras ejecutar las pruebas E2E, ejecutar `npm run db:reset` en `backend` para restaurar el seed determinista antes de una nueva demostración o de JMeter.
