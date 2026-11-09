"""Reconstruye la version ANTES de LabTrack para la evidencia SonarQube.

Copia backend/src y frontend/src dentro de docs/evidencias-sonarqube/antes/src y
vuelve a introducir, en los mismos archivos registrados en docs/sonar-baseline.json,
los 44 hallazgos del estado ANTES (S3358, S1082, S6819, S6847, S6848, S2068, S2245,
S6759, S7718 y S9379).

REGLA: todo lo generado aqui es ANTES REPRODUCIDO, no una captura historica.
Cada defecto queda marcado con el comentario "DEFECTO SEMBRADO (demostracion)".

Uso:
    python docs/evidencias-sonarqube/scripts/reconstruir-antes.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / "docs" / "evidencias-sonarqube" / "antes"
SRC = DEST / "src"

MARK = "DEFECTO SEMBRADO (demostracion)"


def copy_sources() -> None:
    for top in ("backend", "frontend"):
        src = ROOT / top / "src"
        target = SRC / top / "src"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def write(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(text)


def sub(path: Path, old: str, new: str, expected: int = 1) -> None:
    text = read(path)
    found = text.count(old)
    if found != expected:
        raise SystemExit(f"{path}: se esperaban {expected} coincidencias, hay {found}:\n{old[:200]}")
    write(path, text.replace(old, new))


def seed() -> None:
    # ------------------------------------------------------------------
    # backend/src/admin/admin.service.ts  -> S3358 (linea 29 de baseline)
    # ------------------------------------------------------------------
    sub(
        SRC / "backend" / "src" / "admin" / "admin.service.ts",
        """    let where: Prisma.ReservationWhereInput = { status: 'PENDING' };
    if (status === 'ALL') {
      where = {};
    } else if (isKnownStatus) {
      where = { status: status as ReservationStatus };
    }
""",
        """    let where: Prisma.ReservationWhereInput = { status: 'PENDING' };
    where = status === 'ALL' ? {} : isKnownStatus ? { status: status as ReservationStatus } : where; // DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado
""",
    )

    # ------------------------------------------------------------------
    # frontend/src/components/ui.tsx
    #   S6759 x8 (lineas 29,38,54,86,113,133,159,186)
    #   S1082 x2 + S6848 (218) y S6819 + S6847 + S1082 (222)
    # ------------------------------------------------------------------
    ui = SRC / "frontend" / "src" / "components" / "ui.tsx"
    text = read(ui)
    if text.count("Readonly<") != 8 or text.count("}>)") != 8:
        raise SystemExit("ui.tsx: no se encontraron exactamente 8 props Readonly")
    text = text.replace("Readonly<", "").replace("}>)", "})")
    write(ui, text)

    for signature in (
        "export function StatusBadge({ status }: { status: ReservationStatus }) {",
        "export function EquipmentStatusBadge({ status }: { status: EquipmentStatus }) {",
        "export function PageHeader({",
        "export function StatCard({",
        "export function LoadingBlock({ label = 'Cargando información…' }: { label?: string }) {",
        "export function ErrorAlert({",
        "export function EmptyState({",
        "export function Modal({",
    ):
        sub(ui, signature, signature + " // DEFECTO SEMBRADO (demostracion) S6759 - props sin Readonly")

    sub(
        ui,
        """    <div className="fixed inset-0 z-[90] flex items-end justify-center p-4 sm:items-center">
      <button
        type="button"
        aria-label="Cerrar modal"
        onClick={onClose}
        className="absolute inset-0 bg-navy-950/50 backdrop-blur-sm"
      />
      <dialog
        open
        aria-modal="true"
        aria-label={title}
        className="relative m-0 w-full max-w-lg animate-fade-up rounded-2xl border-0 bg-white p-0 shadow-lift"
      >
""",
        """    <div className="fixed inset-0 z-[90] flex items-end justify-center p-4 sm:items-center" onClick={onClose} role="presentation">
      {/* DEFECTO SEMBRADO (demostracion) S1082 S6848 - overlay div clicable sin teclado
          DEFECTO SEMBRADO (demostracion) S6819 S6847 S1082 - role="dialog" sobre un div nativo */}
      <div className="absolute inset-0 bg-navy-950/50 backdrop-blur-sm" />
      <div role="dialog" aria-modal="true" aria-label={title} onClick={(event) => event.stopPropagation()} className="relative m-0 w-full max-w-lg animate-fade-up rounded-2xl border-0 bg-white p-0 shadow-lift">
