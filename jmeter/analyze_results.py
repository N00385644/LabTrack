"""Analiza el JTL de JMeter y genera métricas y gráficas para el informe de LabTrack."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
CHARTS_DIR = REPORTS_DIR / "charts"
JTL_PATH = REPORTS_DIR / "results.jtl"

NAVY = "#0b1f3a"
TEAL = "#14b8a6"
AMBER = "#f59e0b"
SLATE = "#64748b"


def load_samples() -> list[dict]:
    if not JTL_PATH.exists():
        raise SystemExit(f"No existe el archivo JTL: {JTL_PATH}")

    samples: list[dict] = []
    with JTL_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                timestamp = int(float(row.get("timeStamp") or 0))
                elapsed = float(row.get("elapsed") or 0)
            except (TypeError, ValueError):
                continue
            samples.append(
                {
                    "timestamp": timestamp,
                    "elapsed": elapsed,
                    "label": (row.get("label") or "sin-etiqueta").strip(),
                    "success": (row.get("success") or "false").strip().lower() == "true",
                    "response_code": (row.get("responseCode") or "").strip(),
                    "all_threads": int(float(row.get("allThreads") or 0)),
                    "bytes": int(float(row.get("bytes") or 0)),
                    "latency": float(row.get("Latency") or 0) if row.get("Latency") else 0.0,
                }
            )
    if not samples:
        raise SystemExit("El JTL no contiene muestras.")
    return samples


def percentile(values: np.ndarray, value: float) -> float:
    return float(np.percentile(values, value))


def build_metrics(values: np.ndarray) -> dict:
    return {
        "muestras": int(values.size),
        "promedio_ms": round(float(values.mean()), 2),
        "mediana_ms": round(percentile(values, 50), 2),
        "p90_ms": round(percentile(values, 90), 2),
        "p95_ms": round(percentile(values, 95), 2),
        "p99_ms": round(percentile(values, 99), 2),
        "minimo_ms": round(float(values.min()), 2),
        "maximo_ms": round(float(values.max()), 2),
        "desviacion_ms": round(float(values.std(ddof=0)), 2),
    }


def save_charts(samples: list[dict], overall: dict) -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    start = min(sample["timestamp"] for sample in samples)

    buckets: dict[int, list[float]] = defaultdict(list)
    thread_counts: dict[int, int] = defaultdict(int)
    for sample in samples:
        second = int((sample["timestamp"] - start) / 1000)
        buckets[second].append(sample["elapsed"])
        thread_counts[second] = max(thread_counts[second], sample["all_threads"])

    seconds = sorted(buckets)
    averages = [float(np.mean(buckets[second])) for second in seconds]
    p95s = [percentile(np.array(buckets[second]), 95) for second in seconds]
    throughput = [len(buckets[second]) for second in seconds]
    active_threads = [thread_counts[second] for second in seconds]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#cbd5e1",
            "axes.labelcolor": SLATE,
            "xtick.color": SLATE,
            "ytick.color": SLATE,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
        }
    )

    fig, axis = plt.subplots(figsize=(10, 4.6), dpi=160)
    axis.plot(seconds, averages, color=TEAL, linewidth=2.2, label="Promedio")
    axis.plot(seconds, p95s, color=NAVY, linewidth=1.8, label="Percentil 95")
    axis.fill_between(seconds, averages, p95s, color=TEAL, alpha=0.12)
    axis.set_title("Tiempo de respuesta durante la prueba de carga")
    axis.set_xlabel("Segundos desde el inicio")
    axis.set_ylabel("Milisegundos")
    axis.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    axis.legend(frameon=False, loc="upper right")
    axis.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "response-time.png", bbox_inches="tight")
    plt.close(fig)

    labels = ["p50", "p90", "p95", "p99", "Máximo"]
    values = [
        overall["mediana_ms"],
        overall["p90_ms"],
        overall["p95_ms"],
        overall["p99_ms"],
        overall["maximo_ms"],
    ]
    fig, axis = plt.subplots(figsize=(8.4, 4.2), dpi=160)
    bars = axis.bar(labels, values, color=[TEAL, "#0d9488", NAVY, "#1d345d", AMBER], width=0.62)
    for bar, value in zip(bars, values):
        axis.annotate(
            f"{value:.0f} ms",
            (bar.get_x() + bar.get_width() / 2, value),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=9,
            color=NAVY,
            fontweight="bold",
        )
    axis.set_title("Distribución de tiempos de respuesta (todas las peticiones)")
    axis.set_ylabel("Milisegundos")
    axis.set_ylim(0, max(values) * 1.18)
    axis.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "percentiles.png", bbox_inches="tight")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(10, 4.4), dpi=160)
    axis.bar(seconds, throughput, color=TEAL, width=0.85, label="Peticiones por segundo")
    axis.set_title("Throughput y usuarios concurrentes")
    axis.set_xlabel("Segundos desde el inicio")
    axis.set_ylabel("Peticiones por segundo", color=TEAL)
    axis.tick_params(axis="y", labelcolor=TEAL)
    axis.grid(axis="y", color="#e2e8f0", linewidth=0.8)

    twin = axis.twinx()
    twin.plot(seconds, active_threads, color=NAVY, linewidth=2, label="Usuarios activos")
    twin.set_ylabel("Usuarios concurrentes", color=NAVY)
    twin.tick_params(axis="y", labelcolor=NAVY)
    twin.set_ylim(0, max(active_threads + [1]) * 1.15)

    lines, labels_1 = axis.get_legend_handles_labels()
    lines_2, labels_2 = twin.get_legend_handles_labels()
    axis.legend(lines + lines_2, labels_1 + labels_2, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "throughput.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    samples = load_samples()
    durations = np.array([sample["elapsed"] for sample in samples], dtype=float)
    successes = sum(1 for sample in samples if sample["success"])
    errors = len(samples) - successes

    start = min(sample["timestamp"] for sample in samples)
    end = max(sample["timestamp"] for sample in samples)
    window_seconds = max((end - start) / 1000, 0.001)
    overall = build_metrics(durations)
    overall.update(
        {
            "errores": errors,
            "tasa_error_pct": round(errors / len(samples) * 100, 2),
            "throughput_rps": round(len(samples) / window_seconds, 2),
            "duracion_s": round(window_seconds, 2),
            "usuarios_max": max(sample["all_threads"] for sample in samples),
            "inicio": datetime.fromtimestamp(start / 1000, tz=timezone.utc).isoformat(),
            "fin": datetime.fromtimestamp(end / 1000, tz=timezone.utc).isoformat(),
        }
    )

    per_label: dict[str, dict] = {}
    for label in sorted({sample["label"] for sample in samples}):
        subset = [sample for sample in samples if sample["label"] == label]
        label_durations = np.array([sample["elapsed"] for sample in subset], dtype=float)
        label_success = sum(1 for sample in subset if sample["success"])
        label_metrics = build_metrics(label_durations)
        label_metrics.update(
            {
                "errores": len(subset) - label_success,
                "tasa_error_pct": round((len(subset) - label_success) / len(subset) * 100, 2),
                "throughput_rps": round(len(subset) / window_seconds, 2),
            }
        )
        per_label[label] = label_metrics

    save_charts(samples, overall)

    payload = {"general": overall, "por_transaccion": per_label}
    (REPORTS_DIR / "summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rows = [
        "| Transacción | Muestras | Promedio | p95 | p99 | Máximo | Error % |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, metrics in per_label.items():
        rows.append(
            "| {label} | {muestras} | {promedio_ms:.1f} ms | {p95_ms:.1f} ms | "
            "{p99_ms:.1f} ms | {maximo_ms:.1f} ms | {tasa_error_pct:.2f} % |".format(
                label=label, **metrics
            )
        )

    verdict = (
        "APROBADA: cero errores HTTP y percentil 95 dentro del umbral de 3 000 ms."
        if overall["errores"] == 0 and overall["p95_ms"] < 3000
        else "REVISAR: se detectaron errores o el percentil 95 superó el umbral de 3 000 ms."
    )

    markdown = f"""# Resultados de la prueba de carga — LabTrack

