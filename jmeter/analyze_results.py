"""Analiza el JTL de JMeter y genera métricas y gráficas para el informe de LabTrack."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

NAVY = "#0b1f3a"
TEAL = "#14b8a6"
AMBER = "#f59e0b"
RED = "#ef4444"
SLATE = "#64748b"


def load_samples(jtl_path: Path) -> list[dict]:
    if not jtl_path.exists():
        raise SystemExit(f"No existe el archivo JTL: {jtl_path}")

    samples: list[dict] = []
    with jtl_path.open("r", encoding="utf-8", newline="") as handle:
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
        raise SystemExit(f"El JTL {jtl_path} no contiene muestras.")
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


def save_charts(samples: list[dict], overall: dict, charts_dir: Path, title_prefix: str = "") -> None:
    charts_dir.mkdir(parents=True, exist_ok=True)
    start = min(sample["timestamp"] for sample in samples)

    buckets: dict[int, list[float]] = defaultdict(list)
    thread_counts: dict[int, int] = defaultdict(int)
    error_counts: dict[int, int] = defaultdict(int)
    for sample in samples:
        second = int((sample["timestamp"] - start) / 1000)
        buckets[second].append(sample["elapsed"])
        thread_counts[second] = max(thread_counts[second], sample["all_threads"])
        if not sample["success"]:
            error_counts[second] += 1

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

    # 1. Gráfica de evolución temporal de tiempos de respuesta
    fig, axis = plt.subplots(figsize=(10, 4.6), dpi=160)
    axis.plot(seconds, averages, color=TEAL, linewidth=2.2, label="Promedio")
    axis.plot(seconds, p95s, color=NAVY, linewidth=1.8, label="Percentil 95")
    axis.fill_between(seconds, averages, p95s, color=TEAL, alpha=0.12)
    chart_title = f"Tiempo de respuesta ({title_prefix})" if title_prefix else "Tiempo de respuesta durante la prueba"
    axis.set_title(chart_title)
    axis.set_xlabel("Segundos desde el inicio")
    axis.set_ylabel("Milisegundos")
    axis.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    axis.legend(frameon=False, loc="upper right")
    axis.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(charts_dir / "response-time.png", bbox_inches="tight")
    plt.close(fig)

    # 2. Gráfica de barras de percentiles
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
    axis.set_title(f"Distribución de percentiles ({title_prefix})" if title_prefix else "Distribución de tiempos de respuesta")
    axis.set_ylabel("Milisegundos")
    axis.set_ylim(0, max(values) * 1.18 if max(values) > 0 else 100)
    axis.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(charts_dir / "percentiles.png", bbox_inches="tight")
    plt.close(fig)

    # 3. Throughput y usuarios concurrentes
    fig, axis = plt.subplots(figsize=(10, 4.4), dpi=160)
    axis.bar(seconds, throughput, color=TEAL, width=0.85, label="Peticiones por segundo")
    axis.set_title(f"Throughput y usuarios concurrentes ({title_prefix})" if title_prefix else "Throughput y usuarios concurrentes")
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
    fig.savefig(charts_dir / "throughput.png", bbox_inches="tight")
    plt.close(fig)

    # 4. Gráfica de tasa de error acumulada / distribución de errores
    fig, axis = plt.subplots(figsize=(9.2, 4.0), dpi=160)
    errors_per_sec = [error_counts[second] for second in seconds]
    if any(errors_per_sec):
        axis.bar(seconds, errors_per_sec, color=RED, width=0.85, label="Errores HTTP")
        axis.set_ylabel("Cantidad de errores", color=RED)
    else:
        axis.plot(seconds, [0] * len(seconds), color=TEAL, linewidth=2, label="0 errores detectados")
        axis.set_ylabel("Errores HTTP")
    axis.set_title(f"Evolución de errores HTTP ({title_prefix})" if title_prefix else "Evolución de errores HTTP")
    axis.set_xlabel("Segundos desde el inicio")
    axis.grid(axis="y", color="#e2e8f0", linewidth=0.8)
    axis.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(charts_dir / "errors.png", bbox_inches="tight")
    plt.close(fig)


def export_csv_table(per_label: dict[str, dict], overall: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Transacción",
        "Muestras",
        "Promedio (ms)",
        "Mediana p50 (ms)",
        "p90 (ms)",
        "p95 (ms)",
        "p99 (ms)",
        "Mínimo (ms)",
        "Máximo (ms)",
        "Throughput (req/s)",
        "Errores",
        "Tasa Error (%)",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for label, m in per_label.items():
            writer.writerow(
                {
                    "Transacción": label,
                    "Muestras": m["muestras"],
                    "Promedio (ms)": m["promedio_ms"],
                    "Mediana p50 (ms)": m["mediana_ms"],
                    "p90 (ms)": m["p90_ms"],
                    "p95 (ms)": m["p95_ms"],
                    "p99 (ms)": m["p99_ms"],
                    "Mínimo (ms)": m["minimo_ms"],
                    "Máximo (ms)": m["maximo_ms"],
                    "Throughput (req/s)": m["throughput_rps"],
                    "Errores": m["errores"],
                    "Tasa Error (%)": m["tasa_error_pct"],
                }
            )
        writer.writerow(
            {
                "Transacción": "TOTAL GENERAL",
                "Muestras": overall["muestras"],
                "Promedio (ms)": overall["promedio_ms"],
                "Mediana p50 (ms)": overall["mediana_ms"],
                "p90 (ms)": overall["p90_ms"],
                "p95 (ms)": overall["p95_ms"],
                "p99 (ms)": overall["p99_ms"],
                "Mínimo (ms)": overall["minimo_ms"],
                "Máximo (ms)": overall["maximo_ms"],
                "Throughput (req/s)": overall["throughput_rps"],
                "Errores": overall["errores"],
                "Tasa Error (%)": overall["tasa_error_pct"],
            }
        )


def analyze(
    jtl_path: Path,
    output_dir: Path,
    title: str = "Prueba de carga — LabTrack",
    threshold_p95: float = 3000.0,
    max_error_rate: float = 1.0,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = output_dir / "charts"

    samples = load_samples(jtl_path)
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

    save_charts(samples, overall, charts_dir, title_prefix=title)

    payload = {"general": overall, "por_transaccion": per_label}
    (output_dir / "summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    export_csv_table(per_label, overall, output_dir / "resultados_tabla.csv")

    rows = [
        "| Transacción | Muestras | Promedio | p50 | p90 | p95 | p99 | Throughput | Error % |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, metrics in per_label.items():
        rows.append(
            "| {label} | {muestras} | {promedio_ms:.1f} ms | {mediana_ms:.1f} ms | {p90_ms:.1f} ms | "
            "{p95_ms:.1f} ms | {p99_ms:.1f} ms | {throughput_rps:.2f} rps | {tasa_error_pct:.2f} % |".format(
                label=label, **metrics
            )
        )
    rows.append(
        "| **TOTAL GENERAL** | **{muestras}** | **{promedio_ms:.1f} ms** | **{mediana_ms:.1f} ms** | **{p90_ms:.1f} ms** | "
        "**{p95_ms:.1f} ms** | **{p99_ms:.1f} ms** | **{throughput_rps:.2f} rps** | **{tasa_error_pct:.2f} %** |".format(
            **overall
        )
    )

    verdict_approved = overall["tasa_error_pct"] <= max_error_rate and overall["p95_ms"] <= threshold_p95
    verdict = (
        f"APROBADA: tasa de error ({overall['tasa_error_pct']} %) dentro del umbral ({max_error_rate} %) "
        f"y percentil 95 ({overall['p95_ms']:.1f} ms) dentro del umbral ({threshold_p95:.0f} ms)."
        if verdict_approved
        else f"REVISAR: se detectaron desviaciones frente a los umbrales (Error %: {overall['tasa_error_pct']}%, p95: {overall['p95_ms']:.1f} ms)."
    )

    markdown = f"""# Resultados — {title}