""",
    )
    sub(ui, "      </dialog>\n", "      </div>\n")

    # ------------------------------------------------------------------
    # frontend/src/contexts/ToastContext.tsx -> S6759 (39), S2245 (48), S6819 (62)
    # ------------------------------------------------------------------
    toast = SRC / "frontend" / "src" / "contexts" / "ToastContext.tsx"
    sub(
        toast,
        "export function ToastProvider({ children }: Readonly<{ children: ReactNode }>) {",
        "export function ToastProvider({ children }: { children: ReactNode }) { // DEFECTO SEMBRADO (demostracion) S6759 - props sin Readonly",
    )
    sub(toast, "let toastSequence = 0;\n\n", "")
    sub(
        toast,
        "      const id = ++toastSequence;",
        "      const id = Math.floor(Math.random() * 1_000_000); // DEFECTO SEMBRADO (demostracion) S2245 - PRNG inseguro",
    )
    sub(
        toast,
        """      {children}
      <div className="pointer-events-none fixed right-4 top-24 z-[100] flex w-[min(380px,calc(100vw-32px))] flex-col gap-2">""",
        """      {children}
      {/* DEFECTO SEMBRADO (demostracion) S6819 - role="status" en div en lugar de <output> */}
      <div role="status" className="pointer-events-none fixed right-4 top-24 z-[100] flex w-[min(380px,calc(100vw-32px))] flex-col gap-2">""",
    )
    sub(toast, "          <output\n", "          <div\n")
    sub(toast, "          </output>\n", "          </div>\n")

    # ------------------------------------------------------------------
    # frontend/src/pages/AdminHistoryPage.tsx -> S7718 (44), S3358 (98,99,159)
    # ------------------------------------------------------------------
    history = SRC / "frontend" / "src" / "pages" / "AdminHistoryPage.tsx"
    sub(history, "    } catch (error_) {", "    } catch (caught) { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught")
    sub(history, "setError(error_ instanceof Error ? error_.message", "setError(caught instanceof Error ? caught.message")
    # Tercer ternario anidado, en el subtitulo (los otros dos quedan en los bloques de abajo).
    sub(
        history,
        """        subtitle="Consulta todas las reservas registradas y la bitácora de eventos de seguridad y operación."
""",
        """        subtitle={
          // DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado
          tab === 'reservations'
            ? `${reservations.length} reservas registradas`
            : tab === 'audit'
              ? `${audit.length} eventos de auditoría`
              : 'Historial del laboratorio'
        }
""",
    )
    sub(
        history,
        """      {!loading && tab === 'reservations' && reservations.length === 0 ? (
          <EmptyState
            icon={<History className="h-6 w-6" />}
            title="Todavía no hay reservas registradas"
            message="Las solicitudes de los estudiantes aparecerán en este historial."
          />
      ) : null}
""",
        """      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading && tab === 'reservations'
        ? reservations.length === 0
          ? (
              <EmptyState
                icon={<History className="h-6 w-6" />}
                title="Todavía no hay reservas registradas"
                message="Las solicitudes de los estudiantes aparecerán en este historial."
              />
            )
          : null
        : null}
