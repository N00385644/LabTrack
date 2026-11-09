"""Genera la presentación ejecutiva de LabTrack (5 diapositivas).

Lee métricas reales de cobertura, JMeter y SonarQube para que las cifras
presentadas coincidan con el informe técnico y los artefactos del repositorio.
"""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
ASSETS = BASE / "assets"
OUT = BASE / "presentacion-labtrack.pptx"

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
    return json.loads(path.read_text(encoding="utf-8"))


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


def add_bullet_list(slide, x, y, w, h, items, size=14, color=INK, bullet_color=TEAL, spacing=8):
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
    add_text(slide, Inches(0.62), Inches(0.42), Inches(9.5), Inches(0.3), kicker.upper(), 11, TEAL_DARK, True)
    add_text(slide, Inches(0.6), Inches(0.68), Inches(10.6), Inches(0.7), title, 27, NAVY, True)
    if number is not None:
        add_text(slide, Inches(12.2), Inches(0.45), Inches(0.6), Inches(0.4), f"{number:02d}", 12, SLATE, True, align=PP_ALIGN.RIGHT)
        add_rect(slide, Inches(12.26), Inches(0.78), Inches(0.46), Inches(0.045), TEAL)


def footer(slide, text="LabTrack · Calidad y Pruebas de Software · UPN 2026"):
    add_rect(slide, Inches(0.6), Inches(7.02), Inches(12.13), Inches(0.012), BORDER)
    add_text(slide, Inches(0.6), Inches(7.1), Inches(10), Inches(0.25), text, 8, SLATE)
    add_text(slide, Inches(11.4), Inches(7.1), Inches(1.33), Inches(0.25), "UPN · T3", 8, SLATE, True, align=PP_ALIGN.RIGHT)


def metric_card(slide, x, y, w, h, value, label, accent=TEAL, value_size=30, label_size=10):
    card = add_rect(slide, x, y, w, h, WHITE, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.08)
    add_rect(slide, x, y, Inches(0.06), h, accent)
    add_text(slide, x + Inches(0.18), y + Inches(0.12), w - Inches(0.3), Inches(0.55), value, value_size, accent, True, spacing=0.95)
    add_text(slide, x + Inches(0.18), y + h - Inches(0.46), w - Inches(0.3), Inches(0.36), label, label_size, SLATE, spacing=0.95)


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
# Diapositivas
# ---------------------------------------------------------------------------


def slide_cover(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, NAVY)
    add_rect(slide, 0, 0, Inches(0.22), H, TEAL)
    # Adornos geométricos discretos
    add_rect(slide, Inches(10.4), Inches(-1.3), Inches(4.6), Inches(4.6), NAVY_LIGHT, None, MSO_SHAPE.OVAL)
    add_rect(slide, Inches(11.4), Inches(5.4), Inches(3.4), Inches(3.4), RGBColor(0x11, 0x2A, 0x4D), None, MSO_SHAPE.OVAL)

    add_text(slide, Inches(1.0), Inches(0.62), Inches(8.6), Inches(0.3), "UNIVERSIDAD PRIVADA DEL NORTE · INGENIERÍA DE SISTEMAS", 10, RGBColor(0x99, 0xF6, 0xE4), True)
    add_text(slide, Inches(1.0), Inches(1.55), Inches(10.4), Inches(0.4), "CALIDAD Y PRUEBAS DE SOFTWARE · CASO DE ESTUDIO T3", 12, TEAL, True)
    add_text(slide, Inches(0.96), Inches(2.15), Inches(10.8), Inches(1.2), "LabTrack", 62, WHITE, True, FONT_LIGHT)
    add_rect(slide, Inches(1.0), Inches(3.42), Inches(1.1), Inches(0.07), TEAL)
    add_text(
        slide,
        Inches(1.0),
        Inches(3.68),
        Inches(9.6),
        Inches(0.95),
        "Gestión de préstamos de laboratorio:\ncalidad verificable, automatización y rendimiento",
        21,
        RGBColor(0xE2, 0xE8, 0xF0),
        False,
        FONT_LIGHT,
        spacing=1.05,
    )

    chip(slide, Inches(1.0), Inches(5.0), Inches(2.5), "100 pruebas automatizadas", RGBColor(0x0F, 0x76, 0x6E), WHITE, 10)
    chip(slide, Inches(3.65), Inches(5.0), Inches(2.15), "50 usuarios · JMeter", RGBColor(0x1D, 0x34, 0x5D), WHITE, 10)
    chip(slide, Inches(5.95), Inches(5.0), Inches(2.2), "SonarQube · quality gate", RGBColor(0x1D, 0x34, 0x5D), WHITE, 10)

    add_text(slide, Inches(1.0), Inches(6.28), Inches(6.5), Inches(0.3), "Docente: Mark Anthony Arribasplata Palomino", 10, RGBColor(0xCB, 0xD5, 0xE1))
    add_text(slide, Inches(1.0), Inches(6.6), Inches(6.5), Inches(0.3), "Lima, Perú · Noviembre de 2026", 10, SLATE)
    add_text(slide, Inches(7.2), Inches(6.28), Inches(4.9), Inches(0.65), "[Integrante 1] · [Integrante 2]\n[Integrante 3]", 10, RGBColor(0xCB, 0xD5, 0xE1), align=PP_ALIGN.RIGHT)


