# ANTES REPRODUCIDO — guía de reconstrucción

> **Todo el árbol `docs/evidencias-sonarqube/antes/src` es una RECONSTRUCCIÓN.**
> No es una captura histórica de SonarQube ni una versión recuperada de Git.
> Se etiqueta siempre como **ANTES REPRODUCIDO**.

## 1. Por qué se reconstruye

El repositorio de LabTrack tiene **un único commit** (`840052e`, «Initial commit»).
No existe una rama, etiqueta ni commit con la versión previa a la refactorización,
así que no es posible extraer el código ANTES desde Git.

La única fuente del estado ANTES es la instantánea histórica
[`docs/sonar-baseline.json`](../../sonar-baseline.json), que registra **44 hallazgos**
(2 bugs, 2 vulnerabilidades y 40 code smells) con su regla, archivo y línea.

Para poder mostrar visualmente «el código que producía esos hallazgos», este árbol
vuelve a introducir esos 44 defectos en una **copia** de `backend/src` y `frontend/src`.

## 2. Qué se copió

```
docs/evidencias-sonarqube/antes/src/
├── backend/src/...      copia de backend/src
└── frontend/src/...     copia de frontend/src (incluye test/, que Sonar excluye)
```

Los árboles reales `backend/src` y `frontend/src` **no se modificaron**.

## 3. Cómo se generó

El script reproducible es
[`scripts/reconstruir-antes.py`](../scripts/reconstruir-antes.py):

```powershell
python docs/evidencias-sonarqube/scripts/reconstruir-antes.py
```

Hace tres cosas:

1. Copia `backend/src` y `frontend/src` dentro de `antes/src`.
2. Aplica sustituciones exactas por archivo para reintroducir cada defecto.
3. Recorre el resultado y escribe [`defectos-sembrados.json`](defectos-sembrados.json)
   con la línea real de cada marca.

## 4. Convención de marcado

Cada defecto lleva el comentario **`DEFECTO SEMBRADO (demostracion)`**, seguido de la
regla SonarQube y una descripción breve:

```ts
const id = Math.floor(Math.random() * 1_000_000); // DEFECTO SEMBRADO (demostracion) S2245 - PRNG inseguro
```

En zonas JSX, donde no se puede usar `//` dentro de una etiqueta, se usa el comentario
JSX equivalente `{/* DEFECTO SEMBRADO (demostracion) ... */}` o un comentario `//`
en la expresión JavaScript contenedora.

Los dos defectos del modal de `ui.tsx` se declaran en un comentario JSX en las líneas
219–220, pero los elementos que disparan las reglas están en las líneas **218**
(overlay con `onClick`) y **222** (`role="dialog"` sobre `div`).

## 5. Defectos reintroducidos (44)

Línea `baseline` = línea registrada en `docs/sonar-baseline.json`.
Línea `repro.` = línea real del defecto en este árbol.

### Bugs (2)

| Regla | Archivo | Línea baseline | Línea repro. | Qué se reintrodujo |
|---|---|---:|---:|---|
| `S1082` | `frontend/src/components/ui.tsx` | 218 | 218 | `div` overlay con `onClick` y sin listener de teclado |
| `S1082` | `frontend/src/components/ui.tsx` | 222 | 222 | `div role="dialog"` con `onClick` y sin teclado |

### Vulnerabilidades (2)

| Regla | Archivo | Línea baseline | Línea repro. | Qué se reintrodujo |
|---|---|---:|---:|---|
| `S2068` | `frontend/src/pages/LoginPage.tsx` | 31 | 31 | Contraseña de demostración embebida (`'Estudiante2026!'`) |
| `S2245` | `frontend/src/contexts/ToastContext.tsx` | 48 | 48 | Identificador de toast con `Math.random()` |

### Code smells (40)

#### S3358 — ternarios anidados (8)

| Archivo | Línea baseline | Línea repro. |
|---|---:|---:|
| `backend/src/admin/admin.service.ts` | 29 | 29 |
| `frontend/src/pages/AdminHistoryPage.tsx` | 98 | 62 |
| `frontend/src/pages/AdminHistoryPage.tsx` | 99 | 106 |
| `frontend/src/pages/AdminHistoryPage.tsx` | 159 | 119 |
| `frontend/src/pages/AdminPendingPage.tsx` | 152 | 153 |
| `frontend/src/pages/AdminReturnsPage.tsx` | 139 | 140 |
| `frontend/src/pages/CatalogPage.tsx` | 215 | 217 |
| `frontend/src/pages/MyReservationsPage.tsx` | 129 | 131 |

#### S6819 — rol ARIA nativo reemplazable (4)