**Herramienta:** Apache JMeter 5.6.3  
**Escenario:** {overall['usuarios_max']} usuarios concurrentes · ramp-up 10 s · duración {overall['duracion_s']:.0f} s  
**Endpoints:** login JWT, catálogo completo, filtro Cómputo, estadísticas y reservas del estudiante.

## Resumen general

| Métrica | Valor |
|---|---:|
| Peticiones totales | {overall['muestras']:,} |
| Errores HTTP | {overall['errores']} ({overall['tasa_error_pct']:.2f} %) |
| Throughput promedio | {overall['throughput_rps']:.2f} req/s |
| Tiempo promedio | {overall['promedio_ms']:.1f} ms |
| Mediana (p50) | {overall['mediana_ms']:.1f} ms |
| Percentil 90 | {overall['p90_ms']:.1f} ms |
| Percentil 95 | {overall['p95_ms']:.1f} ms |
| Percentil 99 | {overall['p99_ms']:.1f} ms |
| Tiempo máximo | {overall['maximo_ms']:.1f} ms |

## Detalle por transacción

{chr(10).join(rows)}

## Veredicto

**{verdict}**

## Evidencias

- Reporte HTML de JMeter: `reports/html/index.html`
- Datos crudos: `reports/results.jtl`
- Gráficas: `reports/charts/response-time.png`, `percentiles.png`, `throughput.png`
"""

    (REPORTS_DIR / "summary.md").write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