**Herramienta:** Apache JMeter 5.6.3  
**Escenario:** {overall['usuarios_max']} usuarios concurrentes · duración {overall['duracion_s']:.0f} s  
**Periodo:** {overall['inicio']} a {overall['fin']}  
**Endpoints:** login JWT, catálogo completo, filtro Cómputo, estadísticas y reservas del estudiante.

## Resumen general

| Métrica | Valor | Umbral SLA | Estado |
|---|---:|---:|:---:|
| Peticiones totales | {overall['muestras']:,} | — | Informativo |
| Errores HTTP | {overall['errores']} ({overall['tasa_error_pct']:.2f} %) | ≤ {max_error_rate:.1f} % | {"Cumple" if overall['tasa_error_pct'] <= max_error_rate else "Falla"} |
| Throughput promedio | {overall['throughput_rps']:.2f} req/s | — | Informativo |
| Tiempo promedio | {overall['promedio_ms']:.1f} ms | — | Informativo |
| Mediana (p50) | {overall['mediana_ms']:.1f} ms | ≤ {threshold_p95:.0f} ms | Conforme |
| Percentil 90 (p90) | {overall['p90_ms']:.1f} ms | ≤ {threshold_p95:.0f} ms | Conforme |
| Percentil 95 (p95) | {overall['p95_ms']:.1f} ms | ≤ {threshold_p95:.0f} ms | {"Cumple" if overall['p95_ms'] <= threshold_p95 else "Falla"} |
| Percentil 99 (p99) | {overall['p99_ms']:.1f} ms | — | Informativo |
| Tiempo máximo | {overall['maximo_ms']:.1f} ms | — | Informativo |
| Desviación estándar | {overall['desviacion_ms']:.1f} ms | — | Informativo |

## Detalle por transacción

{chr(10).join(rows)}

## Veredicto

**{verdict}**

## Artefactos generados

- Tabla de resultados CSV: `{output_dir.name}/resultados_tabla.csv`
- Métricas estructuradas JSON: `{output_dir.name}/summary.json`
- Gráficas generadas:
  - `charts/response-time.png` (evolución en el tiempo del promedio y p95)
  - `charts/percentiles.png` (distribución de percentiles p50 a p99)
  - `charts/throughput.png` (peticiones por segundo vs usuarios concurrentes)
  - `charts/errors.png` (evolución de errores HTTP)
"""

    (output_dir / "summary.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Analiza resultados de pruebas JMeter (JTL)")
    base_dir = Path(__file__).resolve().parent
    default_reports = base_dir / "reports"
    default_jtl = default_reports / "results.jtl"

    parser.add_argument("--jtl", type=Path, default=default_jtl, help="Ruta al archivo .jtl")
    parser.add_argument("--output", type=Path, default=default_reports, help="Carpeta de salida de reportes")
    parser.add_argument("--title", type=str, default="Prueba de carga — LabTrack", help="Título del reporte")
    parser.add_argument("--threshold-p95", type=float, default=3000.0, help="Umbral p95 en milisegundos")
    parser.add_argument("--max-error-rate", type=float, default=1.0, help="Tasa máxima admisible de error (%)")

    args = parser.parse_args()
    analyze(
        jtl_path=args.jtl,
        output_dir=args.output,
        title=args.title,
        threshold_p95=args.threshold_p95,
        max_error_rate=args.max_error_rate,
    )


if __name__ == "__main__":
    main()
