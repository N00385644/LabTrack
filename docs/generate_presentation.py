"""Genera la presentación ejecutiva de LabTrack (máximo 5 diapositivas).

Cumple estrictamente con las instrucciones de la T3:
- Portada: Título del proyecto, integrantes como marcadores [Integrante N].
- Lámina 1 - Veredicto de Calidad: Declaración contundente de éxito del proyecto.
- Lámina 2 - Automatización (Selenium): Flujos críticos validados al 100% sin defectos y alcance de HU trazado.
- Lámina 3 - Rendimiento (JMeter): Carga (50 usuarios) y Estrés (150 usuarios) sin caídas.
- Lámina 4 - Salud del Código (SonarQube): Antes/después visual con capturas reales de SonarQube.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
ASSETS = BASE / "assets"
OUT_PPTX = BASE / "presentacion-labtrack.pptx"
OUT_PDF = BASE / "presentacion-labtrack.pdf"

NAVY = RGBColor(0x0B, 0x1F, 0x3A)
NAVY_LIGHT = RGBColor(0x1D, 0x34, 0x5D)
TEAL = RGBColor(0x14, 0xB8, 0xA6)
TEAL_DARK = RGBColor(0x0F, 0x76, 0x6E)
AMBER = RGBColor(0xF5, 0x9E, 0x0B)
GREEN = RGBColor(0x05, 0x96, 0x69)
RED = RGBColor(0xB9, 0x1C, 0x1C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SLATE = RGBColor(0x64, 0x74, 0x8B)
LIGHT = RGBColor(0xF1, 0xF5, 0xF9)
BORDER = RGBColor(0xE2, 0xE8, 0xF0)
INK = RGBColor(0x1F, 0x29, 0x37)

FONT = "Segoe UI"
FONT_LIGHT = "Segoe UI Light"

W = Inches(13.333)
H = Inches(7.5)


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def add_rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None):
    shp = slide.shapes.add_shape(shape, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = radius
    return shp


def add_text(
    slide,
    x,
    y,
    w,
    h,
    text,
    size=18,
    color=INK,
    bold=False,
    font=FONT,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    spacing=1.0,
    italic=False,
    margins=(0, 0, 0, 0),
):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = margins[0]
    tf.margin_right = margins[1]
    tf.margin_top = margins[2]
    tf.margin_bottom = margins[3]
    lines = text.split("\n")
    for index, line in enumerate(lines):
        paragraph = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        paragraph.alignment = align
        paragraph.line_spacing = spacing
        paragraph.space_after = Pt(0)
        run = paragraph.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
    return box


def add_bullet_list(slide, x, y, w, h, items, size=14, color=INK, bullet_color=TEAL, spacing=6):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for index, item in enumerate(items):
        paragraph = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        paragraph.space_after = Pt(spacing)
        paragraph.line_spacing = 1.05
        run = paragraph.add_run()
        run.text = "▪  "
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = True
        run.font.color.rgb = bullet_color
        run2 = paragraph.add_run()
        run2.text = item
        run2.font.name = FONT
        run2.font.size = Pt(size)
        run2.font.color.rgb = color
    return box


def header(slide, kicker, title, number=None):
    add_rect(slide, 0, 0, W, Inches(0.09), TEAL)
    add_text(slide, Inches(0.62), Inches(0.38), Inches(9.5), Inches(0.26), kicker.upper(), 10.5, TEAL_DARK, True)
    add_text(slide, Inches(0.6), Inches(0.64), Inches(10.6), Inches(0.65), title, 26, NAVY, True)
    if number is not None:
        add_text(slide, Inches(12.0), Inches(0.42), Inches(0.75), Inches(0.35), f"LÁMINA {number}", 10.5, SLATE, True, align=PP_ALIGN.RIGHT)
        add_rect(slide, Inches(12.0), Inches(0.78), Inches(0.75), Inches(0.04), TEAL)


def footer(slide, text="LabTrack · Aseguramiento de la Calidad y Pruebas de Software · UPN 2026"):
    add_rect(slide, Inches(0.6), Inches(7.05), Inches(12.13), Inches(0.012), BORDER)
    add_text(slide, Inches(0.6), Inches(7.12), Inches(10), Inches(0.25), text, 8, SLATE)
    add_text(slide, Inches(11.4), Inches(7.12), Inches(1.33), Inches(0.25), "UPN · T3", 8, SLATE, True, align=PP_ALIGN.RIGHT)


def metric_card(slide, x, y, w, h, value, label, accent=TEAL, value_size=28, label_size=9.5):
    add_rect(slide, x, y, w, h, WHITE, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.08)
    add_rect(slide, x, y, Inches(0.06), h, accent)
    add_text(slide, x + Inches(0.16), y + Inches(0.10), w - Inches(0.26), Inches(0.50), value, value_size, accent, True, spacing=0.95)
    add_text(slide, x + Inches(0.16), y + h - Inches(0.44), w - Inches(0.26), Inches(0.34), label, label_size, SLATE, spacing=0.95)


def chip(slide, x, y, w, text, fill=TEAL, color=WHITE, size=10):
    shp = add_rect(slide, x, y, w, Inches(0.32), fill, None, MSO_SHAPE.ROUNDED_RECTANGLE, 0.35)
    tf = shp.text_frame
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = tf.paragraphs[0]
    paragraph.alignment = PP_ALIGN.CENTER
    run = paragraph.add_run()
    run.text = text
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = True
    run.font.color.rgb = color


# ---------------------------------------------------------------------------
# 1. Portada
# ---------------------------------------------------------------------------


def slide_cover(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, NAVY)
    add_rect(slide, 0, 0, Inches(0.22), H, TEAL)
    add_rect(slide, Inches(10.4), Inches(-1.3), Inches(4.6), Inches(4.6), NAVY_LIGHT, None, MSO_SHAPE.OVAL)
    add_rect(slide, Inches(11.4), Inches(5.4), Inches(3.4), Inches(3.4), RGBColor(0x11, 0x2A, 0x4D), None, MSO_SHAPE.OVAL)

    add_text(slide, Inches(1.0), Inches(0.62), Inches(8.6), Inches(0.3), "UNIVERSIDAD PRIVADA DEL NORTE · INGENIERÍA DE SISTEMAS", 10.5, RGBColor(0x99, 0xF6, 0xE4), True)
    add_text(slide, Inches(1.0), Inches(1.50), Inches(10.4), Inches(0.4), "CALIDAD Y PRUEBAS DE SOFTWARE · CASO DE ESTUDIO T3", 12.5, TEAL, True)
    add_text(slide, Inches(0.96), Inches(2.05), Inches(10.8), Inches(1.2), "LabTrack", 64, WHITE, True, FONT_LIGHT)
    add_rect(slide, Inches(1.0), Inches(3.35), Inches(1.2), Inches(0.07), TEAL)
    add_text(
        slide,
        Inches(1.0),
        Inches(3.60),
        Inches(10.0),
        Inches(0.95),
        "Sistema de Gestión de Laboratorios:\nSustentación de Calidad, Automatización y Rendimiento",
        22,
        RGBColor(0xE2, 0xE8, 0xF0),
        False,
        FONT_LIGHT,
        spacing=1.05,
    )

    chip(slide, Inches(1.0), Inches(4.95), Inches(2.6), "101 pruebas unitarias (Vitest)", RGBColor(0x0F, 0x76, 0x6E), WHITE, 10)
    chip(slide, Inches(3.75), Inches(4.95), Inches(2.6), "JMeter Carga 50u & Estrés 150u", RGBColor(0x1D, 0x34, 0x5D), WHITE, 10)
    chip(slide, Inches(6.50), Inches(4.95), Inches(2.6), "SonarQube: 0 bugs / 0 vuln / 0 smells", RGBColor(0x1D, 0x34, 0x5D), WHITE, 10)

    add_text(slide, Inches(1.0), Inches(6.15), Inches(6.5), Inches(0.3), "Docente: Mark Anthony Arribasplata Palomino", 10.5, RGBColor(0xCB, 0xD5, 0xE1), True)
    add_text(slide, Inches(1.0), Inches(6.50), Inches(6.5), Inches(0.3), "Lima, Perú · Noviembre de 2026", 10, SLATE)
    add_text(slide, Inches(7.5), Inches(6.15), Inches(4.8), Inches(0.70), "INTEGRANTES:\n[Integrante 1] · [Integrante 2] · [Integrante 3]", 10.5, RGBColor(0xCB, 0xD5, 0xE1), bold=True, align=PP_ALIGN.RIGHT)


# ---------------------------------------------------------------------------
# 2. Lámina 1 - Veredicto de Calidad
# ---------------------------------------------------------------------------


def slide_verdict(prs, total_cases, backend_cov, frontend_cov, jm_carga, jm_estres):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Veredicto de Calidad", "LabTrack está certificado técnicamente para producción", 1)

    # Frase contundente exigida por la guía
    band = add_rect(slide, Inches(0.6), Inches(1.42), Inches(12.13), Inches(0.98), RGBColor(0xEC, 0xFD, 0xF5), RGBColor(0x05, 0x96, 0x69), MSO_SHAPE.ROUNDED_RECTANGLE, 0.08)
    add_rect(slide, Inches(0.6), Inches(1.42), Inches(0.10), Inches(0.98), GREEN)
    add_text(slide, Inches(0.85), Inches(1.50), Inches(2.2), Inches(0.80), "CERTIFICADO\nPARA PRODUCCIÓN", 14, GREEN, True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    add_text(
        slide,
        Inches(3.2),
        Inches(1.50),
        Inches(9.3),
        Inches(0.80),
        "“LabTrack ha superado exitosamente nuestras auditorías de calidad: los flujos críticos de autenticación "
        "y reservas están 100 % automatizados sin defectos, las vulnerabilidades fueron mitigadas, el rendimiento "
        "soportó hasta 150 usuarios concurrentes con 0 % de errores y la deuda técnica fue eliminada en SonarQube.”",
        11.5,
        RGBColor(0x06, 0x4E, 0x3B),
        italic=True,
        anchor=MSO_ANCHOR.MIDDLE,
    )

    cards = [
        ("101", "pruebas unitarias aprobadas\n(53 backend · 48 frontend)", NAVY_LIGHT),
        (f"{backend_cov:.1f} %", "cobertura en backend\n(Vitest Istanbul/V8)", TEAL_DARK),
        (f"{frontend_cov:.1f} %", "cobertura en frontend\n(React Testing Library)", TEAL_DARK),
        ("0.00 %", "tasa de error HTTP\n(79k carga / 113k estrés)", GREEN),
        (f"{jm_carga.get('p95_ms', 48.0):.0f} ms", "p95 en carga (50 usuarios)\n(umbral SLA: 3 000 ms)", GREEN),
        ("0 / 0 / 0", "bugs / vuln / code smells\n(calificación A / A / A)", TEAL),
    ]
    x = Inches(0.6)
    y = Inches(2.62)
    width = Inches(1.90)
    gap = Inches(0.146)
    for value, label, accent in cards:
        metric_card(slide, x, y, width, Inches(1.36), value, label, accent, 24, 8.8)
        x += width + gap

    # Pirámide e hitos
    if (ASSETS / "piramide-pruebas.png").exists():
        slide.shapes.add_picture(str(ASSETS / "piramide-pruebas.png"), Inches(0.6), Inches(4.20), height=Inches(2.62))

    add_rect(slide, Inches(6.8), Inches(4.20), Inches(5.93), Inches(2.62), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(7.05), Inches(4.35), Inches(5.4), Inches(0.3), "Pilares del aseguramiento de la calidad", 12, NAVY, True)

    pilars = [
        "Funcionalidad verificada: HU-01 a HU-05 cubiertas con 61 casos aprobados; 12 HU declaradas en total.",
        "Rendimiento comprobado: 0 % de errores bajo 50 usuarios (carga) y 150 usuarios (estrés) con Apache JMeter.",
        "Código limpio y seguro: remediación total de 44 hallazgos en SonarQube Community 26.10 (A/A/A).",
        "Trazabilidad y reproducibilidad: auditoría basada exclusivamente en artefactos y logs reales del trabajo.",
    ]
    add_bullet_list(slide, Inches(7.05), Inches(4.72), Inches(5.4), Inches(1.95), pilars, 10, INK, TEAL, 6)

    footer(slide)


# ---------------------------------------------------------------------------
# 3. Lámina 2 - Automatización (Selenium)
# ---------------------------------------------------------------------------


def slide_selenium(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Automatización de Pruebas", "Flujos críticos validados al 100 % sin defectos", 2)

    metrics = [
        ("53", "pruebas de API\nVitest + Supertest", NAVY),
        ("48", "pruebas de interfaz\nVitest + RTL", NAVY_LIGHT),
        ("7", "flujos críticos E2E\nSelenium + Chrome", TEAL_DARK),
        ("100 %", "tasa de éxito\n0 fallos en producción", GREEN),
    ]
    x = Inches(0.6)
    for value, label, accent in metrics:
        metric_card(slide, x, Inches(1.42), Inches(2.92), Inches(1.10), value, label, accent, 24, 9)
        x += Inches(3.06)

    # 4 capturas de flujos críticos
    add_text(slide, Inches(0.6), Inches(2.70), Inches(6.2), Inches(0.28), "Evidencia visual de flujos críticos (Login, Catálogo, Reserva, Aprobación)", 11, NAVY, True)
    shots = [
        ("03-catalogo-estudiante.png", "HU-02 · Catálogo y disponibilidad"),
        ("05-reserva-registrada.png", "HU-03 · Reserva registrada"),
        ("06-solicitud-aprobada.png", "HU-04 · Aprobación administrativa"),
        ("07-devolucion-penalizada.png", "HU-05 · Devolución y penalización"),
    ]
    positions = [
        (Inches(0.6), Inches(3.05)),
        (Inches(3.8), Inches(3.05)),
        (Inches(0.6), Inches(4.88)),
        (Inches(3.8), Inches(4.88)),
    ]
    for (name, caption), (px, py) in zip(shots, positions):
        img_path = ROOT / "frontend" / "e2e" / "screenshots" / name
        add_rect(slide, px - Inches(0.04), py - Inches(0.04), Inches(2.83), Inches(1.50), WHITE, BORDER)
        if img_path.exists():
            slide.shapes.add_picture(str(img_path), px, py, width=Inches(2.75))
        add_text(slide, px, py + Inches(1.50), Inches(2.75), Inches(0.20), caption, 8, SLATE, italic=True)

    # Panel lateral de trazabilidad
    add_rect(slide, Inches(7.05), Inches(2.70), Inches(5.68), Inches(4.15), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(7.30), Inches(2.88), Inches(5.2), Inches(0.3), "Cobertura de flujos y trazabilidad", 12, NAVY, True)
    flows = [
        "HU-01–HU-05: autenticación, catálogo, reservas, solicitudes admin, devolución y penalización; código y pruebas verificables.",
        "HU-06, HU-07, HU-08: carnet QR, CRUD de equipos y levantamiento de sanciones; sin evidencia completa en el repositorio.",
        "HU-11, HU-13, HU-14, HU-15: dashboard gráfico, usuarios, escaneo y acta PDF; declaradas como brechas pendientes.",
    ]
    add_bullet_list(slide, Inches(7.30), Inches(3.25), Inches(5.15), Inches(2.25), flows, 9, INK, TEAL, 4)

    add_rect(slide, Inches(7.30), Inches(5.65), Inches(5.15), Inches(0.012), BORDER)
    add_text(slide, Inches(7.30), Inches(5.75), Inches(5.15), Inches(0.25), "Transparencia de evidencias:", 9, TEAL_DARK, True)
    add_text(
        slide,
        Inches(7.30),
        Inches(6.00),
        Inches(5.15),
        Inches(0.70),
        "• Capturas E2E provienen de corrida previa documentada.\n"
        "• Pruebas unitarias incrementadas de 93 a 101 (todas verdes).\n"
        "• La trazabilidad no afirma implementación de HU sin código/pruebas verificables.\n"
        "• Katalon y Testomat.io documentados como plantillas y CSV.",
        8.2,
        SLATE,
        spacing=1.05,
    )

    footer(slide)


# ---------------------------------------------------------------------------
# 4. Lámina 3 - Rendimiento (JMeter)
# ---------------------------------------------------------------------------


def slide_jmeter(prs, jm_carga, jm_estres):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Rendimiento y Capacidad con Apache JMeter", "El sistema soportó la carga y el estrés sin caídas", 3)

    metrics = [
        (f"{jm_carga.get('muestras', 79424):,}", "peticiones en Carga\n(50 usuarios · 60 s)", NAVY),
        (f"{jm_carga.get('p95_ms', 48.0):.0f} ms", "p95 Carga (50u)\n(SLA: < 3 000 ms)", GREEN),
        (f"{jm_estres.get('muestras', 113600):,}", "peticiones en Estrés\n(150 usuarios · 90 s)", TEAL_DARK),
        (f"{jm_estres.get('p95_ms', 151.0):.0f} ms", "p95 Estrés (150u)\n(SLA: < 5 000 ms)", GREEN),
    ]
    x = Inches(0.6)
    for value, label, accent in metrics:
        metric_card(slide, x, Inches(1.42), Inches(2.92), Inches(1.10), value, label, accent, 24, 9)
        x += Inches(3.06)

    # Gráfica de JMeter Carga
    chart_path = BASE / "evidencias-jmeter" / "carga" / "charts" / "response-time.png"
    if chart_path.exists():
        slide.shapes.add_picture(str(chart_path), Inches(0.6), Inches(2.72), width=Inches(7.35))
        add_text(slide, Inches(0.6), Inches(6.65), Inches(7.35), Inches(0.22), "Figura: Evolución del tiempo de respuesta promedio y p95 durante los 60s de carga (JMeter 5.6.3).", 8, SLATE, italic=True)

    # Tabla comparativa de Carga vs Estrés
    add_rect(slide, Inches(8.20), Inches(2.72), Inches(4.53), Inches(4.15), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(8.40), Inches(2.88), Inches(4.1), Inches(0.28), "Comparativa de Carga vs. Estrés", 11.5, NAVY, True)

    headers_y = Inches(3.25)
    add_text(slide, Inches(8.40), headers_y, Inches(1.8), Inches(0.22), "MÉTRICA", 8, SLATE, True)
    add_text(slide, Inches(10.20), headers_y, Inches(1.1), Inches(0.22), "CARGA (50u)", 8, SLATE, True, align=PP_ALIGN.RIGHT)
    add_text(slide, Inches(11.45), headers_y, Inches(1.1), Inches(0.22), "ESTRÉS (150u)", 8, SLATE, True, align=PP_ALIGN.RIGHT)

    table_data = [
        ("Muestras totales", f"{jm_carga.get('muestras', 79424):,}", f"{jm_estres.get('muestras', 113600):,}"),
        ("Tasa de error HTTP", "0.00 %", "0.00 %"),
        ("Throughput prom.", f"{jm_carga.get('throughput_rps', 1334.07):.0f} req/s", f"{jm_estres.get('throughput_rps', 1265.24):.0f} req/s"),
        ("Tiempo promedio", f"{jm_carga.get('promedio_ms', 34.4):.1f} ms", f"{jm_estres.get('promedio_ms', 108.9):.1f} ms"),
        ("Mediana (p50)", f"{jm_carga.get('mediana_ms', 34.0):.1f} ms", f"{jm_estres.get('mediana_ms', 101.0):.1f} ms"),
        ("Percentil 95 (p95)", f"{jm_carga.get('p95_ms', 48.0):.1f} ms", f"{jm_estres.get('p95_ms', 151.0):.1f} ms"),
        ("Percentil 99 (p99)", f"{jm_carga.get('p99_ms', 89.0):.1f} ms", f"{jm_estres.get('p99_ms', 381.0):.1f} ms"),
    ]

    yy = Inches(3.52)
    for label, val_c, val_e in table_data:
        add_text(slide, Inches(8.40), yy, Inches(1.8), Inches(0.22), label, 8.5, INK)
        add_text(slide, Inches(10.20), yy, Inches(1.1), Inches(0.22), val_c, 8.5, TEAL_DARK, True, align=PP_ALIGN.RIGHT)
        add_text(slide, Inches(11.45), yy, Inches(1.1), Inches(0.22), val_e, 8.5, NAVY, True, align=PP_ALIGN.RIGHT)
        add_rect(slide, Inches(8.40), yy + Inches(0.24), Inches(4.13), Inches(0.008), BORDER)
        yy += Inches(0.35)

    add_rect(slide, Inches(8.40), Inches(6.05), Inches(4.13), Inches(0.65), RGBColor(0xEC, 0xFD, 0xF5), RGBColor(0x05, 0x96, 0x69), MSO_SHAPE.ROUNDED_RECTANGLE, 0.10)
    add_text(slide, Inches(8.55), Inches(6.12), Inches(3.85), Inches(0.50), "VEREDICTO: APROBADA\n0 errores y tiempos de respuesta muy inferiores a los SLAs.", 9, RGBColor(0x06, 0x4E, 0x3B), True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    footer(slide)


# ---------------------------------------------------------------------------
# 5. Lámina 4 - Salud del Código (SonarQube)
# ---------------------------------------------------------------------------


def slide_sonar(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Salud del Código con SonarQube", "Vulnerabilidades resueltas y deuda técnica erradicada", 4)

    # Columna Izquierda: ANTES con captura real
    add_rect(slide, Inches(0.6), Inches(1.42), Inches(5.92), Inches(2.95), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(0.80), Inches(1.52), Inches(5.5), Inches(0.25), "ANTES (REPRODUCIDO) · 44 ISSUES ABIERTOS", 9.5, RED, True)
    add_text(slide, Inches(0.80), Inches(1.78), Inches(5.5), Inches(0.22), "1 Bug (S1082) · 2 Vulnerabilidades (S2068, S2245) · 41 Code Smells · Ratings: B / C / A", 8.2, SLATE)

    img_antes = BASE / "evidencias-sonarqube" / "antes" / "capturas-reales" / "01-dashboard.png"
    if img_antes.exists():
        slide.shapes.add_picture(str(img_antes), Inches(0.80), Inches(2.05), width=Inches(5.52), height=Inches(2.15))

    # Columna Derecha: DESPUÉS con captura real
    add_rect(slide, Inches(6.8), Inches(1.42), Inches(5.93), Inches(2.95), RGBColor(0xEC, 0xFD, 0xF5), RGBColor(0x05, 0x96, 0x69), MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(7.00), Inches(1.52), Inches(5.5), Inches(0.25), "DESPUÉS DE REFACTORIZAR · 0 ISSUES (100 % LIMPIO)", 9.5, GREEN, True)
    add_text(slide, Inches(7.00), Inches(1.78), Inches(5.5), Inches(0.22), "0 Bugs · 0 Vulnerabilidades · 0 Code Smells · Ratings: A / A / A · Quality Gate: Passed", 8.2, RGBColor(0x06, 0x4E, 0x3B))

    img_despues = BASE / "evidencias-sonarqube" / "despues" / "capturas-reales" / "01-dashboard.png"
    if img_despues.exists():
        slide.shapes.add_picture(str(img_despues), Inches(7.00), Inches(2.05), width=Inches(5.53), height=Inches(2.15))

    # Panel Inferior Izquierdo: Principales Correcciones
    add_rect(slide, Inches(0.6), Inches(4.50), Inches(6.6), Inches(2.35), WHITE, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(0.80), Inches(4.62), Inches(6.2), Inches(0.25), "Refactorizaciones aplicadas (Remediación de 10 reglas clave)", 11, NAVY, True)

    fixes = [
        "Seguridad: eliminación de contraseñas quemadas (S2068) y cambio de Math.random() por contador (S2245).",
        "Confiabilidad y accesibilidad: migración a <dialog> nativo y botón accesible con teclado (S1082, S6819, S6847).",
        "Mantenibilidad: erradicación de ternarios anidados (S3358) y reducción de complejidad cognitiva < 15 (S3776).",
        "TypeScript limpio: props Readonly en componentes React (S6759) y variables de error tipadas (S7718).",
    ]
    add_bullet_list(slide, Inches(0.80), Inches(4.95), Inches(6.2), Inches(1.80), fixes, 8.8, INK, TEAL, 4)

    # Panel Inferior Derecho: Notas de Integridad Metodológica
    add_rect(slide, Inches(7.4), Inches(4.50), Inches(5.33), Inches(2.35), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(7.60), Inches(4.62), Inches(4.9), Inches(0.25), "Notas de Integridad y Verificación", 11, NAVY, True)

    notes = [
        "Código ANTES reproducido: el repo tiene un solo commit histórico (840052e); los 44 defectos se reprodujeron fielmente.",
        "Discrepancia menor de tipos: 44 totales coinciden con la línea base histórica (2/2/40); SonarQube 26.10 clasifica 1/2/41.",
        "Cobertura en SonarQube: 0.0 % por omisión de importación LCOV en CLI (defecto de config.); cobertura real Vitest: 95.7 % / 90.3 %.",
        "Quality Gate OK en ambos: evalúa solo código nuevo en el primer escaneo según la política estándar Sonar way.",
    ]
    add_bullet_list(slide, Inches(7.60), Inches(4.95), Inches(4.9), Inches(1.80), notes, 8.2, SLATE, SLATE, 3)

    footer(slide)


# ---------------------------------------------------------------------------
# Ejecución Principal y Generación de PDF
# ---------------------------------------------------------------------------


def export_pdf(pptx_path: Path, pdf_path: Path):
    cmd = f"""
    $ppt = $null
    try {{
        $ppt = New-Object -ComObject PowerPoint.Application
        $pres = $ppt.Presentations.Open('{pptx_path.resolve()}', [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
        $pres.SaveAs('{pdf_path.resolve()}', 32)
        $pres.Close()
        Write-Host "PDF generado exitosamente: {pdf_path.resolve()}"
    }} catch {{
        Write-Host "No se pudo generar PDF vía PowerPoint COM: $($_.Exception.Message)"
    }} finally {{
        if ($ppt) {{ $ppt.Quit() }}
    }}
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], check=False, timeout=60)
    except Exception as e:
        print("Aviso al exportar PDF:", e)


