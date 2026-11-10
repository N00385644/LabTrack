"""Genera la presentación ejecutiva de LabTrack (5 diapositivas).

Estructura exigida por la rúbrica T3:
- Portada: título, autores y docente.
- Lámina 1 · Veredicto de calidad (honesto: certificado con observaciones).
- Lámina 2 · Automatización E2E con Selenium: 4/7 -> 7/7 y regresión S6819.
- Lámina 3 · Rendimiento con Apache JMeter: carga 50 y estrés 150 usuarios.
- Lámina 4 · Salud del código con SonarQube: antes y después reales.

Criterio de diseño: poco texto, jerarquía visual y evidencias reales.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BASE = Path(__file__).resolve().parent
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
MINT = RGBColor(0xEC, 0xFD, 0xF5)
ROSE = RGBColor(0xFD, 0xEC, 0xEC)

FONT = "Segoe UI"
FONT_LIGHT = "Segoe UI Light"

W = Inches(13.333)
H = Inches(7.5)

AUTHORS = [
    "BOÑON FERNÁNDEZ, Josue Samuel",
    "HERRERA RUITON, Jhenifer",
    "QUILICHE CABANILLA, Carlos Miguel",
    "RAICO MOYA, Frank Jhancarlos",
    "VILLANUEVA COJAL, Luis Oswaldo",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
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
    for index, line in enumerate(text.split("\n")):
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


def add_picture_fit(slide, path: Path, x, y, width):
    """Inserta una imagen conservando su relación de aspecto."""
    with Image.open(path) as im:
        ratio = im.height / im.width
    return slide.shapes.add_picture(str(path), x, y, width=width, height=int(width * ratio))


def header(slide, kicker, title, number=None):
    add_rect(slide, 0, 0, W, Inches(0.09), TEAL)
    add_text(slide, Inches(0.62), Inches(0.34), Inches(9.6), Inches(0.26), kicker.upper(), 10.5, TEAL_DARK, True)
    add_text(slide, Inches(0.6), Inches(0.60), Inches(10.9), Inches(0.72), title, 25, NAVY, True)
    if number is not None:
        add_text(slide, Inches(11.95), Inches(0.38), Inches(0.8), Inches(0.32), f"LÁMINA {number}", 10.5, SLATE, True, align=PP_ALIGN.RIGHT)
        add_rect(slide, Inches(11.95), Inches(0.72), Inches(0.8), Inches(0.04), TEAL)


def footer(slide, text="LabTrack · Calidad y Pruebas de Software · UPN 2026"):
    add_rect(slide, Inches(0.6), Inches(7.05), Inches(12.13), Inches(0.012), BORDER)
    add_text(slide, Inches(0.6), Inches(7.12), Inches(10.4), Inches(0.25), text, 8, SLATE)
    add_text(slide, Inches(11.4), Inches(7.12), Inches(1.33), Inches(0.25), "UPN · T3", 8, SLATE, True, align=PP_ALIGN.RIGHT)


def metric_card(slide, x, y, w, h, value, label, accent=TEAL, value_size=30, label_size=10, fill=WHITE):
    add_rect(slide, x, y, w, h, fill, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.08)
    add_rect(slide, x, y, Inches(0.07), h, accent)
    add_text(slide, x + Inches(0.22), y + Inches(0.13), w - Inches(0.34), Inches(0.55), value, value_size, accent, True, spacing=0.9)
    add_text(slide, x + Inches(0.22), y + h - Inches(0.52), w - Inches(0.34), Inches(0.42), label, label_size, SLATE, spacing=0.95)


def chip(slide, x, y, w, text, fill=TEAL, color=WHITE, size=9.5, h=Inches(0.32)):
    shp = add_rect(slide, x, y, w, h, fill, None, MSO_SHAPE.ROUNDED_RECTANGLE, 0.35)
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


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ---------------------------------------------------------------------------
# 1. Portada
# ---------------------------------------------------------------------------
def slide_cover(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, NAVY)
    add_rect(slide, 0, 0, Inches(0.2), H, TEAL)
    add_rect(slide, Inches(10.6), Inches(-1.4), Inches(4.4), Inches(4.4), NAVY_LIGHT, None, MSO_SHAPE.OVAL)
    add_rect(slide, Inches(11.6), Inches(5.2), Inches(3.6), Inches(3.6), RGBColor(0x11, 0x2A, 0x4D), None, MSO_SHAPE.OVAL)

    add_text(slide, Inches(0.95), Inches(0.62), Inches(9.6), Inches(0.30), "UNIVERSIDAD PRIVADA DEL NORTE · INGENIERÍA DE SISTEMAS COMPUTACIONALES", 9.5, RGBColor(0x99, 0xF6, 0xE4), True)
    add_text(slide, Inches(0.95), Inches(1.10), Inches(9.0), Inches(0.30), "CALIDAD Y PRUEBAS DE SOFTWARE · CASO DE ESTUDIO T3", 12, TEAL, True)

    add_text(slide, Inches(0.9), Inches(1.85), Inches(10.2), Inches(0.42), "SISTEMA DE GESTIÓN DE LABORATORIOS", 16, RGBColor(0xCB, 0xD5, 0xE1), True)
    add_text(slide, Inches(0.86), Inches(2.18), Inches(10.2), Inches(1.15), "LabTrack", 62, WHITE, True, FONT_LIGHT)
    add_rect(slide, Inches(0.95), Inches(3.42), Inches(1.3), Inches(0.07), TEAL)
    add_text(
        slide,
        Inches(0.95),
        Inches(3.62),
        Inches(6.0),
        Inches(0.85),
        "Informe técnico y sustentación de calidad:\nautomatización, rendimiento y deuda técnica",
        15,
        RGBColor(0xE2, 0xE8, 0xF0),
        False,
        FONT_LIGHT,
        spacing=1.1,
    )

    chips = ["Selenium 7/7", "JMeter 50 y 150 usuarios", "SonarQube 0/0/0"]
    cx = Inches(0.95)
    chip_widths = [Inches(1.80), Inches(2.26), Inches(2.00)]
    for label, width in zip(chips, chip_widths):
        chip(slide, cx, Inches(4.82), width, label, NAVY_LIGHT, WHITE, 9, Inches(0.38))
        cx += width + Inches(0.12)

    add_text(slide, Inches(0.95), Inches(6.02), Inches(5.6), Inches(0.28), "Docente: Mark Anthony Arribasplata Palomino", 10.5, RGBColor(0xCB, 0xD5, 0xE1), True)
    add_text(slide, Inches(0.95), Inches(6.36), Inches(5.6), Inches(0.28), "Cajamarca, Perú · Noviembre de 2026", 10, SLATE)

    add_text(slide, Inches(7.45), Inches(4.02), Inches(5.2), Inches(0.26), "AUTORES", 9, TEAL, True)
    add_rect(slide, Inches(7.45), Inches(4.30), Inches(4.85), Inches(0.015), RGBColor(0x33, 0x4E, 0x75))
    ay = Inches(4.44)
    for name in AUTHORS:
        add_text(slide, Inches(7.45), ay, Inches(5.2), Inches(0.30), f"{name}  (100 %)", 9.2, RGBColor(0xE2, 0xE8, 0xF0))
        ay += Inches(0.34)

    add_notes(
        slide,
        "Presentación de 5 minutos. Portada con el equipo completo y el alcance del caso T3. "
        "Las cifras que se muestran provienen de ejecuciones reales documentadas en docs/.",
    )


# ---------------------------------------------------------------------------
# 2. Lámina 1 · Veredicto de calidad
# ---------------------------------------------------------------------------
def slide_verdict(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Veredicto de calidad", "LabTrack queda certificado con observaciones", 1)

    add_rect(slide, Inches(0.6), Inches(1.46), Inches(12.13), Inches(1.30), MINT, GREEN, MSO_SHAPE.ROUNDED_RECTANGLE, 0.07)
    add_rect(slide, Inches(0.6), Inches(1.46), Inches(0.10), Inches(1.30), GREEN)
    add_text(
        slide,
        Inches(0.95),
        Inches(1.56),
        Inches(11.55),
        Inches(0.48),
        "Apto para operar en el alcance verificado; no para producción sin cerrar las brechas.",
        17,
        RGBColor(0x06, 0x4E, 0x3B),
        True,
    )
    add_text(
        slide,
        Inches(0.95),
        Inches(2.08),
        Inches(11.55),
        Inches(0.55),
        "Los flujos críticos, el rendimiento y la deuda técnica están verificados. Quedan una observación de "
        "accesibilidad y una historia parcial: HU-07 tiene CRUD API sin pantalla administrativa.",
        11.5,
        RGBColor(0x06, 0x4E, 0x3B),
        italic=True,
        spacing=1.05,
    )

    cards = [
        ("7/7", "flujos E2E aprobados\n(Selenium, Chrome headless)", TEAL_DARK),
        ("0.00 %", "errores HTTP bajo carga\ny estrés (JMeter)", GREEN),
        ("0/0/0", "bugs / vulnerabilidades /\ncode smells (SonarQube A/A/A)", NAVY_LIGHT),
        ("11 de 12", "historias con implementación\nverificada; HU-07 parcial", AMBER),
    ]
    x = Inches(0.6)
    for value, label, accent in cards:
        metric_card(slide, x, Inches(3.06), Inches(2.91), Inches(1.72), value, label, accent, 32, 9.5)
        x += Inches(3.07)

    add_text(slide, Inches(0.6), Inches(5.06), Inches(4.4), Inches(0.26), "LO QUE FALTA PARA CERRAR", 9, RED, True)
    pending = [
        "Contraste WCAG 2.1 AA: axe-core reporta 1 regla pendiente.",
        "HU-07: CRUD de equipos en API, sin pantalla administrativa.",
        "HU-06 a HU-15 tienen pruebas unitarias; Selenium E2E cubre HU-01 a HU-05. WAVE pendiente.",
    ]
    y = Inches(5.38)
    for item in pending:
        add_rect(slide, Inches(0.62), y + Inches(0.10), Inches(0.09), Inches(0.09), RED, None, MSO_SHAPE.OVAL)
        add_text(slide, Inches(0.85), y, Inches(11.5), Inches(0.30), item, 10.5, INK)
        y += Inches(0.38)

    add_text(slide, Inches(0.6), Inches(6.55), Inches(12.0), Inches(0.30), "Testomat.io: 65 importados, 61 passed según CSV y 4 pending de validación humana.", 10.5, TEAL_DARK)
    footer(slide)
    add_notes(
        slide,
        "Veredicto honesto: el sistema supera las pruebas en el alcance verificado, pero no se declara conformidad total. HU-01 usa código N + 8 dígitos (N00385644), administrador ADMIN01 y bloqueo de 5 minutos tras 3 fallos. Las historias originales del docente no fijan formato ni duración. HU-07 es parcial por falta de pantalla administrativa. Testomat.io: corrida d1058425, 61 passed trasladados del CSV y 4 pending; no es una nueva ejecución de Selenium o Vitest. Los cinco casos IA tienen diseño validado, no ejecución; IA-05 no se importó.",
    )


# ---------------------------------------------------------------------------
# 3. Lámina 2 · Automatización E2E con Selenium
# ---------------------------------------------------------------------------
def slide_selenium(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Automatización E2E · Selenium 4.27", "Login y reservas: de 4/7 a 7/7 tras corregir la regresión", 2)

    # Panel izquierdo: antes y después
    add_rect(slide, Inches(0.6), Inches(1.46), Inches(5.55), Inches(2.34), ROSE, RGBColor(0xF3, 0xC0, 0xC0), MSO_SHAPE.ROUNDED_RECTANGLE, 0.06)
    add_text(slide, Inches(0.85), Inches(1.55), Inches(2.4), Inches(0.25), "CORRIDA 1", 9, RED, True)
    add_text(slide, Inches(0.85), Inches(1.74), Inches(2.2), Inches(0.60), "4/7", 46, RED, True)
    add_text(slide, Inches(0.85), Inches(2.42), Inches(2.85), Inches(0.30), "3 fallos por selectores", 10, RED)

    add_text(slide, Inches(2.95), Inches(1.86), Inches(0.9), Inches(0.6), "→", 34, SLATE, True, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(3.55), Inches(1.46), Inches(2.60), Inches(2.34), MINT, GREEN, MSO_SHAPE.ROUNDED_RECTANGLE, 0.06)
    add_text(slide, Inches(3.78), Inches(1.55), Inches(2.2), Inches(0.25), "CORRIDA FINAL", 9, GREEN, True)
    add_text(slide, Inches(3.78), Inches(1.74), Inches(2.2), Inches(0.60), "7/7", 46, GREEN, True)
    add_text(slide, Inches(3.78), Inches(2.42), Inches(2.2), Inches(0.30), "0 fallos", 10, GREEN)

    add_rect(slide, Inches(0.6), Inches(3.96), Inches(5.55), Inches(1.32), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.05)
    add_text(slide, Inches(0.82), Inches(4.04), Inches(5.15), Inches(0.26), "CAUSA Y CORRECCIÓN", 8.5, TEAL_DARK, True)
    add_text(
        slide,
        Inches(0.82),
        Inches(4.30),
        Inches(5.15),
        Inches(0.92),
        "La refactorización S6819 cambió [role=\"status\"] y [role=\"dialog\"] por <output> y <dialog>. "
        "Se corrigieron solo los selectores de prueba; el sistema nunca dejó de funcionar.",
        9.6,
        INK,
        spacing=1.08,
    )

    add_text(slide, Inches(0.6), Inches(5.42), Inches(5.55), Inches(0.24), "COBERTURA DE LA SUITE FINAL", 8.5, TEAL_DARK, True)
    covered = [
        ("HU-01", "Login inválido, bloqueo y sesión"),
        ("HU-02", "Filtros exactos por categoría"),
        ("HU-03", "Reserva desde el catálogo"),
        ("HU-04", "Aprobación administrativa"),
        ("HU-05", "Devolución tardía y penalización"),
    ]
    y = Inches(5.68)
    for code, label in covered:
        add_text(slide, Inches(0.6), y, Inches(0.62), Inches(0.24), code, 8.5, NAVY, True)
        add_text(slide, Inches(1.24), y, Inches(4.9), Inches(0.24), label, 8.5, SLATE)
        y += Inches(0.25)

    # Panel derecho: capturas reales de la corrida final
    shots = [
        ("03-catalogo-estudiante.png", "Catálogo del estudiante"),
        ("05-reserva-registrada.png", "Reserva registrada"),
        ("06-solicitud-aprobada.png", "Solicitud aprobada"),
        ("07-devolucion-penalizada.png", "Devolución penalizada"),
    ]
    shot_dir = BASE / "evidencias-pruebas" / "selenium" / "corrida-3-final-aprobada" / "screenshots"
    x0, y0 = Inches(6.30), Inches(1.46)
    tw, th = Inches(3.10), Inches(1.85)
    gap = Inches(0.14)
    for index, (name, caption) in enumerate(shots):
        col, row = index % 2, index // 2
        px = x0 + col * (tw + gap)
        py = y0 + row * (th + Inches(0.43))
        add_rect(slide, px - Inches(0.02), py - Inches(0.02), tw + Inches(0.04), th + Inches(0.04), WHITE, BORDER)
        img = shot_dir / name
        if img.exists():
            slide.shapes.add_picture(str(img), px, py, width=tw, height=th)
        add_text(slide, px, py + th + Inches(0.05), tw, Inches(0.22), caption, 7.8, SLATE, italic=True)

    # Ficha técnica de la corrida final
    add_rect(slide, Inches(6.30), Inches(5.98), Inches(6.44), Inches(0.76), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.10)
    stats = [("7", "pruebas"), ("5", "historias"), ("5.84 s", "duración"), ("JUnit", "evidencia")]
    sx = Inches(6.55)
    for value, label in stats:
        add_text(slide, sx, Inches(6.05), Inches(1.10), Inches(0.30), value, 13, NAVY, True)
        add_text(slide, sx, Inches(6.34), Inches(1.10), Inches(0.22), label, 7.8, SLATE)
        sx += Inches(1.56)

    footer(slide, "Fuente: docs/evidencias-pruebas/selenium · JUnit de la corrida final y capturas 01–08")
    add_notes(
        slide,
        "La corrida 1 aprobó 4 de 7. El fallo fue de los selectores de prueba tras la refactorización "
        "de accesibilidad S6819, no del producto. Se corrigieron las pruebas y la corrida final aprobó 7 de 7. "
        "La regresión quedó registrada como RF-13 en el backlog.",
    )


# ---------------------------------------------------------------------------
# 4. Lámina 3 · Rendimiento con Apache JMeter
# ---------------------------------------------------------------------------
def slide_jmeter(prs, carga, estres):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Rendimiento · Apache JMeter 5.6.3", "Soportó 50 y 150 usuarios sin un solo error", 3)

    samples = int(carga.get("muestras", 79424)) + int(estres.get("muestras", 113600))
    cards = [
        (f"{carga.get('p95_ms', 48.0):.0f} ms", "p95 · carga 50 usuarios", TEAL_DARK),
        (f"{estres.get('p95_ms', 151.0):.0f} ms", "p95 · estrés 150 usuarios", NAVY_LIGHT),
        (f"{carga.get('tasa_error_pct', 0.0):.2f} %", "tasa de error en ambos escenarios", GREEN),
        (f"{samples:,}".replace(",", " "), "peticiones procesadas en total", AMBER),
    ]
    x = Inches(0.6)
    for value, label, accent in cards:
        metric_card(slide, x, Inches(1.36), Inches(2.91), Inches(1.05), value, label, accent, 24, 9)
        x += Inches(3.07)

    chart_y = Inches(2.62)
    chart_w = Inches(5.95)
    left = BASE / "assets" / "jmeter" / "carga-response-time.png"
    right = BASE / "assets" / "jmeter" / "estres-response-time.png"
    if left.exists():
        add_picture_fit(slide, left, Inches(0.6), chart_y, chart_w)
    if right.exists():
        add_picture_fit(slide, right, Inches(6.78), chart_y, chart_w)
    add_text(slide, Inches(0.6), Inches(5.14), chart_w, Inches(0.24), "Carga · 50 usuarios · 60 s · promedio y p95", 8.2, SLATE, italic=True)
    add_text(slide, Inches(6.78), Inches(5.14), chart_w, Inches(0.24), "Estrés · 150 usuarios · 90 s · promedio y p95", 8.2, SLATE, italic=True)

    verdicts = [
        ("SLA p95 ≤ 3 000 ms", "48 ms", GREEN),
        ("SLA p95 ≤ 5 000 ms", "151 ms", GREEN),
        ("Throughput de carga", "1 334 req/s", TEAL_DARK),
        ("Degradación controlada", "sin caídas", NAVY_LIGHT),
    ]
    x = Inches(0.6)
    for label, value, accent in verdicts:
        add_rect(slide, x, Inches(5.52), Inches(2.91), Inches(0.92), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.09)
        add_text(slide, x + Inches(0.18), Inches(5.60), Inches(2.6), Inches(0.22), label, 8, SLATE)
        add_text(slide, x + Inches(0.18), Inches(5.84), Inches(2.6), Inches(0.38), value, 16, accent, True)
        x += Inches(3.07)

    footer(slide, "Fuente: docs/evidencias-jmeter · summary.json de las corridas de carga y estrés")
    add_notes(
        slide,
        "Carga: 79 424 peticiones, 0 % de error, p95 de 48 ms. Estrés: 113 600 peticiones, 0 % de error, "
        "p95 de 151 ms. El máximo del estrés fue 1 072 ms, muy por debajo del umbral de 5 000 ms.",
    )


# ---------------------------------------------------------------------------
# 5. Lámina 4 · Salud del código con SonarQube
# ---------------------------------------------------------------------------
def slide_sonar(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, W, H, WHITE)
    header(slide, "Salud del código · SonarQube", "44 incidencias antes, 0 después de refactorizar", 4)

    antes = BASE / "evidencias-sonarqube" / "antes" / "capturas-reales" / "01-dashboard.png"
    despues = BASE / "evidencias-sonarqube" / "despues" / "capturas-reales" / "01-dashboard.png"

    # Antes
    add_rect(slide, Inches(0.6), Inches(1.42), Inches(5.95), Inches(4.34), ROSE, RGBColor(0xF3, 0xC0, 0xC0), MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    chip(slide, Inches(0.82), Inches(1.54), Inches(1.10), "ANTES", RED, WHITE, 9)
    add_text(slide, Inches(2.04), Inches(1.55), Inches(4.3), Inches(0.30), "44 incidencias · Ratings B / C / A", 10, RED, True)
    if antes.exists():
        with Image.open(antes) as im:
            ar = im.height / im.width
        img_w = Inches(5.55)
        slide.shapes.add_picture(str(antes), Inches(0.80), Inches(1.94), width=img_w, height=int(img_w * ar))

    # Después
    add_rect(slide, Inches(6.78), Inches(1.42), Inches(5.95), Inches(4.34), MINT, GREEN, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    chip(slide, Inches(7.00), Inches(1.54), Inches(1.22), "DESPUÉS", GREEN, WHITE, 9)
    add_text(slide, Inches(8.34), Inches(1.55), Inches(4.2), Inches(0.30), "0 incidencias · Ratings A / A / A", 10, GREEN, True)
    if despues.exists():
        with Image.open(despues) as im:
            dr = im.height / im.width
        img_w = Inches(5.55)
        slide.shapes.add_picture(str(despues), Inches(6.98), Inches(1.94), width=img_w, height=int(img_w * dr))

    # Franja de cierre
    add_rect(slide, Inches(0.6), Inches(5.92), Inches(12.13), Inches(0.88), LIGHT, BORDER, MSO_SHAPE.ROUNDED_RECTANGLE, 0.10)
    add_text(slide, Inches(0.85), Inches(6.00), Inches(6.4), Inches(0.26), "1 bug · 2 vulnerabilidades · 41 code smells", 9, SLATE)
    add_text(slide, Inches(0.85), Inches(6.24), Inches(6.4), Inches(0.40), "→  0 bugs · 0 vulnerabilidades · 0 code smells", 15, GREEN, True)
    add_text(
        slide,
        Inches(7.6),
        Inches(6.05),
        Inches(4.95),
        Inches(0.60),
        "El ANTES se reprodujo desde el commit 840052e con los 44 defectos documentados.",
        8.8,
        SLATE,
        italic=True,
        spacing=1.05,
    )

    footer(slide, "Fuente: docs/evidencias-sonarqube · capturas reales 01-dashboard.png de ambos estados")
    add_notes(
        slide,
        "Se corrigieron las 44 incidencias: 1 bug, 2 vulnerabilidades y 41 code smells. Las calificaciones "
        "pasaron de B/C/A a A/A/A. El estado ANTES fue reproducido porque el repositorio tiene un único commit histórico.",
    )


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------
def export_pdf(pptx_path: Path, pdf_path: Path):
    cmd = f"""
    $ppt = $null
    try {{
        $ppt = New-Object -ComObject PowerPoint.Application
        $pres = $ppt.Presentations.Open('{pptx_path.resolve()}', [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
        $pres.SaveAs('{pdf_path.resolve()}', 32)
        $pres.Close()
        Write-Output "PDF_OK"
    }} catch {{
        Write-Output "PDF_WARN: $($_.Exception.Message)"
    }} finally {{
        if ($ppt) {{ $ppt.Quit() }}
    }}
    """
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], check=False, timeout=180, capture_output=True, text=True)
        print((result.stdout or "").strip())
    except Exception as exc:
        print("Aviso al exportar PDF:", exc)


def main():
    carga_file = BASE / "evidencias-jmeter" / "carga" / "summary.json"
    carga = load_json(carga_file, {}).get("general", {}) if carga_file.exists() else {}
    estres_file = BASE / "evidencias-jmeter" / "estres" / "summary.json"
    estres = load_json(estres_file, {}).get("general", {}) if estres_file.exists() else {}

    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H

    slide_cover(prs)
    slide_verdict(prs)
    slide_selenium(prs)
    slide_jmeter(prs, carga, estres)
    slide_sonar(prs)

    prs.save(OUT_PPTX)
    print("Presentación generada:", OUT_PPTX)
    print("Total de diapositivas:", len(prs.slides))
    export_pdf(OUT_PPTX, OUT_PDF)


if __name__ == "__main__":
    main()
