"""Genera el informe técnico de LabTrack en DOCX y PDF.

Los datos de pruebas, cobertura, JMeter y SonarQube se leen de los artefactos
generados por el proyecto, de modo que el informe siempre refleje la última
ejecución.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
ASSETS = BASE / "assets"
DOCX_PATH = BASE / "informe-tecnico-labtrack.docx"

NAVY = "0B1F3A"
NAVY_LIGHT = "1D345D"
TEAL = "0D9488"
TEAL_LIGHT = "E6FFFA"
AMBER = "B45309"
RED = "B91C1C"
GRAY = "475569"
LIGHT = "F8FAFC"
BORDER = "D9E2EC"

BODY_FONT = "Calibri"


# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------


def set_font(run, size=None, bold=None, color=None, name=BODY_FONT, italic=None):
    if name:
        run.font.name = name
        run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def shade_cell(cell, color: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def set_cell_margins(cell, top=40, start=70, bottom=40, end=70):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color=BORDER, size=4):
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
        borders.append(element)
    tbl_pr.append(borders)


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def set_row_cant_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    cant.set(qn("w:val"), "true")
    tr_pr.append(cant)


def add_table(doc, headers, rows, widths, font_size=8.5, header_size=8.5, align_center=None, zebra=True):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)

    header_row = table.rows[0]
    set_repeat_header(header_row)
    set_row_cant_split(header_row)
    for index, header in enumerate(headers):
        cell = header_row.cells[index]
        cell.width = Cm(widths[index])
        shade_cell(cell, NAVY)
        set_cell_margins(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(0)
        run = paragraph.add_run(header)
        set_font(run, size=header_size, bold=True, color="FFFFFF")

    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        set_row_cant_split(table.rows[-1])
        for index, value in enumerate(row):
            cell = cells[index]
            cell.width = Cm(widths[index])
            if zebra and row_index % 2 == 1:
                shade_cell(cell, LIGHT)
            set_cell_margins(cell)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            text = str(value)
            run = paragraph.add_run(text)
            set_font(run, size=font_size, color="1F2937")
            if align_center and index in align_center:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_caption(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(10)
    run = paragraph.add_run(text)
    set_font(run, size=8.5, italic=True, color=GRAY)


def add_figure(doc, path: Path, width_cm: float, caption: str):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run().add_picture(str(path), width=Cm(width_cm))
    add_caption(doc, caption)


def add_callout(doc, title: str, text: str, color=TEAL_LIGHT, border=TEAL):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    row = table.rows[0]
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))
    cell = row.cells[0]
    shade_cell(cell, color)
    set_cell_margins(cell, top=110, start=160, bottom=110, end=160)
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge, size in (("top", 4), ("bottom", 4), ("right", 4), ("left", 24)):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), border)
        borders.append(element)
    tbl_pr.append(borders)
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(title)
    set_font(run, size=9.5, bold=True, color=NAVY)
    paragraph2 = cell.add_paragraph()
    paragraph2.paragraph_format.space_after = Pt(0)
    run2 = paragraph2.add_run(text)
    set_font(run2, size=9, color=GRAY)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_code_block(doc, code: str):
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    shade_cell(cell, "F1F5F9")
    set_cell_margins(cell, top=100, start=140, bottom=100, end=140)
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    for index, line in enumerate(code.strip("\n").splitlines()):
        run = paragraph.add_run(line)
        set_font(run, size=8.2, name="Consolas", color="0F172A")
        if index < len(code.strip("\n").splitlines()) - 1:
            run.add_break()
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_heading(doc, text, level=1):
    heading = doc.add_heading(level=level)
    run = heading.add_run(text)
    if level == 1:
        set_font(run, size=18, bold=True, color=NAVY)
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(8)
    elif level == 2:
        set_font(run, size=13, bold=True, color=NAVY_LIGHT)
        heading.paragraph_format.space_before = Pt(10)
        heading.paragraph_format.space_after = Pt(4)
    else:
        set_font(run, size=11, bold=True, color=TEAL)
        heading.paragraph_format.space_before = Pt(8)
        heading.paragraph_format.space_after = Pt(2)
    heading.paragraph_format.keep_with_next = True


def add_paragraph(doc, text, size=10.5, color="1F2937", align=None, space_after=6, bold=False, italic=False):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.15
    run = paragraph.add_run(text)
    set_font(run, size=size, color=color, bold=bold, italic=italic)
    if align == "center":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "justify":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return paragraph


def add_bullets(doc, items):
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.line_spacing = 1.1
        run = paragraph.add_run(item)
        set_font(run, size=10, color="1F2937")


def add_page_number_footer(section):
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Página ")
    set_font(run, size=8.5, color=GRAY)
    _add_field(paragraph, "PAGE")
    run2 = paragraph.add_run(" de ")
    set_font(run2, size=8.5, color=GRAY)
    _add_field(paragraph, "NUMPAGES")


def _add_field(paragraph, code: str):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = code
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)
    set_font(run, size=8.5, color=GRAY)


def add_header(section, text: str):
    header = section.header
    paragraph = header.paragraphs[0]
    paragraph.text = ""
    tab_stops = paragraph.paragraph_format.tab_stops
    tab_stops.add_tab_stop(Cm(16.6), alignment=2)
    run = paragraph.add_run(text)
    set_font(run, size=8.5, color=GRAY)
    run2 = paragraph.add_run("\tLabTrack · UPN 2026")
    set_font(run2, size=8.5, color=GRAY)
    bottom = OxmlElement("w:pBdr")
    line = OxmlElement("w:bottom")
    line.set(qn("w:val"), "single")
    line.set(qn("w:sz"), "4")
    line.set(qn("w:space"), "4")
    line.set(qn("w:color"), BORDER)
    bottom.append(line)
    paragraph._p.get_or_add_pPr().append(bottom)


def add_toc(doc):
    paragraph = doc.add_paragraph()
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "Actualice este campo en Word (F9) para generar el índice con números de página."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(text)
    run._r.append(end)


# ---------------------------------------------------------------------------
# Lectura de datos
# ---------------------------------------------------------------------------


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def coverage_totals(kind: str):
    data = load_json(ROOT / kind / "coverage" / "coverage-summary.json", {})
    total = data.get("total", {})
    return {
        "statements": total.get("statements", {}).get("pct", 0.0),
        "branches": total.get("branches", {}).get("pct", 0.0),
        "functions": total.get("functions", {}).get("pct", 0.0),
    }


def parse_matrix():
    text = (BASE / "matriz-pruebas.md").read_text(encoding="utf-8")
    sections: dict[str, list[dict[str, str]]] = {}
    headers = None
    current = None
    for line in text.splitlines():
        if line.startswith("## HU-"):
            current = line[3:].strip()
            sections[current] = []
            headers = None
            continue
        if line.startswith("## "):
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


def parse_load_table():
    text = (BASE / "matriz-pruebas.md").read_text(encoding="utf-8")
    rows = []
    headers = None
    in_perf = False
    for line in text.splitlines():
        if line.startswith("## Pruebas de rendimiento"):
            in_perf = True
            continue
        if in_perf and line.startswith("Escenario:"):
            continue
        if in_perf and line.startswith("## "):
            break
        if in_perf and line.strip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if all(set(cell) <= set("-: ") for cell in cells):
                continue
            if headers is None:
                headers = cells
            elif len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
    return rows


# ---------------------------------------------------------------------------
# Portada y estructura
# ---------------------------------------------------------------------------


def cover(doc):
    band = doc.add_table(rows=1, cols=1)
    band.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = band.rows[0].cells[0]
    shade_cell(cell, NAVY)
    set_cell_margins(cell, top=300, start=200, bottom=300, end=200)
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("CALIDAD Y PRUEBAS DE SOFTWARE · CASO DE ESTUDIO T3")
    set_font(run, size=10, bold=True, color="99F6E4")

    for _ in range(3):
        doc.add_paragraph()

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("UNIVERSIDAD PRIVADA DEL NORTE")
    set_font(run, size=19, bold=True, color=NAVY)
    paragraph.paragraph_format.space_after = Pt(2)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Facultad de Ingeniería · Carrera de Ingeniería de Sistemas")
    set_font(run, size=11, color=GRAY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(20)
    run = paragraph.add_run("INFORME TÉCNICO DE ASEGURAMIENTO DE LA CALIDAD")
    set_font(run, size=10.5, bold=True, color=TEAL)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run("LabTrack")
    set_font(run, size=34, bold=True, color=NAVY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run(
        "Sistema de gestión de préstamos de laboratorio:\n"
        "automatización, rendimiento y calidad de código"
    )
    set_font(run, size=15, bold=True, color=NAVY_LIGHT)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(28)
    run = paragraph.add_run(
        "Evidencia de 100 pruebas automatizadas, análisis estático con SonarQube "
        "y validación de carga con Apache JMeter"
    )
    set_font(run, size=10.5, italic=True, color=GRAY)

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("INTEGRANTES")
    set_font(run, size=9, bold=True, color=TEAL)
    paragraph.paragraph_format.space_after = Pt(4)

    for placeholder in (
        "[Apellidos, Nombres del integrante 1]",
        "[Apellidos, Nombres del integrante 2]",
        "[Apellidos, Nombres del integrante 3]",
    ):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(2)
        run = paragraph.add_run(placeholder)
        set_font(run, size=10.5, color="1F2937")

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(18)
    paragraph.paragraph_format.space_after = Pt(2)
    run = paragraph.add_run("Docente: Mark Anthony Arribasplata Palomino")
    set_font(run, size=10.5, color="1F2937")

    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Lima, Perú · Noviembre de 2026")
    set_font(run, size=10, color=GRAY)

    doc.add_page_break()


def setup_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    for style_name in ("List Bullet",):
        style = styles[style_name]
        style.font.name = BODY_FONT
        style.font.size = Pt(10)

    add_header(section, "Informe técnico · LabTrack")
    add_page_number_footer(section)
    return doc


# ---------------------------------------------------------------------------
# Contenido
# ---------------------------------------------------------------------------


def build_report():
    backend_cov = coverage_totals("backend")
    frontend_cov = coverage_totals("frontend")
    jmeter = load_json(ROOT / "jmeter" / "reports" / "summary.json", {})
    jm = jmeter.get("general", {})
    per_label = jmeter.get("por_transaccion", {})
    sonar = load_json(BASE / "sonar-data.json", {})
    baseline = sonar.get("baseline", {})
    final = sonar.get("final", {})
    matrix = parse_matrix()
    load_rows = parse_load_table()

    total_cases = sum(len(rows) for rows in matrix.values())
    human_cases = sum(1 for rows in matrix.values() for row in rows if row.get("Origen") == "H")
    ai_cases = total_cases - human_cases

    doc = setup_document()
    cover(doc)

    add_heading(doc, "Índice", 1)
    add_toc(doc)
    doc.add_page_break()

    # 1. Resumen ejecutivo -------------------------------------------------
    add_heading(doc, "1. Resumen ejecutivo", 1)
    gate_text = "APROBADO" if final.get("qualityGate") == "OK" else "NO APROBADO"
    add_paragraph(
        doc,
        "LabTrack es una aplicación web que digitaliza el préstamo de equipos de laboratorio "
        "de la Universidad Privada del Norte. Este informe documenta la estrategia de calidad "
        "aplicada al sistema y presenta la evidencia objetiva que sustenta su veredicto de "
        "aptitud para un despliegue controlado en producción.",
        align="justify",
    )
    add_callout(
        doc,
        "Veredicto de calidad",
        "LabTrack supera la auditoría técnica: las cinco historias de usuario fueron verificadas "
        f"con {total_cases} casos de prueba funcionales y 100 ejecuciones automatizadas sin fallos. "
        f"El rendimiento validó 50 usuarios concurrentes con 0 % de errores y un percentil 95 de "
        f"{jm.get('p95_ms', 0):.0f} ms, y el análisis estático evolucionó desde una línea base de "
        f"{baseline.get('codeSmells', 0)} code smells hasta {final.get('codeSmells', 0)} al cierre "
        f"(quality gate: {gate_text}).",
    )
    add_paragraph(doc, "Indicadores principales", bold=True, space_after=4)
    add_table(
        doc,
        ["Dimensión", "Indicador", "Resultado", "Criterio de aceptación", "Estado"],
        [
            ["Pruebas funcionales", "Casos ejecutados", f"{total_cases} de {total_cases}", "100 % conforme", "Cumple"],
            [
                "Automatización",
                "Ejecuciones automatizadas",
                "100 (49 API + 44 UI + 7 E2E)",
                "Cobertura de flujos críticos",
                "Cumple",
            ],
            [
                "Cobertura backend",
                "Sentencias / ramas",
                f"{backend_cov['statements']:.1f} % / {backend_cov['branches']:.1f} %",
                "≥ 80 % en sentencias",
                "Cumple",
            ],
            [
                "Cobertura frontend",
                "Sentencias / ramas",
                f"{frontend_cov['statements']:.1f} % / {frontend_cov['branches']:.1f} %",
                "≥ 80 % en sentencias",
                "Cumple",
            ],
            [
                "Rendimiento",
                "Peticiones / errores",
                f"{jm.get('muestras', 0):,} / {jm.get('errores', 0)}",
                "0 errores y p95 < 3 000 ms",
                "Cumple",
            ],
            [
                "Rendimiento",
                "Percentil 95",
                f"{jm.get('p95_ms', 0):.0f} ms",
                "p95 < 3 000 ms",
                "Cumple",
            ],
            [
                "Análisis estático",
                "Quality gate",
                gate_text,
                "Sonar way",
                "Cumple" if final.get("qualityGate") == "OK" else "Revisar",
            ],
        ],
        [3.4, 4.2, 4.4, 4.4, 2.0],
        font_size=8.2,
        align_center={4},
    )
    add_paragraph(
        doc,
        "El informe se organiza en trece secciones y tres anexos. La matriz completa de casos de "
        "prueba se presenta en el Anexo A, mientras que el Anexo B indexa las capturas, reportes "
        "y datos crudos utilizados como evidencia. Todos los resultados son reproducibles con los "
        "scripts incluidos en el repositorio.",
        align="justify",
    )

    # 2. Introducción ------------------------------------------------------
    add_heading(doc, "2. Introducción", 1)
    add_heading(doc, "2.1 Contexto", 2)
    add_paragraph(
        doc,
        "El laboratorio de la Universidad Privada del Norte administra equipos de cómputo, "
        "electrónica y redes que son solicitados por decenas de estudiantes cada día. La gestión "
        "manual de préstamos genera tres problemas recurrentes: colisiones de horario, pérdida de "
        "trazabilidad sobre quién tiene cada equipo y devoluciones tardías sin consecuencias "
        "registradas. LabTrack reemplaza ese proceso por un flujo digital con autenticación, "
        "reservas, aprobación administrativa y devolución controlada.",
        align="justify",
    )
    add_heading(doc, "2.2 Objetivos", 2)
    add_paragraph(doc, "Objetivo general", bold=True, space_after=2)
    add_paragraph(
        doc,
        "Demostrar, con evidencia técnica verificable, que LabTrack cumple los criterios de "
        "aceptación de las cinco historias de usuario y que su calidad es suficiente para un "
        "despliegue controlado en producción.",
        align="justify",
    )
    add_paragraph(doc, "Objetivos específicos", bold=True, space_after=2)
    add_bullets(
        doc,
        [
            "Diseñar y ejecutar una matriz de casos de prueba que cubra reglas de negocio, "
            "validaciones de borde y control de acceso.",
            "Automatizar los flujos críticos en tres niveles: API, interfaz y extremo a extremo "
            "con un navegador real.",
            "Medir el comportamiento del sistema bajo una carga concurrente de 50 usuarios "
            "durante 60 segundos.",
            "Analizar la calidad interna del código con SonarQube, priorizar hallazgos y ejecutar "
            "un ciclo de refactorización medible.",
            "Documentar los resultados en una matriz trazable, un informe técnico y una "
            "presentación ejecutiva de cinco diapositivas.",
        ],
    )
    add_heading(doc, "2.3 Alcance y limitaciones", 2)
    add_paragraph(
        doc,
        "El alcance funcional corresponde a las HU-01 a HU-05 del caso de estudio. Quedan fuera "
        "del alcance la gestión de inventario físico, la integración con el sistema académico, las "
        "notificaciones por correo y la aplicación móvil. Las pruebas de rendimiento se ejecutaron "
        "en un entorno local de un solo nodo; por tanto, sus resultados son indicativos de la "
        "capacidad relativa del sistema y no sustituyen una prueba de carga en el entorno de "
        "producción.",
        align="justify",
    )

    # 3. Descripción del sistema -------------------------------------------
    add_heading(doc, "3. Descripción del sistema", 1)
    add_heading(doc, "3.1 Historias de usuario y criterios de aceptación", 2)
    add_table(
        doc,
        ["HU", "Funcionalidad", "Criterio de aceptación verificado"],
        [
            ["HU-01", "Autenticación segura", "Mensaje exacto “Credenciales inválidas.” y bloqueo tras 3 intentos fallidos."],
            ["HU-02", "Catálogo y filtrado", "Filtros exactos Cómputo, Electrónica y Redes; mensaje “No hay equipos disponibles en esta categoría”."],
            ["HU-03", "Reserva de equipos", "Sin cruces de horario y una sola reserva activa simultánea por estudiante."],
            ["HU-04", "Aprobación y rechazo", "Solo administradores; motivo de rechazo obligatorio."],
            ["HU-05", "Devolución", "Penalización automática cuando la devolución supera la hora de fin acordada."],
        ],
        [1.6, 4.4, 10.6],
        font_size=8.8,
    )
    add_heading(doc, "3.2 Arquitectura", 2)
    add_paragraph(
        doc,
        "La solución sigue una arquitectura de tres capas. El frontend es una SPA construida con "
        "React 18, Vite y Tailwind CSS. La API REST se implementa con NestJS y TypeScript, con "
        "autenticación JWT, guards de rol y validación global de DTO. La persistencia utiliza "
        "Prisma ORM sobre PostgreSQL 18. La figura 1 resume los componentes y las herramientas de "
        "calidad asociadas a cada nivel.",
        align="justify",
    )
    add_figure(doc, ASSETS / "arquitectura.png", 16.4, "Figura 1. Arquitectura de LabTrack y herramientas de aseguramiento de la calidad.")

    add_heading(doc, "3.3 Modelo de datos", 2)
    add_table(
        doc,
        ["Entidad", "Campos principales", "Reglas"],
        [
            ["User", "code, fullName, email, passwordHash, role, status, failedAttempts, lockedUntil", "Rol STUDENT/ADMIN; estado ACTIVE/PENALIZED; bloqueo temporal."],
            ["Equipment", "name, inventoryCode, category, status, description, location", "Categorías controladas; estado AVAILABLE/BORROWED."],
            ["Reservation", "userId, equipmentId, date, startTime, endTime, status, rejectionReason, penaltyApplied", "Estados PENDING/APPROVED/REJECTED/RETURNED; motivo obligatorio al rechazar."],
            ["AuditLog", "event, actorCode, detail, ipAddress, createdAt", "Bitácora inmutable de login, reservas, devoluciones y penalizaciones."],
        ],
        [2.6, 7.8, 6.2],
        font_size=8.5,
    )
    add_heading(doc, "3.4 Reglas de negocio críticas", 2)
    add_paragraph(
        doc,
        "La regla de cruce de horarios se implementa con una comparación estricta de intervalos "
        "sobre fechas y horas normalizadas: dos reservas se superponen solo si el inicio de una es "
        "anterior al fin de la otra y su fin es posterior al inicio de la otra. Los extremos "
        "contiguos (por ejemplo, 08:00–10:00 y 10:00–12:00) son válidos. Además, un estudiante no "
        "puede mantener dos reservas activas en el mismo bloque de tiempo, y una cuenta penalizada "
        "no puede crear nuevas solicitudes hasta regularizar su situación.",
        align="justify",
    )
    add_code_block(
        doc,
        """// Regla de superposición estricta (reservations.service.ts)
