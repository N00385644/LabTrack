#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el informe tecnico de LabTrack a partir de la plantilla UPN.

El documento conserva la portada institucional (con sus dos logotipos), el
encabezado y el pie de pagina de ``plantilla-upn-informe.docx``. Todo el
contenido posterior a la portada se reconstruye con indices reales (campos
TOC/SEQ), formato Arial 11, texto justificado, interlineado 1,5 y A4.

Uso:
    python generate_report.py            # DOCX + PDF (Word COM)
    python generate_report.py --no-pdf   # solo DOCX
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
TEMPLATE = BASE / "fuentes-curso" / "plantilla-upn-informe.docx"
DOCX_PATH = BASE / "informe-tecnico-labtrack.docx"
PDF_PATH = BASE / "informe-tecnico-labtrack.pdf"
ASSETS = BASE / "assets"

PROJECT_TITLE = "SISTEMA DE GESTIÓN DE LABORATORIOS LABTRACK"
AUTHORS = "BOÑON, J.; HERRERA, J.; QUILICHE, C.; RAICO, F.; VILLANUEVA, L."

TEXT_WIDTH_CM = 15.0
NAVY = "1F3864"
GRAY = "4B5563"
RED = "B91C1C"
MARKERS: list[str] = []
doc: Document  # se asigna en build_report()
COUNTERS = {"Tabla": 0, "Figura": 0, "Anexo": 0}

MARKER_RE = re.compile(r"(\[COMPLETAR POR EL EQUIPO:[^\]]*\])")


# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------
def style_run(run, size=11, bold=False, italic=False, color=None, name="Arial"):
    """Aplica fuente y tamano explicitos (la plantilla usa TNR en Normal)."""
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def fmt_par(par, align="justify", before=0, after=6, line=1.5, indent=1.27):
    pf = par.paragraph_format
    pf.alignment = {
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
    }[align]
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if indent:
        pf.first_line_indent = Cm(indent)


def write_marked(par, text, size=11, bold=False, italic=False, color=None):
    """Escribe texto resaltando los marcadores pendientes del equipo."""
    for piece in MARKER_RE.split(text):
        if not piece:
            continue
        run = par.add_run(piece)
        if MARKER_RE.fullmatch(piece):
            style_run(run, size=size, bold=True, italic=False, color=RED)
            if piece not in MARKERS:
                MARKERS.append(piece)
        else:
            style_run(run, size=size, bold=bold, italic=italic, color=color)
    return par


def p(text="", size=11, bold=False, italic=False, color=None, align="justify",
      before=0, after=6, line=1.5, indent=1.27):
    par = doc.add_paragraph()
    fmt_par(par, align=align, before=before, after=after, line=line, indent=indent)
    if text:
        write_marked(par, text, size=size, bold=bold, italic=italic, color=color)
    return par


def label_par(label, text, size=11, after=6):
    """Parrafo con una etiqueta en negrita seguida de texto normal."""
    par = doc.add_paragraph()
    fmt_par(par, after=after)
    run = par.add_run(label)
    style_run(run, size=size, bold=True)
    write_marked(par, text, size=size)
    return par


def bullets(items, size=11, symbol="•"):
    for item in items:
        par = doc.add_paragraph()
        pf = par.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.left_indent = Cm(0.9)
        pf.first_line_indent = Cm(-0.45)
        pf.space_after = Pt(3)
        pf.line_spacing = 1.5
        run = par.add_run(f"{symbol} ")
        style_run(run, size=size)
        write_marked(par, item, size=size)


def h1(text, new_page=True):
    if new_page:
        doc.add_page_break()
    par = doc.add_paragraph(style="Heading 1")
    par.paragraph_format.space_before = Pt(0)
    par.paragraph_format.space_after = Pt(10)
    par.paragraph_format.line_spacing = 1.0
    par.paragraph_format.keep_with_next = True
    run = par.add_run(text)
    style_run(run, size=14, bold=True, color=NAVY)
    return par


def h2(text):
    par = doc.add_paragraph(style="Heading 2")
    par.paragraph_format.space_before = Pt(12)
    par.paragraph_format.space_after = Pt(6)
    par.paragraph_format.line_spacing = 1.0
    par.paragraph_format.keep_with_next = True
    run = par.add_run(text)
    style_run(run, size=12, bold=True, color=NAVY)
    return par


def h3(text):
    par = doc.add_paragraph()
    par.paragraph_format.space_before = Pt(10)
    par.paragraph_format.space_after = Pt(4)
    par.paragraph_format.line_spacing = 1.15
    par.paragraph_format.keep_with_next = True
    run = par.add_run(text)
    style_run(run, size=11, bold=True, color=GRAY)
    return par


# ---------------------------------------------------------------------------
# Campos de Word (indices y numeracion de tablas/figuras/anexos)
# ---------------------------------------------------------------------------
def add_field(par, instr, placeholder="Actualice el campo con F9 en Word."):
    run = par.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = f" {instr} "
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    text_el = OxmlElement("w:t")
    text_el.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr_el, sep, text_el, end):
        run._r.append(el)


def add_seq(par, identifier="Tabla", fmt=None):
    instr = f"SEQ {identifier}"
    if fmt:
        instr += f" \\* {fmt}"
    add_field(par, instr, "1")


def index_title(text):
    par = doc.add_paragraph()
    fmt_par(par, align="center", before=0, after=12, line=1.0, indent=0)
    run = par.add_run(text)
    style_run(run, size=12, bold=True, color=NAVY)
    return par


def add_index(title, instr, new_page=True):
    if new_page:
        doc.add_page_break()
    index_title(title)
    par = doc.add_paragraph()
    fmt_par(par, align="left", after=0, line=1.15, indent=0)
    add_field(par, instr, "El índice se genera al actualizar los campos en Word.")