| Archivo | Línea baseline | Línea repro. | Detalle |
|---|---:|---:|---|
| `frontend/src/components/ui.tsx` | 222 | 222 | `role="dialog"` sobre `<div>` |
| `frontend/src/contexts/ToastContext.tsx` | 62 | 61 | `role="status"` sobre `<div>` en lugar de `<output>` |
| `frontend/src/pages/CatalogPage.tsx` | 168 | 169 | `role="group"` en lugar de `<fieldset>` |
| `frontend/src/pages/MyReservationsPage.tsx` | 99 | 100 | `role="group"` en lugar de `<fieldset>` |

#### S6847 / S6848 — interactividad no nativa (2)

| Regla | Archivo | Línea baseline | Línea repro. |
|---|---|---:|---:|
| `S6847` | `frontend/src/components/ui.tsx` | 222 | 222 |
| `S6848` | `frontend/src/components/ui.tsx` | 218 | 218 |

#### S9379 — `autoFocus` (1)

| Archivo | Línea baseline | Línea repro. |
|---|---:|---:|
| `frontend/src/pages/LoginPage.tsx` | 172 | 172 |

#### S6759 — props sin `Readonly` (14)

| Archivo | Línea baseline | Línea repro. |
|---|---:|---:|
| `frontend/src/components/ui.tsx` | 29 | 29 |
| `frontend/src/components/ui.tsx` | 38 | 38 |
| `frontend/src/components/ui.tsx` | 54 | 54 |
| `frontend/src/components/ui.tsx` | 86 | 86 |
| `frontend/src/components/ui.tsx` | 113 | 113 |
| `frontend/src/components/ui.tsx` | 133 | 133 |
| `frontend/src/components/ui.tsx` | 159 | 159 |
| `frontend/src/components/ui.tsx` | 186 | 186 |
| `frontend/src/components/AppLayout.tsx` | 83 | 83 |
| `frontend/src/components/CategoryIconLabel.tsx` | 3 | 3 |
| `frontend/src/components/ProtectedRoute.tsx` | 7 | 7 |
| `frontend/src/pages/CatalogPage.tsx` | 36 | 36 |
| `frontend/src/contexts/AuthContext.tsx` | 30 | 24 |
| `frontend/src/contexts/ToastContext.tsx` | 39 | 39 |

> En `AuthContext.tsx` la regla se aplica a la interfaz `AuthProviderProps` (línea 24);
> la baseline apuntaba a la línea 30, donde estaba la firma del componente.

#### S7718 — parámetro de captura `caught` (11)

| Archivo | Línea baseline | Línea repro. |
|---|---:|---:|
| `frontend/src/pages/AdminHistoryPage.tsx` | 44 | 44 |
| `frontend/src/pages/AdminPendingPage.tsx` | 49 | 49 |
| `frontend/src/pages/AdminPendingPage.tsx` | 69 | 69 |
| `frontend/src/pages/AdminPendingPage.tsx` | 96 | 96 |
| `frontend/src/pages/AdminReturnsPage.tsx` | 54 | 54 |
| `frontend/src/pages/AdminReturnsPage.tsx` | 94 | 94 |
| `frontend/src/pages/CatalogPage.tsx` | 65 | 65 |
| `frontend/src/pages/LoginPage.tsx` | 71 | 71 |
| `frontend/src/pages/MyReservationsPage.tsx` | 44 | 44 |
| `frontend/src/pages/NewReservationPage.tsx` | 71 | 71 |
| `frontend/src/pages/NewReservationPage.tsx` | 133 | 133 |

## 6. Fidelidad y límites

- Se conservaron los **mismos archivos y las mismas reglas** de la baseline; 33 de los
  44 defectos quedaron en la **misma línea** y 38 a una línea de distancia o menos.
- En las páginas cuyo JSX se reestructuró para volver a anidar ternarios
  (`AdminHistoryPage`, `CatalogPage`, `MyReservationsPage`, `AdminPendingPage`,
  `AdminReturnsPage`) las líneas se desplazan porque el arreglo original cambió la
  estructura del bloque. La tabla anterior documenta el desplazamiento exacto.
- **No se ejecutó un escaneo** sobre este árbol: SonarQube no estaba disponible.
  Por tanto, las 44 incidencias son las registradas en la baseline histórica, no un
  resultado nuevo del analizador. Ver [`../README.md`](../README.md) y
  [`../INDICE.md`](../INDICE.md).
- Este árbol no participa del build ni de las pruebas de LabTrack; existe solo como
  evidencia documental.

## 7. Reproducir el escaneo cuando SonarQube esté disponible

```powershell
$env:SONAR_TOKEN = '<token-generado-en-SonarQube>'   # nunca se guarda en archivos
sonar-scanner `
  -Dsonar.host.url=http://localhost:9000 `
  -Dsonar.projectKey=labtrack-antes `
  -Dsonar.projectName="LabTrack ANTES (reproducido)" `
  -Dsonar.sources=docs/evidencias-sonarqube/antes/src
```

Las propiedades equivalentes están en [`sonar-antes.properties`](sonar-antes.properties).