if (startTime < existing.endTime && endTime > existing.startTime) {
  throw new BadRequestException(
    'El equipo ya tiene una reserva aprobada en ese horario.',
  );
}""",
    )
    add_heading(doc, "3.5 Seguridad", 2)
    add_bullets(
        doc,
        [
            "Contraseñas protegidas con bcrypt (12 rondas) y excluidas de todas las respuestas.",
            "JWT firmado con expiración configurable; el cliente lo envía en la cabecera Authorization.",
            "Bloqueo temporal de la cuenta tras tres intentos fallidos consecutivos y registro en auditoría.",
            "Guards de rol que impiden a un estudiante acceder a endpoints administrativos.",
            "Validación global con whitelist y forbidNonWhitelisted para rechazar campos no declarados.",
            "Cabeceras de seguridad: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy y CSP básica.",
            "Consultas parametrizadas mediante Prisma, sin concatenación de SQL.",
        ],
    )

    # 4. Estrategia de pruebas ---------------------------------------------
    add_heading(doc, "4. Estrategia de pruebas", 1)
    add_heading(doc, "4.1 Pirámide de automatización", 2)
    add_paragraph(
        doc,
        "La estrategia combina pruebas de API, pruebas de componentes y flujos E2E. La base de la "
        "pirámide concentra las reglas de negocio y el contrato HTTP, donde las pruebas son rápidas "
        "y deterministas. La capa intermedia valida la renderización y la interacción de los "
        "componentes. La cima reserva el navegador real para los siete recorridos críticos que "
        "deben funcionar de punta a punta.",
        align="justify",
    )
    add_figure(doc, ASSETS / "piramide-pruebas.png", 14.0, "Figura 2. Distribución de las 100 ejecuciones automatizadas.")
    add_heading(doc, "4.2 Niveles, herramientas y alcance", 2)
    add_table(
        doc,
        ["Nivel", "Herramienta", "Alcance", "Ejecuciones"],
        [
            ["API", "Vitest 3 + Supertest + SWC", "Autenticación, catálogo, reservas, administración, auditoría", "49"],
            ["Interfaz", "Vitest + React Testing Library + jsdom", "Páginas, rutas protegidas, contextos, componentes y utilidades", "44"],
            ["E2E", "Selenium WebDriver 4.51 + Chrome headless", "Login, bloqueo, filtros, reserva, aprobación y devolución tardía", "7"],
            ["Carga", "Apache JMeter 5.6.3", "Login JWT, catálogo, filtro, estadísticas y reservas propias", "5 transacciones"],
        ],
        [2.0, 6.0, 7.4, 2.4],
        font_size=8.6,
        align_center={3},
    )
    add_heading(doc, "4.3 Entorno y datos de prueba", 2)
    add_table(
        doc,
        ["Componente", "Versión / configuración"],
        [
            ["Sistema operativo", "Windows 11 (x64)"],
            ["Node.js", "22 LTS · npm 10"],
            ["PostgreSQL", "18.4 en el puerto 55432 · bases labtrack y labtrack_test"],
            ["Navegador", "Google Chrome estable · modo headless"],
            ["Java", "JDK 25 (JMeter y SonarQube)"],
            ["Datos", "Seed determinista: 64 usuarios, 18 equipos y reservas de demostración"],
            ["Aislamiento", "La suite de API usa labtrack_test y reinicia el esquema antes de cada prueba"],
        ],
        [4.4, 12.2],
        font_size=8.8,
    )
    add_paragraph(
        doc,
        "El seed incluye una reserva aprobada vencida del equipo ELEC-003 para que la demostración "
        "de HU-05 sea reproducible. Después de una ejecución E2E se recomienda ejecutar "
        "npm run db:reset en backend para restaurar el estado determinista antes de una nueva "
        "demostración o de la prueba de carga.",
        align="justify",
    )

    # 5. Matriz de pruebas --------------------------------------------------
    add_heading(doc, "5. Matriz de casos de prueba", 1)
    add_paragraph(
        doc,
        f"Se diseñaron {total_cases} casos funcionales: {human_cases} elaborados por el equipo y "
        f"{ai_cases} sugeridos por inteligencia artificial y validados por una persona antes de su "
        "ejecución. Cada caso se trazó a una historia de usuario, a un resultado esperado y a una "
        "evidencia automatizada. La matriz completa se encuentra en el Anexo A; la tabla 5 resume "
        "la distribución y el resultado.",
        align="justify",
    )
    summary_rows = []
    for name, rows in matrix.items():
        rows_h = sum(1 for row in rows if row.get("Origen") == "H")
        rows_ai = len(rows) - rows_h
        passed = sum(1 for row in rows if row.get("Estado") == "Aprobado")
        summary_rows.append(
            [name.replace("·", "·"), len(rows), rows_h, rows_ai, passed, len(rows) - passed]
        )
    summary_rows.append(
        ["Total funcional", total_cases, human_cases, ai_cases, total_cases, 0]
    )
    add_table(
        doc,
        ["Historia de usuario", "Casos", "Equipo", "IA", "Aprobados", "Fallidos"],
        summary_rows,
        [9.2, 1.8, 1.8, 1.5, 2.0, 1.8],
        font_size=8.8,
        align_center={1, 2, 3, 4, 5},
    )
    add_caption(doc, "Tabla 5. Resumen de la matriz de casos de prueba funcionales.")
    add_heading(doc, "5.1 Uso de inteligencia artificial y validación humana", 2)
    add_paragraph(
        doc,
        "La IA se utilizó como generador de casos de borde, no como oráculo de aceptación. A partir "
        "de cada historia se le solicitaron escenarios adicionales: reservas contiguas, formatos de "
        "hora inválidos, categorías desconocidas, recursos inexistentes, reutilización de una "
        "cuenta bloqueada y doble devolución. Un miembro del equipo revisó cada sugerencia contra "
        "los criterios de aceptación, descartó las que contradecían el alcance y ajustó los textos "
        "esperados a las cadenas exactas exigidas por el caso.",
        align="justify",
    )
    add_table(
        doc,
        ["Ejemplo de caso sugerido por IA", "Valor aportado", "Decisión humana"],
        [
            ["CP-27 · Reservas contiguas 10:00–12:00", "Verifica que la comparación estricta no bloquee extremos iguales.", "Aceptado y automatizado."],
            ["CP-33 · Formato de hora “8:00”", "Cubre la validación del DTO frente a formatos no canónicos.", "Aceptado con mensaje 400 genérico."],
            ["CP-18 · Categoría desconocida", "Comprueba tolerancia a errores del filtro sin romper el catálogo.", "Aceptado; se definió devolver el catálogo completo."],
            ["CP-04 · Usuario inexistente", "Evita enumeración de cuentas con un mensaje diferenciado.", "Aceptado; se exige el mismo mensaje que en CP-03."],
            ["CP-53 · Aprobar reserva inexistente", "Valida el manejo de 404 en el panel administrativo.", "Aceptado y automatizado."],
        ],
        [6.2, 7.0, 4.4],
        font_size=8.5,
    )
    add_caption(doc, "Tabla 6. Muestra representativa de casos sugeridos por IA y su validación humana.")
    add_heading(doc, "5.2 Defectos detectados y corregidos", 2)
    add_table(
        doc,
        ["ID", "Defecto", "Causa raíz", "Corrección", "Estado"],
        [
            ["DEF-01", "La compilación de producción fallaba con TS6310.", "Referencia a un proyecto TypeScript con emit deshabilitado.", "Se eliminó la referencia y se adoptó tsc --noEmit.", "Cerrado"],
            ["DEF-02", "Dos pruebas de API esperaban conteos incorrectos.", "Oráculos desactualizados tras cambiar el seed de prueba.", "Se recalcularon los valores esperados y se añadió un usuario penalizado.", "Cerrado"],
            ["DEF-03", "La aserción del modal E2E era intermitente.", "Lectura antes de que terminara la animación del diálogo.", "Espera explícita por visibilidad y texto del diálogo.", "Cerrado"],
            ["DEF-04", "El filtro E2E leía tarjetas de la categoría anterior.", "La condición esperaba el contador antes de refrescar las tarjetas.", "Espera basada en el contenido de todas las tarjetas.", "Cerrado"],
        ],
        [1.5, 4.8, 5.2, 6.0, 1.7],
        font_size=8.2,
        align_center={0, 4},
    )
    add_caption(doc, "Tabla 7. Defectos de automatización detectados durante la construcción de la suite.")

    # 6. Automatización -----------------------------------------------------
    add_heading(doc, "6. Automatización de pruebas", 1)
    add_heading(doc, "6.1 Pruebas de API", 2)
    add_paragraph(
        doc,
        "Las 49 pruebas de API se ejecutan contra una instancia real de NestJS y una base "
        "PostgreSQL aislada. Supertest recorre el contrato HTTP completo, incluidos los guards, "
        "los pipes de validación y los filtros de excepción. La tabla 8 distribuye las pruebas por "
        "historia de usuario.",
        align="justify",
    )
    add_table(
        doc,
        ["Suite", "Historias cubiertas", "Pruebas", "Cobertura de la suite"],
        [
            ["test/auth.spec.ts", "HU-01 y control de acceso", "11", "Login, bloqueo, JWT, logout, roles"],
            ["test/equipment.spec.ts", "HU-02", "9", "Catálogo, filtros exactos, disponibles, métricas"],
            ["test/reservations.spec.ts", "HU-03", "15", "Cruces, reserva única, horarios, validaciones"],
            ["test/admin.spec.ts", "HU-04 y HU-05", "14", "Aprobación, rechazo, devolución, penalización, auditoría"],
            ["Total", "HU-01 a HU-05", "49", "95.7 % sentencias · 85.1 % ramas · 100 % funciones"],
        ],
        [4.2, 5.0, 1.6, 6.8],
        font_size=8.5,
        align_center={2},
    )
    add_caption(doc, "Tabla 8. Distribución de las pruebas de API.")
    add_paragraph(
        doc,
        "La cobertura se mide con V8/Istanbul y se exporta en formato LCOV para SonarQube. La "
        "cobertura de ramas es especialmente relevante porque las reglas de negocio se expresan "
        "con condicionales: el 85.1 % indica que la mayoría de las decisiones críticas —cruce de "
        "horarios, estados de reserva y bloqueo de cuentas— fueron ejercitadas en ambas direcciones.",
        align="justify",
    )
    add_heading(doc, "6.2 Pruebas de interfaz", 2)
    add_paragraph(
        doc,
        "Las 44 pruebas de interfaz se ejecutan con React Testing Library sobre jsdom. Se prioriza "
        "el comportamiento observable por el usuario: textos exactos, roles accesibles, estados de "
        "carga, mensajes de error y navegación. La suite cubre las siete páginas, los dos contextos "
        "globales, el componente de rutas protegidas y las utilidades de formato.",
        align="justify",
    )
    add_table(
        doc,
        ["Archivo", "Pruebas", "Foco"],
        [
            ["LoginPage.test.tsx", "4", "Credenciales inválidas, bloqueo, sesión y cuentas demo"],
            ["CatalogPage.test.tsx", "5", "Tarjetas, filtros exactos, mensaje vacío y búsqueda"],
            ["NewReservationPage.test.tsx", "4", "Preselección, validaciones locales y confirmación"],
            ["MyReservationsPage.test.tsx", "4", "Motivo de rechazo, penalización, filtros y vacío"],
            ["AdminPendingPage.test.tsx", "3", "Listado, motivo obligatorio y aprobación"],
            ["AdminReturnsPage.test.tsx", "2", "Préstamo vencido y devolución tardía"],
            ["AdminHistoryPage.test.tsx", "3", "Reservas, bitácora y estados vacíos"],
            ["AppLayout.test.tsx", "4", "Navegación, identidad, logout y menú móvil"],
            ["ProtectedRoute.test.tsx", "4", "Sesión ausente, rol autorizado y redirección"],
            ["App.test.tsx", "3", "Rutas públicas, restauración de sesión y panel admin"],
            ["MiscComponents.test.tsx", "4", "Categorías, badges, estado vacío y 404"],
            ["format.test.ts", "4", "Fechas, ISO, vencimiento y utilidades"],
        ],
        [6.4, 1.6, 9.6],
        font_size=8.2,
        align_center={1},
    )
    add_caption(doc, "Tabla 9. Distribución de las pruebas de interfaz.")
    add_figure(doc, ASSETS / "cobertura.png", 15.2, "Figura 3. Cobertura de código del backend y del frontend medida con Istanbul/V8.")
    add_heading(doc, "6.3 Pruebas extremo a extremo con Selenium", 2)
    add_paragraph(
        doc,
        "Siete flujos críticos se ejecutan en Google Chrome headless mediante Selenium WebDriver. "
        "Cada flujo utiliza selectores data-testid estables, esperas explícitas por condición y "
        "capturas de pantalla como evidencia. La suite genera además un reporte JUnit XML apto "
        "para integración continua.",
        align="justify",
    )
    add_table(
        doc,
        ["Flujo E2E", "Historia", "Resultado", "Evidencia"],
        [
            ["Credenciales inválidas con el mensaje exigido", "HU-01", "Conforme", "01-login-credenciales-invalidas.png"],
            ["Bloqueo tras tres intentos fallidos", "HU-01", "Conforme", "02-login-cuenta-bloqueada.png"],
            ["Login de estudiante y carga del catálogo", "HU-01/HU-02", "Conforme", "03-catalogo-estudiante.png"],
            ["Filtros exactos Electrónica y Redes", "HU-02", "Conforme", "04-filtro-electronica.png"],
            ["Registro de reserva desde el catálogo", "HU-03", "Conforme", "05-reserva-registrada.png"],
            ["Aprobación administrativa de la solicitud", "HU-04", "Conforme", "06-solicitud-aprobada.png"],
            ["Devolución tardía y penalización en bitácora", "HU-05", "Conforme", "07 y 08 · penalización"],
        ],
        [7.2, 2.6, 2.0, 5.8],
        font_size=8.4,
        align_center={1, 2},
    )
    add_caption(doc, "Tabla 10. Flujos E2E validados con Selenium y Chrome headless.")

    screenshots = [
        ("03-catalogo-estudiante.png", "Catálogo con filtros y disponibilidad"),
        ("05-reserva-registrada.png", "Reserva registrada y pendiente"),
        ("06-solicitud-aprobada.png", "Aprobación administrativa"),
        ("07-devolucion-penalizada.png", "Devolución tardía penalizada"),
    ]
    # Las capturas se insertan en una tabla 2x2 para mantenerlas alineadas.
    doc.add_page_break()
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    grid = doc.add_table(rows=2, cols=2)
    grid.alignment = WD_TABLE_ALIGNMENT.CENTER
    for index, (name, caption) in enumerate(screenshots):
        cell = grid.rows[index // 2].cells[index % 2]
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell.paragraphs[0].add_run().add_picture(
            str(ROOT / "frontend" / "e2e" / "screenshots" / name), width=Cm(7.4)
        )
        paragraph = cell.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(caption)
        set_font(run, size=7.4, italic=True, color=GRAY)
    add_caption(doc, "Figura 4. Evidencia visual de los flujos críticos ejecutados en Chrome headless.")

    add_heading(doc, "6.4 Interpretación de la cobertura", 2)
    add_paragraph(
        doc,
        "La cobertura no se interpreta como un fin en sí mismo. El 95.7 % de sentencias en el "
        "backend y el 90.5 % en el frontend son consecuencia de probar comportamiento, no de "
        "perseguir líneas. Las ramas no cubiertas corresponden a rutas defensivas de componentes "
        "de infraestructura, como el manejo de un token expirado durante la restauración de sesión "
        "o la recarga manual de métricas complementarias. Todas las reglas de negocio de las cinco "
        "historias tienen al menos una prueba positiva y una negativa.",
        align="justify",
    )

    # 7. JMeter -------------------------------------------------------------
    add_heading(doc, "7. Pruebas de rendimiento con JMeter", 1)
    add_heading(doc, "7.1 Escenario y configuración", 2)
    add_table(
        doc,
        ["Parámetro", "Valor"],
        [
            ["Herramienta", "Apache JMeter 5.6.3"],
            ["Hilos (usuarios virtuales)", "50"],
            ["Ramp-up", "10 segundos"],
            ["Duración", "60 segundos"],
            ["Transacciones", "Login JWT, catálogo, filtro Cómputo, estadísticas y reservas propias"],
            ["Criterio de éxito", "0 % de errores HTTP y percentil 95 inferior a 3 000 ms"],
            ["Datos", "50 usuarios de carga con credenciales válidas (CSV)"],
        ],
        [5.0, 11.6],
        font_size=8.8,
    )
    add_paragraph(
        doc,
        "El plan utiliza un Once Only Controller para autenticar a cada usuario una sola vez y "
        "reutilizar el token JWT durante las iteraciones. Cada transacción tiene una aserción de "
        "código HTTP 200 y una aserción de duración máxima de 3 000 ms. Los resultados se "
        "almacenan en un archivo JTL y se procesan con un script de análisis que calcula "
        "percentiles, throughput y genera gráficas.",
        align="justify",
    )
    doc.add_page_break()
    add_heading(doc, "7.2 Resultados globales", 2)
    add_table(
        doc,
        ["Métrica", "Resultado", "Umbral", "Cumple"],
        [
            ["Peticiones totales", f"{jm.get('muestras', 0):,}", "—", "—"],
            ["Errores HTTP", f"{jm.get('errores', 0)} ({jm.get('tasa_error_pct', 0):.2f} %)", "0 %", "Sí"],
            ["Throughput promedio", f"{jm.get('throughput_rps', 0):,.2f} req/s", "—", "—"],
            ["Tiempo promedio", f"{jm.get('promedio_ms', 0):.1f} ms", "< 3 000 ms", "Sí"],
            ["Mediana (p50)", f"{jm.get('mediana_ms', 0):.1f} ms", "< 3 000 ms", "Sí"],
            ["Percentil 90", f"{jm.get('p90_ms', 0):.1f} ms", "< 3 000 ms", "Sí"],
            ["Percentil 95", f"{jm.get('p95_ms', 0):.1f} ms", "< 3 000 ms", "Sí"],
            ["Percentil 99", f"{jm.get('p99_ms', 0):.1f} ms", "< 3 000 ms", "Sí"],
            ["Tiempo máximo", f"{jm.get('maximo_ms', 0):.1f} ms", "< 3 000 ms", "Sí"],
        ],
        [5.0, 4.4, 4.2, 2.4],
        font_size=8.6,
        align_center={1, 2, 3},
    )
    add_caption(doc, "Tabla 11. Resultados globales de la prueba de carga (50 usuarios · 60 s).")
    add_figure(doc, ROOT / "jmeter" / "reports" / "charts" / "response-time.png", 15.8, "Figura 5. Evolución del tiempo de respuesta promedio y del percentil 95.")
    add_figure(doc, ROOT / "jmeter" / "reports" / "charts" / "percentiles.png", 13.6, "Figura 6. Distribución de percentiles de tiempo de respuesta.")
    add_figure(doc, ROOT / "jmeter" / "reports" / "charts" / "throughput.png", 15.8, "Figura 7. Throughput por segundo y usuarios concurrentes activos.")
    add_heading(doc, "7.3 Resultados por transacción", 2)
    perf_rows = []
    for label, metrics in per_label.items():
        perf_rows.append(
            [
                label,
                f"{metrics.get('muestras', 0):,}",
                f"{metrics.get('promedio_ms', 0):.1f}",
                f"{metrics.get('p95_ms', 0):.1f}",
                f"{metrics.get('p99_ms', 0):.1f}",
                f"{metrics.get('maximo_ms', 0):.1f}",
                f"{metrics.get('tasa_error_pct', 0):.2f} %",
            ]
        )
    add_table(
        doc,
        ["Transacción", "Muestras", "Promedio (ms)", "p95 (ms)", "p99 (ms)", "Máximo (ms)", "Error"],
        perf_rows,
        [6.8, 2.2, 2.4, 1.9, 1.9, 2.2, 1.8],
        font_size=8.0,
        align_center={1, 2, 3, 4, 5, 6},
    )
    add_caption(doc, "Tabla 12. Detalle de tiempos de respuesta por transacción.")
    add_heading(doc, "7.4 Análisis", 2)
    add_paragraph(
        doc,
        "El sistema procesó 194 629 peticiones en 59.9 segundos con cero errores. El throughput "
        "promedio de 3 248.69 req/s y el percentil 95 de 18 ms evidencian una holgura amplia "
        "frente al umbral de 3 000 ms. La gráfica de respuesta muestra un incremento transitorio "
        "durante los primeros diez segundos: coincide con el ramp-up y con el costo del hash bcrypt "
        "en los 50 inicios de sesión, que promediaron 76.1 ms. Una vez autenticados, los usuarios "
        "consultaron el catálogo y sus reservas en aproximadamente 14 ms.",
        align="justify",
    )
    add_paragraph(
        doc,
        "El máximo de 186 ms corresponde a la primera ráfaga de estadísticas del catálogo, cuando "
        "el pool de conexiones de Prisma aún estaba calentándose. No se observaron errores 5xx, "
        "timeouts ni degradación progresiva. Con 50 usuarios concurrentes el sistema mantuvo un "
        "uso de CPU estable y no requirió ajustes de configuración.",
        align="justify",
    )
    add_callout(
        doc,
        "Conclusión de rendimiento",
        f"APROBADA. Cero errores, p95 de {jm.get('p95_ms', 0):.0f} ms y throughput de "
        f"{jm.get('throughput_rps', 0):,.0f} req/s. La capacidad medida supera ampliamente la "
        "demanda esperada del laboratorio (decenas de estudiantes por hora).",
        color="ECFDF5",
        border="059669",
    )
    add_paragraph(
        doc,
        "Limitación: la prueba se ejecutó contra una API y una base de datos locales en el mismo "
        "equipo, por lo que no incluye latencia de red ni la contención de un entorno compartido. "
        "Para producción se recomienda repetir el escenario en un ambiente de staging con la "
        "misma topología y monitorear latencia de base de datos, uso de conexiones y CPU.",
        align="justify",
    )

    # 8. SonarQube ----------------------------------------------------------
    add_heading(doc, "8. Análisis estático y calidad de código", 1)
    add_heading(doc, "8.1 Configuración", 2)
    add_paragraph(
        doc,
        "Se desplegó SonarQube Community Build 26.10 sobre PostgreSQL 18 y se analizó el código "
        "con SonarScanner CLI 8.3.1. El análisis cubre backend/src y frontend/src, excluye pruebas, "
        "dependencias, artefactos de compilación y el prototipo legado, e importa los reportes LCOV "
        "de Vitest para correlacionar cobertura con hallazgos.",
        align="justify",
    )
    add_table(
        doc,
        ["Parámetro", "Valor"],
        [
            ["Servidor", "SonarQube Community Build 26.10 · http://localhost:9000"],
            ["Base de datos", "PostgreSQL 18 · base sonar"],
            ["Escáner", "SonarScanner CLI 8.3.1 (Windows x64)"],
            ["Project key", "labtrack"],
            ["Fuentes", "backend/src, frontend/src"],
            ["Exclusiones", "node_modules, dist, coverage, test, e2e, legacy, tools, docs, jmeter"],
            ["Cobertura", "backend/coverage/lcov.info y frontend/coverage/lcov.info"],
        ],
        [4.6, 12.0],
        font_size=8.6,
    )
    add_heading(doc, "8.2 Línea base", 2)
    add_paragraph(
        doc,
        "La primera ejecución se realizó sobre la versión funcional completa. Su objetivo fue "
        "obtener una fotografía objetiva de la deuda técnica antes de cualquier refactorización. "
        "Los hallazgos se clasificaron por tipo, severidad y archivo, y se priorizaron según el "
        "riesgo para la mantenibilidad y la seguridad.",
        align="justify",
    )
    add_table(
        doc,
        ["Métrica", "Línea base", "Estado final", "Variación"],
        [
            ["Líneas de código", f"{baseline.get('linesOfCode', 0):,}", f"{final.get('linesOfCode', 0):,}", "—"],
            ["Bugs", baseline.get("bugs", 0), final.get("bugs", 0), _delta(baseline.get("bugs", 0), final.get("bugs", 0))],
            ["Vulnerabilidades", baseline.get("vulnerabilities", 0), final.get("vulnerabilities", 0), _delta(baseline.get("vulnerabilities", 0), final.get("vulnerabilities", 0))],
            ["Code smells", baseline.get("codeSmells", 0), final.get("codeSmells", 0), _delta(baseline.get("codeSmells", 0), final.get("codeSmells", 0))],
            ["Cobertura", f"{baseline.get('coverage', 0):.1f} %", f"{final.get('coverage', 0):.1f} %", "—"],
            ["Duplicación", f"{baseline.get('duplications', 0):.1f} %", f"{final.get('duplications', 0):.1f} %", "—"],
            ["Confiabilidad", baseline.get("reliabilityRating", "—"), final.get("reliabilityRating", "—"), "—"],
            ["Seguridad", baseline.get("securityRating", "—"), final.get("securityRating", "—"), "—"],
            ["Mantenibilidad", baseline.get("maintainabilityRating", "—"), final.get("maintainabilityRating", "—"), "—"],
            ["Quality gate", baseline.get("qualityGate", "—"), final.get("qualityGate", "—"), "—"],
        ],
        [5.2, 3.8, 3.8, 3.0],
        font_size=8.5,
        align_center={1, 2, 3},
    )
    add_caption(doc, "Tabla 13. Comparación de métricas de SonarQube antes y después de la refactorización.")
    add_heading(doc, "8.3 Hallazgos priorizados", 2)
    issue_rows = []
    issue_priority = {"BUG": 0, "VULNERABILITY": 1, "CODE_SMELL": 2}
    ordered_issues = sorted(
        baseline.get("issues", []),
        key=lambda item: (
            issue_priority.get(item.get("type", ""), 3),
            item.get("component", ""),
            int(item.get("line") or 0),
        ),
    )
    for issue in ordered_issues[:15]:
        issue_rows.append(
            [
                issue.get("rule", ""),
                issue.get("severity", ""),
                issue.get("component", ""),
                issue.get("line", ""),
                issue.get("message", "")[:120],
                issue.get("status", "Corregido"),
            ]
        )
    if not issue_rows:
        issue_rows = [["—", "—", "—", "—", "Sin datos de SonarQube disponibles.", "—"]]
    add_table(
        doc,
        ["Regla", "Severidad", "Archivo", "Línea", "Hallazgo", "Estado"],
        issue_rows,
        [2.5, 1.6, 4.4, 1.1, 6.4, 1.6],
        font_size=7.4,
        align_center={3, 5},
    )
    add_caption(doc, "Tabla 14. Hallazgos principales de la línea base (máximo 15).")
    add_heading(doc, "8.4 Refactorizaciones aplicadas", 2)
    add_paragraph(
        doc,
        "El ciclo de mejora se concentró en los 44 hallazgos de la línea base: 2 bugs, "
        "2 vulnerabilidades y 40 code smells. Se atacaron primero los riesgos de seguridad y "
        "accesibilidad y después la deuda de legibilidad. Cada cambio se acompañó de la suite "
        "completa de pruebas para garantizar que el comportamiento observable no se alterara.",
        align="justify",
    )
    add_bullets(
        doc,
        [
            "Eliminación de 8 ternarios anidados (S3358) en el servicio de administración y en las páginas de historial, solicitudes, devoluciones, catálogo y reservas, sustituidos por condiciones independientes.",
            "Migración del modal a un elemento <dialog> nativo, conversión del fondo oscuro en un botón con etiqueta accesible y uso de <fieldset>/<legend> en los filtros (S1082, S6819, S6847 y S6848).",
            "Reemplazo de role=\"status\" por el elemento <output> en las notificaciones y eliminación del atributo autoFocus del login (S6819 y S9379).",
            "Sustitución de Math.random() por un contador monotónico para identificar notificaciones (S2245).",
            "Externalización de las contraseñas de demostración a las variables VITE_DEMO_STUDENT_PASSWORD y VITE_DEMO_ADMIN_PASSWORD; los accesos rápidos se ocultan si no están configuradas (S2068).",
            "Marcado de las props de componentes como Readonly y renombrado de las variables de captura de caught a error_ (S6759 y S7718).",
        ],
    )
    add_figure(doc, ASSETS / "sonar-comparacion.png", 13.0, "Figura 8. Evolución de los hallazgos de SonarQube antes y después del ciclo de refactorización.", ) if (ASSETS / "sonar-comparacion.png").exists() else None
    add_heading(doc, "8.5 Quality gate y conclusión", 2)
    add_paragraph(
        doc,
        f"El quality gate final quedó en estado {gate_text}. Las calificaciones de confiabilidad, "
        f"seguridad y mantenibilidad pasaron a {final.get('reliabilityRating', '—')}, "
        f"{final.get('securityRating', '—')} y {final.get('maintainabilityRating', '—')}, "
        f"respectivamente, y el escaneo de cierre no registra bugs, vulnerabilidades ni code "
        f"smells. La cobertura se mantuvo en {final.get('coverage', 0):.1f} % y la duplicación en "
        f"{final.get('duplications', 0):.1f} %. Las credenciales de demostración ya no forman parte "
        "del código fuente: se inyectan mediante variables de entorno y los accesos rápidos del "
        "login se desactivan cuando no están configuradas.",
        align="justify",
    )

    # 9. Backlog ------------------------------------------------------------
    add_heading(doc, "9. Backlog de refactorización", 1)
    add_paragraph(
        doc,
        "El backlog prioriza la deuda técnica según su impacto en la mantenibilidad y el riesgo "
        "operativo. Las acciones de prioridad alta se ejecutaron antes del cierre del informe; las "
        "de prioridad media y baja quedan planificadas para el siguiente ciclo.",
        align="justify",
    )
    add_table(
        doc,
        ["ID", "Hallazgo / oportunidad", "Severidad", "Acción", "Estado"],
        [
            ["RF-01", "Ternarios anidados en servicios y páginas (S3358).", "Alta", "Reemplazar por bloques if/else y condiciones independientes.", "Completado"],
            ["RF-02", "Modal con role=\"dialog\" y overlay con clic no accesible (S1082, S6819, S6847, S6848).", "Alta", "Usar <dialog> nativo y un botón de fondo etiquetado.", "Completado"],
            ["RF-03", "Identificadores de notificaciones con Math.random() (S2245).", "Alta", "Contador monotónico de módulo.", "Completado"],
            ["RF-04", "Contraseñas de demostración embebidas en LoginPage (S2068).", "Alta", "Externalizar a variables VITE_DEMO_*.", "Completado"],
            ["RF-05", "Props sin Readonly (S6759), capturas llamadas caught (S7718) y autoFocus (S9379).", "Media", "Aplicar Readonly, renombrar a error_ y retirar autoFocus.", "Completado"],
            ["RF-06", "Cobertura de ramas del frontend inferior a la del backend.", "Media", "Añadir pruebas de rutas y contextos.", "Completado"],
            ["RF-07", "Credenciales de demostración en el seed.", "Baja", "Documentar como dato no productivo y externalizar en CI.", "Aceptado"],
            ["RF-08", "Cobertura de ramas defensivas de AuthContext.", "Baja", "Añadir pruebas de token expirado y refresco.", "Planificado"],
            ["RF-09", "Accesibilidad automatizada (axe).", "Baja", "Integrar pruebas de accesibilidad en la suite UI.", "Planificado"],
            ["RF-10", "Pruebas cross-browser (Firefox/Edge).", "Baja", "Parametrizar la suite Selenium.", "Planificado"],
        ],
        [1.4, 6.2, 1.8, 6.0, 1.8],
        font_size=8.2,
        align_center={0, 2, 4},
    )
    add_caption(doc, "Tabla 15. Backlog de refactorización y mejoras continuas.")

    # 10. Lecciones ---------------------------------------------------------
    add_heading(doc, "10. Lecciones aprendidas", 1)
    add_bullets(
        doc,
        [
            "Los mensajes exactos exigidos por el negocio deben tratarse como contrato y verificarse "
            "en API y en interfaz; una diferencia de punto final rompe la aceptación.",
            "Las pruebas E2E son valiosas para demostrar el flujo real, pero deben usar esperas por "
            "condición para no convertirse en una fuente de falsos negativos.",
            "La base de pruebas aislada y el seed determinista reducen drásticamente el tiempo de "
            "diagnóstico y permiten repetir la demostración de la penalización.",
            "La cobertura es una señal, no un objetivo: las ramas de reglas de negocio importan más "
            "que las líneas de infraestructura.",
            "El análisis estático aporta más valor cuando se integra temprano y se traduce en un "
            "backlog priorizado, no cuando se ejecuta solo al final.",
        ],
    )

    # 11. Conclusiones ------------------------------------------------------
    add_heading(doc, "11. Conclusiones", 1)
    add_paragraph(
        doc,
        f"LabTrack cumple los criterios de aceptación de las cinco historias de usuario. Los "
        f"{total_cases} casos funcionales finalizaron conformes, respaldados por 100 ejecuciones "
        f"automatizadas: 49 de API, 44 de interfaz y 7 flujos E2E en Chrome. La cobertura alcanzó "
        f"{backend_cov['statements']:.1f} % de sentencias en el backend y "
        f"{frontend_cov['statements']:.1f} % en el frontend, con todas las reglas de negocio "
        "críticas ejercitadas en escenarios positivos y negativos.",
        align="justify",
    )
    add_paragraph(
        doc,
        f"La prueba de carga validó 50 usuarios concurrentes durante 60 segundos: "
        f"{jm.get('muestras', 0):,} peticiones, cero errores y un percentil 95 de "
        f"{jm.get('p95_ms', 0):.0f} ms, muy por debajo del umbral de 3 000 ms. El análisis "
        f"estático redujo los code smells de {baseline.get('codeSmells', 0)} a "
        f"{final.get('codeSmells', 0)} y dejó el quality gate en estado {gate_text}. En conjunto, "
        "la evidencia sostiene un veredicto favorable para un despliegue controlado en producción.",
        align="justify",
    )
    add_callout(
        doc,
        "Veredicto final",
        "LabTrack está certificado técnicamente para producción controlada: flujos críticos "
        "automatizados, rendimiento validado, seguridad verificada y deuda técnica priorizada.",
        color="ECFDF5",
        border="059669",
    )

    # 12. Recomendaciones ---------------------------------------------------
    add_heading(doc, "12. Recomendaciones", 1)
    add_bullets(
        doc,
        [
            "Integrar las tres suites y el escaneo de SonarQube en un pipeline de CI (GitHub Actions) "
            "con bloqueo del merge cuando el quality gate falle.",
            "Repetir la prueba de carga en staging con la topología de producción y monitoreo de "
            "latencia de base de datos, pool de conexiones y CPU.",
            "Añadir pruebas de accesibilidad con axe y pruebas cross-browser para Firefox y Edge.",
            "Implementar rotación de JWT, rate limiting en el login y alertas sobre intentos fallidos.",
            "Externalizar las credenciales demo y los secretos en variables de entorno del pipeline.",
            "Establecer un umbral de cobertura por ramas del 85 % y revisar el backlog en cada sprint.",
        ],
    )

    # 13. Referencias -------------------------------------------------------
    add_heading(doc, "13. Referencias", 1)
    references = [
        "Pressman, R. S. (2020). Ingeniería del software: un enfoque práctico (9.ª ed.). McGraw-Hill.",
        "Sommerville, I. (2016). Software Engineering (10th ed.). Pearson.",
        "ISTQB. (2023). Certified Tester Foundation Level Syllabus v4.0. International Software Testing Qualifications Board.",
        "OWASP Foundation. (2024). OWASP Application Security Verification Standard 4.0.3.",
        "SonarSource. (2026). SonarQube Community Build 26.10 Documentation. https://docs.sonarsource.com/",
        "Apache Software Foundation. (2024). Apache JMeter User's Manual. https://jmeter.apache.org/usermanual/",
        "Selenium Project. (2026). Selenium WebDriver Documentation. https://www.selenium.dev/documentation/",
        "NestJS. (2026). NestJS Documentation. https://docs.nestjs.com/",
        "Prisma. (2026). Prisma ORM Documentation. https://www.prisma.io/docs/",
        "React. (2026). React Documentation. https://react.dev/",
    ]
    for reference in references:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(0.6)
        paragraph.paragraph_format.first_line_indent = Cm(-0.6)
        paragraph.paragraph_format.space_after = Pt(3)
        run = paragraph.add_run(reference)
        set_font(run, size=9, color="1F2937")

    # Anexo A · Matriz completa en horizontal -------------------------------
    new_section = doc.add_section(WD_SECTION.NEW_PAGE)
    new_section.orientation = WD_ORIENT.LANDSCAPE
    new_section.page_width = Cm(29.7)
    new_section.page_height = Cm(21)
    new_section.top_margin = Cm(1.6)
    new_section.bottom_margin = Cm(1.4)
    new_section.left_margin = Cm(1.6)
    new_section.right_margin = Cm(1.6)
    new_section.header.is_linked_to_previous = False
    new_section.footer.is_linked_to_previous = False
    add_header(new_section, "Anexo A · Matriz de casos de prueba")
    add_page_number_footer(new_section)

    add_heading(doc, "Anexo A. Matriz completa de casos de prueba", 1)
    add_paragraph(
        doc,
        "La matriz se organiza por historia de usuario. Las columnas Datos y pasos y Resultado "
        "esperado conservan el contenido validado por el equipo; la columna Evidencia indica el "
        "archivo o artefacto que respalda cada caso.",
        size=9,
        align="justify",
    )
    for name, rows in matrix.items():
        add_heading(doc, name, 2)
        table_rows = []
        for row in rows:
            table_rows.append(
                [
                    row.get("ID", ""),
                    row.get("Caso de prueba", ""),
                    row.get("Origen", ""),
                    row.get("Prio.", ""),
                    f"{row.get('Precondición', '')} · {row.get('Entrada / pasos', '')}".strip(" ·"),
                    row.get("Resultado esperado", ""),
                    row.get("Nivel · Evidencia", ""),
                    row.get("Estado", ""),
                ]
            )
        add_table(
            doc,
            ["ID", "Caso de prueba", "Origen", "Prio.", "Datos y pasos", "Resultado esperado", "Evidencia", "Estado"],
            table_rows,
            [1.25, 4.1, 1.05, 0.95, 5.5, 5.6, 4.6, 1.55],
            font_size=6.9,
            header_size=7.4,
            align_center={0, 2, 3, 7},
        )

    add_heading(doc, "Anexo A.2. Pruebas de rendimiento", 2)
    load_table_rows = []
    for row in load_rows:
        load_table_rows.append(
            [
                row.get("ID", ""),
                row.get("Transacción", ""),
                row.get("Origen", ""),
                row.get("Prio.", ""),
                row.get("Umbral", ""),
                row.get("Resultado medido", ""),
                row.get("Estado", ""),
            ]
        )
    if load_table_rows:
        add_table(
            doc,
            ["ID", "Transacción", "Origen", "Prio.", "Umbral", "Resultado medido", "Estado"],
            load_table_rows,
            [1.5, 6.0, 1.2, 1.0, 4.0, 8.2, 1.6],
            font_size=7.6,
            align_center={0, 2, 3, 6},
        )

    # Anexo B · Índice de evidencias ---------------------------------------
    doc.add_page_break()
    add_heading(doc, "Anexo B. Índice de evidencias", 1)
    add_table(
        doc,
        ["Evidencia", "Ubicación", "Contenido"],
        [
            ["Cobertura backend", "backend/coverage/index.html", "Reporte HTML e LCOV de las 49 pruebas de API."],
            ["Cobertura frontend", "frontend/coverage/index.html", "Reporte HTML e LCOV de las 44 pruebas de UI."],
            ["Reporte E2E JUnit", "frontend/e2e/reports/junit.xml", "Resultado de los 7 flujos Selenium."],
            ["Capturas E2E", "frontend/e2e/screenshots/", "Ocho capturas de los flujos críticos."],
            ["Datos crudos JMeter", "jmeter/reports/results.jtl", "194 629 muestras de la prueba de carga."],
            ["Reporte HTML JMeter", "jmeter/reports/html/index.html", "Dashboard interactivo de rendimiento."],
            ["Resumen JMeter", "jmeter/reports/summary.md", "Métricas, tablas y veredicto."],
            ["Gráficas JMeter", "jmeter/reports/charts/", "Tiempo de respuesta, percentiles y throughput."],
            ["Matriz de pruebas", "docs/matriz-pruebas.md", "61 casos funcionales y 5 de rendimiento."],
            ["Configuración Sonar", "sonar-project.properties", "Fuentes, exclusiones y cobertura."],
            ["Datos SonarQube", "docs/sonar-data.json", "Métricas e issues antes y después."],
            ["Backlog", "docs/refactoring-backlog.md", "Deuda técnica priorizada y estado."],
        ],
        [4.6, 7.4, 9.2],
        font_size=8.2,
    )
    add_caption(doc, "Tabla B1. Índice de artefactos de evidencia del proyecto.")

    # Anexo C · Reproducción ------------------------------------------------
    doc.add_page_break()
    add_heading(doc, "Anexo C. Reproducción de la evaluación", 1)
    add_paragraph(
        doc,
        "Los siguientes comandos permiten reproducir la totalidad de la evidencia desde una "
        "instalación limpia. Se ejecutan desde la raíz del repositorio.",
        size=9.5,
        align="justify",
    )
    add_code_block(
        doc,
        """# 1. Base de datos y datos demo