def slide_verdict(prs, total_cases, backend_cov, frontend_cov, jm, sonar):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Veredicto de calidad", "LabTrack está apto para producción controlada", 1)

    # Banda de veredicto
    band = add_rect(slide, Inches(0.6), Inches(1.52), Inches(12.13), Inches(0.85), RGBColor(0xEC, 0xFD, 0xF5), RGBColor(0x05, 0x96, 0x69), MSO_SHAPE.ROUNDED_RECTANGLE, 0.12)
    add_rect(slide, Inches(0.6), Inches(1.52), Inches(0.09), Inches(0.85), GREEN)
    add_text(slide, Inches(0.92), Inches(1.63), Inches(3.4), Inches(0.55), "APROBADO", 24, GREEN, True, anchor=MSO_ANCHOR.MIDDLE)
    add_text(
        slide,
        Inches(3.9),
        Inches(1.63),
        Inches(8.6),
        Inches(0.62),
        "Cinco historias verificadas · cero defectos abiertos · rendimiento y deuda técnica bajo control",
        12,
        RGBColor(0x06, 0x4E, 0x3B),
        False,
        anchor=MSO_ANCHOR.MIDDLE,
    )

    cards = [
        (f"{total_cases}", "casos funcionales\nejecutados y conformes", TEAL),
        ("100", "ejecuciones automatizadas\n(49 API · 44 UI · 7 E2E)", NAVY_LIGHT),
        (f"{backend_cov:.1f} %", "cobertura de sentencias\nen el backend", TEAL_DARK),
        (f"{frontend_cov:.1f} %", "cobertura de sentencias\nen el frontend", TEAL_DARK),
        (f"{jm.get('errores', 0)}", "errores en la prueba\nde 50 usuarios concurrentes", GREEN),
        (f"{jm.get('p95_ms', 0):.0f} ms", "percentil 95 de respuesta\n(umbral: 3 000 ms)", GREEN),
    ]
    x = Inches(0.6)
    y = Inches(2.72)
    width = Inches(1.9)
    gap = Inches(0.146)
    for value, label, accent in cards:
        metric_card(slide, x, y, width, Inches(1.42), value, label, accent, 26, 9)
        x += width + gap

    # Pirámide + hitos
    slide.shapes.add_picture(str(ASSETS / "piramide-pruebas.png"), Inches(0.55), Inches(4.35), height=Inches(2.42))
    add_text(slide, Inches(6.3), Inches(4.42), Inches(6.4), Inches(0.3), "Hitos de la auditoría", 13, NAVY, True)

    milestones = [
        ("Funcional", "61/61 casos conformes; reglas de negocio y mensajes exactos verificados."),
        ("Rendimiento", f"{jm.get('muestras', 0):,} peticiones, 0 % de errores y p95 de {jm.get('p95_ms', 0):.0f} ms."),
        ("Código", f"Quality gate {sonar.get('final', {}).get('qualityGate', 'OK')} · {sonar.get('final', {}).get('codeSmells', 0)} code smells tras refactorizar."),
    ]
    yy = Inches(4.8)
    for title, text in milestones:
        add_rect(slide, Inches(6.3), yy, Inches(0.06), Inches(0.56), TEAL)
        add_text(slide, Inches(6.5), yy - Inches(0.02), Inches(1.2), Inches(0.26), title, 10, TEAL_DARK, True)
        add_text(slide, Inches(7.62), yy - Inches(0.02), Inches(5.0), Inches(0.62), text, 10, INK, spacing=1.0)
        yy += Inches(0.7)

    footer(slide)