# ---------------------------------------------------------------------------
# Tablas, figuras y bloques
# ---------------------------------------------------------------------------
def _shade(cell, color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def _cell_margins(table, top=40, start=70, bottom=40, end=70):
    tbl_pr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        el = OxmlElement(f"w:{tag}")
        el.set(qn("w:w"), str(value))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tbl_pr.insert_element_before(
        mar, "w:tblLook", "w:tblCaption", "w:tblDescription"
    )


def _table_borders(table, color="8EA9C1", size=4):
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    table._tbl.tblPr.insert_element_before(
        borders,
        "w:shd",
        "w:tblLayout",
        "w:tblCellMar",
        "w:tblLook",
        "w:tblCaption",
        "w:tblDescription",
    )


def add_table(headers, rows, widths, font_size=8.2, header_size=8.2,
              center_cols=(), zebra=True):
    widths = [w * TEXT_WIDTH_CM / sum(widths) for w in widths]
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _table_borders(table)
    _cell_margins(table)

    header = table.rows[0]
    tr_pr = header._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:tblHeader"))
    tr_pr.append(OxmlElement("w:cantSplit"))
    for i, text in enumerate(headers):
        cell = header.cells[i]
        cell.width = Cm(widths[i])
        _shade(cell, NAVY)
        par = cell.paragraphs[0]
        fmt_par(par, align="center", after=0, line=1.0, indent=0)
        run = par.add_run(text)
        style_run(run, size=header_size, bold=True, color="FFFFFF")

    for idx, row in enumerate(rows):
        tr = table.add_row()
        tr._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        total = str(row[0]).upper().startswith("TOTAL")
        for i, value in enumerate(row):
            cell = tr.cells[i]
            cell.width = Cm(widths[i])
            if total:
                _shade(cell, "DCE6F1")
            elif zebra and idx % 2 == 1:
                _shade(cell, "F4F7FB")
            for j, chunk in enumerate(str(value).split("\n")):
                par = cell.paragraphs[0] if j == 0 else cell.add_paragraph()
                fmt_par(
                    par,
                    align="center" if i in center_cols else "left",
                    after=0,
                    line=1.0,
                    indent=0,
                )
                run = par.add_run(chunk)
                style_run(run, size=font_size, bold=total or (i == 0 and total))
    p("", after=0, line=1.0, indent=0)
    return table


def ensure_caption_styles(document):
    specs = [
        ("TablaCaption", "Normal"),
        ("FiguraCaption", "Normal"),
        ("AnexoTitle", "Heading 1"),
    ]
    for name, base in specs:
        try:
            document.styles[name]
            continue
        except KeyError:
            pass
        style = document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = document.styles[base]
        style.font.name = "Arial"
        style.font.size = Pt(10)
        if name == "AnexoTitle":
            style.font.size = Pt(14)
            style.font.bold = True
            style.font.color.rgb = RGBColor.from_string(NAVY)
            ppr = style.element.get_or_add_pPr()
            outline = OxmlElement("w:outlineLvl")
            outline.set(qn("w:val"), "0")
            ppr.append(outline)


def add_seq(par, identifier="Tabla", placeholder="1", fmt=None):
    instr = f"SEQ {identifier}"
    if fmt:
        instr += f" \\* {fmt}"
    add_field(par, instr, placeholder)


def table_caption(text):
    COUNTERS["Tabla"] += 1
    par = doc.add_paragraph(style="TablaCaption")
    fmt_par(par, align="left", before=6, after=4, line=1.0, indent=0)
    par.paragraph_format.keep_with_next = True
    run = par.add_run("Tabla ")
    style_run(run, size=10, bold=True)
    add_seq(par, "Tabla", str(COUNTERS["Tabla"]))
    run = par.add_run(". ")
    style_run(run, size=10, bold=True)
    write_marked(par, text, size=10)
    return par


def figure_caption(text):
    COUNTERS["Figura"] += 1
    par = doc.add_paragraph(style="FiguraCaption")
    fmt_par(par, align="left", before=2, after=10, line=1.0, indent=0)
    run = par.add_run("Figura ")
    style_run(run, size=10, bold=True)
    add_seq(par, "Figura", str(COUNTERS["Figura"]))
    run = par.add_run(". ")
    style_run(run, size=10, bold=True)
    write_marked(par, text, size=10)
    return par


def add_figure(path, width_cm, caption):
    path = Path(path)
    if not path.exists():
        p(f"[Figura no disponible: {path.name}]", italic=True, color=RED)
        figure_caption(caption)
        return
    par = doc.add_paragraph()
    fmt_par(par, align="center", before=6, after=2, line=1.0, indent=0)
    par.paragraph_format.keep_with_next = True
    par.add_run().add_picture(str(path), width=Cm(min(width_cm, TEXT_WIDTH_CM)))
    figure_caption(caption)


def callout(title, text, fill="EAF1F8", border="1F3864"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _table_borders(table, color=border, size=8)
    _cell_margins(table, top=90, start=120, bottom=90, end=120)
    cell = table.rows[0].cells[0]
    cell.width = Cm(TEXT_WIDTH_CM)
    _shade(cell, fill)
    par = cell.paragraphs[0]
    fmt_par(par, align="left", after=3, line=1.1, indent=0)
    run = par.add_run(title)
    style_run(run, size=10, bold=True, color=NAVY)
    for chunk in text.split("\n"):
        par = cell.add_paragraph()
        fmt_par(par, align="justify", after=2, line=1.15, indent=0)
        write_marked(par, chunk, size=10)
    p("", after=4, line=1.0, indent=0)


def code_block(code):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _table_borders(table, color="D1D5DB", size=4)
    _cell_margins(table, top=60, start=100, bottom=60, end=100)
    cell = table.rows[0].cells[0]
    cell.width = Cm(TEXT_WIDTH_CM)
    _shade(cell, "F7F7F7")
    first = True
    for line in code.split("\n"):
        par = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        fmt_par(par, align="left", after=0, line=1.0, indent=0)
        run = par.add_run(line if line else " ")
        style_run(run, size=8, name="Consolas")
    p("", after=6, line=1.0, indent=0)


# ---------------------------------------------------------------------------
# Portada, encabezado y pie de pagina de la plantilla
# ---------------------------------------------------------------------------
def _replace_runs(par, new_text):
    for run in par.runs:
        run.text = ""
    if par.runs:
        par.runs[0].text = new_text
    else:
        par.add_run(new_text)


def adapt_cover(document):
    """Conserva los logotipos y ajusta los textos de la portada."""
    pars = document.paragraphs
    title = next((x for x in pars if "SISTEMA DE MONITOREO" in x.text), None)
    if title is not None:
        _replace_runs(title, PROJECT_TITLE)

    author = next((x for x in pars if "Josue" in x.text and "BOÑON" in x.text), None)
    if author is not None:
        for run in author.runs:
            if run.text.strip() == "samuel":
                run.text = " Samuel"
    year = next((x for x in pars if x.text.strip() == "2026-1"), None)
    if year is not None:
        _replace_runs(year, "2026-2")


def adapt_header_footer(document):
    section = document.sections[0]
    header_par = section.header.paragraphs[0]
    runs = header_par.runs
    # runs: [0] logotipo, [1] '<', [2]+[3] titulo de ejemplo, [4] '>'
    if len(runs) >= 5:
        runs[1].text = ""
        runs[2].text = PROJECT_TITLE
        runs[3].text = ""
        runs[4].text = ""
        style_run(runs[2], size=9, bold=False, color=GRAY)
    else:
        for run in runs:
            if "SISTEMA DE MONITOREO" in run.text or "ÓNICO DE SUNAT" in run.text:
                run.text = ""
        header_par.add_run(PROJECT_TITLE)

    footer = section.footer
    first = footer.paragraphs[0]
    # runs: [0] imagen decorativa, [1] vacio, [2] '<', [3] texto de ejemplo
    if len(first.runs) >= 4:
        first.runs[2].text = ""
        first.runs[3].text = AUTHORS
        style_run(first.runs[3], size=8, italic=False, color=GRAY)
    if len(footer.paragraphs) > 1:
        second = footer.paragraphs[1]
        # runs: [0] resto del texto de ejemplo, [1] '>', [2:] tabuladores y campo PAGE
        for run in second.runs:
            if "separados por punto y coma" in run.text or run.text.strip() == ">":
                run.text = ""


def remove_template_body(document):
    body = document.element.body
    children = list(body)
    for element in children[25:]:
        if element.tag == qn("w:sectPr"):
            continue
        body.remove(element)


def enable_field_update(document):
    settings = document.settings.element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")


# ---------------------------------------------------------------------------
# Contenido del informe
# ---------------------------------------------------------------------------
def build_report():
    global doc
    doc = Document(str(TEMPLATE))
    adapt_cover(doc)
    adapt_header_footer(doc)
    remove_template_body(doc)
    ensure_caption_styles(doc)
    enable_field_update(doc)

    # ------------------------------------------------------------------
    # Indices
    # ------------------------------------------------------------------
    add_index(
        "ÍNDICE DE CONTENIDO",
        'TOC \\o "1-2" \\h \\z \\u',
        new_page=True,
    )
    add_index("ÍNDICE DE TABLAS", 'TOC \\h \\z \\c "Tabla"')
    add_index("ÍNDICE DE FIGURAS", 'TOC \\h \\z \\c "Figura"')
    add_index("ÍNDICE DE ANEXOS", 'TOC \\h \\z \\c "Anexo"')

    # ------------------------------------------------------------------
    # RESUMEN
    # ------------------------------------------------------------------
    h1("RESUMEN")
    p(
        "El presente informe documenta la auditoría de calidad aplicada al Sistema de Gestión de "
        "Laboratorios LabTrack, una aplicación web para reservar, aprobar y devolver equipos de los "
        "laboratorios de cómputo, electrónica y redes de la Universidad Privada del Norte. El trabajo "
        "se organizó en cinco frentes verificables: análisis estático con SonarQube, pruebas unitarias "
        "y de integración con Vitest, automatización funcional de extremo a extremo con Selenium, "
        "pruebas de rendimiento con Apache JMeter y revisión de accesibilidad con axe-core. Cada "
        "resultado se contrastó contra un artefacto del repositorio; las cifras que no pudieron "
        "sustentarse se marcan expresamente como pendientes."
    )
    p(
        "El alcance declarado por el equipo comprende doce historias de usuario (HU-01, HU-02, HU-03, "
        "HU-04, HU-05, HU-06, HU-07, HU-08, HU-11, HU-13, HU-14 y HU-15). La verificación del "
        "repositorio confirma evidencia completa, con código y pruebas, para cinco de ellas; las siete "
        "restantes se reportan como brechas y no se contabilizan como funcionalidad implementada. En "
        "el plano técnico, SonarQube pasó de 44 incidencias abiertas (1 bug, 2 vulnerabilidades y 41 "
        "code smells; confiabilidad B y seguridad C) a 0 incidencias (A/A/A). Las pruebas unitarias "
        "crecieron de 93 a 101 casos aprobados, con una cobertura de 95.71 % en el backend y 90.26 % "
        "en el frontend. La suite Selenium aprobó 4 de 7 flujos en su primera corrida y 7 de 7 en la "
        "corrida final, después de corregir una regresión de selectores provocada por la refactorización "
        "de accesibilidad S6819. Las pruebas de carga (50 usuarios) y estrés (150 usuarios) registraron "
        "0.00 % de errores, con percentiles 95 de 48 ms y 151 ms respectivamente. La revisión de "
        "accesibilidad detectó únicamente fallas de contraste de color, todavía pendientes de corrección."
    )
    p(
        "Palabras clave: calidad de software; pruebas automatizadas; análisis estático; pruebas de "
        "rendimiento; accesibilidad web.",
        indent=0,
    )

    h2("Abstract")
    p(
        "This report documents the quality audit of LabTrack, a web system for managing laboratory "
        "equipment reservations at Universidad Privada del Norte. The audit covered static analysis "
        "with SonarQube, unit and integration testing with Vitest, end-to-end automation with Selenium, "
        "performance testing with Apache JMeter and accessibility review with axe-core. SonarQube went "
        "from 44 open issues to zero (A/A/A); unit tests increased from 93 to 101 with 95.71 % backend "
        "and 90.26 % frontend coverage; the Selenium suite improved from 4 of 7 passing flows to 7 of 7 "
        "after fixing a selector regression caused by the S6819 accessibility refactor; load (50 users) "
        "and stress (150 users) tests reported 0.00 % errors with p95 values of 48 ms and 151 ms. "
        "Accessibility review found only color-contrast violations, which remain open. Seven of the "
        "twelve declared user stories lack verifiable evidence in the repository and are reported as gaps."
    )
    p("Keywords: software quality; automated testing; static analysis; performance testing; web accessibility.", indent=0)

    table_caption("Indicadores consolidados de la auditoría de calidad de LabTrack.")
    add_table(
        ["Dimensión", "Indicador", "Antes", "Después", "Criterio", "Veredicto"],
        [
            ["Pruebas unitarias", "Casos aprobados", "93", "101 (+8)", "100 % en verde", "Cumple"],
            ["Cobertura backend", "Sentencias / ramas", "95.71 % / 85.00 %", "95.71 % / 85.00 %", "≥ 80 %", "Cumple"],
            ["Cobertura frontend", "Sentencias / ramas", "90.26 % / 81.69 %", "90.26 % / 81.69 %", "≥ 80 %", "Cumple"],
            ["SonarQube", "Bugs / vulnerabilidades / smells", "1 / 2 / 41", "0 / 0 / 0", "0 incidencias", "Cumple"],
            ["Confiabilidad y seguridad", "Ratings SonarQube", "B / C", "A / A", "A / A", "Cumple"],
            ["Selenium E2E", "Flujos aprobados", "4 de 7", "7 de 7", "7 de 7", "Cumple tras corrección"],
            ["JMeter carga", "Muestras / error / p95", "—", "79 424 / 0.00 % / 48 ms", "p95 < 3000 ms", "Cumple"],
            ["JMeter estrés", "Muestras / error / p95", "—", "113 600 / 0.00 % / 151 ms", "p95 < 5000 ms", "Cumple"],
            ["Accesibilidad", "Violaciones axe-core", "—", "1 en login, 17 en catálogo", "0 violaciones", "Pendiente"],
            ["Trazabilidad", "HU con evidencia completa", "5 de 12", "5 de 12", "12 de 12", "Brecha declarada"],
        ],
        [3.0, 3.4, 2.6, 2.9, 2.4, 2.0],
        font_size=7.8,
        center_cols={2, 3, 4, 5},
    )

    # ------------------------------------------------------------------
    # INTRODUCCIÓN
    # ------------------------------------------------------------------
    h1("INTRODUCCIÓN")
    h2("Motivación del proyecto")
    p(
        "La gestión física de los laboratorios universitarios suele apoyarse en bitácoras de papel o "
        "en hojas de cálculo que no se sincronizan entre sí. Esa práctica produce tres problemas "
        "recurrentes: colisiones de horario sobre un mismo equipo, pérdida de la trazabilidad del "
        "responsable del préstamo y devoluciones fuera de plazo que no generan consecuencia alguna. "
        "La digitalización del ciclo completo —reserva, aprobación, entrega, devolución y "
        "penalización— permite sustituir la confianza informal por reglas verificables y por un "
        "registro de auditoría consultable."
    )
    p(
        "La motivación académica del trabajo es complementaria. Un sistema que funciona no es "
        "necesariamente un sistema de calidad: para afirmarlo hace falta evidencia empírica sobre su "
        "corrección funcional, su comportamiento bajo concurrencia, la salud de su código y su "
        "accesibilidad. Este informe reúne esa evidencia y, sobre todo, distingue con claridad lo que "
        "fue ejecutado de lo que quedó pendiente."
    )

    h2("Propuestas")
    p(
        "LabTrack se propone como una aplicación web con tres perfiles de uso: el estudiante reserva "
        "equipos y consulta sus préstamos; el administrador aprueba o rechaza solicitudes y registra "
        "devoluciones; el sistema aplica automáticamente la penalización cuando la devolución ocurre "
        "fuera del horario comprometido. La arquitectura es desacoplada: una interfaz de página única "
        "en React, una API REST en NestJS y una base de datos relacional PostgreSQL administrada con "
        "Prisma ORM."
    )
    p(
        "Sobre esa base, la propuesta de aseguramiento de la calidad combina cuatro mecanismos. El "
        "primero es el análisis estático continuo, que detecta deuda técnica antes de que llegue a "
        "producción. El segundo es la pirámide de pruebas: unitarias e integración en la base, "
        "funcionales de extremo a extremo en la cima. El tercero es la medición del rendimiento con "
        "perfiles de carga y estrés. El cuarto es la revisión de accesibilidad, entendida como "
        "requisito de calidad y no como un añadido cosmético."
    )

    h2("Alcance y limitaciones del informe")
    bullets(
        [
            "El código del estado ANTES de SonarQube es reproducido, no histórico: el repositorio tiene un único commit y no conserva una versión previa a la refactorización. Los 44 defectos se reinyectaron en una copia de trabajo y así se documenta en todo el informe.",
            "Testomat.io, TestLink y Katalon Studio no se ejecutaron. Se entrega la plantilla de importación y el archivo CSV, sin fabricar capturas de herramientas que no se abrieron.",
            "WAVE no se ejecutó. La revisión de accesibilidad se realizó con axe-core 4.10.2, el mismo motor de la extensión, sobre las páginas de login y catálogo.",
            "Siete de las doce historias de usuario declaradas no tienen evidencia verificable de implementación completa; se reportan como brechas y no como funcionalidades terminadas.",
            "Los datos organizacionales que la plantilla solicita (historia de la institución, tamaño del área, indicadores internos) no fueron provistos por el equipo y se dejan como marcadores visibles.",
        ]
    )

    # ------------------------------------------------------------------
    # ANÁLISIS DEL PROBLEMA
    # ------------------------------------------------------------------
    h1("ANÁLISIS DEL PROBLEMA")
    h2("Antecedentes")
    p(
        "La plantilla institucional incluye antecedentes sobre automatización de buzones tributarios "
        "de SUNAT y SUNAFIL que pertenecen a otro caso de estudio y no guardan relación con LabTrack. "
        "Para no atribuir a este proyecto investigaciones que no se consultaron, esos párrafos se "
        "retiran y se deja el espacio para que el equipo incorpore sus propias fuentes."
    )
    p(
        "[COMPLETAR POR EL EQUIPO: antecedentes de investigación del proyecto, con autor, año, objetivo, "
        "metodología y resultado verificable; citar solo fuentes efectivamente leídas y enlazadas en las "
        "referencias]"
    )
    p(
        "Como marco de referencia técnico —no como antecedente de investigación— este informe se apoya "
        "en estándares públicos: la familia ISO/IEC 25010 para el modelo de calidad de producto "
        "(International Organization for Standardization [ISO], 2011), el syllabus del ISTQB para la "
        "terminología de pruebas (International Software Testing Qualifications Board [ISTQB], 2023) y "
        "las WCAG 2.1 del W3C para accesibilidad (World Wide Web Consortium [W3C], 2018)."
    )

    h2("Descripción de la organización")
    p(
        "El caso de estudio se sitúa en los laboratorios de la carrera de Ingeniería de Sistemas "
        "Computacionales de la Universidad Privada del Norte, sede Cajamarca. El equipo del curso "
        "Calidad y Pruebas de Software desarrolló LabTrack como proyecto formativo y lo sometió a una "
        "auditoría de calidad completa durante el periodo 2026-2."
    )
    p(
        "[COMPLETAR POR EL EQUIPO: descripción formal de la organización (reseña institucional, "
        "población de usuarios, cantidad de laboratorios y equipos, procesos internos de préstamo y "
        "responsables), usando únicamente información oficial o proporcionada por la institución]"
    )

    h2("Identificación y formulación del problema")
    p(
        "El proceso manual presenta cuatro fallas observables. Primero, la disponibilidad de un equipo "
        "no se conoce en tiempo real, de modo que dos estudiantes pueden creer que tienen derecho al "
        "mismo recurso en la misma franja. Segundo, la aprobación depende de la presencia física del "
        "responsable, lo que concentra la operación en horarios de oficina. Tercero, la devolución "
        "tardía no deja rastro ni consecuencia, por lo que el incentivo a devolver a tiempo es débil. "
        "Cuarto, no existe un registro único que permita responder quién tuvo un equipo, cuándo y en "
        "qué estado lo devolvió."
    )
    p(
        "Formulación: ¿en qué medida un sistema web con reglas de negocio explícitas, trazabilidad de "
        "eventos y controles automatizados de calidad puede sustituir el proceso manual de préstamo de "
        "equipos, cumpliendo criterios verificables de corrección funcional, rendimiento, "
        "mantenibilidad y accesibilidad?"
    )

    h2("Definición de objetivos")
    h3("Objetivo general")
    p(
        "Demostrar, con evidencia empírica y artefactos auditables, que LabTrack satisface los "
        "requisitos funcionales y no funcionales definidos para su operación en los laboratorios, y "
        "determinar con honestidad qué brechas impiden afirmar una certificación plena."
    )
    h3("Objetivos específicos")
    bullets(
        [
            "Diseñar y ejecutar una matriz de casos de prueba para las historias con evidencia verificable, e identificar las historias declaradas que carecen de sustento en el repositorio.",
            "Verificar la corrección funcional en tres niveles: integración de API, componentes de interfaz y flujos de extremo a extremo en navegador real.",
            "Medir el comportamiento no funcional bajo carga sostenida y estrés, y contrastarlo con umbrales de servicio explícitos.",
            "Diagnosticar la deuda técnica con análisis estático, aplicar una refactorización guiada y comprobar la reducción de incidencias.",
            "Evaluar la accesibilidad de las pantallas principales y registrar los defectos que permanecen abiertos.",
            "Consolidar la trazabilidad entre requisitos, casos de prueba, defectos y evidencias, dejando constancia de los límites del alcance.",
        ]
    )

    # ------------------------------------------------------------------
    # BASES TEÓRICAS
    # ------------------------------------------------------------------
    h1("BASES TEÓRICAS")
    h2("Calidad de producto de software")
    p(
        "La norma ISO/IEC 25010 define un modelo de calidad de producto con ocho características: "
        "adecuación funcional, eficiencia de desempeño, compatibilidad, usabilidad, fiabilidad, "
        "seguridad, mantenibilidad y portabilidad (ISO, 2011). El modelo es útil porque obliga a "
        "evaluar el sistema desde varias dimensiones y no solo desde «funciona o no funciona». En este "
        "informe, la adecuación funcional se evalúa con la matriz de casos y Selenium; la eficiencia de "
        "desempeño, con JMeter; la fiabilidad y la mantenibilidad, con SonarQube y las pruebas "
        "unitarias; la seguridad, con las reglas de análisis estático y el OWASP Top 10; la usabilidad "
        "y la accesibilidad, con axe-core y las WCAG 2.1."
    )

    h2("Pruebas de software y niveles de verificación")
    p(
        "El ISTQB organiza las pruebas por nivel —componentes, integración, sistema y aceptación— y "
        "por tipo —funcionales y no funcionales— (ISTQB, 2023). La pirámide de pruebas traduce esa "
        "clasificación en una estrategia económica: muchas pruebas rápidas en la base y pocas pruebas "
        "lentas en la cima. LabTrack aplica esa idea con 101 pruebas de Vitest en la base, pruebas de "
        "componentes con React Testing Library en la interfaz y siete flujos de extremo a extremo con "
        "Selenium en la cima. La norma IEEE 829 complementa el marco al definir el contenido esperado "
        "de la documentación de pruebas (IEEE, 2008)."
    )

    h2("Análisis estático y deuda técnica")
    p(
        "El análisis estático examina el código sin ejecutarlo y clasifica los hallazgos en bugs "
        "(fiabilidad), vulnerabilidades (seguridad) y code smells (mantenibilidad). SonarQube aplica "
        "reglas parametrizadas por lenguaje, calcula calificaciones de A a E y estima el esfuerzo de "
        "remediación (SonarSource, 2024). Su filosofía «Clean as You Code» prioriza el código nuevo, "
        "razón por la cual la puerta de calidad puede aprobar un proyecto que aún conserva deuda "
        "antigua. Comprender esa distinción es imprescindible para interpretar correctamente los "
        "resultados de este informe."
    )

    h2("Pruebas de rendimiento: carga, estrés y percentiles")
    p(
        "Una prueba de carga verifica el cumplimiento de los acuerdos de nivel de servicio bajo la "
        "demanda esperada; una prueba de estrés lleva el sistema más allá de su dimensionamiento para "
        "observar cómo degrada (Apache Software Foundation, 2024). El percentil 95 es la métrica "
        "preferida frente al promedio porque revela la latencia de cola: un promedio bajo puede ocultar "
        "un pequeño grupo de usuarios con esperas enormes. En este trabajo se reportan mediana, p90, "
        "p95, p99, máximo, desviación estándar, throughput y tasa de error para cada transacción."
    )

    h2("Automatización de pruebas de interfaz")
    p(
        "Selenium WebDriver controla un navegador real mediante el protocolo W3C WebDriver y permite "
        "automatizar recorridos completos de usuario (Selenium Project, 2024). Su fortaleza es la "
        "fidelidad: prueba lo mismo que ve la persona. Su debilidad es la fragilidad de los localizadores, "
        "que se rompen cuando cambia el marcado. Esa fragilidad se materializó en este proyecto y se "
        "documenta como hallazgo, porque constituye una lección de ingeniería más valiosa que una "
        "corrida perfecta."
    )

    h2("Accesibilidad web")
    p(
        "Las WCAG 2.1 organizan los requisitos de accesibilidad en cuatro principios —perceptible, "
        "operable, comprensible y robusto— con niveles A, AA y AAA (W3C, 2018). El nivel AA es el "
        "referente habitual para sitios institucionales. La especificación WAI-ARIA advierte que los "
        "elementos nativos de HTML deben preferirse a los roles ARIA simulados, porque aportan "
        "semántica y comportamiento de teclado de forma gratuita (W3C, 2023). axe-core automatiza "
        "parte de la verificación, aunque no sustituye la revisión manual ni las pruebas con usuarios "
        "(Deque Systems, 2024)."
    )

    h2("Seguridad de aplicaciones")
    p(
        "El OWASP Top 10 identifica las categorías de riesgo más relevantes para aplicaciones web, "
        "entre ellas el fallo de control de acceso, la identificación y autenticación deficientes y la "
        "exposición de credenciales (OWASP Foundation, 2021). Las reglas S2068 y S2245 de SonarQube, "
        "que detectaron una contraseña embebida y un generador pseudoaleatorio inseguro, se interpretan "
        "en este informe a la luz de esa taxonomía."
    )

    # ------------------------------------------------------------------
    # HERRAMIENTAS DE INGENIERÍA
    # ------------------------------------------------------------------
    h1("HERRAMIENTAS DE INGENIERÍA")
    h2("Marcos de trabajo y estándares adoptados")
    p(
        "El equipo no documentó la adopción formal de Scrum, Kanban ni otro marco ágil, por lo que este "
        "informe no atribuye uno. Lo que sí puede verificarse es la secuencia de trabajo: definición de "
        "requisitos, construcción, verificación automatizada, análisis estático, corrección y nueva "
        "verificación. Esa secuencia se corresponde con un ciclo de aseguramiento iterativo y con los "
        "estándares que se resumen a continuación."
    )
    p(
        "[COMPLETAR POR EL EQUIPO: marco de trabajo y cronograma efectivamente utilizados (sprints, "
        "iteraciones o fases), con fechas y responsables; si se usó Scrum u otro marco, adjuntar la "
        "evidencia de su aplicación]"
    )
    table_caption("Estándares y marcos de referencia utilizados en la auditoría.")
    add_table(
        ["Estándar o marco", "Aporte al proyecto", "Dónde se aplica en este informe"],
        [
            ["ISO/IEC 25010:2011", "Modelo de calidad de producto en ocho características.", "Estructura de la evaluación no funcional y de las conclusiones."],
            ["ISTQB CTFL 4.0", "Vocabulario y niveles de prueba.", "Diseño de la matriz de casos y de la pirámide de pruebas."],
            ["IEEE 829-2008", "Contenido de la documentación de pruebas.", "Estructura de la matriz y de los registros de ejecución."],
            ["WCAG 2.1 nivel AA", "Criterios de accesibilidad verificables.", "Revisión con axe-core y registro del defecto de contraste."],
            ["WAI-ARIA 1.2", "Uso correcto de roles y preferencia por HTML nativo.", "Hallazgos S6819, S1082 y S6847."],
            ["OWASP Top 10:2021", "Taxonomía de riesgos de seguridad.", "Interpretación de S2068 y S2245."],
            ["Sonar way", "Perfil de reglas y puerta de calidad.", "Análisis estático antes y después."],
        ],
        [3.4, 6.4, 5.2],
        font_size=8.0,
    )

    h2("Selección de herramientas de software")
    p(
        "Las herramientas se eligieron por tres criterios: gratuidad para uso académico, disponibilidad "
        "en el entorno local del equipo y capacidad de producir evidencia exportable. La tabla siguiente "
        "registra las versiones realmente utilizadas, tomadas de los archivos de configuración del "
        "repositorio y de los reportes de ejecución."
    )
    table_caption("Herramientas de ingeniería y versiones utilizadas.")
    add_table(
        ["Herramienta", "Versión", "Propósito", "Evidencia generada"],
        [
            ["SonarQube Community Build", "26.10.0.133078", "Análisis estático de backend y frontend.", "Capturas reales, JSON de API y tabla comparativa."],
            ["SonarScanner CLI", "8.3.1.16491", "Envío de métricas al servidor SonarQube.", "Registros de escaneo sin credenciales."],
            ["OpenJDK", "21", "Requisito de SonarQube y del scanner.", "Entorno de ejecución."],
            ["Node.js / npm", "Entorno del proyecto", "Ejecución de backend, frontend y pruebas.", "Salidas de consola."],
            ["NestJS", "11.1.6", "Framework de la API REST.", "Código fuente y pruebas de integración."],
            ["React", "18", "Interfaz de usuario de página única.", "Componentes y pruebas de interfaz."],
            ["Vite", "6.0.7", "Servidor de desarrollo y compilación del frontend.", "Frontend compilado en el puerto 4173."],
            ["Prisma ORM", "6.16.2", "Modelo y acceso a datos PostgreSQL.", "Esquema y migraciones."],
            ["PostgreSQL", "18", "Motor de base de datos relacional.", "Base de pruebas labtrack_test."],
            ["Vitest", "3.2.4", "Pruebas unitarias e integración; cobertura V8.", "101 pruebas y reportes de cobertura."],
            ["Supertest", "7.1.4", "Pruebas HTTP de la API NestJS.", "Casos de integración del backend."],
            ["React Testing Library", "Incluida en el proyecto", "Pruebas de componentes sobre jsdom.", "Casos de interfaz del frontend."],
            ["Selenium WebDriver", "4.27 (^4.27.0)", "Automatización E2E en Chrome headless.", "JUnit XML y capturas de pantalla."],
            ["Apache JMeter", "5.6.3", "Carga (50 usuarios) y estrés (150 usuarios).", "Dashboard HTML, summary.json y gráficos."],
            ["axe-core", "4.10.2", "Revisión automatizada de accesibilidad.", "JSON con violaciones por página."],
            ["python-docx / python-pptx", "1.2.0 / versión instalada", "Generación de informe y presentación.", "DOCX, PPTX y PDF exportados."],
        ],
        [3.4, 2.6, 5.2, 4.4],
        font_size=7.8,
        center_cols={1},
    )
    p(
        "El hardware utilizado no quedó registrado en los artefactos del proyecto. Dado que las cifras "
        "de rendimiento dependen del equipo, se deja constancia expresa de esa omisión."
    )
    p(
        "[COMPLETAR POR EL EQUIPO: características del hardware de las pruebas de rendimiento (CPU, "
        "memoria, disco, sistema operativo y versión de Chrome) para permitir la reproducción exacta]"
    )

    h2("Lista de requerimientos")
    p(
        "Los requerimientos funcionales se derivaron de las historias declaradas y se contrastaron con "
        "el código. La columna de estado distingue lo implementado, lo implementado parcialmente y lo "
        "declarado sin sustento; esa distinción es la que evita presentar como terminado lo que solo "
        "está enunciado."
    )
    table_caption("Requerimientos funcionales y estado verificado en el repositorio.")
    add_table(
        ["ID", "Requerimiento funcional", "Estado verificado", "Evidencia principal"],
        [
            ["RQ-01", "Autenticación con código y contraseña, emisión de JWT y cierre de sesión.", "Implementado", "auth.controller.ts, auth.service.ts, LoginPage.tsx"],
            ["RQ-02", "Bloqueo temporal tras tres intentos fallidos.", "Implementado (5 min; el criterio declara 15)", "auth.service.ts, auth.spec.ts"],
            ["RQ-03", "Catálogo de equipos con filtros por categoría y estado.", "Implementado", "equipment.service.ts, CatalogPage.tsx"],
            ["RQ-04", "Registro de reservas con validación de horario, duración y solapamiento.", "Implementado", "reservations.service.ts, reservation-boundaries.extra.spec.ts"],
            ["RQ-05", "Aprobación y rechazo administrativo con motivo obligatorio.", "Implementado", "admin.service.ts, AdminPendingPage.tsx"],
            ["RQ-06", "Devolución con penalización automática por retraso.", "Implementado (sin plazo persistido)", "admin.service.ts, AdminReturnsPage.tsx"],
            ["RQ-07", "Bitácora de auditoría de eventos del sistema.", "Implementado", "AuditLog en schema.prisma, audit service"],
            ["RQ-08", "Panel administrativo con contadores de gestión.", "Parcial (sin gráficos ni tasa de puntualidad)", "admin.service.ts, AdminPendingPage.tsx"],
            ["RQ-09", "Carnet digital QR del estudiante.", "Declarado, sin evidencia", "Sin archivos ni pruebas"],
            ["RQ-10", "CRUD administrativo de equipos con fotos y QR.", "Parcial (solo consultas)", "equipment.controller.ts"],
            ["RQ-11", "Levantamiento de sanciones con justificación.", "Declarado, sin evidencia", "Sin endpoint ni interfaz"],
            ["RQ-12", "Acta oficial de préstamo en PDF.", "Declarado, sin evidencia", "Sin generador ni ruta"],
        ],
        [1.3, 6.4, 4.2, 5.1],
        font_size=7.8,
        center_cols={0},
    )
    table_caption("Requerimientos no funcionales y criterio de aceptación.")
    add_table(
        ["ID", "Requerimiento no funcional", "Criterio de aceptación", "Resultado"],
        [
            ["RNF-01", "Seguridad de credenciales y sesiones.", "Contraseñas con bcrypt; sin secretos embebidos; JWT firmado.", "Cumple tras refactorización"],
            ["RNF-02", "Eficiencia de desempeño bajo carga.", "p95 < 3000 ms y error ≤ 1 % con 50 usuarios.", "Cumple: 48 ms y 0.00 %"],
            ["RNF-03", "Eficiencia de desempeño bajo estrés.", "p95 < 5000 ms y error ≤ 5 % con 150 usuarios.", "Cumple: 151 ms y 0.00 %"],
            ["RNF-04", "Mantenibilidad estática.", "Cero bugs, vulnerabilidades y code smells.", "Cumple: 0/0/0"],
            ["RNF-05", "Cobertura de pruebas.", "≥ 80 % de sentencias en backend y frontend.", "Cumple: 95.71 % y 90.26 %"],
            ["RNF-06", "Accesibilidad.", "WCAG 2.1 AA sin violaciones automatizadas.", "Parcial: contraste pendiente"],
            ["RNF-07", "Compatibilidad de navegadores.", "Ejecución E2E en Chrome, Firefox y Edge.", "Parcial: solo Chrome"],
            ["RNF-08", "Trazabilidad y auditoría.", "Registro de eventos críticos con actor y detalle.", "Cumple: modelo AuditLog"],
        ],
        [1.3, 4.8, 6.2, 4.7],
        font_size=7.8,
        center_cols={0},
    )

    # ------------------------------------------------------------------
    # GENERACIÓN DE SOLUCIONES
    # ------------------------------------------------------------------
    h1("GENERACIÓN DE SOLUCIONES")
    h2("Visión general de la solución")
    p(
        "La solución se organiza en tres capas. La capa de presentación es una SPA en React con Vite y "
        "Tailwind CSS, que consume la API mediante fetch y protege las rutas con un componente de "
        "guarda. La capa de negocio es una API REST NestJS con módulos de autenticación, equipos, "
        "reservas y administración; aplica validación de DTO, guards de rol y transacciones Prisma para "
        "las operaciones críticas. La capa de datos es PostgreSQL, modelada con Prisma y sembrada con "
        "usuarios y equipos de demostración."
    )
    add_figure(
        ASSETS / "arquitectura.png",
        15.0,
        "Arquitectura de tres capas de LabTrack y ubicación de las herramientas de calidad.",
    )

    h2("Diagrama de clases")
    p(
        "El repositorio no contiene un diagrama de clases formal. Para no inventar relaciones que el "
        "código no declara, se deja el espacio correspondiente y se documenta el modelo de datos real "
        "en el apartado siguiente."
    )
    p(
        "[COMPLETAR POR EL EQUIPO: diagrama de clases UML con servicios, controladores, DTO y entidades "
        "del dominio, generado a partir de backend/src y frontend/src]"
    )

    h2("Modelo y diagrama de base de datos")
    p(
        "El modelo real se compone de cuatro entidades. User almacena credenciales, rol, estado y control "
        "de bloqueo. Equipment registra el inventario con código único, categoría, estado y ubicación. "
        "Reservation relaciona usuario y equipo, guarda fecha, hora de inicio y fin, estado, motivo de "
        "rechazo, marcas de revisión y devolución, y la bandera de penalización. AuditLog conserva los "
        "eventos con actor, detalle, dirección IP y fecha."
    )
    table_caption("Modelo de datos implementado en backend/prisma/schema.prisma.")
    add_table(
        ["Entidad", "Campos principales", "Relaciones e índices"],
        [
            ["User", "id, code (único), fullName, email, passwordHash, role, status, failedAttempts, lockedUntil, createdAt", "1:N con Reservation y AuditLog; índice por role"],
            ["Equipment", "id, name, inventoryCode (único), category, status, description, location, createdAt", "1:N con Reservation; índices por category y status"],
            ["Reservation", "id, userId, equipmentId, date, startTime, endTime, status, rejectionReason, reviewedBy, reviewedAt, returnedAt, penaltyApplied", "N:1 con User y Equipment; índices por usuario/fecha, equipo/fecha y estado"],
            ["AuditLog", "id, event, actorCode, detail, ipAddress, userId, createdAt", "N:1 opcional con User; índices por evento y fecha"],
        ],
        [1.9, 8.3, 4.8],
        font_size=7.8,
    )
    p(
        "El diagrama entidad-relación no existe como archivo en el repositorio; el esquema Prisma es la "
        "fuente de verdad y permite generarlo."
    )
    p(
        "[COMPLETAR POR EL EQUIPO: diagrama entidad-relación exportado desde Prisma o desde una "
        "herramienta de modelado, con cardinalidades y claves]"
    )

    h2("Script de base de datos")
    p(
        "El proyecto utiliza Prisma Migrate, de modo que el DDL se genera a partir del esquema. Se "
        "reproduce el esquema real, que actúa como script de definición de la base de datos."
    )
    code_block(
        """enum Role { STUDENT ADMIN }
enum UserStatus { ACTIVE PENALIZED }
enum EquipmentStatus { AVAILABLE BORROWED }
enum ReservationStatus { PENDING APPROVED REJECTED RETURNED }

model User {
  id             String   @id @default(cuid())
  code           String   @unique
  fullName       String
  email          String   @default("")
  passwordHash   String
  role           Role     @default(STUDENT)
  status         UserStatus @default(ACTIVE)
  failedAttempts Int      @default(0)
  lockedUntil    DateTime?
  createdAt      DateTime @default(now())
  reservations   Reservation[]
  auditLogs      AuditLog[]
  @@index([role])
}

model Equipment {
  id            String  @id @default(cuid())
  name          String
  inventoryCode String  @unique
  category      String
  status        EquipmentStatus @default(AVAILABLE)
  description   String  @default("")
  location      String  @default("Laboratorio principal")
  createdAt     DateTime @default(now())
  reservations  Reservation[]
  @@index([category]) @@index([status])
}

model Reservation {
  id              String @id @default(cuid())
  userId          String
  equipmentId     String
  date            DateTime @db.Date
  startTime       String @db.VarChar(5)
  endTime         String @db.VarChar(5)
  status          ReservationStatus @default(PENDING)
  rejectionReason String? @db.VarChar(300)
  reviewedBy      String?
  reviewedAt      DateTime?
  returnedAt      DateTime?
  penaltyApplied  Boolean @default(false)
  createdAt       DateTime @default(now())
  user            User @relation(fields: [userId], references: [id])
  equipment       Equipment @relation(fields: [equipmentId], references: [id])
  @@index([userId, date]) @@index([equipmentId, date]) @@index([status])
}

model AuditLog {
  id        String @id @default(cuid())
  event     String
  actorCode String @default("")
  detail    String @default("") @db.VarChar(300)
  ipAddress String @default("") @db.VarChar(60)
  userId    String?
  createdAt DateTime @default(now())
  user      User? @relation(fields: [userId], references: [id])
  @@index([event]) @@index([createdAt])
}"""
    )

    h2("Diagrama de paquetes y modelo arquitectónico")
    p(
        "El backend se organiza por módulos de dominio (auth, equipment, reservations, admin) con "
        "controlador, servicio y DTO por módulo, más un servicio transversal de auditoría y un módulo "
        "Prisma. El frontend se organiza por páginas, componentes reutilizables, contextos de "
        "autenticación y notificaciones, y una capa de acceso a API. La figura de arquitectura resume "
        "esa distribución y la posición de las herramientas de calidad respecto de cada capa."
    )
    p(
        "[COMPLETAR POR EL EQUIPO: diagrama de paquetes formal con dependencias permitidas y prohibidas "
        "entre módulos, si el curso exige el artefacto en notación UML]"
    )

    h2("Capturas del software en implementación")
    p(
        "Las siguientes capturas provienen de la corrida final de Selenium sobre el sistema en "
        "funcionamiento. No son maquetas: muestran el navegador real recorriendo el catálogo, el "
        "registro de una reserva, la aprobación administrativa y la devolución con penalización."
    )
    shots = [
        ("03-catalogo-estudiante.png", "Catálogo de equipos visible para una sesión de estudiante."),
        ("05-reserva-registrada.png", "Reserva registrada en estado pendiente desde el catálogo."),
        ("06-solicitud-aprobada.png", "Solicitud aprobada por el administrador."),
        ("07-devolucion-penalizada.png", "Devolución tardía con penalización aplicada."),
    ]
    for name, caption in shots:
        add_figure(
            BASE / "evidencias-pruebas" / "selenium" / "corrida-3-final-aprobada" / "screenshots" / name,
            14.6,
            caption,
        )

    # ------------------------------------------------------------------
    # METODOLOGÍA DE DESARROLLO
    # ------------------------------------------------------------------
    h1("METODOLOGÍA DE DESARROLLO")
    p(
        "La metodología efectivamente aplicada fue un ciclo de aseguramiento iterativo: se definieron "
        "los requisitos y sus criterios, se construyó la solución, se ejecutaron las pruebas en varios "
        "niveles, se midió el código con análisis estático, se corrigieron los hallazgos y se volvió a "
        "verificar. El ciclo no terminó con «todo verde»: terminó con un balance honesto de lo logrado y "
        "de lo que quedó pendiente. Esta sección documenta cada una de esas etapas con sus artefactos."
    )
    add_figure(
        ASSETS / "piramide-pruebas.png",
        13.8,
        "Pirámide de pruebas aplicada: base de pruebas unitarias, interfaz y cima de flujos E2E.",
    )

    h2("Definición de los requerimientos del negocio")
    p(
        "Los requerimientos del negocio se expresaron como historias de usuario con criterios de "
        "aceptación verificables. La fuente de alcance es el documento de historias implementadas del "
        "equipo, que declara doce historias. La verificación se hizo archivo por archivo en backend/src, "
        "frontend/src, backend/test y frontend/src/test, sin inferir funcionalidad a partir de la "
        "declaración. El resultado es una tabla de trazabilidad con tres estados posibles: implementada "
        "con pruebas, implementada sin pruebas y declarada sin evidencia verificable."
    )

    h2("Historias de usuario, criterios de aceptación y trazabilidad")
    p(
        "La tabla siguiente resume las doce historias declaradas, sus criterios de aceptación y la "
        "evidencia encontrada. Las cinco primeras cuentan con código y pruebas automatizadas; las siete "
        "restantes carecen de sustento suficiente y se reportan como brechas."
    )
    table_caption("Historias de usuario declaradas, criterios de aceptación y estado de evidencia.")
    add_table(
        ["HU", "Descripción", "Criterios de aceptación (resumen)", "Evidencia en el repositorio", "Estado"],
        [
            ["HU-01", "Autenticación segura y control de bloqueos", "Código N0 + 8 dígitos; mensaje exacto de credenciales inválidas; bloqueo de 15 minutos tras 3 fallos.", "auth.controller.ts, auth.service.ts, login.dto.ts, LoginPage.tsx, AuthContext.tsx; auth.spec.ts, LoginPage.test.tsx", "Implementada con pruebas; bloqueo configurado en 5 min y sin regex estricta"],
            ["HU-02", "Catálogo y filtrado de equipos", "Filtros exactos Cómputo, Electrónica y Redes; mensaje exacto cuando no hay equipos.", "equipment.controller.ts, equipment.service.ts, CatalogPage.tsx; equipment.spec.ts, CatalogPage.test.tsx", "Implementada con pruebas"],
            ["HU-03", "Reserva de equipos y reglas críticas", "Sin cruces del mismo equipo; una reserva activa por estudiante en el mismo horario; bloquear estudiantes penalizados.", "reservations.controller.ts, reservations.service.ts, NewReservationPage.tsx; reservations.spec.ts, reservation-boundaries.extra.spec.ts", "Implementada con pruebas"],
            ["HU-04", "Gestión administrativa de solicitudes", "Aprobar o rechazar; el rechazo exige motivo.", "admin.controller.ts, admin.service.ts, AdminPendingPage.tsx; admin.spec.ts, AdminPendingPage.test.tsx", "Implementada con pruebas"],
            ["HU-05", "Devolución y penalización automática", "La devolución deja el equipo disponible; el retraso cambia al alumno a penalizado durante 7 días.", "admin.controller.ts, admin.service.ts, AdminReturnsPage.tsx; admin.spec.ts, AdminReturnsPage.test.tsx", "Implementada con pruebas; no se persiste el plazo de 7 días"],
            ["HU-06", "Carnet digital QR del estudiante", "Credencial digital escaneable en ventanilla.", "Sin componente, ruta, modelo ni prueba identificable.", "Declarada, sin evidencia"],
            ["HU-07", "Gestión integral de equipos (CRUD admin)", "Registrar equipos con fotos, especificaciones, ubicación y QR.", "Solo consultas de catálogo; sin CRUD, carga de imágenes ni QR.", "Declarada, sin evidencia completa"],
            ["HU-08", "Gestión y levantamiento de penalizaciones", "Panel admin para levantar sanciones con justificación.", "Aplicación automática de la sanción; sin operación de levantamiento.", "Declarada, sin evidencia completa"],
            ["HU-11", "Dashboard y métricas de uso", "Gráficos de inventario y tasa de puntualidad.", "Tarjetas numéricas; sin gráficos ni tasa de puntualidad.", "Evidencia parcial"],
            ["HU-13", "Administración y creación de usuarios", "Crear alumnos o admins; resetear claves; desbloquear cuentas.", "Sin módulo, endpoints ni pruebas de administración de usuarios.", "Declarada, sin evidencia"],
            ["HU-14", "Escaneo rápido con cámara o lector QR", "Despacho y devolución sin teclear.", "Sin integración de cámara, lector ni pantalla de escaneo.", "Declarada, sin evidencia"],
            ["HU-15", "Acta oficial de préstamo en PDF", "Descargar constancia formal con cláusula de responsabilidad.", "Sin generador, endpoint, botón ni plantilla PDF.", "Declarada, sin evidencia"],
        ],
        [1.1, 3.0, 4.2, 4.5, 2.6],
        font_size=7.2,
        center_cols={0},
    )
    callout(
        "Hallazgo de trazabilidad: 7 de 12 historias sin evidencia verificable",
        "La verificación del repositorio confirma cinco historias con código y pruebas (HU-01 a HU-05). "
        "HU-06, HU-07, HU-08, HU-11, HU-13, HU-14 y HU-15 no cuentan con evidencia suficiente para "
        "afirmar que estén implementadas: no existen rutas, componentes, modelos o pruebas que las "
        "sostengan, o solo existe una parte mínima. Además, HU-01 y HU-05 incumplen dos criterios "
        "declarados (duración del bloqueo y persistencia del plazo de sanción). El informe no convierte "
        "esas brechas en funcionalidades: las registra y las prioriza en el backlog.",
        fill="FEF2F2",
        border="B91C1C",
    )
    p(
        "La distinción importa porque el sistema puede aprobar sus pruebas y, aun así, no cubrir el "
        "alcance prometido. Un informe que solo reportara «7 de 7 flujos E2E aprobados» sería "
        "técnicamente cierto y estratégicamente engañoso: esos siete flujos cubren cinco historias, no "
        "doce. La conclusión del trabajo incorpora esa diferencia."
    )

    h2("Casos de prueba")
    p(
        "La matriz completa se organiza por historia y contiene 66 casos funcionales: 61 aprobados para "
        "las cinco historias verificables y 5 casos de borde sugeridos por inteligencia artificial con "
        "validación humana pendiente. Cada caso declara origen, prioridad, precondición, pasos, "
        "resultado esperado, nivel de ejecución y evidencia. La matriz completa se reproduce en el "
        "Anexo A y su versión editable vive en docs/matriz-pruebas.md."
    )
    table_caption("Distribución de casos de prueba por historia de usuario y origen.")
    add_table(
        ["Historia", "Casos", "Diseño del equipo", "Sugeridos por IA", "Aprobados", "Pendientes de validación"],
        [
            ["HU-01 Autenticación", "12", "8", "4", "12", "0"],
            ["HU-02 Catálogo", "11", "7", "4", "11", "0"],
            ["HU-03 Reserva", "18", "11", "7", "18", "0"],
            ["HU-04 Aprobación y rechazo", "12", "7", "5", "12", "0"],
            ["HU-05 Devolución y penalización", "8", "5", "3", "8", "0"],
            ["Casos IA complementarios", "5", "0", "5", "0", "5"],
            ["TOTAL", "66", "38", "28", "61", "5"],
        ],
        [5.4, 1.8, 2.4, 2.4, 1.8, 2.6],
        font_size=8.0,
        center_cols={1, 2, 3, 4, 5},
    )
    p(
        "Los casos sugeridos por IA no se presentan como validados. Se listan con su comportamiento "
        "esperado y se mantienen en estado pendiente hasta que una persona los revise, los ejecute y "
        "firme el resultado."
    )
    table_caption("Casos de borde sugeridos por IA con validación humana pendiente.")
    add_table(
        ["ID", "Caso sugerido", "Prio.", "Nivel", "Comportamiento esperado", "Validación"],
        [
            ["IA-01", "Reservas contiguas del mismo equipo (10:00–12:00 tras 08:00–10:00)", "P1", "API + UI", "Debe aceptarse: los extremos contiguos no se solapan.", "PENDIENTE"],
            ["IA-02", "Solicitud con duración cero (inicio igual a fin)", "P1", "UI", "Debe bloquearse en el cliente antes de enviar la petición.", "PENDIENTE"],
            ["IA-03", "Límites exactos del horario (07:00 y 22:00)", "P2", "API + UI", "07:00 y 22:00 se admiten; 06:59 y 22:01 se rechazan con 400.", "PENDIENTE"],
            ["IA-04", "Código de estudiante con espacios y minúsculas", "P2", "API", "El backend aplica trim y mayúsculas y permite el acceso legítimo.", "PENDIENTE"],
            ["IA-05", "Reintento con token JWT expirado", "P1", "UI + E2E", "El cliente limpia el almacenamiento y redirige a /login sin pantalla en blanco.", "PENDIENTE"],
        ],
        [1.2, 4.6, 1.1, 1.8, 5.3, 1.8],
        font_size=7.6,
        center_cols={0, 2, 5},
    )

    h2("Definición de las reglas del negocio")
    p(
        "Las reglas de negocio se extrajeron del código y de los criterios de aceptación, no de una "
        "suposición sobre cómo debería funcionar el sistema. Cada regla indica su implementación real y "
        "la prueba que la respalda."
    )
    table_caption("Reglas de negocio implementadas y su verificación.")
    add_table(
        ["ID", "Regla de negocio", "Implementación", "Verificación"],
        [
            ["RN-01", "El laboratorio atiende de 07:00 a 22:00.", "Constantes LAB_OPEN y LAB_CLOSE en reservations.service.ts.", "reservation-boundaries.extra.spec.ts"],
            ["RN-02", "Una reserva no puede exceder 4 horas continuas.", "MAX_RESERVATION_HOURS = 4.", "Pruebas de límites del backend"],
            ["RN-03", "La hora de inicio debe ser anterior a la de fin y la fecha no puede ser pasada.", "Validación en createReservation.", "reservations.spec.ts"],
            ["RN-04", "Un equipo no puede tener dos reservas solapadas.", "Consulta de solapamiento dentro de una transacción.", "reservations.spec.ts"],
            ["RN-05", "Un estudiante no puede tener dos reservas activas en el mismo horario.", "Segunda consulta de solapamiento por usuario.", "reservations.spec.ts"],
            ["RN-06", "Solo se reservan equipos disponibles.", "Verificación de estado AVAILABLE.", "equipment y reservations specs"],
            ["RN-07", "Las cuentas administrativas no registran reservas.", "Rechazo explícito por rol.", "reservations.spec.ts"],
            ["RN-08", "Tres intentos fallidos bloquean la cuenta.", "MAX_FAILED_ATTEMPTS = 3; LOCKOUT_MINUTES = 5.", "auth.spec.ts"],
            ["RN-09", "El rechazo exige un motivo de al menos 5 caracteres.", "Validación en admin.service.ts.", "admin.spec.ts"],
            ["RN-10", "Solo se aprueban o rechazan reservas pendientes; solo se devuelven reservas aprobadas.", "Verificación de estado previo.", "admin.spec.ts"],
            ["RN-11", "La devolución tardía aplica penalización y cambia el estado del alumno a penalizado.", "markReturned con comparación de hora y actualización de usuario.", "admin.spec.ts"],
            ["RN-12", "Toda transición relevante se registra en la bitácora.", "AuditLog con evento, actor y detalle.", "Pruebas de administración"],
        ],
        [1.2, 6.1, 5.0, 3.4],
        font_size=7.6,
        center_cols={0},
    )

    h2("Implementación del proyecto")
    p(
        "El proyecto se ejecuta en tres procesos: la API NestJS en el puerto 3000, el frontend de "
        "desarrollo en el puerto 5173 y el frontend compilado en el puerto 4173 para las pruebas E2E. La "
        "base de pruebas se denomina labtrack_test y se siembra con usuarios y equipos deterministas. "
        "Las credenciales de demostración están documentadas en el anexo de reproducción y no se "
        "reproducen en el cuerpo del informe."
    )
    p(
        "La compilación exige que TypeScript no emita errores (tsc --noEmit) tanto en backend como en "
        "frontend. Esa condición se usó como criterio de cierre de cada refactorización, junto con la "
        "ejecución completa de la suite de pruebas."
    )

    h2("Pruebas unitarias y de integración")
    p(
        "Las pruebas unitarias y de integración se ejecutan con Vitest 3.2.4. En el backend se apoya en "
        "Supertest para atacar la API contra una base de pruebas; en el frontend se apoya en React "
        "Testing Library y jsdom para verificar componentes y contextos. La suite pasó de 93 a 101 casos "
        "aprobados: cuatro nuevos en backend y cuatro en frontend, dedicados a límites de reserva, "
        "ventanas contiguas, duración cero y bordes del horario de atención."
    )
    table_caption("Evolución de las pruebas unitarias y de la cobertura de código.")
    add_table(
        ["Suite", "Antes", "Después", "Archivos", "Cobertura de sentencias", "Cobertura de ramas", "Estado"],
        [
            ["Backend (NestJS + Supertest)", "49", "53", "5", "95.71 %", "85.00 %", "100 % aprobadas"],
            ["Frontend (React + RTL)", "44", "48", "13", "90.26 %", "81.69 %", "100 % aprobadas"],
            ["TOTAL", "93", "101", "18", "91.50 % global", "82.50 % global", "Código de salida 0"],
        ],
        [4.6, 1.5, 1.7, 1.6, 2.9, 2.7, 2.6],
        font_size=7.8,
        center_cols={1, 2, 3, 4, 5, 6},
    )
    p(
        "Además de las pruebas verdes, la suite incluye casos con it.fails que registran la falla "
        "esperada de funciones defectuosas simuladas en mocks locales. Esa técnica demuestra que las "
        "pruebas tienen poder de detección: una prueba que nunca puede fallar no aporta información "
        "sobre la calidad del sistema."
    )
    add_figure(
        BASE / "evidencias-pruebas" / "capturas" / "02-backend-despues.png",
        14.4,
        "Salida de Vitest del backend después de incorporar los casos de límites (53 pruebas aprobadas).",
    )
    add_figure(
        BASE / "evidencias-pruebas" / "capturas" / "04-frontend-despues.png",
        14.4,
        "Salida de Vitest del frontend después de incorporar los casos de límites (48 pruebas aprobadas).",
    )
    add_figure(
        BASE / "evidencias-pruebas" / "capturas" / "05-defectos-simulados-fallan.png",
        14.4,
        "Ejecución contra mocks defectuosos: la suite detecta el fallo y termina con código de salida 1.",
    )
    add_figure(
        BASE / "evidencias-pruebas" / "unitarias" / "cobertura" / "backend-report.png",
        14.4,
        "Reporte HTML de cobertura del backend generado con Istanbul/V8.",
    )
    add_figure(
        ASSETS / "cobertura.png",
        13.6,
        "Comparativa de cobertura entre backend y frontend medida con Istanbul/V8.",
    )

    h2("Pruebas funcionales con Selenium")
    p(
        "La suite de extremo a extremo se implementó con Selenium WebDriver 4.27 sobre Google Chrome "
        "headless y consta de siete pruebas en frontend/e2e/critical-flows.e2e.test.ts. El entorno de "
        "ejecución fue el backend en localhost:3000 con la base labtrack_test y el frontend compilado en "
        "localhost:4173. Los resultados se documentan en JUnit XML y en capturas del navegador."
    )
    table_caption("Corridas reales de la suite Selenium y resultado obtenido.")
    add_table(
        ["Corrida", "Selectores utilizados", "Resultado", "Detalle"],
        [
            ["1", "[role=\"status\"] y [role=\"dialog\"] sobre el código ya refactorizado", "4 aprobadas / 3 fallidas", "Fallan HU-03, HU-04 y HU-05: el aviso y el diálogo ya no exponen el atributo role explícito."],
            ["2", "Ajuste intermedio de los localizadores", "Uso interno de diagnóstico", "Se identificó que el comportamiento del sistema era correcto y el fallo estaba en la prueba."],
            ["3 (final)", "output, [role=\"status\"] y dialog, [role=\"dialog\"]", "7 aprobadas / 0 fallidas", "JUnit XML sin fallos y capturas 01 a 08 de la corrida final."],
        ],
        [2.0, 5.6, 3.0, 4.4],
        font_size=7.8,
        center_cols={0, 2},
    )
    callout(
        "Regresión detectada: la refactorización S6819 rompió los selectores E2E",
        "La corrección de la regla S6819 sustituyó <div role=\"status\"> por <output> y <div "
        "role=\"dialog\"> por <dialog>. Ambos elementos ya poseen el rol de forma implícita, de modo que "
        "la accesibilidad mejoró y el comportamiento funcional se mantuvo. Sin embargo, los selectores "
        "CSS [role=\"status\"] y [role=\"dialog\"] solo encuentran el atributo escrito, no el rol "
        "implícito; por eso las pruebas dejaron de localizar el aviso y el cuadro de confirmación. El "
        "sistema creaba la reserva correctamente: lo que fallaba era la prueba. La corrección se aplicó "
        "solo en frontend/e2e/helpers/e2e.ts y frontend/e2e/critical-flows.e2e.test.ts, sin tocar el "
        "código de producción. La lección se incorporó al backlog: toda refactorización de accesibilidad "
        "obliga a reejecutar la suite E2E.",
        fill="FEF2F2",
        border="B91C1C",
    )
    p(
        "Este hallazgo es el resultado más valioso de la automatización. Una corrida de 7 de 7 desde el "
        "primer intento habría ocultado una dependencia frágil entre las pruebas y el marcado. La "
        "regresión quedó documentada con su causa, su corrección y su evidencia, y alimenta una regla de "
        "proceso para el futuro."
    )
    table_caption("Flujos críticos automatizados con Selenium y evidencia asociada.")
    add_table(
        ["Flujo automatizado", "HU", "Comportamiento validado", "Captura"],
        [
            ["Rechazo de credenciales inválidas", "HU-01", "Alerta con el texto exacto «Credenciales inválidas.»", "01-login-credenciales-invalidas.png"],
            ["Bloqueo tras tres intentos fallidos", "HU-01", "Alerta de bloqueo temporal y respuesta 423", "02-login-cuenta-bloqueada.png"],
            ["Inicio de sesión y catálogo", "HU-01, HU-02", "Ingreso exitoso y renderizado de tarjetas", "03-catalogo-estudiante.png"],
            ["Filtro por categoría Electrónica", "HU-02", "Filtrado reactivo del catálogo", "04-filtro-electronica.png"],
            ["Registro de reserva", "HU-03", "Reserva pendiente y redirección a Mis Reservas", "05-reserva-registrada.png"],
            ["Aprobación administrativa", "HU-04", "Cambio a APPROVED y equipo a BORROWED", "06-solicitud-aprobada.png"],
            ["Devolución tardía con penalización", "HU-05", "Detección del retraso y sanción al alumno", "07-devolucion-penalizada.png"],
        ],
        [4.8, 2.0, 5.4, 4.2],
        font_size=7.8,
        center_cols={1},
    )
    add_figure(
        BASE / "evidencias-pruebas" / "capturas" / "10-selenium-corrida-1-regresion.png",
        6.6,
        "Consola de la primera corrida: 4 pruebas aprobadas y 3 fallidas por la regresión de selectores.",
    )
    add_figure(
        BASE / "evidencias-pruebas" / "capturas" / "11-selenium-corrida-3-final.png",
        6.6,
        "Consola de la corrida final: 7 pruebas aprobadas y 0 fallidas.",
    )
    p(
        "Herramientas de gestión de pruebas. Testomat.io, TestLink y Katalon Studio no se ejecutaron: "
        "requieren cuenta o servidor y no formaban parte del entorno disponible. Para no fabricar "
        "evidencias, se entrega la plantilla de importación y el archivo "
        "docs/evidencias-pruebas/testomatio-import.csv, listos para cargar los casos cuando la cátedra "
        "habilite el acceso. Esta limitación se declara también en la conclusión y en las "
        "recomendaciones."
    )

    h2("Documentación de la refactorización")
    p(
        "La refactorización no fue una colección de parches: fue una estrategia para eliminar deuda "
        "técnica sin alterar el comportamiento observable. Cada cambio se acompañó de la suite completa "
        "de pruebas y de un nuevo análisis estático. La tabla siguiente resume las diez reglas que "
        "concentraban las 44 incidencias iniciales."
    )
    table_caption("Hallazgos de SonarQube que concentraban la deuda técnica inicial.")
    add_table(
        ["Regla", "Hallazgo", "Tipo y severidad", "Cantidad", "Archivos principales", "Corrección aplicada"],
        [
            ["S3358", "Ternarios anidados", "Code smell · Major", "8", "admin.service.ts y páginas React", "Sustitución por if/else y variables auxiliares"],
            ["S6759", "Props sin Readonly", "Code smell · Major", "14", "Componentes, contextos y páginas", "Readonly<Props> en componentes funcionales"],
            ["S7718", "Parámetro catch fuera de convención", "Code smell · Major", "11", "Once archivos de páginas", "Renombrado a error_"],
            ["S6819", "Rol ARIA en lugar de HTML nativo", "Code smell · Major", "5", "ui.tsx, ToastContext, CatalogPage", "Migración a dialog y output"],
            ["S2068", "Credencial embebida", "Vulnerabilidad · Blocker", "1", "LoginPage.tsx", "Variables de entorno VITE_DEMO_*"],
            ["S2245", "PRNG inseguro", "Vulnerabilidad · Critical", "1", "ToastContext.tsx", "Secuencia monotónica en memoria"],
            ["S1082", "Clic sin soporte de teclado", "Bug · Minor", "1", "ui.tsx", "Botón de cierre accesible y dialog nativo"],
            ["S6847", "Evento interactivo en elemento no interactivo", "Code smell · Major", "1", "ui.tsx", "Aislamiento modal semántico con dialog"],
            ["S9379", "autoFocus en campo de entrada", "Code smell · Minor", "1", "LoginPage.tsx", "Eliminación del atributo"],
            ["S3776", "Complejidad cognitiva alta", "Code smell · Critical", "1", "AdminHistoryPage.tsx", "Extracción de bloques de renderizado"],
        ],
        [1.4, 3.6, 3.0, 1.3, 3.2, 3.9],
        font_size=7.4,
        center_cols={0, 3},
    )
    p(
        "Se reproducen tres ejemplos representativos. El primero corresponde al bug de accesibilidad: un "
        "contenedor con manejador de clic y sin interacción de teclado. El segundo ilustra la "
        "vulnerabilidad más grave: una contraseña en texto plano. El tercero muestra la corrección que, "
        "sin proponérselo, rompió los selectores de la suite E2E."
    )
    code_block(
        """// ANTES (S1082 + S6847)
<div onClick={onClose} role="presentation">
  <div role="dialog" aria-modal="true" aria-label={title}
       onClick={(event) => event.stopPropagation()}>
    {/* contenido */}
  </div>
</div>

// DESPUÉS (HTML nativo y cierre accesible)
<div className="fixed inset-0 z-[90] flex items-end justify-center p-4">
  <button type="button" aria-label="Cerrar modal" onClick={onClose}
          className="absolute inset-0 bg-navy-950/50 backdrop-blur-sm" />
  <dialog open aria-modal="true" aria-label={title}
          className="relative m-0 w-full max-w-lg rounded-2xl border-0 bg-white p-0 shadow-lift">
    {/* contenido */}
  </dialog>
</div>"""
    )
    code_block(
        """// ANTES (S2068): credencial en texto plano
password: 'Estudiante2026!'

// DESPUÉS: variable de entorno
password: import.meta.env.VITE_DEMO_STUDENT_PASSWORD ?? ''"""
    )
    code_block(
        """// ANTES (S6819): rol ARIA sobre un div
<div role="status" aria-live="polite">{toast.message}</div>
<div role="dialog" aria-modal="true" aria-label={title}>

// DESPUÉS: elementos nativos con el mismo rol implícito
<output aria-live="polite">{toast.message}</output>
<dialog open aria-modal="true" aria-label={title}>

// Consecuencia en las pruebas: [role="status"] deja de encontrarlo.
// Corrección en el test, no en producción:
const toast = await driver.findElement(By.css('output, [role="status"]'));
const modal = await driver.findElement(By.css('dialog, [role="dialog"]'));"""
    )
    p(
        "El backlog de refactorización registra catorce ítems técnicos y nueve brechas funcionales. Los "
        "dos últimos ítems son los más relevantes para este informe: la regresión de Selenium provocada "
        "por S6819 y el defecto de contraste detectado por axe-core, que permanece abierto."
    )
    table_caption("Backlog de refactorización con estado y evidencia de cierre.")
    add_table(
        ["ID", "Hallazgo", "Prioridad", "Solución", "Estado", "Evidencia"],
        [
            ["RF-01", "Ternarios anidados (S3358)", "Alta", "if/else explícitos", "Completado", "8 incidencias cerradas"],
            ["RF-02", "Modal inaccesible (S1082, S6819, S6847)", "Alta", "dialog y botón de cierre", "Completado", "Bug cerrado; confiabilidad A"],
            ["RF-03", "PRNG inseguro (S2245)", "Alta", "Secuencia monotónica", "Completado", "Vulnerabilidad cerrada"],
            ["RF-04", "Credencial embebida (S2068)", "Alta", "Variables VITE_DEMO_*", "Completado", "Seguridad A"],
            ["RF-05", "Props sin Readonly (S6759)", "Media", "Readonly<Props>", "Completado", "14 incidencias cerradas"],
            ["RF-06", "Catch fuera de convención (S7718)", "Media", "Renombrado a error_", "Completado", "11 incidencias cerradas"],
            ["RF-07", "autoFocus (S9379)", "Media", "Eliminación del atributo", "Completado", "Incidencia cerrada"],
            ["RF-08", "Complejidad cognitiva (S3776)", "Media", "Extracción de bloques", "Completado", "Complejidad < 15"],
            ["RF-09", "Cobertura no reportada al scanner", "Media", "Rutas LCOV en la configuración", "Completado", "Reportes V8 archivados"],
            ["RF-10", "Casos límite sin pruebas", "Media", "Suites de límites", "Completado", "93 → 101 pruebas"],
            ["RF-11", "Credenciales demo en el seed", "Baja", "Aislamiento del entorno", "Aceptado", "Riesgo documentado"],
            ["RF-12", "E2E solo en Chrome", "Baja", "Parametrizar Firefox y Edge", "Planificado", "Sprint siguiente"],
            ["RF-13", "Regresión de selectores E2E por S6819", "Alta", "Selectores que aceptan rol implícito en helpers y flujos críticos", "Resuelto", "Corrida final 7/7 y JUnit XML"],
            ["RF-14", "Contraste de color insuficiente (axe-core)", "Alta", "Ajustar paleta y revalidar con axe", "Pendiente", "1 elemento en login y 17 en catálogo"],
        ],
        [1.1, 3.3, 1.55, 3.3, 1.75, 3.8],
        font_size=7.2,
        center_cols={0, 2, 4},
    )
    p(
        "La regresión RF-13 se resolvió modificando únicamente los archivos de prueba "
        "(frontend/e2e/helpers/e2e.ts y critical-flows.e2e.test.ts). El código de producción no se "
        "alteró, precisamente porque su comportamiento era correcto. El defecto RF-14 no se corrigió: "
        "se documenta con su impacto, sus elementos afectados y la acción requerida."
    )

    h2("Análisis estático: SonarQube antes y después")
    p(
        "El análisis se ejecutó con SonarQube Community Build 26.10.0.133078 sobre PostgreSQL 18, con "
        "SonarScanner CLI 8.3.1.16491 y OpenJDK 21. Se aplicó el perfil Sonar way para TypeScript y "
        "JavaScript sobre backend/src y frontend/src, excluyendo node_modules, dist, coverage, "
        "declaraciones y pruebas. El estado ANTES se reproduce en una copia de trabajo porque el "
        "repositorio no conserva una versión previa; el estado DESPUÉS se analiza sobre el código actual."
    )
    callout(
        "Transparencia metodológica sobre el estado ANTES y la cobertura",
        "1. El código ANTES es REPRODUCIDO, no histórico. El repositorio tiene un único commit; para "
        "comparar en el mismo servidor y con los mismos parámetros se reinyectaron los 44 defectos "
        "documentados en una copia de trabajo. Las capturas del ANTES provienen de esa ejecución real, "
        "no de un panel reconstruido.\n"
        "2. La cobertura reportada por SonarQube fue 0.0 % porque no se inyectaron las rutas LCOV en esa "
        "ejecución puntual. Es un defecto de configuración, registrado como RF-09. La cobertura real, "
        "medida con Istanbul/V8, es 95.71 % en backend y 90.26 % en frontend.\n"
        "3. La puerta de calidad se aprobó en ambos estados porque evalúa código nuevo. Aprobar la puerta "
        "no equivale a tener cero deuda: el valor está en la comparación de incidencias totales.",
        fill="FEF3C7",
        border="B45309",
    )
    table_caption("Comparación de métricas de SonarQube antes y después de la refactorización.")
    add_table(
        ["Métrica", "Antes", "Después", "Variación", "Lectura"],
        [
            ["Bugs", "1", "0", "−1 (−100 %)", "Se elimina la falla de accesibilidad con teclado"],
            ["Vulnerabilidades", "2", "0", "−2 (−100 %)", "Sin credenciales expuestas ni PRNG predecible"],
            ["Code smells", "41", "0", "−41 (−100 %)", "Código más legible y desacoplado"],
            ["Confiabilidad", "B", "A", "B → A", "Sin fallos potenciales detectados"],
            ["Seguridad", "C", "A", "C → A", "Cierre de S2068 y S2245"],
            ["Mantenibilidad", "A", "A", "Se mantiene", "Deuda técnica de 1 h 37 min a 0"],
            ["Líneas de código (NCLOC)", "4 145", "4 120", "−25", "Eliminación de redundancias"],
            ["Duplicación", "0.7 %", "0.7 %", "Sin cambio", "Muy por debajo del umbral del 3 %"],
            ["Quality Gate", "Aprobada", "Aprobada", "Sin cambio", "Evalúa código nuevo en ambos casos"],
        ],
        [3.8, 2.2, 2.2, 2.8, 4.0],
        font_size=7.8,
        center_cols={1, 2, 3},
    )
    p(
        "El total de 44 incidencias coincide con la línea base histórica registrada en "
        "docs/sonar-baseline.json (2 bugs, 2 vulnerabilidades y 40 smells). La distribución por tipo "
        "difiere levemente (1 bug y 41 smells) porque la versión 26.10 del motor reclasificó uno de los "
        "elementos interactivos y computó la regla de complejidad cognitiva S3776. La diferencia se "
        "explica por la evolución del motor, no por una manipulación de los datos."
    )
    add_figure(
        BASE / "evidencias-sonarqube" / "antes" / "capturas-reales" / "01-dashboard.png",
        14.4,
        "SonarQube, estado ANTES reproducido: 44 incidencias, confiabilidad B y seguridad C.",
    )
    add_figure(
        BASE / "evidencias-sonarqube" / "antes" / "capturas-reales" / "02-issues-todas.png",
        14.4,
        "Listado completo de las 44 incidencias del estado ANTES con regla y archivo.",
    )
    add_figure(
        BASE / "evidencias-sonarqube" / "despues" / "capturas-reales" / "01-dashboard.png",
        14.4,
        "SonarQube, estado DESPUÉS: 0 incidencias y calificaciones A/A/A.",
    )
    add_figure(
        BASE / "evidencias-sonarqube" / "despues" / "capturas-reales" / "02-issues-todas.png",
        14.4,
        "Bandeja de incidencias vacía después de la refactorización.",
    )
    add_figure(
        BASE / "evidencias-sonarqube" / "comparacion" / "real" / "grafico-comparativo-real.png",
        13.6,
        "Comparativo real de incidencias de SonarQube antes y después.",
    )
    table_caption("Matriz consolidada de los pilares de calidad de SonarQube.")
    add_table(
        ["Pilar", "Antes", "Después", "Condición exigida", "Resultado"],
        [
            ["Confiabilidad", "B (1 bug)", "A (0 bugs)", "A sin bugs abiertos", "Conforme"],
            ["Seguridad", "C (2 vulnerabilidades)", "A (0 vulnerabilidades)", "A sin vulnerabilidades", "Conforme"],
            ["Mantenibilidad", "A (41 smells)", "A (0 smells)", "A con deuda < 5 %", "Conforme"],
            ["Hotspots de seguridad", "0", "0", "100 % revisados", "Conforme"],
            ["Duplicación", "0.7 %", "0.7 %", "< 3.0 %", "Conforme"],
            ["Quality Gate", "Aprobada", "Aprobada", "Sonar way", "Conforme"],
        ],
        [3.8, 3.6, 3.6, 3.4, 2.4],
        font_size=7.8,
        center_cols={1, 2, 3, 4},
    )

    h2("Pruebas de carga y estrés con Apache JMeter")
    p(
        "Se ejecutaron dos escenarios con Apache JMeter 5.6.3. La prueba de carga simuló 50 usuarios "
        "concurrentes durante 60 segundos con rampa de 10 segundos; la prueba de estrés elevó la "
        "concurrencia a 150 usuarios durante 90 segundos con rampa de 15 segundos. El guion recorrió "
        "inicio de sesión con JWT, catálogo completo, filtro por categoría, estadísticas y consultas de "
        "reservas del estudiante."
    )
    p(
        "El percentil 95 se adoptó como métrica principal porque el promedio oculta la latencia de cola. "
        "Un sistema puede promediar 30 ms y, al mismo tiempo, castigar a un grupo pequeño de usuarios "
        "con esperas de varios segundos. El p95 responde a la pregunta relevante para el usuario: "
        "¿cuánto espera el 95 % de las peticiones?"
    )
    table_caption("Resumen global de la prueba de carga con 50 usuarios concurrentes.")
    add_table(
        ["Métrica", "Resultado", "Umbral", "Estado"],
        [
            ["Muestras procesadas", "79 424", "Volumen informativo", "Informativo"],
            ["Tasa de error", "0.00 %", "≤ 1.0 %", "Cumple"],
            ["Throughput", "1 334.07 req/s", "Alta capacidad", "Excelente"],
            ["Promedio", "34.4 ms", "Informativo", "Informativo"],
            ["Mediana (p50)", "34.0 ms", "≤ 3000 ms", "Cumple"],
            ["p90", "42.0 ms", "≤ 3000 ms", "Cumple"],
            ["p95", "48.0 ms", "≤ 3000 ms", "Cumple"],
            ["p99", "89.0 ms", "Informativo", "Informativo"],
            ["Máximo", "230.0 ms", "≤ 3000 ms", "Cumple"],
            ["Desviación estándar", "11.8 ms", "Informativo", "Alta estabilidad"],
        ],
        [4.6, 3.8, 3.8, 3.8],
        font_size=7.8,
        center_cols={1, 2, 3},
    )
    table_caption("Detalle por transacción de la prueba de carga.")
    add_table(
        ["Transacción", "Muestras", "Promedio", "p95", "p99", "Throughput", "Error"],
        [
            ["GET /api/equipment", "19 865", "34.5 ms", "49.0 ms", "89.0 ms", "333.67 req/s", "0.00 %"],
            ["GET /api/equipment/stats", "19 836", "34.4 ms", "48.0 ms", "88.0 ms", "333.18 req/s", "0.00 %"],
            ["GET /api/equipment?category=Cómputo", "19 848", "34.3 ms", "48.0 ms", "88.5 ms", "333.38 req/s", "0.00 %"],
            ["GET /api/reservations/me", "19 825", "34.3 ms", "48.0 ms", "88.0 ms", "333.00 req/s", "0.00 %"],
            ["POST /api/auth/login", "50", "113.5 ms", "160.8 ms", "204.5 ms", "0.84 req/s", "0.00 %"],
            ["TOTAL", "79 424", "34.4 ms", "48.0 ms", "89.0 ms", "1 334.07 req/s", "0.00 %"],
        ],
        [5.4, 1.6, 1.7, 1.6, 1.6, 2.2, 1.4],
        font_size=7.2,
        center_cols={1, 2, 3, 4, 5, 6},
    )
    add_figure(
        BASE / "evidencias-jmeter" / "carga" / "captura-dashboard-resumen.png",
        14.0,
        "Dashboard de JMeter de la prueba de carga: 0.00 % de error sobre 79 424 peticiones.",
    )
    add_figure(
        BASE / "assets" / "jmeter" / "carga-response-time.png",
        14.0,
        "Tiempo de respuesta (promedio y percentil 95) durante la prueba de carga con 50 usuarios.",
    )
    add_figure(
        BASE / "assets" / "jmeter" / "carga-percentiles.png",
        12.6,
        "Distribución de percentiles de la prueba de carga con 50 usuarios.",
    )
    add_figure(
        BASE / "assets" / "jmeter" / "carga-throughput.png",
        14.0,
        "Throughput y usuarios concurrentes durante la prueba de carga con 50 usuarios.",
    )

    table_caption("Resumen global de la prueba de estrés con 150 usuarios concurrentes.")
    add_table(
        ["Métrica", "Resultado", "Umbral", "Estado"],
        [
            ["Muestras procesadas", "113 600", "Carga extrema", "Informativo"],
            ["Tasa de error", "0.00 %", "≤ 5.0 %", "Cumple"],
            ["Throughput", "1 265.24 req/s", "Alta concurrencia", "Excelente"],
            ["Promedio", "108.9 ms", "Informativo", "Informativo"],
            ["Mediana (p50)", "101.0 ms", "≤ 5000 ms", "Cumple"],
            ["p90", "132.0 ms", "≤ 5000 ms", "Cumple"],
            ["p95", "151.0 ms", "≤ 5000 ms", "Cumple"],
            ["p99", "381.0 ms", "Informativo", "Informativo"],
            ["Máximo", "1 072.0 ms", "≤ 5000 ms", "Cumple"],
            ["Desviación estándar", "47.9 ms", "Informativo", "Comportamiento predecible"],
        ],
        [4.6, 3.8, 3.8, 3.8],
        font_size=7.8,
        center_cols={1, 2, 3},
    )
    table_caption("Detalle por transacción de la prueba de estrés.")
    add_table(
        ["Transacción", "Muestras", "Promedio", "p95", "p99", "Throughput", "Error"],
        [
            ["GET /api/equipment", "28 421", "108.9 ms", "152.0 ms", "380.0 ms", "316.55 req/s", "0.00 %"],
            ["GET /api/equipment/stats", "28 345", "108.3 ms", "150.0 ms", "374.0 ms", "315.70 req/s", "0.00 %"],
            ["GET /api/equipment?category=Cómputo", "28 377", "108.4 ms", "150.0 ms", "380.2 ms", "316.06 req/s", "0.00 %"],
            ["GET /api/reservations/me", "28 307", "108.1 ms", "150.0 ms", "369.0 ms", "315.28 req/s", "0.00 %"],
            ["POST /api/auth/login", "150", "461.2 ms", "963.3 ms", "1 033.4 ms", "1.67 req/s", "0.00 %"],
            ["TOTAL", "113 600", "108.9 ms", "151.0 ms", "381.0 ms", "1 265.24 req/s", "0.00 %"],
        ],
        [5.4, 1.6, 1.7, 1.6, 1.7, 2.2, 1.4],
        font_size=7.2,
        center_cols={1, 2, 3, 4, 5, 6},
    )
    add_figure(
        BASE / "evidencias-jmeter" / "estres" / "captura-dashboard-resumen.png",
        14.0,
        "Dashboard de JMeter de la prueba de estrés: 0.00 % de error sobre 113 600 peticiones.",
    )
    add_figure(
        BASE / "assets" / "jmeter" / "estres-response-time.png",
        14.0,
        "Tiempo de respuesta (promedio y percentil 95) durante la prueba de estrés con 150 usuarios.",
    )
    add_figure(
        BASE / "assets" / "jmeter" / "estres-percentiles.png",
        12.6,
        "Distribución de percentiles de la prueba de estrés con 150 usuarios.",
    )
    add_figure(
        BASE / "assets" / "jmeter" / "estres-throughput.png",
        14.0,
        "Throughput y usuarios concurrentes durante la prueba de estrés con 150 usuarios.",
    )
    p(
        "El incremento de latencia entre carga y estrés es coherente con el tripling de concurrencia: el "
        "p95 pasó de 48 ms a 151 ms y el máximo de 230 ms a 1 072 ms, sin errores ni caídas. La "
        "transacción de inicio de sesión es la más costosa porque implica bcrypt, un diseño deliberado "
        "para dificultar ataques de fuerza bruta. El sistema no colapsó en ninguno de los dos escenarios."
    )

    h2("Accesibilidad e inclusión")
    p(
        "La revisión se hizo con axe-core 4.10.2, el mismo motor de la extensión, sobre el frontend "
        "compilado en localhost:4173. Se evaluaron las páginas de inicio de sesión y catálogo con las "
        "reglas WCAG 2.0 y 2.1 de niveles A y AA. WAVE no se ejecutó, por lo que no se reportan sus "
        "resultados ni se simulan sus paneles."
    )
    table_caption("Resultados de la revisión automatizada de accesibilidad con axe-core.")
    add_table(
        ["Página", "Reglas aprobadas", "Violaciones", "Elementos afectados", "Revisión manual"],
        [
            ["Inicio de sesión", "19", "color-contrast (serious)", "1", "1"],
            ["Catálogo", "17", "color-contrast (serious)", "17", "0"],
        ],
        [3.6, 3.2, 4.4, 2.6, 2.6],
        font_size=8.0,
        center_cols={1, 3, 4},
    )
    p(
        "El único tipo de violación detectado es el contraste de color. No aparecieron faltas de nombre "
        "accesible, de etiquetas de formulario, de orden de encabezados ni de atributos ARIA inválidos, "
        "lo que sugiere que la refactorización de diálogos y avisos cumplió su objetivo. El contraste, "
        "sin embargo, afecta la legibilidad para personas con baja visión y debe corregirse antes de "
        "afirmar conformidad con WCAG 2.1 AA."
    )
    p(
        "El defecto se registra como RF-14 en el backlog, con prioridad alta y estado pendiente. La "
        "corrección exige ajustar la paleta de los elementos señalados y volver a ejecutar axe-core "
        "hasta obtener cero violaciones. También conviene complementar la revisión automática con pruebas "
        "de teclado y con al menos una sesión de prueba con usuario real, porque axe-core solo cubre "
        "parte de los criterios."
    )

    # ------------------------------------------------------------------
    # RECOMENDACIONES FINALES
    # ------------------------------------------------------------------
    h1("RECOMENDACIONES FINALES")
    h2("Conclusiones")
    p(
        "La auditoría permite afirmar que LabTrack es un sistema funcionalmente correcto en el alcance "
        "que puede verificarse, con un código limpio y un desempeño sólido bajo concurrencia. No permite "
        "afirmar que esté completo respecto del alcance declarado ni que sea plenamente accesible. El "
        "veredicto honesto es «certificado con observaciones»: apto para operar en el alcance verificado, "
        "con brechas documentadas que deben cerrarse antes de una implantación institucional plena."
    )
    bullets(
        [
            "Corrección funcional verificada: los siete flujos críticos de las cinco historias con evidencia pasan de extremo a extremo en un navegador real. La primera corrida había aprobado cuatro; las tres fallas restantes se explicaron por una regresión de selectores y se corrigieron en el código de pruebas.",
            "Salud del código: SonarQube pasó de 44 incidencias (1 bug, 2 vulnerabilidades, 41 code smells; confiabilidad B, seguridad C) a cero incidencias con calificaciones A/A/A. La deuda técnica estimada se redujo de 1 h 37 min a cero.",
            "Cobertura de pruebas: 101 casos aprobados, con 95.71 % de sentencias cubiertas en backend y 90.26 % en frontend. Las pruebas de límites añadidas elevan la confianza sobre las reglas de reserva.",
            "Desempeño: 0.00 % de errores en carga y estrés, con p95 de 48 ms y 151 ms. El sistema soporta el triple de la concurrencia nominal sin degradación catastrófica.",
            "Accesibilidad: la revisión automatizada solo encontró fallas de contraste, lo que confirma la mejora semántica de la refactorización, pero impide declarar conformidad WCAG 2.1 AA.",
            "Alcance: siete de las doce historias declaradas carecen de evidencia verificable. El sistema no debe presentarse como completo hasta que esas brechas se implementen y se prueben.",
        ]
    )
    h2("Recomendaciones")
    bullets(
        [
            "Corregir el contraste de color señalado por axe-core y volver a ejecutar la revisión hasta obtener cero violaciones; complementarla con navegación por teclado y una prueba con usuario.",
            "Implementar las historias HU-06, HU-07, HU-08, HU-11, HU-13, HU-14 y HU-15, o bien reducir formalmente el alcance del proyecto para que coincida con lo verificable.",
            "Ajustar HU-01 y HU-05 a sus criterios declarados: validación estricta del código y persistencia del plazo de sanción de siete días.",
            "Incorporar la suite completa y el escaneo de SonarQube en integración continua, con bloqueo de la fusión cuando falle la puerta de calidad o alguna prueba.",
            "Inyectar las rutas LCOV en el scanner para que SonarQube refleje la cobertura real y no un 0.0 % engañoso.",
            "Reejecutar la suite E2E después de cualquier refactorización de accesibilidad o de marcado; la regresión S6819 demostró que un cambio correcto puede romper las pruebas.",
            "Validar formalmente los cinco casos sugeridos por IA antes de incorporarlos a la suite oficial, dejando registro del revisor y del resultado.",
            "Ejecutar Testomat.io o TestLink y WAVE cuando el entorno lo permita, y archivar las capturas correspondientes para completar la evidencia de herramientas.",
            "Parametrizar Selenium para Firefox y Edge y ampliar las pruebas de rendimiento con escenarios de red lenta y base de datos degradada.",
        ]
    )
    p(
        "El valor del trabajo no reside solo en las cifras favorables, sino en la trazabilidad de lo que "
        "se hizo y en la honestidad sobre lo que falta. Un informe que declare cero defectos y doce "
        "historias completas sería más agradable de leer y menos útil para tomar decisiones."
    )

    # ------------------------------------------------------------------
    # REFERENCIAS
    # ------------------------------------------------------------------
    h1("REFERENCIAS O BIBLIOGRAFÍA")
    references = [
        "American Psychological Association. (2020). Publication manual of the American Psychological Association (7th ed.). https://doi.org/10.1037/0000165-000",
        "Apache Software Foundation. (2024). Apache JMeter user's manual (Version 5.6.3). https://jmeter.apache.org/usermanual/",
        "Deque Systems. (2024). axe-core: Accessibility engine for automated web UI testing. https://github.com/dequelabs/axe-core",
        "IEEE. (2008). IEEE standard for software and system test documentation (IEEE Std 829-2008). https://doi.org/10.1109/IEEESTD.2008.4578383",
        "International Organization for Standardization. (2011). Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models (ISO/IEC 25010:2011). https://www.iso.org/standard/35733.html",
        "International Software Testing Qualifications Board. (2023). Certified tester foundation level syllabus (Version 4.0). https://www.istqb.org/",
        "NestJS. (2024). NestJS documentation: A progressive Node.js framework. https://docs.nestjs.com/",
        "OWASP Foundation. (2021). OWASP Top 10:2021. https://owasp.org/Top10/",
        "Prisma. (2024). Prisma ORM documentation. https://www.prisma.io/docs",
        "React. (2024). React documentation. https://react.dev/",
        "Selenium Project. (2024). Selenium WebDriver documentation. https://www.selenium.dev/documentation/",
        "SonarSource. (2024). SonarQube documentation. https://docs.sonarsource.com/sonarqube/",
        "Testomat.io. (2024). Testomat.io documentation. https://testomat.io/",
        "Vitest. (2024). Vitest documentation. https://vitest.dev/",
        "World Wide Web Consortium. (2018). Web Content Accessibility Guidelines (WCAG) 2.1. https://www.w3.org/TR/WCAG21/",
        "World Wide Web Consortium. (2023). Accessible Rich Internet Applications (WAI-ARIA) 1.2. https://www.w3.org/TR/wai-aria-1.2/",
    ]
    for ref in references:
        par = doc.add_paragraph()
        pf = par.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.left_indent = Cm(1.27)
        pf.first_line_indent = Cm(-1.27)
        pf.space_after = Pt(6)
        pf.line_spacing = 1.5
        run = par.add_run(ref)
        style_run(run, size=10)

    # ------------------------------------------------------------------
    # ANEXOS
    # ------------------------------------------------------------------
    def anexo_heading(title):
        COUNTERS["Anexo"] += 1
        letter = chr(64 + COUNTERS["Anexo"])
        doc.add_page_break()
        par = doc.add_paragraph(style="AnexoTitle")
        par.paragraph_format.space_before = Pt(0)
        par.paragraph_format.space_after = Pt(10)
        par.paragraph_format.line_spacing = 1.0
        par.paragraph_format.keep_with_next = True
        run = par.add_run("Anexo ")
        style_run(run, size=14, bold=True, color=NAVY)
        add_seq(par, "Anexo", letter, "ALPHABETIC")
        run = par.add_run(f". {title}")
        style_run(run, size=14, bold=True, color=NAVY)

    h1("ANEXOS – RECURSOS")
    p(
        "Los anexos reúnen la matriz completa de casos, el registro del uso de agentes de inteligencia "
        "artificial, el índice de artefactos y la guía de reproducción. Se incluyen como evidencia "
        "auditable y como material de consulta para el equipo."
    )

    anexo_heading("Matriz completa de casos de prueba y trazabilidad")
    p(
        "La matriz se organiza por historia de usuario. Cada fila indica el identificador del caso, su "
        "origen (equipo o IA), la prioridad, el resultado esperado, la evidencia automatizada y el "
        "estado. La versión editable, con precondiciones y pasos detallados, está en "
        "docs/matriz-pruebas.md."
    )
    for hu_name, cases in parse_matrix().items():
        h3(hu_name)
        rows = []
        for case in cases:
            rows.append(
                [
                    case.get("ID", ""),
                    case.get("Caso de Prueba", case.get("Caso de prueba", "")),
                    case.get("Origen", ""),
                    case.get("Prio.", ""),
                    case.get("Resultado Esperado", case.get("Resultado esperado", "")),
                    case.get("Nivel · Evidencia", ""),
                    case.get("Estado", ""),
                ]
            )
        if rows:
            add_table(
                ["ID", "Caso de prueba", "Origen", "Pri.", "Resultado esperado", "Nivel y evidencia", "Estado"],
                rows,
                [0.95, 3.05, 1.18, 0.92, 4.12, 3.43, 1.35],
                font_size=6.8,
                header_size=7.2,
                center_cols={0, 2, 3, 6},
            )

    anexo_heading("Uso de agentes de IA: prompts y skills")
    p(
        "El trabajo se desarrolló con un equipo de agentes de inteligencia artificial coordinado desde "
        "la línea de comandos. Un agente líder dividió el trabajo en tareas con alcances de archivos que "
        "no se solapan; cada agente trabajó en su propia copia aislada del repositorio y el líder revisó "
        "el reporte y el diff antes de integrar. Este anexo deja constancia de qué se le pidió a cada "
        "agente y de las intervenciones humanas que fueron necesarias. El documento completo está en "
        "docs/prompts-y-skills-agentes.md."
    )
    h3("Skills y mecanismos utilizados")
    table_caption("Skills y mecanismos empleados durante el desarrollo asistido.")
    add_table(
        ["Skill o mecanismo", "Quién la usó", "Para qué"],
        [
            ["multi-cli-team (invocada con /team)", "Agente líder", "Orquestar el equipo: planificación, ejecución, recolección y fusión mediante team.ps1."],
            ["Herramientas MCP de Playwright", "Agente líder", "Capturas reales de SonarQube y de los reportes de JMeter; ejecución de axe-core."],
            ["sonar-scanner, SonarQube, JMeter, Vitest, Selenium", "Líder y agentes", "Análisis estático, carga y estrés, pruebas unitarias y flujos E2E."],
        ],
        [5.6, 3.4, 6.0],
        font_size=7.8,
    )
    p(
        "Los agentes de trabajo podían cargar sus propias skills y servidores MCP; no se registró cuáles "
        "usó cada uno, por lo que no se afirma nada al respecto."
    )
    h3("Reparto de agentes")
    table_caption("Tareas asignadas a cada agente y alcance de archivos.")
    add_table(
        ["Tarea", "Agente", "Alcance", "Resultado"],
        [
            ["sonar-antes-despues", "opencode", "docs/evidencias-sonarqube/**", "Reprodujo el ANTES y generó JSON y paneles de apoyo; la ejecución real la completó el líder."],
            ["pruebas-unitarias", "copilot", "docs/evidencias-pruebas/**, pruebas .extra", "Ejecutó y documentó las pruebas; agregó dos archivos con ocho casos nuevos."],
            ["jmeter-carga-estres", "agy", "jmeter/**, docs/evidencias-jmeter/**", "Dejó plan de estrés y análisis; la ejecución real la hizo el líder tras instalar JMeter."],
            ["informe-presentacion-backlog", "agy", "docs/*.py, *.docx, *.pdf, *.pptx, *.md, assets/**", "Informe, presentación y backlog del primer intento."],
            ["historias-usuario", "copilot", "docs/generate_*.py, *.md, *.docx, *.pdf, *.pptx", "Verificó cada historia contra el código y actualizó los entregables."],
        ],
        [3.6, 1.8, 4.6, 5.0],
        font_size=7.4,
        center_cols={1},
    )
    p(
        "Decisión del usuario: la redacción del informe y de la presentación no debía realizarla el "
        "agente líder; se asignó a agy y luego la verificación de historias a copilot. El agente dsh no "
        "estaba instalado y no se utilizó."
    )
    h3("Prompts enviados a cada agente")
    p(
        "Los prompts se transcriben tal como figuran en el registro del equipo. En el primer envío se "
        "pedían además evidencias con capturas del ANTES y del DESPUÉS."
    )
    prompts = [
        (
            "sonar-antes-despues — agente opencode",
            "Objetivo: evidencias visuales de SonarQube del ANTES y DESPUÉS de LabTrack. No existe "
            "versión ANTES en Git (solo un commit). Crear en docs/evidencias-sonarqube/antes/src/ una "
            "copia de backend/src y frontend/src y reintroducir los defectos de sonar-baseline.json "
            "(S3358, S1082, S6819, S6847, S2068, S2245, S6759 y el resto), con los mismos archivos y "
            "líneas. Todo lo reconstruido debe etiquetarse como ANTES REPRODUCIDO, nunca como captura "
            "histórica. No modificar backend/src ni frontend/src reales. Para el DESPUÉS analizar el "
            "código actual con projectKey labtrack-despues. Guardar capturas legibles de dashboard, "
            "bugs, vulnerabilidades, code smells, ratings, quality gate y listado de issues, además de "
            "JSON de la API, logs sin tokens, tabla comparativa y gráfico. (El registro del prompt está "
            "truncado en el documento fuente.)",
        ),
        (
            "pruebas-unitarias — agente copilot",
            "Contexto: backend NestJS con Vitest y frontend React con Vitest. Ejecutar las pruebas y la "
            "cobertura de ambos, guardar salidas y capturas. Documentar el estado antes y después de "
            "agregar casos. Agregar pruebas nuevas solo como archivos nuevos terminados en .extra, "
            "cubriendo casos límite. Incluir al menos dos pruebas que demuestren falla ante un defecto "
            "simulado en un mock local, sin editar backend/src ni frontend/src. Escribir la matriz de "
            "casos con pruebas unitarias, funcionales, referencia a JMeter y casos sugeridos por IA con "
            "validación pendiente. Agregar plantillas para Katalon y Testomat.io/TestLink y el CSV "
            "importable, sin inventar capturas de herramientas no ejecutadas. No hacer commit.",
        ),
        (
            "jmeter-carga-estres — agente agy",
            "Levantar el backend en un puerto local con base de pruebas y ejecutar una prueba de carga y "
            "una de estrés con JMeter. Si JMeter no está instalado, reportarlo y dejar los comandos "
            "exactos; no inventar resultados. Guardar .jtl crudos, reporte HTML, tablas de muestras, "
            "promedios, percentiles, throughput y porcentaje de error, gráficas y capturas del reporte. "
            "Escribir un análisis en español con contexto sobre carga, estrés y percentiles. No tocar "
            "backend/src ni frontend/src. Apagar el backend al terminar. No hacer commit.",
        ),
        (
            "informe-presentacion-backlog — agente agy",
            "Redactar el informe y la presentación usando solo cifras que salgan de los archivos de "
            "evidencia. Respetar los hechos: SonarQube 44 incidencias antes y 0 después, con el ANTES "
            "reproducido; cobertura de SonarQube en 0.0 % por falta de LCOV y cobertura real de Vitest "
            "de 95.71 % y 90.26 %; JMeter con 50 y 150 usuarios; pruebas unitarias de 93 a 101; Katalon "
            "y Testomat.io/TestLink no ejecutados; casos de IA con validación pendiente. Incrustar las "
            "capturas reales y no usar los paneles reconstruidos. Actualizar el backlog y la matriz. "
            "Ejecutar los generadores y verificar los productos. No hacer commit.",
        ),
        (
            "historias-usuario — agente copilot",
            "Para cada historia declarada, verificar en backend/src, frontend/src, backend/test y "
            "frontend/src/test si existe código y pruebas, y clasificarla como implementada con pruebas, "
            "implementada sin pruebas o declarada sin evidencia verificable. No afirmar implementación "
            "ni pruebas que no se encuentren. Crear la trazabilidad, actualizar el informe, la matriz, "
            "el backlog y la presentación sin superar las cinco diapositivas. Regenerar los entregables "
            "y verificar. No modificar backend/src, frontend/src ni docs/evidencias-*. No hacer commit.",
        ),
    ]
    for title, text in prompts:
        h3(title)
        p(text, size=10)

    p("Intervenciones del líder que los agentes no realizaron:", bold=True, after=3)
    bullets(
        [
            "Instaló y ejecutó SonarQube, sonar-scanner, JDK 21 y JMeter, herramientas que los agentes no tenían disponibles.",
            "Detectó y corrigió falsos positivos del ANTES y un escaneo del DESPUÉS contaminado por configuraciones de carpetas de trabajo.",
            "Ejecutó Selenium y encontró la regresión causada por la refactorización S6819.",
            "Ejecutó axe-core para la revisión de accesibilidad.",
            "Verificó que no se filtraran tokens al repositorio y resolvió el fallo de identidad de Git local.",
        ],
        size=10,
    )

    anexo_heading("Índice de artefactos y evidencias")
    p(
        "Todos los archivos citados están presentes en el repositorio y forman parte del inventario "
        "auditable. La columna de naturaleza distingue lo real, lo reproducido, lo planificado y lo no "
        "ejecutado."
    )
    table_caption("Artefactos, ubicación y naturaleza de la evidencia.")
    add_table(
        ["Artefacto", "Ubicación", "Naturaleza", "Contenido"],
        [
            ["Capturas SonarQube antes", "docs/evidencias-sonarqube/antes/capturas-reales/", "Real (estado reproducido)", "Siete capturas con 44 incidencias"],
            ["Capturas SonarQube después", "docs/evidencias-sonarqube/despues/capturas-reales/", "Real", "Siete capturas con 0 incidencias"],
            ["Comparativo SonarQube", "docs/evidencias-sonarqube/comparacion/real/", "Real", "Tabla y gráfico de evolución"],
            ["Código del ANTES", "docs/evidencias-sonarqube/antes/src/", "Reproducido", "Copia con los defectos reinyectados"],
            ["Salidas de pruebas", "docs/evidencias-pruebas/capturas/", "Real", "Consolas de Vitest y de Selenium"],
            ["Reportes de cobertura", "docs/evidencias-pruebas/unitarias/cobertura/", "Real", "Resúmenes y reporte HTML"],
            ["Selenium corrida 1", "docs/evidencias-pruebas/selenium/corrida-1-regresion-detectada/", "Real", "JUnit XML con 3 fallos y capturas"],
            ["Selenium corrida final", "docs/evidencias-pruebas/selenium/corrida-3-final-aprobada/", "Real", "JUnit XML sin fallos y capturas 01–08"],
            ["JMeter carga", "docs/evidencias-jmeter/carga/", "Real", "Dashboard, summary.json, tablas y gráficos"],
            ["JMeter estrés", "docs/evidencias-jmeter/estres/", "Real", "Dashboard, summary.json, tablas y gráficos"],
            ["Accesibilidad", "docs/evidencias-accesibilidad/axe-resultados.json", "Real", "Violaciones de contraste por página"],
            ["Plantilla Testomat.io", "docs/evidencias-pruebas/testomatio-import.csv", "Plantilla", "Importación de casos, no ejecutada"],
            ["Trazabilidad", "docs/trazabilidad-historias-usuario.md", "Documento", "Verificación de las doce historias"],
            ["Backlog", "docs/refactoring-backlog.md", "Documento", "Catorce ítems técnicos y nueve brechas"],
            ["Matriz de pruebas", "docs/matriz-pruebas.md", "Documento", "66 casos funcionales y 10 de rendimiento"],
        ],
        [4.0, 5.6, 3.0, 5.4],
        font_size=7.2,
    )

    anexo_heading("Guía de reproducción y credenciales de demostración")
    p(
        "Los siguientes comandos permiten reproducir las evaluaciones en una máquina con Node.js, Java "
        "y Python instalados. Las rutas son relativas a la raíz del repositorio."
    )
    code_block(
        """# 1. Base de datos y datos sembrados
cd backend
npm install
npm run db:setup

# 2. Pruebas unitarias y cobertura
npm run test:cov
cd ..\\frontend
npm install
npm run test:cov

# 3. Verificación de tipos
npx tsc --noEmit
cd ..\\backend
npx tsc --noEmit

# 4. Pruebas E2E con Selenium (backend en 3000, frontend en 4173)
cd ..\\frontend
npm run test:e2e

# 5. Carga y estrés con JMeter
cd ..\\jmeter
powershell -ExecutionPolicy Bypass -File .\\run-load-test.ps1
powershell -ExecutionPolicy Bypass -File .\\run-stress-test.ps1

# 6. Generación de figuras y entregables
cd ..\\docs
python make_figures.py
python generate_report.py
python generate_presentation.py"""
    )
    p(
        "Credenciales deterministas de demostración: estudiante con código 20240001 y administrador con "
        "código ADMIN01. Las contraseñas se obtienen del archivo de entorno o del seed de desarrollo y "
        "no se reproducen en este informe. Después de ejecutar pruebas E2E conviene restaurar la base "
        "con npm run db:reset en backend para recuperar el estado inicial."
    )

    # ------------------------------------------------------------------
    # NOTAS ACLARATORIAS
    # ------------------------------------------------------------------
    h1("NOTAS ACLARATORIAS")
    bullets(
        [
            "Formato: el informe parte de la plantilla institucional, conserva su portada con los logotipos, el encabezado y el pie, y aplica Arial 11, texto justificado, interlineado 1,5, papel A4 y citas en APA 7.",
            "Índices: el índice de contenido, el de tablas, el de figuras y el de anexos se generan con campos de Word a partir de los títulos y de la numeración SEQ. Si el documento se abre en un procesador que no actualiza campos, deben actualizarse manualmente con F9.",
            "Cifras: todas las cifras provienen de archivos del repositorio. No se estimaron ni se redondearon valores para mejorar la presentación.",
            "Estado ANTES: el código previo a la refactorización no existe en el historial de Git; fue reproducido con los defectos documentados. Las capturas corresponden a esa ejecución real y se identifican como estado reproducido.",
            "Evidencias no realizadas: Testomat.io, TestLink, Katalon Studio y WAVE no se ejecutaron. Se entregan plantillas y se declara la limitación en lugar de simular capturas.",
            "Casos de IA: los cinco casos sugeridos por inteligencia artificial permanecen con validación humana pendiente y no se contabilizan como aprobados.",
            "Historias de usuario: siete de las doce declaradas no tienen evidencia verificable. El informe las reporta como brechas y no como funcionalidades terminadas.",
            "Marcadores pendientes: los textos resaltados con la expresión «COMPLETAR POR EL EQUIPO» indican información que el equipo debe aportar. Se listan en docs/pendientes-del-equipo.md.",
            "Las referencias se limitan a documentación oficial y estándares públicos verificables; no se incluyeron fuentes que el equipo no hubiera consultado.",
        ],
        size=10,
    )

    doc.save(str(DOCX_PATH))
    print(f"DOCX generado: {DOCX_PATH}")
    print(f"Marcadores pendientes: {len(MARKERS)}")
    for marker in MARKERS:
        print("  -", marker)

    if "--no-pdf" not in sys.argv:
        export_pdf(DOCX_PATH, PDF_PATH)


# ---------------------------------------------------------------------------
# Matriz de pruebas y exportacion a PDF
# ---------------------------------------------------------------------------
def parse_matrix():
    text = (BASE / "matriz-pruebas.md").read_text(encoding="utf-8")
    sections: dict[str, list[dict[str, str]]] = {}
    headers = None
    current = None
    for line in text.splitlines():
        if line.startswith("### HU-"):
            current = line[4:].strip()
            sections[current] = []
            headers = None
            continue
        if line.startswith("## ") or line.startswith("### "):
            if not line.startswith("### HU-"):
                current = None
            continue
        if not line.strip().startswith("|") or current is None:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        if headers is None:
            headers = cells
        else:
            sections[current].append(dict(zip(headers, cells)))
    return sections


PS_EXPORT = r'''
$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $null
try {
    $doc = $word.Documents.Open("__DOCX__", $false, $false, $false)
    try { $doc.Fields.Update() | Out-Null } catch { Write-Output "FIELDS_WARN" }
    try {
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
    } catch { Write-Output "TOC_WARN" }
    try { $doc.Fields.Update() | Out-Null } catch { Write-Output "FIELDS_WARN2" }
    $doc.Repaginate()
    try {
        foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
    } catch { Write-Output "TOC_WARN2" }
    $doc.Save()
    $doc.ExportAsFixedFormat("__PDF__", 17)
    Write-Output "PDF_OK"
} finally {
    if ($doc) { $doc.Close([ref]0) }
    $word.Quit()
}
'''


def export_pdf(docx_path: Path, pdf_path: Path):
    script = PS_EXPORT.replace("__DOCX__", str(docx_path)).replace("__PDF__", str(pdf_path))
    with tempfile.TemporaryDirectory() as tmp:
        ps1 = Path(tmp) / "export.ps1"
        ps1.write_text(script, encoding="utf-8-sig")
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
                capture_output=True,
                text=True,
                timeout=600,
            )
            print((result.stdout or "").strip())
            if result.returncode != 0 or "PDF_OK" not in (result.stdout or ""):
                print("Aviso al exportar PDF:", (result.stderr or "").strip())
        except Exception as exc:  # pragma: no cover
            print("Aviso al exportar PDF:", exc)
            return

    try:
        import fitz

        pdf = fitz.open(str(pdf_path))
        print(f"PDF generado: {pdf_path} ({pdf.page_count} páginas)")
        text = "\n".join(page.get_text() for page in pdf)
        for needle in ("ÍNDICE DE TABLAS", "ÍNDICE DE FIGURAS", "ÍNDICE DE ANEXOS"):
            print(f"  {needle}: {'OK' if needle in text else 'REVISAR'}")
        pdf.close()
    except Exception as exc:  # pragma: no cover
        print("Verificación del PDF omitida:", exc)


if __name__ == "__main__":
    if not TEMPLATE.exists():
        raise SystemExit(f"No se encontró la plantilla: {TEMPLATE}")
    build_report()