""",
    )
    sub(
        history,
        "      {!loading && tab === 'reservations' && reservations.length > 0 ? (\n",
        """      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading && tab === 'reservations'
        ? reservations.length > 0
          ? (
""",
    )
    sub(
        history,
        """          </div>
      ) : null}

      {!loading && tab === 'audit' && audit.length === 0 ? (""",
        """          </div>
            )
          : null
        : null}

      {!loading && tab === 'audit' && audit.length === 0 ? (""",
    )

    # ------------------------------------------------------------------
    # frontend/src/pages/AdminPendingPage.tsx -> S3358 (152), S7718 (49,69,96)
    # ------------------------------------------------------------------
    pending = SRC / "frontend" / "src" / "pages" / "AdminPendingPage.tsx"
    pending_text = read(pending)
    if pending_text.count("} catch (error_) {") != 3:
        raise SystemExit("AdminPendingPage: se esperaban 3 catch(error_)")
    pending_text = pending_text.replace(
        "    } catch (error_) {",
        "    } catch (caught) { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught",
    )
    pending_text = pending_text.replace("setError(error_ instanceof Error ? error_.message", "setError(caught instanceof Error ? caught.message")
    pending_text = pending_text.replace(
        "toast.push(error_ instanceof Error ? error_.message",
        "toast.push(caught instanceof Error ? caught.message",
    )
    pending_text = pending_text.replace(
        "setRejectError(error_ instanceof Error ? error_.message",
        "setRejectError(caught instanceof Error ? caught.message",
    )
    write(pending, pending_text)
    sub(
        pending,
        """      {!loading && reservations.length === 0 ? (
        <EmptyState
          testId="empty-pending"
          icon={<CheckCircle2 className="h-6 w-6" />}
          title="No hay solicitudes pendientes"
          message="Todas las reservas han sido revisadas. Las nuevas solicitudes aparecerán aquí."
        />
      ) : null}
""",
        """      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading
        ? reservations.length === 0
          ? (
              <EmptyState
                testId="empty-pending"
                icon={<CheckCircle2 className="h-6 w-6" />}
                title="No hay solicitudes pendientes"
                message="Todas las reservas han sido revisadas. Las nuevas solicitudes aparecerán aquí."
              />
            )
          : null
        : null}
""",
    )

    # ------------------------------------------------------------------
    # frontend/src/pages/AdminReturnsPage.tsx -> S3358 (139), S7718 (54,94)
    # ------------------------------------------------------------------
    returns = SRC / "frontend" / "src" / "pages" / "AdminReturnsPage.tsx"
    returns_text = read(returns)
    if returns_text.count("} catch (error_) {") != 2:
        raise SystemExit("AdminReturnsPage: se esperaban 2 catch(error_)")
    returns_text = returns_text.replace(
        "    } catch (error_) {",
        "    } catch (caught) { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught",
    )
    returns_text = returns_text.replace("setError(error_ instanceof Error ? error_.message", "setError(caught instanceof Error ? caught.message")
    returns_text = returns_text.replace(
        "toast.push(error_ instanceof Error ? error_.message",
        "toast.push(caught instanceof Error ? caught.message",
    )
    write(returns, returns_text)
    sub(
        returns,
        """      {!loading && filtered.length === 0 ? (
        <EmptyState
          testId="empty-returns"
          icon={<Undo2 className="h-6 w-6" />}
          title="No hay préstamos activos por devolver"
          message="Cuando se apruebe una reserva, el equipo aparecerá aquí hasta que registres su devolución."
        />
      ) : null}
""",
        """      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading
        ? filtered.length === 0
          ? (
              <EmptyState
                testId="empty-returns"
                icon={<Undo2 className="h-6 w-6" />}
                title="No hay préstamos activos por devolver"
                message="Cuando se apruebe una reserva, el equipo aparecerá aquí hasta que registres su devolución."
              />
            )
          : null
        : null}
""",
    )

    # ------------------------------------------------------------------
    # frontend/src/pages/CatalogPage.tsx -> S6759 (36), S7718 (65), S6819 (168), S3358 (215)
    # ------------------------------------------------------------------
    catalog = SRC / "frontend" / "src" / "pages" / "CatalogPage.tsx"
    sub(
        catalog,
        "function CategoryIcon({ category, className }: Readonly<{ category: string; className?: string }>) {",
        "function CategoryIcon({ category, className }: { category: string; className?: string }) { // DEFECTO SEMBRADO (demostracion) S6759 - props sin Readonly",
    )
    sub(
        catalog,
        "      .catch((error_) => {",
        "      .catch((caught) => { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught",
    )
    sub(catalog, "setError(error_ instanceof Error ? error_.message", "setError(caught instanceof Error ? caught.message")
    sub(
        catalog,
        """          <fieldset className="flex flex-wrap items-center gap-2">
            <legend className="sr-only">Filtrar por categoría</legend>
""",
        """          {/* DEFECTO SEMBRADO (demostracion) S6819 - role="group" en div nativo */}
          <div role="group" aria-label="Filtrar por categoría" className="flex flex-wrap items-center gap-2">
""",
    )
    sub(catalog, "          </fieldset>\n", "          </div>\n")
    sub(
        catalog,
        """      {!loading && filtered.length === 0 ? (
        <EmptyState
          testId="empty-catalog"
          icon={<Inbox className="h-6 w-6" />}
          title="No hay equipos disponibles en esta categoría"
          message="Prueba con otra categoría o limpia el término de búsqueda."
          action={
            <button
              type="button"
              onClick={() => {
                setCategory('Todos');
                setSearch('');
              }}
              className="btn-ghost btn-sm mt-1"
            >
              Ver todos los equipos
            </button>
          }
        />
      ) : null}
