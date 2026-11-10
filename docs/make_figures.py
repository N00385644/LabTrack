"""Genera las figuras base del informe técnico de LabTrack."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon

BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

NAVY = "#0b1f3a"
NAVY_LIGHT = "#1d345d"
TEAL = "#14b8a6"
TEAL_DARK = "#0f766e"
AMBER = "#f59e0b"
SLATE = "#64748b"
GRID = "#e2e8f0"
WHITE = "#ffffff"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.edgecolor": "#cbd5e1",
        "axes.labelcolor": SLATE,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "figure.facecolor": WHITE,
    }
)


def box(ax, x, y, w, h, title, subtitle, color, text_color=WHITE):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=0,
        facecolor=color,
        zorder=3,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h * 0.62,
        title,
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=text_color,
        zorder=4,
    )
    ax.text(
        x + w / 2,
        y + h * 0.28,
        subtitle,
        ha="center",
        va="center",
        fontsize=8.5,
        color=text_color,
        linespacing=1.5,
        zorder=4,
    )


def arrow(ax, x1, y1, x2, y2, label, color=SLATE):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=2,
            color=color,
            zorder=2,
        )
    )
    ax.text(
        (x1 + x2) / 2,
        y1 + 0.32,
        label,
        ha="center",
        va="bottom",
        fontsize=8,
        color=color,
        fontweight="bold",
    )


def architecture() -> None:
    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=180)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.2)
    ax.axis("off")

    ax.text(0.2, 5.85, "Arquitectura de LabTrack", fontsize=16, fontweight="bold", color=NAVY)
    ax.text(
        0.2,
        5.5,
        "Aplicación web de tres capas con autenticación JWT y trazabilidad de auditoría",
        fontsize=9,
        color=SLATE,
    )

    box(ax, 0.4, 2.9, 2.9, 1.9, "Frontend SPA", "React 18 · Vite 6\nTailwind CSS · React Router\nContext API", TEAL)
    box(ax, 4.55, 2.9, 2.9, 1.9, "API REST", "NestJS 11 · TypeScript\nJWT · Guards · Swagger\nValidación global", NAVY)
    box(ax, 8.7, 2.9, 2.9, 1.9, "Persistencia", "Prisma ORM\nPostgreSQL 18\nSeed determinista", AMBER, NAVY)

    arrow(ax, 3.35, 3.85, 4.5, 3.85, "HTTPS\nBearer JWT", TEAL_DARK)
    arrow(ax, 7.5, 3.85, 8.65, 3.85, "SQL\nparametrizado", NAVY_LIGHT)

    ax.add_patch(
        FancyBboxPatch(
            (0.4, 0.55),
            11.2,
            1.55,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            linewidth=1,
            edgecolor="#cbd5e1",
            facecolor="#f8fafc",
            zorder=1,
        )
    )
    ax.text(0.7, 1.78, "Aseguramiento de la calidad", fontsize=10, fontweight="bold", color=NAVY)

    tools = [
        ("Vitest + Supertest", "53 pruebas de API"),
        ("React Testing Library", "48 pruebas de UI"),
        ("Selenium + Chrome", "7 flujos E2E"),
        ("Apache JMeter", "50 usuarios · 60 s"),
        ("SonarQube", "análisis estático"),
    ]
    width = 2.02
    for index, (name, detail) in enumerate(tools):
        x = 0.7 + index * 2.16
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.82),
                width,
                0.72,
                boxstyle="round,pad=0.01,rounding_size=0.08",
                linewidth=0,
                facecolor=WHITE,
                edgecolor="#e2e8f0",
                zorder=2,
            )
        )
        ax.text(x + width / 2, 1.31, name, ha="center", fontsize=7.6, fontweight="bold", color=TEAL_DARK)
        ax.text(x + width / 2, 1.03, detail, ha="center", fontsize=7, color=SLATE)

    fig.savefig(ASSETS / "arquitectura.png", bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def pyramid() -> None:
    fig, ax = plt.subplots(figsize=(9, 5.6), dpi=180)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.2)
    ax.axis("off")

    ax.text(0.2, 5.9, "Pirámide de automatización de LabTrack", fontsize=15, fontweight="bold", color=NAVY)
    ax.text(0.2, 5.55, "108 ejecuciones automatizadas sobre tres niveles complementarios", fontsize=9, color=SLATE)

    bands = [
        ([(4.0, 3.65), (6.0, 3.65), (5.45, 5.0), (4.55, 5.0)], "7 E2E", "Selenium", TEAL, 9.5),
        ([(2.6, 2.0), (7.4, 2.0), (6.3, 3.65), (3.7, 3.65)], "48 pruebas de interfaz", "Vitest + React Testing Library", NAVY_LIGHT, 11),
        ([(0.7, 0.35), (9.3, 0.35), (7.4, 2.0), (2.6, 2.0)], "53 pruebas de API", "Vitest + Supertest + SWC", NAVY, 11),
    ]
    for points, title, subtitle, color, title_size in bands:
        ax.add_patch(Polygon(points, closed=True, facecolor=color, edgecolor=WHITE, linewidth=3))
        center_x = sum(point[0] for point in points) / 4
        center_y = sum(point[1] for point in points) / 4
        ax.text(center_x, center_y + 0.12, title, ha="center", va="center", fontsize=title_size, fontweight="bold", color=WHITE)
        ax.text(center_x, center_y - 0.22, subtitle, ha="center", va="center", fontsize=7.8, color=WHITE)

    ax.text(0.7, 0.05, "Base: validación de reglas de negocio y contrato HTTP", fontsize=7.5, color=SLATE)
    ax.text(9.3, 0.05, "Cima: verificación del flujo real del usuario", fontsize=7.5, color=SLATE, ha="right")

    fig.savefig(ASSETS / "piramide-pruebas.png", bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def coverage() -> None:
    backend_path = BASE.parent / "backend" / "coverage" / "coverage-summary.json"
    if not backend_path.exists():
        backend_path = BASE / "evidencias-pruebas" / "unitarias" / "cobertura" / "backend-coverage-summary.json"
    frontend_path = BASE.parent / "frontend" / "coverage" / "coverage-summary.json"
    if not frontend_path.exists():
        frontend_path = BASE / "evidencias-pruebas" / "unitarias" / "cobertura" / "frontend-coverage-summary.json"

    backend = json.loads(backend_path.read_text(encoding="utf-8"))["total"]
    frontend = json.loads(frontend_path.read_text(encoding="utf-8"))["total"]

    metrics = ["Sentencias", "Ramas", "Funciones"]
    backend_values = [
        backend["statements"]["pct"],
        backend["branches"]["pct"],
        backend["functions"]["pct"],
    ]
    frontend_values = [
        frontend["statements"]["pct"],
        frontend["branches"]["pct"],
        frontend["functions"]["pct"],
    ]

    x = range(len(metrics))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=180)
    bars_backend = ax.bar([i - width / 2 for i in x], backend_values, width, color=NAVY, label="Backend (53 pruebas)")
    bars_frontend = ax.bar([i + width / 2 for i in x], frontend_values, width, color=TEAL, label="Frontend (48 pruebas)")

    for bars in (bars_backend, bars_frontend):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.1f} %",
                (bar.get_x() + bar.get_width() / 2, height),
                textcoords="offset points",
                xytext=(0, 4),
                ha="center",
                fontsize=8.5,
                fontweight="bold",
                color=NAVY,
            )

    ax.set_xticks(list(x))
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Cobertura (%)")
    ax.set_title("Cobertura de código medida con Istanbul/V8")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right", ncol=2)
    fig.tight_layout()
    fig.savefig(ASSETS / "cobertura.png", bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def execution_summary() -> None:
    labels = ["API\nSupertest", "UI\nRTL", "E2E\nSelenium", "Carga\nJMeter"]
    values = [53, 48, 7, 5]
    colors = [NAVY, NAVY_LIGHT, TEAL, AMBER]
    fig, ax = plt.subplots(figsize=(8.6, 3.9), dpi=180)
    bars = ax.bar(labels, values, color=colors, width=0.58)
    for bar, value in zip(bars, values):
        ax.annotate(
            str(value),
            (bar.get_x() + bar.get_width() / 2, value),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=13,
            fontweight="bold",
            color=NAVY,
        )
    ax.set_ylim(0, max(values) * 1.22)
    ax.set_ylabel("Ejecuciones")
    ax.set_title("Distribución de las pruebas automatizadas")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(ASSETS / "resumen-pruebas.png", bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


def sonar_comparison() -> None:
    data = json.loads((BASE / "sonar-data.json").read_text(encoding="utf-8"))
    baseline = data["baseline"]
    final = data["final"]

    labels = ["Bugs", "Vulnerabilidades", "Code smells"]
    before = [baseline.get("bugs", 0), baseline.get("vulnerabilities", 0), baseline.get("codeSmells", 0)]
    after = [final.get("bugs", 0), final.get("vulnerabilities", 0), final.get("codeSmells", 0)]

    x = range(len(labels))
    width = 0.34
    fig, ax = plt.subplots(figsize=(9.4, 4.8), dpi=180)
    bars_before = ax.bar([i - width / 2 for i in x], before, width, color="#B91C1C", label="Línea base")
    bars_after = ax.bar([i + width / 2 for i in x], after, width, color=TEAL, label="Estado final")

    for bars in (bars_before, bars_after):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.0f}",
                (bar.get_x() + bar.get_width() / 2, height),
                textcoords="offset points",
                xytext=(0, 5),
                ha="center",
                fontsize=11,
                fontweight="bold",
                color=NAVY,
            )

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(before) * 1.25 if max(before) else 1)
    ax.set_ylabel("Hallazgos")
    ax.set_title("SonarQube: línea base vs. cierre de la refactorización")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper right")

    ax.text(
        0.99,
        0.62,
        f"Quality gate: {final.get('qualityGate', 'OK')}\n"
        f"Confiabilidad: {baseline.get('reliabilityRating', '—')} → {final.get('reliabilityRating', '—')}\n"
        f"Seguridad: {baseline.get('securityRating', '—')} → {final.get('securityRating', '—')}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8.5,
        color=SLATE,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#F8FAFC", edgecolor="#E2E8F0"),
    )
    fig.tight_layout()
    fig.savefig(ASSETS / "sonar-comparacion.png", bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)


if __name__ == "__main__":
    architecture()
    pyramid()
    coverage()
    execution_summary()
    sonar_comparison()
    print("Figuras generadas en", ASSETS)