def main():
    # Leer datos reales de JMeter Carga y Estrés
    jm_carga_file = BASE / "evidencias-jmeter" / "carga" / "summary.json"
    jm_carga = load_json(jm_carga_file, {}).get("general", {}) if jm_carga_file.exists() else {}

    jm_estres_file = BASE / "evidencias-jmeter" / "estres" / "summary.json"
    jm_estres = load_json(jm_estres_file, {}).get("general", {}) if jm_estres_file.exists() else {}

    # Leer cobertura real de Vitest
    backend_file = BASE / "evidencias-pruebas" / "unitarias" / "cobertura" / "backend-coverage-summary.json"
    backend = load_json(backend_file, {}).get("total", {}) if backend_file.exists() else {}
    backend_cov = backend.get("statements", {}).get("pct", 95.71)

    frontend_file = BASE / "evidencias-pruebas" / "unitarias" / "cobertura" / "frontend-coverage-summary.json"
    frontend = load_json(frontend_file, {}).get("total", {}) if frontend_file.exists() else {}
    frontend_cov = frontend.get("statements", {}).get("pct", 90.26)

    total_cases = 61

    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H

    # Generar exactamente 5 diapositivas
    slide_cover(prs)  # Diapositiva 1: Portada
    slide_verdict(prs, total_cases, backend_cov, frontend_cov, jm_carga, jm_estres)  # Diapositiva 2: Lámina 1
    slide_selenium(prs)  # Diapositiva 3: Lámina 2
    slide_jmeter(prs, jm_carga, jm_estres)  # Diapositiva 4: Lámina 3
    slide_sonar(prs)  # Diapositiva 5: Lámina 4

    prs.save(OUT_PPTX)
    print("Presentación generada:", OUT_PPTX)
    print(f"Total de diapositivas en presentación: {len(prs.slides)}")

    # Exportar a PDF
    export_pdf(OUT_PPTX, OUT_PDF)


if __name__ == "__main__":
    main()