""",
        """      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading
        ? filtered.length === 0
          ? (
              <EmptyState
                testId="empty-catalog"
                icon={<Inbox className="h-6 w-6" />}
                title="No hay equipos disponibles en esta categoría"
                message="Prueba con otra categoría o limpia el término de búsqueda."
                action={
                  <button
                    type="button"
                    onClick={() => {
                      setCategory('Todos');
                      setSearch('');
                    }}
                    className="btn-ghost btn-sm mt-1"
                  >
                    Ver todos los equipos
                  </button>
                }
              />
            )
          : null
        : null}
""",
    )

    # ------------------------------------------------------------------
    # frontend/src/pages/LoginPage.tsx -> S2068 (31), S7718 (71), S9379 (172)
    # ------------------------------------------------------------------
    login = SRC / "frontend" / "src" / "pages" / "LoginPage.tsx"
    sub(
        login,
        "    password: import.meta.env.VITE_DEMO_STUDENT_PASSWORD ?? '',",
        "    password: 'Estudiante2026!', // DEFECTO SEMBRADO (demostracion) S2068 - credencial embebida",
    )
    sub(login, "    } catch (error_) {", "    } catch (caught) { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught")
    sub(login, "setError(error_ instanceof Error ? error_.message", "setError(caught instanceof Error ? caught.message")
    sub(
        login,
        """                    autoComplete="username"
                    required
""",
        """                    autoComplete="username"
                    autoFocus
                    required
""",
    )
    # El marcador de S9379 va en un comentario JS para no romper el JSX.
    sub(
        login,
        "  return (\n    <div className=\"grid min-h-screen bg-slate-50 lg:grid-cols-[1.05fr_1fr]\">",
        "  return ( // DEFECTO SEMBRADO (demostracion) S9379 - autoFocus en el campo de código\n    <div className=\"grid min-h-screen bg-slate-50 lg:grid-cols-[1.05fr_1fr]\">",
    )

    # ------------------------------------------------------------------
    # frontend/src/pages/MyReservationsPage.tsx -> S3358 (129), S6819 (99), S7718 (44)
    # ------------------------------------------------------------------
    mine = SRC / "frontend" / "src" / "pages" / "MyReservationsPage.tsx"
    sub(mine, "    } catch (error_) {", "    } catch (caught) { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught")
    sub(mine, "setError(error_ instanceof Error ? error_.message", "setError(caught instanceof Error ? caught.message")
    sub(
        mine,
        """      <fieldset className="mb-4 flex flex-wrap gap-2">
        <legend className="sr-only">Filtrar mis reservas</legend>
""",
        """      {/* DEFECTO SEMBRADO (demostracion) S6819 - role="group" en div nativo */}
      <div role="group" aria-label="Filtrar mis reservas" className="mb-4 flex flex-wrap gap-2">
""",
    )
    sub(mine, "      </fieldset>\n", "      </div>\n")
    sub(
        mine,
        """      {!loading && visible.length === 0 ? (
        <EmptyState
          testId="empty-reservations"
          icon={<ClipboardList className="h-6 w-6" />}
          title={
            filter === 'ALL'
              ? 'Todavía no tienes reservas registradas'
              : 'No tienes reservas con este estado'
          }
          message="Cuando solicites un equipo, podrás seguir aquí su aprobación y devolución."
          action={
            <Link to="/catalogo" className="btn-teal btn-sm mt-1">
              Explorar catálogo
            </Link>
          }
        />
      ) : null}
""",
        """      {/* DEFECTO SEMBRADO (demostracion) S3358 - ternario anidado */}
      {!loading
        ? visible.length === 0
          ? (
              <EmptyState
                testId="empty-reservations"
                icon={<ClipboardList className="h-6 w-6" />}
                title={
                  filter === 'ALL'
                    ? 'Todavía no tienes reservas registradas'
                    : 'No tienes reservas con este estado'
                }
                message="Cuando solicites un equipo, podrás seguir aquí su aprobación y devolución."
                action={
                  <Link to="/catalogo" className="btn-teal btn-sm mt-1">
                    Explorar catálogo
                  </Link>
                }
              />
            )
          : null
        : null}