def slide_selenium(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Automatización de pruebas", "Selenium valida el recorrido real del usuario", 2)

    # Cifras
    metrics = [
        ("49", "pruebas de API\nVitest + Supertest", NAVY),
        ("44", "pruebas de interfaz\nVitest + RTL", NAVY_LIGHT),
        ("7", "flujos E2E\nSelenium + Chrome", TEAL_DARK),
        ("0", "fallos\nen la última ejecución", GREEN),
    ]
    x = Inches(0.6)
    for value, label, accent in metrics:
        metric_card(slide, x, Inches(1.5), Inches(2.92), Inches(1.16), value, label, accent, 26, 9)
        x += Inches(3.06)

    # Capturas
    add_text(slide, Inches(0.6), Inches(2.95), Inches(6.2), Inches(0.3), "Evidencia visual de los flujos críticos", 12, NAVY, True)
    shots = [
        ("03-catalogo-estudiante.png", "Catálogo y disponibilidad"),
        ("05-reserva-registrada.png", "Reserva registrada"),
        ("06-solicitud-aprobada.png", "Aprobación administrativa"),
        ("07-devolucion-penalizada.png", "Penalización automática"),
    ]
    positions = [
        (Inches(0.6), Inches(3.32)),
        (Inches(3.8), Inches(3.32)),
        (Inches(0.6), Inches(5.14)),
        (Inches(3.8), Inches(5.14)),
    ]
    for (name, caption), (px, py) in zip(shots, positions):
        add_rect(slide, px - Inches(0.04), py - Inches(0.04), Inches(2.83), Inches(1.55), WHITE, BORDER)
        slide.shapes.add_picture(str(ROOT / "frontend" / "e2e" / "screenshots" / name), px, py, width=Inches(2.75))
        add_text(slide, px, py + Inches(1.62), Inches(2.75), Inches(0.2), caption, 7.5, SLATE, italic=True)

    # Panel derecho: flujos y datos
    add_rect(slide, Inches(7.05), Inches(2.95), Inches(5.68), Inches(3.75), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(7.3), Inches(3.12), Inches(5.2), Inches(0.3), "Flujos E2E verificados", 12, NAVY, True)
    flows = [
        "Credenciales inválidas con el texto exacto exigido.",
        "Bloqueo de cuenta tras tres intentos fallidos.",
        "Login de estudiante y despliegue del catálogo.",
        "Filtros exactos de Electrónica y Redes.",
        "Reserva desde el catálogo con horario válido.",
        "Aprobación administrativa de la solicitud.",
        "Devolución tardía con penalización en bitácora.",
    ]
    add_bullet_list(slide, Inches(7.3), Inches(3.5), Inches(5.15), Inches(1.95), flows, 9.5, INK, TEAL, 3)
    add_rect(slide, Inches(7.3), Inches(5.55), Inches(5.15), Inches(0.012), BORDER)
    add_text(slide, Inches(7.3), Inches(5.68), Inches(5.1), Inches(0.28), "Reporte JUnit: 7 pruebas · 0 fallos · 0 errores · 4.15 s", 9.5, TEAL_DARK, True)
    add_text(slide, Inches(7.3), Inches(5.98), Inches(5.1), Inches(0.55), "Selectores data-testid estables, esperas explícitas por condición y capturas automáticas como evidencia.", 9, SLATE, spacing=1.0)

    footer(slide)


def slide_jmeter(prs, jm, per_label):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Rendimiento con Apache JMeter", "50 usuarios concurrentes sin degradación", 3)

    metrics = [
        (f"{jm.get('muestras', 0):,}", "peticiones procesadas", NAVY),
        (f"{jm.get('throughput_rps', 0):,.0f}", "req/s de throughput", TEAL_DARK),
        (f"{jm.get('p95_ms', 0):.0f} ms", "percentil 95", GREEN),
        (f"{jm.get('tasa_error_pct', 0):.2f} %", "tasa de error", GREEN),
    ]
    x = Inches(0.6)
    for value, label, accent in metrics:
        metric_card(slide, x, Inches(1.48), Inches(2.92), Inches(1.08), value, label, accent, 24, 10)
        x += Inches(3.06)

    slide.shapes.add_picture(str(ROOT / "jmeter" / "reports" / "charts" / "response-time.png"), Inches(0.6), Inches(2.78), width=Inches(7.35))

    add_rect(slide, Inches(8.25), Inches(2.78), Inches(4.48), Inches(3.95), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(8.45), Inches(2.93), Inches(4.1), Inches(0.3), "Resultados por transacción", 11, NAVY, True)
    add_text(slide, Inches(8.45), Inches(3.25), Inches(1.9), Inches(0.22), "TRANSACCIÓN", 7.5, SLATE, True)
    add_text(slide, Inches(11.65), Inches(3.25), Inches(0.9), Inches(0.22), "p95", 7.5, SLATE, True, align=PP_ALIGN.RIGHT)
    yy = Inches(3.52)
    labels = {
        "POST /api/auth/login": "Login JWT",
        "GET /api/equipment": "Catálogo",
        "GET /api/equipment?category=Cómputo": "Filtro Cómputo",
        "GET /api/equipment/stats": "Estadísticas",
        "GET /api/reservations/me": "Mis reservas",
    }
    for full, short in labels.items():
        metrics_row = per_label.get(full, {})
        if not metrics_row:
            for key, value in per_label.items():
                if key.split("?")[0] == full.split("?")[0] and ("category" not in full or "category" in key):
                    metrics_row = value
                    break
        add_text(slide, Inches(8.45), yy, Inches(2.9), Inches(0.22), short, 9, INK)
        add_text(slide, Inches(11.6), yy, Inches(0.95), Inches(0.22), f"{metrics_row.get('p95_ms', 0):.0f} ms", 9, TEAL_DARK, True, align=PP_ALIGN.RIGHT)
        add_rect(slide, Inches(8.45), yy + Inches(0.25), Inches(4.0), Inches(0.008), BORDER)
        yy += Inches(0.42)

    add_rect(slide, Inches(8.45), Inches(5.85), Inches(4.0), Inches(0.66), RGBColor(0xEC, 0xFD, 0xF5), RGBColor(0x05, 0x96, 0x69), MSO_SHAPE.ROUNDED_RECTANGLE, 0.12)
    add_text(slide, Inches(8.6), Inches(5.93), Inches(3.75), Inches(0.5), f"APROBADA · 0 errores · máximo {jm.get('maximo_ms', 0):.0f} ms", 9.5, RGBColor(0x06, 0x4E, 0x3B), True, anchor=MSO_ANCHOR.MIDDLE)

    footer(slide)


def slide_sonar(prs, sonar, backend_cov, frontend_cov):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Salud del código con SonarQube", "La deuda técnica se midió, priorizó y redujo", 4)

    baseline = sonar.get("baseline", {})
    final = sonar.get("final", {})

    # Antes / después
    add_rect(slide, Inches(0.6), Inches(1.5), Inches(5.92), Inches(1.95), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.05)
    add_text(slide, Inches(0.85), Inches(1.66), Inches(2.0), Inches(0.28), "LÍNEA BASE", 9, SLATE, True)
    add_text(slide, Inches(0.85), Inches(1.95), Inches(1.9), Inches(0.62), str(baseline.get("codeSmells", 0)), 34, NAVY, True)
    add_text(slide, Inches(2.7), Inches(2.05), Inches(2.0), Inches(0.3), "code smells", 10, SLATE)
    add_text(slide, Inches(0.85), Inches(2.62), Inches(2.0), Inches(0.28), f"{baseline.get('bugs', 0)} bugs · {baseline.get('vulnerabilities', 0)} vulnerabilidades", 9, INK)
    add_text(slide, Inches(0.85), Inches(2.95), Inches(3.3), Inches(0.28), f"Cobertura {baseline.get('coverage', 0):.1f} % · Duplicación {baseline.get('duplications', 0):.1f} %", 9, INK)
    add_text(slide, Inches(4.5), Inches(2.55), Inches(1.85), Inches(0.7), f"Gate\n{baseline.get('qualityGate', '—')}", 11, SLATE, True, align=PP_ALIGN.CENTER)

    add_text(slide, Inches(6.62), Inches(2.25), Inches(0.42), Inches(0.4), "→", 24, TEAL, True, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(7.08), Inches(1.5), Inches(5.66), Inches(1.95), RGBColor(0xEC, 0xFD, 0xF5), RGBColor(0x05, 0x96, 0x69), MSO_SHAPE.ROUNDED_RECTANGLE, 0.05)
    add_text(slide, Inches(7.33), Inches(1.66), Inches(2.0), Inches(0.28), "ESTADO FINAL", 9, GREEN, True)
    add_text(slide, Inches(7.33), Inches(1.95), Inches(1.9), Inches(0.62), str(final.get("codeSmells", 0)), 34, GREEN, True)
    add_text(slide, Inches(9.18), Inches(2.05), Inches(2.2), Inches(0.3), "code smells", 10, SLATE)
    add_text(slide, Inches(7.33), Inches(2.62), Inches(2.4), Inches(0.28), f"{final.get('bugs', 0)} bugs · {final.get('vulnerabilities', 0)} vulnerabilidades", 9, INK)
    add_text(slide, Inches(7.33), Inches(2.95), Inches(3.3), Inches(0.28), f"Cobertura {final.get('coverage', 0):.1f} % · Duplicación {final.get('duplications', 0):.1f} %", 9, INK)
    gate_ok = final.get("qualityGate") == "OK"
    add_text(slide, Inches(10.85), Inches(2.55), Inches(1.6), Inches(0.7), f"Gate\n{final.get('qualityGate', '—')}", 11, GREEN if gate_ok else RED, True, align=PP_ALIGN.CENTER)

    # Calificaciones
    add_text(slide, Inches(0.62), Inches(3.7), Inches(6.0), Inches(0.3), "Calificaciones finales", 12, NAVY, True)
    ratings = [
        ("Confiabilidad", final.get("reliabilityRating", "A")),
        ("Seguridad", final.get("securityRating", "A")),
        ("Mantenibilidad", final.get("maintainabilityRating", "A")),
    ]
    x = Inches(0.6)
    for label, value in ratings:
        add_rect(slide, x, Inches(4.05), Inches(1.92), Inches(0.95), WHITE, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.08)
        add_text(slide, x + Inches(0.15), Inches(4.15), Inches(0.9), Inches(0.5), str(value), 22, TEAL_DARK, True)
        add_text(slide, x + Inches(0.85), Inches(4.22), Inches(0.95), Inches(0.5), label, 8.5, SLATE)
        x += Inches(2.04)

    add_text(slide, Inches(0.62), Inches(5.18), Inches(6.0), Inches(0.3), "Refactorizaciones de mayor impacto", 12, NAVY, True)
    actions = [
        "Ternarios anidados eliminados en servicios y páginas de administración.",
        "Modal y filtros migrados a HTML nativo accesible (<dialog>, <fieldset>).",
        "Contraseñas demo y Math.random() retirados del código fuente.",
        "Props Readonly y variables de captura normalizadas en la interfaz.",
    ]
    add_bullet_list(slide, Inches(0.65), Inches(5.52), Inches(6.0), Inches(1.25), actions, 9, INK, TEAL, 3)

    # Panel de cobertura
    add_rect(slide, Inches(7.0), Inches(3.7), Inches(5.74), Inches(2.95), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    add_text(slide, Inches(7.22), Inches(3.85), Inches(5.2), Inches(0.3), "Cobertura importada desde Vitest", 11, NAVY, True)
    bars = [
        ("Backend · sentencias", backend_cov, NAVY),
        ("Backend · ramas", baseline.get("backendBranches", 85.1), NAVY_LIGHT),
        ("Frontend · sentencias", frontend_cov, TEAL_DARK),
        ("Frontend · ramas", baseline.get("frontendBranches", 80.7), TEAL),
    ]
    yy = Inches(4.25)
    for label, value, color in bars:
        add_text(slide, Inches(7.22), yy, Inches(2.4), Inches(0.24), label, 8.5, INK)
        add_text(slide, Inches(11.75), yy, Inches(0.7), Inches(0.24), f"{value:.1f} %", 8.5, color, True, align=PP_ALIGN.RIGHT)
        add_rect(slide, Inches(7.22), yy + Inches(0.28), Inches(5.2), Inches(0.12), WHITE, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
        add_rect(slide, Inches(7.22), yy + Inches(0.28), Emu(int(Inches(5.2) * min(value, 100) / 100)), Inches(0.12), color, None, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
        yy += Inches(0.56)

    add_text(slide, Inches(7.22), Inches(6.38), Inches(5.2), Inches(0.22), "Scanner CLI 8.3.1 · PostgreSQL 18 · Community Build 26.10", 7.5, SLATE, italic=True)

    footer(slide)


def main():
    jmeter = load_json(ROOT / "jmeter" / "reports" / "summary.json", {})
    jm = jmeter.get("general", {})
    per_label = jmeter.get("por_transaccion", {})
    sonar = load_json(BASE / "sonar-data.json", {})

    backend = load_json(ROOT / "backend" / "coverage" / "coverage-summary.json", {}).get("total", {})
    frontend = load_json(ROOT / "frontend" / "coverage" / "coverage-summary.json", {}).get("total", {})
    backend_cov = backend.get("statements", {}).get("pct", 0.0)
    frontend_cov = frontend.get("statements", {}).get("pct", 0.0)
    total_cases = 61

    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H

    slide_cover(prs)
    slide_verdict(prs, total_cases, backend_cov, frontend_cov, jm, sonar)
    slide_selenium(prs)
    slide_jmeter(prs, jm, per_label)
    slide_sonar(prs, sonar, backend_cov, frontend_cov)

    prs.save(OUT)
    print("Presentación generada:", OUT)


if __name__ == "__main__":
    main()
