"""Genera el documento independiente de evidencias del T3 de LabTrack."""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


BASE = Path(__file__).resolve().parent
DOCX_PATH = BASE / "documento-evidencias-t3.docx"
PDF_PATH = BASE / "documento-evidencias-t3.pdf"
FONT = "Arial"
BLUE = "1F4E79"
LIGHT_BLUE = "D9EAF7"
GRAY = "666666"


def set_font(run, size=11, bold=False, italic=False, color=None):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def shade(cell, color=LIGHT_BLUE):
    properties = cell._tc.get_or_add_tcPr()
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), color)
    properties.append(element)


def set_cell_text(cell, text, bold=False, size=9):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(str(text))
    set_font(run, size=size, bold=bold)


def add_table(doc, headers, rows, font_size=8.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for cell, header in zip(table.rows[0].cells, headers):
        shade(cell, BLUE)
        set_cell_text(cell, header, bold=True, size=font_size)
        for run in cell.paragraphs[0].runs:
            run.font.color.rgb = RGBColor(255, 255, 255)
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            set_cell_text(cell, value, size=font_size)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_heading(doc, text, level=1):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(text)
    set_font(run, size=15 if level == 1 else 12, bold=True, color=BLUE)
    return paragraph


def add_text(doc, text, bold=False, italic=False):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.08
    paragraph.paragraph_format.space_after = Pt(5)
    run = paragraph.add_run(text)
    set_font(run, bold=bold, italic=italic)
    return paragraph


def add_bullet(doc, text):
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(2)
    run = paragraph.add_run(text)
    set_font(run)
    return paragraph


def add_figure(doc, path, caption, context, number):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe la evidencia requerida: {path}")
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(1)
    paragraph.paragraph_format.keep_with_next = True
    with Image.open(path) as image:
        width, height = image.size
    scale = min(Cm(15.7) / width, Cm(21) / height)
    paragraph.add_run().add_picture(str(path), width=int(width * scale), height=int(height * scale))
    caption_paragraph = doc.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.space_after = Pt(1)
    caption_paragraph.paragraph_format.keep_with_next = True
    caption_paragraph.paragraph_format.keep_together = True
    caption_run = caption_paragraph.add_run(f"Figura {number}. {caption}")
    set_font(caption_run, size=9, italic=True, color=GRAY)
    context_paragraph = doc.add_paragraph()
    context_paragraph.paragraph_format.space_after = Pt(5)
    context_paragraph.paragraph_format.keep_together = True
    context_run = context_paragraph.add_run("Que demuestra: ")
    set_font(context_run, size=9, bold=True, color=BLUE)
    context_run = context_paragraph.add_run(context)
    set_font(context_run, size=9)
    return number + 1


def image_list(folder, pattern="*.png"):
    return sorted(Path(folder).glob(pattern))


def export_pdf(docx_path, pdf_path):
    command = f"""
    $word = $null
    try {{
      $word = New-Object -ComObject Word.Application
      $word.Visible = $false
      $doc = $word.Documents.Open('{docx_path.resolve()}')
      $doc.SaveAs([ref]'{pdf_path.resolve()}', [ref]17)
      $doc.Close()
      Write-Host 'PDF generado'
    }} catch {{
      Write-Host ('PDF no generado vía Word COM: ' + $_.Exception.Message)
    }} finally {{
      if ($word) {{ $word.Quit() }}
    }}
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", command], check=False, timeout=120)
    except (OSError, subprocess.SubprocessError) as error:
        print(f"PDF no generado vía Word COM: {error}")


def configure_document(doc):
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    styles = doc.styles
    styles["Normal"].font.name = FONT
    styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    styles["Normal"].font.size = Pt(11)
    for style_name in ("List Bullet", "List Number"):
        styles[style_name].font.name = FONT
        styles[style_name]._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        styles[style_name].font.size = Pt(11)


def build_document():
    doc = Document()
    configure_document(doc)
    figure = 1

    # 1. Portada
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(80)
    run = title.add_run("LABTRACK")
    set_font(run, size=27, bold=True, color=BLUE)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("DOCUMENTO DE EVIDENCIAS T3")
    set_font(run, size=18, bold=True)
    for line in (
        "Curso: Calidad y Pruebas de Software",
        "Docente: Mark Anthony Arribasplata Palomino",
        "",
        "Integrantes",
        "BOÑON FERNANDEZ Josue Samuel",
        "HERRERA RUITON Jhenifer",
        "QUILICHE CABANILLA Carlos Miguel",
        "RAICO MOYA Frank Jhancarlos",
        "VILLANUEVA COJAL Luis Oswaldo",
    ):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(line)
        set_font(run, size=12, bold=line == "Integrantes")
    doc.add_page_break()

    # 2. Índice
    add_heading(doc, "2. Índice")
    add_text(doc, "Este documento reúne evidencias ejecutadas o conservadas en el repositorio. Cada captura incluye un pie de figura y una explicación para lectores que no conocen LabTrack.")
    for item in (
        "1. Portada",
        "2. Índice",
        "3. Matriz de casos de prueba",
        "4. Evidencias de automatización",
        "5. Resultados de JMeter",
        "6. Análisis de SonarQube",
        "7. Backlog de refactorización",
        "8. Historias de usuario y trazabilidad",
        "9. Accesibilidad",
        "10. Uso de agentes de IA",
    ):
        add_bullet(doc, item)

    # 3. Matriz
    add_heading(doc, "3. Matriz de casos de prueba")
    add_text(doc, "La matriz separa pruebas unitarias, funcionales automatizadas, rendimiento y escenarios sugeridos por IA. El sistema gestiona autenticación, catálogo, reservas, aprobación administrativa y devoluciones.")
    add_table(doc, ["Grupo", "Alcance", "Resultado / estado"], [
        ["Unitarias", "Backend y frontend; límites de reservas y ventanas horarias", "101 pruebas después; 93 antes"],
        ["Funcionales automatizadas", "Login, catálogo, reservas, aprobación y devolución", "Ejecutadas"],
        ["Carga y estrés", "JMeter; 50 y 150 usuarios concurrentes", "Aprobadas; ver sección 5"],
        ["Casos IA", "IA-01 a IA-05", "Validación humana PENDIENTE"],
    ])
    add_text(doc, "La matriz original está en docs/matriz-pruebas.md y la matriz complementaria en docs/evidencias-pruebas/matriz-casos.md. Testomat.io contiene 65 casos importados: 61 passed según CSV y cuatro pending. Los cinco casos de IA de la matriz siguen pendientes de validación humana; el CSV importado solo incluye IA-01 a IA-04. TestLink y Katalon no se ejecutaron.")
    add_table(doc, ["ID", "Caso representativo", "Resultado"], [
        ["U-01", "Reserva contigua no cruza", "Aprobado"],
        ["U-02", "Duración cero es inválida", "Aprobado"],
        ["U-03/U-04", "Mocks defectuosos de duración y cruce", "Falla simulada esperada"],
        ["F-01 a F-05", "Flujos API/UI principales", "Ejecutados"],
        ["F-06", "Flujos E2E Selenium", "Corrida final aprobada"],
    ])

    # 4. Automatización
    add_heading(doc, "4. Evidencias de automatización")
    add_text(doc, "Las pruebas unitarias se ejecutan con Vitest y las funcionales de navegador con Selenium REAL. La corrida inicial tuvo tres fallas asociadas a la regresión S6819; la corrida final conservada terminó 7/7. Las capturas E2E se presentan como evidencia de la corrida registrada.")
    for filename, caption, context in (
        ("01-backend-antes.png", "Pruebas unitarias backend antes", "El backend tenía 49 pruebas distribuidas en cuatro archivos antes de agregar los casos límite."),
        ("02-backend-despues.png", "Pruebas unitarias backend después", "El backend alcanza 53 pruebas aprobadas después de incorporar cuatro casos adicionales."),
        ("03-frontend-antes.png", "Pruebas unitarias frontend antes", "El frontend tenía 44 pruebas antes de la ampliación de cobertura."),
        ("04-frontend-despues.png", "Pruebas unitarias frontend después", "El frontend alcanza 48 pruebas aprobadas."),
        ("05-defectos-simulados-fallan.png", "Defectos simulados en mocks locales", "Los casos it.fails documentan que los mocks defectuosos fallan como se esperaba sin modificar código de producción."),
        ("10-selenium-corrida-1-regresion.png", "Corrida Selenium inicial", "La automatización detectó tres fallas en la corrida afectada por la regresión S6819."),
        ("11-selenium-corrida-3-final.png", "Corrida Selenium final", "La ejecución final conserva el resultado 7/7 pruebas aprobadas."),
    ):
        figure = add_figure(doc, BASE / "evidencias-pruebas" / "capturas" / filename, caption, context, figure)
    add_text(doc, "El comparativo documenta 93 pruebas iniciales frente a 101 finales: backend 49→53 y frontend 44→48. La cobertura real registrada es 95.71 % en backend y 90.26 % en frontend.")
    selenium_dir = BASE / "evidencias-pruebas" / "selenium" / "corrida-3-final-aprobada" / "screenshots"
    for path in image_list(selenium_dir):
        figure = add_figure(doc, path, f"Selenium: {path.stem.replace('-', ' ')}", "La captura muestra un paso verificable del flujo funcional automatizado final.", figure)
    add_heading(doc, "4.1 Gestión de casos en Testomat.io", level=2)
    add_text(doc, "En el proyecto LabTrack T3 se importaron 61 casos CP-01 a CP-61 y cuatro casos IA-01 a IA-04. La corrida Corrida T3 - automatizada (d1058425) conserva 61 passed, 0 failed, 0 skipped y 4 pending. Los resultados se registraron según el CSV; no representan una nueva ejecución de Selenium o Vitest.")
    add_text(doc, "Las suites H e IA contienen 38 y 23 casos de la matriz. Casos sugeridos por IA contiene cuatro casos con Validacion humana: pendiente. IA-05 está propuesto en la matriz, pero no figura en el CSV importado. La corrida permanece abierta: finalizarla convertiría los pending en skipped.")
    add_text(doc, "El primer intento falló con Runtime error Page[Tests] require columns[Folder]. Las copias compatibles conservaron los datos originales y las importaciones finales aceptaron 61 y 4 casos, sin filas rechazadas. La cuenta usa una prueba gratuita Enterprise; la importación en el plan gratuito permanente no fue verificada. TestLink y Katalon no se ejecutaron.")
    for filename, caption, context in (
        ("01-suites.png", "Testomat.io: suites y conteos", "Las tres suites contienen 38, 23 y 4 casos; total importado: 65."),
        ("02-detalle-caso.png", "Testomat.io: detalle de CP-01", "El caso conserva sus precondiciones, pasos y resultado esperado."),
        ("03-run-resumen.png", "Testomat.io: resumen de la corrida", "Los 61 passed proceden de Status Aprobado en el CSV; los cuatro casos de IA siguen pending."),
        ("04-reporte.png", "Testomat.io: estadísticas por suite", "La distribución distingue los 61 aprobados de la matriz y los cuatro casos pendientes de validación."),
        ("05-casos-ia.png", "Testomat.io: casos sugeridos por IA", "Los cuatro casos importados conservan el campo Validacion humana: pendiente."),
    ):
        figure = add_figure(doc, BASE / "evidencias-pruebas" / "testomatio" / filename, caption, context, figure)
    add_text(doc, "Proyecto: https://app.testomat.io/projects/labtrack-t3/. Corrida: https://app.testomat.io/projects/labtrack-t3/runs/d1058425.")

    # 5. JMeter
    add_heading(doc, "5. Resultados de JMeter")
    add_text(doc, "JMeter mide el comportamiento no funcional del backend. Carga usa 50 usuarios concurrentes durante 60 segundos; estrés usa 150 usuarios durante 90 segundos. Los percentiles indican el tiempo bajo el cual termina el porcentaje indicado de solicitudes.")
    add_table(doc, ["Escenario", "Peticiones", "Error", "Promedio", "p95", "Veredicto"], [
        ["Carga (50 usuarios)", "79,424", "0 (0.00 %)", "34.4 ms", "48.0 ms", "Aprobada"],
        ["Estrés (150 usuarios)", "113,600", "0 (0.00 %)", "108.9 ms", "151.0 ms", "Aprobada"],
    ])
    for scenario in ("carga", "estres"):
        folder = BASE / "evidencias-jmeter" / scenario
        label = "carga" if scenario == "carga" else "estrés"
        for filename in (
            "captura-dashboard-resumen.png",
            "captura-percentiles-y-distribucion.png",
            "captura-throughput.png",
            "captura-tiempos-respuesta-en-el-tiempo.png",
        ):
            figure = add_figure(doc, folder / filename, f"JMeter {label}: {filename.replace('.png', '').replace('-', ' ')}", f"El reporte visual documenta las métricas del escenario de {label} ejecutado con JMeter.", figure)
        for path in image_list(folder / "charts"):
            figure = add_figure(doc, path, f"JMeter {label}: gráfico {path.stem}", "El gráfico permite interpretar tiempos, percentiles, throughput o errores del escenario.", figure)
    add_text(doc, "En carga el p95 de 48.0 ms está bajo el SLA de 3,000 ms y en estrés el p95 de 151.0 ms está bajo el SLA de 5,000 ms. Ambos escenarios registran 0.00 % de error.")

    # 6. SonarQube
    add_heading(doc, "6. Análisis de SonarQube")
    add_text(doc, "SonarQube analiza el código sin ejecutar la aplicación y clasifica bugs, vulnerabilidades y code smells. Los escaneos se ejecutaron en localhost:9000. El ANTES es código REPRODUCIDO porque el repositorio tiene un solo commit; no es una versión histórica recuperada.")
    add_table(doc, ["Métrica", "ANTES", "DESPUÉS", "Cambio"], [
        ["Bugs", "1", "0", "-1"],
        ["Vulnerabilidades", "2", "0", "-2"],
        ["Code smells", "41", "0", "-41"],
        ["Issues abiertos", "44", "0", "-44"],
        ["Confiabilidad / Seguridad / Mantenibilidad", "B / C / A", "A / A / A", "Mejora"],
        ["Quality Gate", "OK", "OK", "Igual"],
    ])
    before = BASE / "evidencias-sonarqube" / "antes" / "capturas-reales"
    after = BASE / "evidencias-sonarqube" / "despues" / "capturas-reales"
    before_context = "La captura es real del proyecto labtrack-antes y documenta el estado inicial reproducido con sus hallazgos."
    after_context = "La captura es real del proyecto labtrack-despues y documenta el estado final sin issues abiertos."
    for path in image_list(before):
        figure = add_figure(doc, path, f"SonarQube ANTES: {path.stem.replace('-', ' ')}", before_context, figure)
    add_text(doc, "Las capturas por regla del ANTES muestran un error concreto con el código marcado. Las reglas representativas incluyen S1082, S2068, S2245, S3358, S3776, S6759, S6819, S6847, S7718 y S9379.")
    for path in image_list(before / "por-regla"):
        figure = add_figure(doc, path, f"SonarQube ANTES por regla: {path.stem}", "La captura identifica la regla y el fragmento de código que originaba el issue.", figure)
    for path in image_list(after):
        figure = add_figure(doc, path, f"SonarQube DESPUÉS: {path.stem.replace('-', ' ')}", after_context, figure)
    for path in image_list(after / "por-regla"):
        figure = add_figure(doc, path, f"SonarQube DESPUÉS por regla: {path.stem}", "La captura confirma que la regla corregida ya no tiene issues en el escaneo final.", figure)
    chart = BASE / "evidencias-sonarqube" / "comparacion" / "real" / "grafico-comparativo-real.png"
    figure = add_figure(doc, chart, "Comparación real de SonarQube", "El gráfico resume la reducción de 44 issues del ANTES a cero en el DESPUÉS.", figure)
    add_text(doc, "La diferencia entre la línea base histórica 2 bugs/2 vulnerabilidades/40 smells y el escaneo real 1/2/41 se explica en la documentación por la versión y reglas de SonarQube. El total real comparable es 44 frente a 0.")

    # 7. Backlog
    add_heading(doc, "7. Backlog de refactorización")
    add_text(doc, "El backlog de docs/refactoring-backlog.md registra la deuda técnica, su prioridad, módulo afectado, solución y evidencia de cierre. Las correcciones SonarQube se verificaron con el escaneo final y las suites automatizadas.")
    add_table(doc, ["Área", "Ejemplos", "Estado / evidencia"], [
        ["Accesibilidad semántica", "S1082, S6819, S6847", "Completado; reglas sin issues"],
        ["Complejidad y legibilidad", "S3358, S3776, S7718", "Completado; SonarQube DESPUÉS"],
        ["Seguridad", "S2068, S2245", "Completado; 0 vulnerabilidades"],
        ["Inmutabilidad React", "S6759", "Completado; 14 issues eliminadas"],
        ["Brechas funcionales", "HU sin evidencia verificable", "Pendiente, trazadas en sección 8"],
    ])

    # 8. Trazabilidad
    add_heading(doc, "8. Historias de usuario y trazabilidad")
    add_text(doc, "La trazabilidad contrasta las historias declaradas con archivos y pruebas encontrados. De las 12 historias declaradas, 7 quedan sin evidencia verificable completa; se conservan como brechas y no como funcionalidades demostradas.")
    add_table(doc, ["Estado", "Cantidad", "Interpretación"], [
        ["Implementada con pruebas", "5", "Existe código y pruebas asociadas"],
        ["Sin evidencia verificable completa", "7 de 12", "La declaración no basta para afirmar cobertura"],
    ])
    add_text(doc, "La matriz detallada, criterios de aceptación, archivos y pruebas se encuentra en docs/trazabilidad-historias-usuario.md. Las brechas deben permanecer en el backlog hasta contar con evidencia reproducible.")

    alignment_note = next(line.removeprefix("> ") for line in (BASE / "historias-usuario-implementadas.md").read_text(encoding="utf-8").splitlines() if line.startswith("> Nota de alineacion:"))
    add_text(doc, alignment_note)
    add_text(doc, "HU-BR-01: Resuelto por alineacion documental, prioridad Baja. HU-01 usa código de estudiante de 8 dígitos (20240001), código alfanumérico ADMIN01 para el administrador y bloqueo de 5 minutos tras 3 fallos. HU-05 conserva la brecha de duración de 7 días no modelada; HU-06, 07, 08, 11, 13, 14 y 15 siguen sin evidencia completa.")

    # 9. Accesibilidad
    add_heading(doc, "9. Accesibilidad")
    add_text(doc, "Se ejecutó axe-core 4.10.2 sobre login y catálogo. No se ejecutó la extensión WAVE.")
    add_table(doc, ["Pantalla", "Reglas aprobadas", "Violaciones", "Hallazgo"], [
        ["Login", "19", "1 serious", "color-contrast en 1 elemento"],
        ["Catálogo", "17", "1 regla serious", "color-contrast en 17 elementos"],
    ])
    add_text(doc, "No se detectaron fallas estructurales de etiquetas, roles, nombres accesibles o teclado. El hallazgo pendiente es contraste insuficiente en textos secundarios, registrado en el backlog con objetivo de razón mínima 4.5:1.")

    # 10. IA
    add_heading(doc, "10. Uso de agentes de IA")
    add_text(doc, "El trabajo fue coordinado por agentes en worktrees separados. Se usaron herramientas para análisis estático, pruebas unitarias, Selenium, JMeter y axe-core. La documentación de prompts y reparto está en docs/prompts-y-skills-agentes.md.")
    add_table(doc, ["Actividad", "Evidencia"], [
        ["Análisis SonarQube", "Capturas reales, JSON y tabla ANTES/DESPUÉS"],
        ["Pruebas unitarias", "Logs, cobertura y comparativo 93→101"],
        ["Automatización funcional", "Selenium real, corrida final 7/7"],
        ["Rendimiento", "JMeter carga/estrés con tablas y gráficos"],
        ["Escenarios exploratorios", "IA-01 a IA-05; validación humana PENDIENTE"],
    ])
    add_text(doc, "La IA se empleó para acelerar documentación, exploración y coordinación, pero los resultados se conservaron únicamente cuando existía evidencia en archivos o capturas del repositorio.")

    # Footer
    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = footer.add_run("LabTrack · Documento de evidencias T3")
        set_font(run, size=8, color=GRAY)

    doc.save(DOCX_PATH)
    export_pdf(DOCX_PATH, PDF_PATH)
    print(f"DOCX generado: {DOCX_PATH}")
    print(f"Figuras insertadas: {figure - 1}")
    if PDF_PATH.exists():
        print(f"PDF generado: {PDF_PATH}")
    else:
        print("PDF no generado: Word COM no está disponible.")


if __name__ == "__main__":
    build_document()