""",
    )

    # ------------------------------------------------------------------
    # Props sin Readonly: AppLayout (83), CategoryIconLabel (3), ProtectedRoute (7)
    # ------------------------------------------------------------------
    sub(
        SRC / "frontend" / "src" / "components" / "AppLayout.tsx",
        "function SidebarContent({ onNavigate }: Readonly<{ onNavigate?: () => void }>) {",
        "function SidebarContent({ onNavigate }: { onNavigate?: () => void }) { // DEFECTO SEMBRADO (demostracion) S6759 - props sin Readonly",
    )
    sub(
        SRC / "frontend" / "src" / "components" / "CategoryIconLabel.tsx",
        "export function CategoryIconLabel({ category }: Readonly<{ category: string }>) {",
        "export function CategoryIconLabel({ category }: { category: string }) { // DEFECTO SEMBRADO (demostracion) S6759 - props sin Readonly",
    )
    sub(
        SRC / "frontend" / "src" / "components" / "ProtectedRoute.tsx",
        "export function ProtectedRoute({ role }: Readonly<{ role?: Role }>) {",
        "export function ProtectedRoute({ role }: { role?: Role }) { // DEFECTO SEMBRADO (demostracion) S6759 - props sin Readonly",
    )

    # ------------------------------------------------------------------
    # frontend/src/contexts/AuthContext.tsx -> S6759 (30)
    # ------------------------------------------------------------------
    auth = SRC / "frontend" / "src" / "contexts" / "AuthContext.tsx"
    sub(
        auth,
        """interface AuthProviderProps {
  readonly children: ReactNode;
  readonly initialUser?: User | null;
  readonly initialToken?: string | null;
}""",
        """interface AuthProviderProps { // DEFECTO SEMBRADO (demostracion) S6759 - props mutables
  children: ReactNode;
  initialUser?: User | null;
  initialToken?: string | null;
}""",
    )

    # ------------------------------------------------------------------
    # frontend/src/pages/NewReservationPage.tsx -> S7718 (71,133)
    # ------------------------------------------------------------------
    newres = SRC / "frontend" / "src" / "pages" / "NewReservationPage.tsx"
    newres_text = read(newres)
    if newres_text.count("      .catch((error_) => {") != 1:
        raise SystemExit("NewReservationPage: no se encontro catch de carga")
    newres_text = newres_text.replace(
        "      .catch((error_) => {",
        "      .catch((caught) => { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught",
    )
    newres_text = newres_text.replace(
        "setLoadError(error_ instanceof Error ? error_.message",
        "setLoadError(caught instanceof Error ? caught.message",
    )
    if newres_text.count("    } catch (error_) {") != 1:
        raise SystemExit("NewReservationPage: no se encontro catch de envio")
    newres_text = newres_text.replace(
        "    } catch (error_) {",
        "    } catch (caught) { // DEFECTO SEMBRADO (demostracion) S7718 - parametro caught",
    )
    newres_text = newres_text.replace(
        "setFormError(error_ instanceof Error ? error_.message",
        "setFormError(caught instanceof Error ? caught.message",
    )
    write(newres, newres_text)


def inventory() -> None:
    """Registra linea real de cada marca y los archivos afectados."""
    entries = []
    for path in sorted(SRC.rglob("*.ts*")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if MARK in line:
                rel = path.relative_to(SRC).as_posix()
                markers = []
                if " S3358" in line:
                    markers.append("S3358")
                if " S1082" in line:
                    markers.append("S1082")
                if " S6819" in line:
                    markers.append("S6819")
                if " S6847" in line:
                    markers.append("S6847")
                if " S6848" in line:
                    markers.append("S6848")
                if " S2068" in line:
                    markers.append("S2068")
                if " S2245" in line:
                    markers.append("S2245")
                if " S6759" in line:
                    markers.append("S6759")
                if " S7718" in line:
                    markers.append("S7718")
                if " S9379" in line:
                    markers.append("S9379")
                if rel.endswith("components/ui.tsx"):
                    # El comentario JSX ocupa 219-220; los elementos afectados son 218 y 222.
                    if number == 219:
                        entries.append(
                            {"file": rel, "line": 218, "rules": markers, "text": line.strip()}
                        )
                        continue
                    if number == 220:
                        entries.append(
                            {"file": rel, "line": 222, "rules": markers, "text": line.strip()}
                        )
                        continue
                entries.append({"file": rel, "line": number, "rules": markers, "text": line.strip()})
    total_rules = sum(len(entry["rules"]) for entry in entries)
    payload = {
        "nota": "ANTES REPRODUCIDO: lineas reales del arbol docs/evidencias-sonarqube/antes/src. No es una captura historica.",
        "total_marcas": len(entries),
        "total_reglas_sembradas": total_rules,
        "marcas": entries,
    }
    (DEST / "defectos-sembrados.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Marcas registradas: {len(entries)}")
    for entry in entries:
        print(f"  {entry['file']}:{entry['line']} {','.join(entry['rules'])}")


def main() -> None:
    copy_sources()
    seed()
    inventory()
    print(f"ANTES reproducido en {SRC}")


if __name__ == "__main__":
    main()