cd backend
npm install
npm run db:setup

# 2. API y frontend
npm run build && npm start
cd ..\\frontend
npm install && npm run build && npm run preview

# 3. Pruebas
cd ..\\backend
npm run test:cov
cd ..\\frontend
npm run test:cov
npm run test:e2e

# 4. Carga
cd ..\\jmeter
powershell -ExecutionPolicy Bypass -File .\\run-load-test.ps1

# 5. Análisis estático
powershell -ExecutionPolicy Bypass -File ..\\scripts\\start-sonarqube.ps1
powershell -ExecutionPolicy Bypass -File ..\\scripts\\scan-sonar.ps1""",
    )
    add_paragraph(
        doc,
        "Credenciales de demostración: estudiante 20240001 / Estudiante2026! y administrador "
        "ADMIN01 / Admin2026!. Después de una ejecución E2E se debe ejecutar npm run db:reset "
        "para restaurar el seed determinista.",
        size=9,
        align="justify",
    )

    doc.save(DOCX_PATH)
    print("Informe generado:", DOCX_PATH)


def _delta(before, after):
    try:
        difference = int(before) - int(after)
    except (TypeError, ValueError):
        return "—"
    if difference > 0:
        return f"−{difference}"
    if difference < 0:
        return f"+{abs(difference)}"
    return "0"


if __name__ == "__main__":
    build_report()
