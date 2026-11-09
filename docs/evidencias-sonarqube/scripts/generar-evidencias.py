"""Genera las evidencias documentales de SonarQube para LabTrack.

Lee docs/sonar-baseline.json (ANTES) y docs/sonar-data.json (DESPUES/final) y
produce, dentro de docs/evidencias-sonarqube:

  antes/api/*.json, despues/api/*.json     respuestas con forma de API de SonarQube
  antes/logs/*.log, despues/logs/*.log     transcripcion del intento de escaneo
  comparacion/tabla-comparativa.md         tabla Metrica | Antes | Despues | Mejora
  comparacion/comparacion.json             datos de la comparacion
  render/*.html                            paneles que luego se capturan con Playwright

Ningun JSON de este script es una respuesta nueva del servidor: son
reconstrucciones etiquetadas a partir de las instantaneas historicas.
"""

from __future__ import annotations

import html
import json
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "docs" / "evidencias-sonarqube"
RENDER = BASE / "render"

HOST = "http://localhost:9000"
COMMIT = "840052e769ac7386f458d9cac2332d6a4dd2d50d"
COMMIT_SHORT = "840052e"
COMMIT_DATE = "2026-11-09 13:15:16 -0500"
CAPTURE_DATE = "2026-11-09"
SONAR_VERSION = "SonarQube Community Build 26.10 · SonarScanner CLI 8.3.1"
RATING = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}
RATING_VALUE = {value: key for key, value in RATING.items()}

ISSUE_ORDER = ["BUG", "VULNERABILITY", "CODE_SMELL"]
TYPE_LABEL = {"BUG": "Bug", "VULNERABILITY": "Vulnerabilidad", "CODE_SMELL": "Code Smell"}


def load() -> tuple[dict, dict]:
    baseline = json.loads((ROOT / "docs" / "sonar-baseline.json").read_text(encoding="utf-8"))
    combined = json.loads((ROOT / "docs" / "sonar-data.json").read_text(encoding="utf-8"))
    return baseline, combined["final"]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def measures_payload(key: str, name: str, data: dict) -> dict:
    measures = [
        {"metric": "bugs", "value": str(data["bugs"])},
        {"metric": "vulnerabilities", "value": str(data["vulnerabilities"])},
        {"metric": "code_smells", "value": str(data["codeSmells"])},
        {"metric": "coverage", "value": f"{data['coverage']}"},
        {"metric": "duplicated_lines_density", "value": f"{data['duplications']}"},
        {"metric": "reliability_rating", "value": RATING_VALUE[data["reliabilityRating"]]},
        {"metric": "security_rating", "value": RATING_VALUE[data["securityRating"]]},
        {"metric": "sqale_rating", "value": RATING_VALUE[data["maintainabilityRating"]]},
        {"metric": "ncloc", "value": str(data["linesOfCode"])},
        {"metric": "complexity", "value": str(data["complexity"])},
        {"metric": "cognitive_complexity", "value": str(data["cognitiveComplexity"])},
    ]
    return {
        "reconstruido": True,
        "fuente": "docs/sonar-baseline.json" if key.endswith("antes") else "docs/sonar-data.json#final",
        "nota": "Respuesta con forma de api/measures/component reconstruida desde una instantanea historica. NO es un escaneo nuevo.",
        "proyecto": key,
        "capturado": CAPTURE_DATE,
        "commit": COMMIT,
        "component": {"key": key, "name": name, "qualifier": "TRK", "measures": measures},
    }


def issues_payload(key: str, data: dict, source: str) -> dict:
    issues = []
    for number, issue in enumerate(data["issues"], start=1):
        issues.append(
            {
                "key": f"{key.upper()}-{number:03d}",
                "rule": issue["rule"],
                "severity": issue["severity"],
                "type": issue["type"],
                "component": f"{key}:{issue['component']}",
                "textRange": {"startLine": issue["line"]},
                "message": issue["message"],
                "effort": issue["effort"],
                "status": "OPEN",
            }
        )
    return {
        "reconstruido": True,
        "fuente": source,
        "nota": "Respuesta con forma de api/issues/search reconstruida desde una instantanea historica. NO es un escaneo nuevo.",
        "proyecto": key,
        "capturado": CAPTURE_DATE,
        "commit": COMMIT,
        "p": 1,
        "ps": 500,
        "total": len(issues),
        "issues": issues,
    }


def gate_payload(key: str, data: dict, source: str) -> dict:
    return {
        "reconstruido": True,
        "fuente": source,
        "nota": "Respuesta con forma de api/qualitygates/project_status reconstruida. NO es un escaneo nuevo.",
        "projectStatus": {
            "status": data["qualityGate"],
            "conditions": [
                {
                    "metricKey": condition["metric"],
                    "status": condition["status"],
                    "actualValue": condition["actual"],
                    "errorThreshold": condition["threshold"],
                }
                for condition in data["conditions"]
            ],
        },
    }


def scan_log(state: str, key: str, source: str) -> str:
    if state == "antes":
        extra = (
            "$ sonar-scanner -Dsonar.host.url=http://localhost:9000 \\\n"
            "    -Dsonar.projectKey=labtrack-antes \\\n"
            "    -Dsonar.projectName=\"LabTrack ANTES (reproducido)\" \\\n"
            "    -Dsonar.sources=docs/evidencias-sonarqube/antes/src"
        )
    else:
        extra = (
            "$ sonar-scanner -Dsonar.host.url=http://localhost:9000 \\\n"
            "    -Dsonar.projectKey=labtrack-despues \\\n"
            "    -Dsonar.sources=backend/src,frontend/src"
        )
    return f"""== LabTrack · evidencia SonarQube · {state.upper()} ==
Fecha de la comprobacion: {CAPTURE_DATE}
Proyecto solicitado: {key}
Host esperado: {HOST}
Herramienta esperada: {SONAR_VERSION}
Fuente de datos usada: {source}

[1] Estado del servidor
$ Invoke-WebRequest {HOST}/api/system/status
ERROR: No es posible conectar con el servidor remoto.

[2] Credencial
SONAR_TOKEN: NO definido en el entorno
instance/sonar-token.txt: no existe
(El token nunca se escribe en archivos ni en logs.)

[3] Scanner
tools/sonar-scanner-8.3.1.16491-windows-x64/bin/sonar-scanner.bat: no existe
sonar-scanner en PATH: no encontrado

[4] Comando previsto (no ejecutado)
{extra}

[5] Resultado
ESCANEO NO EJECUTADO. Servidor SonarQube no disponible, sin token y sin scanner.
No se creo ninguna tarea en el Compute Engine.
Se usan las instantaneas historicas {source} y se etiquetan como
{'ANTES REPRODUCIDO' if state == 'antes' else 'DESPUES (instantanea historica)'}.
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, kicker: str, state: str, body: str) -> str:
    tone = "warning" if state == "antes" else "info"
    banner = (
        "ANTES REPRODUCIDO — Código reconstruido y métricas tomadas de docs/sonar-baseline.json. "
        "NO es una captura histórica de SonarQube ni un escaneo nuevo."
        if state == "antes"
        else "DESPUÉS — Métricas tomadas de docs/sonar-data.json (estado final). "
        "NO es un escaneo nuevo: SonarQube no estaba disponible."
    )
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{esc(title)}</title>
<style>
  :root {{ --ink:#0f172a; --muted:#5b6b82; --line:#dfe6ee; --teal:#0f766e; --navy:#16233a; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#eef3f8; color:var(--ink);
         font-family:"Segoe UI",system-ui,-apple-system,sans-serif; }}
  .page {{ width:1240px; margin:0 auto; padding:26px 32px 30px; }}
  .top {{ display:flex; justify-content:space-between; align-items:flex-start;
          gap:20px; border-bottom:2px solid #cdd8e5; padding-bottom:14px; }}
  .kicker {{ font-size:12px; letter-spacing:.18em; text-transform:uppercase;
             color:var(--teal); font-weight:700; }}
  h1 {{ margin:6px 0 4px; font-size:27px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .brand {{ font-size:12px; font-weight:800; letter-spacing:.12em; text-transform:uppercase;
            color:var(--navy); text-align:right; }}
  .brand small {{ display:block; color:var(--muted); font-weight:600; letter-spacing:.02em;
                  text-transform:none; margin-top:4px; }}
  .banner {{ margin:16px 0 6px; padding:11px 14px; border-radius:10px; font-size:12.5px;
             font-weight:600; border:1px solid; }}
  .banner.warning {{ background:#fff7e6; border-color:#f2c66d; color:#7a4a05; }}
  .banner.info {{ background:#eaf3ff; border-color:#b7d2f5; color:#1d4c8c; }}
  .meta {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:14px 0 18px; }}
  .meta div {{ background:#fff; border:1px solid var(--line); border-radius:10px;
               padding:9px 11px; font-size:11.5px; color:var(--muted); }}
  .meta b {{ display:block; color:var(--ink); font-size:12.5px; margin-top:3px;
             font-family:Consolas,monospace; font-weight:600; }}
  .kpis {{ display:grid; grid-template-columns:repeat(6,1fr); gap:11px; margin-bottom:16px; }}
  .kpi {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:12px 14px; }}
  .kpi span {{ display:block; font-size:11px; text-transform:uppercase; letter-spacing:.09em;
               color:var(--muted); font-weight:700; }}
  .kpi b {{ display:block; font-size:32px; line-height:1.15; margin-top:4px; letter-spacing:-.03em; }}
  .kpi small {{ color:var(--muted); font-size:11px; }}
  .kpi.bad b {{ color:#b42318; }}
  .kpi.good b {{ color:#067647; }}
  h2 {{ font-size:17px; margin:22px 0 10px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; font-size:12.3px;
           border:1px solid var(--line); border-radius:10px; overflow:hidden; }}
  th {{ background:var(--navy); color:#fff; text-align:left; padding:8px 9px; font-size:11.5px;
        text-transform:uppercase; letter-spacing:.05em; }}
  td {{ padding:6px 9px; border-bottom:1px solid var(--line); vertical-align:top; }}
  tr:nth-child(even) td {{ background:#f7fafd; }}
  .rule {{ font-family:Consolas,monospace; color:var(--teal); font-weight:700; white-space:nowrap; }}
  .file {{ font-family:Consolas,monospace; color:#2b3a52; }}
  .pill {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:10.5px;
           font-weight:700; text-transform:uppercase; letter-spacing:.05em; }}
  .pill.bug {{ background:#fee4e2; color:#b42318; }}
  .pill.vuln {{ background:#fde7d9; color:#9a3412; }}
  .pill.smell {{ background:#e8eefc; color:#2f4b8f; }}
  .pill.ok {{ background:#dcfae6; color:#067647; }}
  .ratings {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }}
  .rating {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:18px;
             display:flex; align-items:center; gap:16px; }}
  .grade {{ width:64px; height:64px; border-radius:14px; display:grid; place-items:center;
            font-size:32px; font-weight:800; color:#fff; }}
  .grade.A {{ background:#0e8a5f; }} .grade.B {{ background:#7aa62b; }}
  .grade.C {{ background:#d98b16; }} .grade.D {{ background:#c2570f; }} .grade.E {{ background:#b42318; }}
  .rating p {{ margin:2px 0; color:var(--muted); font-size:12px; }}
  .rating b {{ font-size:14px; }}
  .cards {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
  .card {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:14px; }}
  .card span {{ color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.08em;
                font-weight:700; }}
  .card b {{ display:block; font-size:28px; margin-top:4px; }}
  .delta-down {{ color:#067647; font-weight:800; }}
  .delta-flat {{ color:#8a6d1f; font-weight:800; }}
  .bar-row {{ display:grid; grid-template-columns:210px 1fr 90px; align-items:center;
              gap:12px; margin:9px 0; }}
  .bar-label {{ font-size:12.5px; font-weight:600; }}
  .bar-track {{ background:#edf2f8; border-radius:6px; height:26px; overflow:hidden; }}
  .bar {{ height:100%; border-radius:6px; }}
  .bar.antes {{ background:#b42318; }} .bar.despues {{ background:#0e8a5f; }}
  .bar-value {{ font-family:Consolas,monospace; font-weight:700; font-size:12.5px; }}
  .legend {{ display:flex; gap:18px; font-size:12px; color:var(--muted); margin:6px 0 14px; }}
  .dot {{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; }}
  .note {{ background:#fff; border-left:4px solid #b7d2f5; border-radius:8px; padding:11px 14px;
           color:var(--muted); font-size:12px; margin-top:14px; }}
  ul {{ margin:8px 0 0; padding-left:18px; color:var(--muted); font-size:12.5px; }}
  footer {{ margin-top:22px; padding-top:12px; border-top:1px solid #cdd8e5;
            color:var(--muted); font-size:11px; display:flex; justify-content:space-between; }}
  .empty {{ background:#fff; border:1px dashed #b8c6d8; border-radius:12px; padding:34px;
            text-align:center; color:var(--muted); font-size:13px; }}
</style></head>
<body><div class="page">
  <div class="top">
    <div><div class="kicker">{esc(kicker)}</div><h1>{esc(title)}</h1>
      <div class="sub">{esc(SONAR_VERSION)}</div></div>
    <div class="brand">LabTrack<small>Calidad y Pruebas de Software</small></div>
  </div>
  <div class="banner {tone}">{esc(banner)}</div>
  {body}
  <footer><span>Captura local: {CAPTURE_DATE} · commit {COMMIT_SHORT}</span>
  <span>docs/evidencias-sonarqube · datos: sonar-baseline.json / sonar-data.json</span></footer>
</div></body></html>
"""


def meta_strip(key: str, state_label: str, source: str) -> str:
    return f"""<div class="meta">
  <div>Proyecto<b>{esc(key)}</b></div>
  <div>Estado<b>{esc(state_label)}</b></div>
  <div>Commit<b>{COMMIT_SHORT} · {esc(COMMIT_DATE)}</b></div>
  <div>Fuente<b>{esc(source)}</b></div>
</div>"""


def kpis(data: dict) -> str:
    return f"""<div class="kpis">
  <div class="kpi {'bad' if data['bugs'] else 'good'}"><span>Bugs</span><b>{data['bugs']}</b><small>fiabilidad</small></div>
  <div class="kpi {'bad' if data['vulnerabilities'] else 'good'}"><span>Vulnerabilidades</span><b>{data['vulnerabilities']}</b><small>seguridad</small></div>
  <div class="kpi {'bad' if data['codeSmells'] else 'good'}"><span>Code Smells</span><b>{data['codeSmells']}</b><small>mantenibilidad</small></div>
  <div class="kpi"><span>Líneas (ncloc)</span><b>{data['linesOfCode']}</b><small>código analizado</small></div>
  <div class="kpi"><span>Cobertura</span><b>{data['coverage']}%</b><small>histórica</small></div>
  <div class="kpi"><span>Duplicación</span><b>{data['duplications']}%</b><small>líneas duplicadas</small></div>
</div>"""


def ratings_block(data: dict) -> str:
    rows = [
        ("Confiabilidad", data["reliabilityRating"], "Bugs abiertos y severidad"),
        ("Seguridad", data["securityRating"], "Vulnerabilidades abiertas"),
        ("Mantenibilidad", data["maintainabilityRating"], "Deuda técnica y code smells"),
    ]
    cards = "".join(
        f'<div class="rating"><div class="grade {r}">{r}</div>'
        f'<div><b>{esc(title)}</b><p>Rating {r}</p><p>{esc(detail)}</p></div></div>'
        for title, r, detail in rows
    )
    return f'<div class="ratings">{cards}</div>'


def gate_block(data: dict) -> str:
    status = data["qualityGate"]
    rows = data["conditions"]
    if rows:
        body = "".join(
            f"<tr><td class='rule'>{esc(c['metric'])}</td>"
            f"<td><span class='pill {'ok' if c['status'] == 'OK' else 'bug'}'>{esc(c['status'])}</span></td>"
            f"<td>{esc(c['actual'])}</td><td>{esc(c['threshold'])}</td></tr>"
            for c in rows
        )
        table = (
            "<table><thead><tr><th>Condición</th><th>Estado</th><th>Valor</th>"
            f"<th>Umbral</th></tr></thead><tbody>{body}</tbody></table>"
        )
    else:
        table = (
            '<div class="empty">La instantánea histórica no registró condiciones '
            "de quality gate (lista vacía). El estado global fue OK.</div>"
        )
    return (
        f'<div class="cards" style="grid-template-columns:1fr 1fr 1fr;margin-bottom:14px">'
        f'<div class="card"><span>Quality Gate</span><b><span class="pill '
        f'{"ok" if status == "OK" else "bug"}">{esc(status)}</span></b></div>'
        f'<div class="card"><span>Condiciones registradas</span><b>{len(rows)}</b></div>'
        f'<div class="card"><span>Issues abiertos</span><b>{len(data["issues"])}</b></div></div>'
        + table
    )


def issue_rows(issues: list[dict], limit: int | None = None) -> str:
    selected = issues if limit is None else issues[:limit]
    out = []
    for issue in selected:
        rule = issue["rule"].split(":", 1)[-1]
        pill = {"BUG": "bug", "VULNERABILITY": "vuln", "CODE_SMELL": "smell"}[issue["type"]]
        out.append(
            f"<tr><td><span class='pill {pill}'>{esc(issue['type'])}</span></td>"
            f"<td class='rule'>{esc(rule)}</td><td class='file'>{esc(issue['component'])}"
            f":{esc(issue['line'])}</td><td>{esc(issue['severity'])}</td>"
            f"<td>{esc(issue['message'])}</td></tr>"
        )
    return "".join(out)


def issues_table(issues: list[dict]) -> str:
    if not issues:
        return '<div class="empty">Sin issues abiertos en la instantánea.</div>'
    return (
        "<table><thead><tr><th>Tipo</th><th>Regla</th><th>Archivo:línea</th>"
        f"<th>Severidad</th><th>Mensaje</th></tr></thead><tbody>{issue_rows(issues)}</tbody></table>"
    )


def smell_cards(issues: list[dict]) -> str:
    counts = Counter(issue["rule"].split(":", 1)[-1] for issue in issues if issue["type"] == "CODE_SMELL")
    files = Counter(issue["component"] for issue in issues if issue["type"] == "CODE_SMELL")
    top = "".join(
        f'<div class="card"><span>{esc(rule)}</span><b>{count}</b>'
        f"<small>{esc(next(i['message'] for i in issues if i['rule'].endswith(':' + rule))[:70])}…</small></div>"
        for rule, count in counts.most_common(4)
    )
    file_rows = "".join(
        f"<tr><td class='file'>{esc(name)}</td><td>{count}</td></tr>"
        for name, count in files.most_common()
    )
    return (
        f'<div class="cards" style="grid-template-columns:repeat(4,1fr);margin-bottom:14px">{top}</div>'
        f"<table><thead><tr><th>Archivo</th><th>Code smells</th></tr></thead><tbody>{file_rows}</tbody></table>"
    )


def build_pages(antes: dict, despues: dict) -> None:
    RENDER.mkdir(parents=True, exist_ok=True)
    config = {
        "antes": (
            "labtrack-antes",
            "ANTES REPRODUCIDO",
            "docs/sonar-baseline.json",
            antes,
            "warning",
        ),
        "despues": (
            "labtrack-despues",
            "DESPUÉS (instantánea histórica)",
            "docs/sonar-data.json · final",
            despues,
            "info",
        ),
    }

    for state, (key, label, source, data, _tone) in config.items():
        target = BASE / state
        write_json(
            target / "api" / "measures-component.json",
            measures_payload(key, f"LabTrack {label}", data),
        )
        write_json(target / "api" / "issues-search.json", issues_payload(key, data, source))
        write_json(
            target / "api" / "qualitygates-project-status.json",
            gate_payload(key, data, source),
        )
        (target / "logs").mkdir(parents=True, exist_ok=True)
        (target / "logs" / f"scan-{state}.log").write_text(
            scan_log(state, key, source), encoding="utf-8"
        )

        pages = {
            "dashboard": page(
                "Dashboard de métricas",
                f"Evidencia SonarQube · {label}",
                state,
                meta_strip(key, label, source) + kpis(data) + "<h2>Ratings</h2>" + ratings_block(data),
            ),
            "bugs": page(
                f"Bugs ({data['bugs']})",
                f"Evidencia SonarQube · {label}",
                state,
                meta_strip(key, label, source)
                + issues_table([i for i in data["issues"] if i["type"] == "BUG"]),
            ),
            "vulnerabilidades": page(
                f"Vulnerabilidades ({data['vulnerabilities']})",
                f"Evidencia SonarQube · {label}",
                state,
                meta_strip(key, label, source)
                + issues_table([i for i in data["issues"] if i["type"] == "VULNERABILITY"]),
            ),
            "code-smells": page(
                f"Code Smells ({data['codeSmells']})",
                f"Evidencia SonarQube · {label}",
                state,
                meta_strip(key, label, source) + smell_cards(data["issues"]),
            ),
            "ratings": page(
                "Ratings de calidad",
                f"Evidencia SonarQube · {label}",
                state,
                meta_strip(key, label, source)
                + ratings_block(data)
                + '<div class="note">Escala SonarQube: A es la mejor calificación y E la peor. '
                "El ANTES reproducible conserva los ratings registrados en la instantánea histórica.</div>",
            ),
            "quality-gate": page(
                f"Quality Gate · {data['qualityGate']}",
                f"Evidencia SonarQube · {label}",
                state,
                meta_strip(key, label, source) + gate_block(data),
            ),
            "issues-lista": page(
                f"Listado de issues ({len(data['issues'])}) · regla + archivo",
                f"Evidencia SonarQube · {label}",
                state,
                meta_strip(key, label, source) + issues_table(data["issues"]),
            ),
            "fecha-commit": page(
                "Trazabilidad: fecha y commit",
                f"Evidencia SonarQube · {label}",
                state,
                meta_strip(key, label, source)
                + f"""<table><thead><tr><th>Dato</th><th>Valor</th></tr></thead><tbody>
<tr><td>Fecha de captura de esta evidencia</td><td>{CAPTURE_DATE}</td></tr>
<tr><td>Commit analizado</td><td class="file">{COMMIT}</td></tr>
<tr><td>Fecha del commit</td><td>{COMMIT_DATE}</td></tr>
<tr><td>Mensaje del commit</td><td>Initial commit</td></tr>
<tr><td>Proyecto SonarQube</td><td class="file">{key}</td></tr>
<tr><td>Origen de los datos</td><td class="file">{source}</td></tr>
<tr><td>Estado del escaneo</td><td>NO ejecutado: SonarQube no disponible</td></tr>
</tbody></table>
<div class="note">La fecha del commit es la del único commit del repositorio. No existe una
versión ANTES en Git, por lo que el árbol ANTES fue reconstruido en
docs/evidencias-sonarqube/antes/src y se identifica como ANTES REPRODUCIDO.</div>""",
            ),
        }
        for name, content in pages.items():
            (RENDER / f"{state}-{name}.html").write_text(content, encoding="utf-8")


def comparison() -> dict:
    antes, despues = load()
    rows = [
        ("Bugs", str(antes["bugs"]), str(despues["bugs"]), "-2 (-100 %)"),
        ("Vulnerabilidades", str(antes["vulnerabilities"]), str(despues["vulnerabilities"]), "-2 (-100 %)"),
        ("Code Smells", str(antes["codeSmells"]), str(despues["codeSmells"]), "-40 (-100 %)"),
        ("Confiabilidad", antes["reliabilityRating"], despues["reliabilityRating"], "B → A"),
        ("Seguridad", antes["securityRating"], despues["securityRating"], "C → A"),
        ("Mantenibilidad", antes["maintainabilityRating"], despues["maintainabilityRating"], "A → A (sin deuda abierta)"),
        ("Quality Gate", antes["qualityGate"], despues["qualityGate"], "OK → OK (0 issues abiertos)"),
    ]
    secondary = [
        ("Líneas de código (ncloc)", str(antes["linesOfCode"]), str(despues["linesOfCode"]), "+19"),
        ("Cobertura", f"{antes['coverage']} %", f"{despues['coverage']} %", "sin cambio"),
        ("Duplicación", f"{antes['duplications']} %", f"{despues['duplications']} %", "sin cambio"),
        ("Complejidad ciclomática", str(antes["complexity"]), str(despues["complexity"]), "+24"),
        ("Complejidad cognitiva", str(antes["cognitiveComplexity"]), str(despues["cognitiveComplexity"]), "-6"),
        ("Issues abiertos", str(len(antes["issues"])), str(len(despues["issues"])), "-44 (-100 %)"),
    ]
    payload = {
        "nota": "Comparacion de instantaneas historicas. NO proviene de un escaneo nuevo: SonarQube no estaba disponible.",
        "commit": COMMIT,
        "fecha": CAPTURE_DATE,
        "proyectos": {"antes": "labtrack-antes", "despues": "labtrack-despues"},
        "metricas_principales": [
            {"metrica": m, "antes": a, "despues": d, "mejora": j} for m, a, d, j in rows
        ],
        "metricas_secundarias": [
            {"metrica": m, "antes": a, "despues": d, "mejora": j} for m, a, d, j in secondary
        ],
        "antes": antes,
        "despues": despues,
    }
    md = [
        "# Tabla comparativa SonarQube — ANTES vs DESPUÉS",
        "",
        "> Datos reconstruidos desde `docs/sonar-baseline.json` y `docs/sonar-data.json`.",
        "> **No es un escaneo nuevo**: SonarQube no estaba disponible el 2026-11-09.",
        "> El estado ANTES se identifica como **ANTES REPRODUCIDO**.",
        "",
        f"Commit: `{COMMIT}` · Fecha de captura: {CAPTURE_DATE}",
        "",
        "## Métricas principales",
        "",
        "| Métrica | Antes | Después | Mejora |",
        "|---|---:|---:|---|",
    ]
    md += [f"| {m} | {a} | {d} | {j} |" for m, a, d, j in rows]
    md += [
        "",
        "## Métricas secundarias",
        "",
        "| Métrica | Antes | Después | Variación |",
        "|---|---:|---:|---|",
    ]
    md += [f"| {m} | {a} | {d} | {j} |" for m, a, d, j in secondary]
    md += [
        "",
        "## Lectura",
        "",
        "- Los 44 hallazgos del ANTES (2 bugs, 2 vulnerabilidades, 40 code smells) se reducen a 0.",
        "- Los ratings pasan de B/C/A a A/A/A.",
        "- El quality gate permanece OK en ambas instantáneas; la diferencia es el número de issues abiertos.",
        "- El ANTES no existe en Git: fue reconstruido en `docs/evidencias-sonarqube/antes/src`.",
        "",
    ]
    (BASE / "comparacion").mkdir(parents=True, exist_ok=True)
    (BASE / "comparacion" / "tabla-comparativa.md").write_text("\n".join(md), encoding="utf-8")
    write_json(BASE / "comparacion" / "comparacion.json", payload)
    return payload


def comparison_pages(payload: dict) -> None:
    RENDER.mkdir(parents=True, exist_ok=True)
    rows = payload["metricas_principales"]
    table = "".join(
        f"<tr><td>{esc(r['metrica'])}</td><td class='bar-value'>{esc(r['antes'])}</td>"
        f"<td class='bar-value'>{esc(r['despues'])}</td><td>{esc(r['mejora'])}</td></tr>"
        for r in rows
    )
    secondary = "".join(
        f"<tr><td>{esc(r['metrica'])}</td><td>{esc(r['antes'])}</td>"
        f"<td>{esc(r['despues'])}</td><td>{esc(r['mejora'])}</td></tr>"
        for r in payload["metricas_secundarias"]
    )
    meta = meta_strip("labtrack-antes / labtrack-despues", "Comparación", "sonar-baseline.json + sonar-data.json")

    table_page = page(
        "Tabla comparativa · Métrica | Antes | Después | Mejora",
        "Evidencia SonarQube · Comparación",
        "despues",
        meta
        + "<table><thead><tr><th>Métrica</th><th>Antes</th><th>Después</th>"
        f"<th>Mejora</th></tr></thead><tbody>{table}</tbody></table>"
        + "<h2>Métricas secundarias</h2>"
        + "<table><thead><tr><th>Métrica</th><th>Antes</th><th>Después</th>"
        f"<th>Variación</th></tr></thead><tbody>{secondary}</tbody></table>",
    )

    bars = [("Bugs", 2, 0, 10), ("Vulnerabilidades", 2, 0, 10), ("Code Smells", 40, 0, 40)]
    bar_html = "".join(
        f'<div class="bar-row"><div class="bar-label">{esc(name)}</div>'
        f'<div><div class="bar-track"><div class="bar antes" style="width:{a / maximo * 100:.1f}%"></div></div>'
        f'<div class="bar-track" style="margin-top:4px"><div class="bar despues" style="width:{d / maximo * 100:.1f}%"></div></div></div>'
        f'<div class="bar-value">{a} → {d}</div></div>'
        for name, a, d, maximo in bars
    )
    chart_page = page(
        "Gráfico comparativo de hallazgos",
        "Evidencia SonarQube · Comparación",
        "despues",
        meta
        + '<div class="legend"><span><i class="dot" style="background:#b42318"></i>ANTES</span>'
        '<span><i class="dot" style="background:#0e8a5f"></i>DESPUÉS</span></div>'
        + bar_html
        + f"""<div class="kpis" style="grid-template-columns:repeat(3,1fr);margin-top:22px">
<div class="kpi bad"><span>Issues abiertos ANTES</span><b>{len(payload['antes']['issues'])}</b><small>44 reproducidos</small></div>
<div class="kpi good"><span>Issues abiertos DESPUÉS</span><b>{len(payload['despues']['issues'])}</b><small>instantánea final</small></div>
<div class="kpi good"><span>Reducción</span><b>100 %</b><small>44 → 0 hallazgos</small></div>
</div>""",
    )

    dashboard_page = page(
        "Dashboard comparativo ANTES / DESPUÉS",
        "Evidencia SonarQube · Comparación",
        "despues",
        meta
        + f"""<div class="cards" style="grid-template-columns:repeat(4,1fr);margin-bottom:14px">
<div class="card"><span>Bugs</span><b>2 <span class="delta-down">→ 0</span></b></div>
<div class="card"><span>Vulnerabilidades</span><b>2 <span class="delta-down">→ 0</span></b></div>
<div class="card"><span>Code Smells</span><b>40 <span class="delta-down">→ 0</span></b></div>
<div class="card"><span>Quality Gate</span><b>OK <span class="delta-flat">→ OK</span></b></div>
</div>"""
        + ratings_block(payload["despues"]).replace(
            "Confiabilidad", "Confiabilidad (después)"
        )
        + "<h2>Detalle</h2>"
        + "<table><thead><tr><th>Métrica</th><th>Antes</th><th>Después</th>"
        f"<th>Mejora</th></tr></thead><tbody>{table}</tbody></table>",
    )

    for name, content in {
        "tabla-comparativa": table_page,
        "grafico-comparativo": chart_page,
        "dashboard-comparativo": dashboard_page,
    }.items():
        (RENDER / f"comparacion-{name}.html").write_text(content, encoding="utf-8")


def main() -> None:
    antes, despues = load()
    build_pages(antes, despues)
    payload = comparison()
    comparison_pages(payload)
    print(f"Antes: {antes['bugs']} bugs · {antes['vulnerabilities']} vulns · {antes['codeSmells']} smells · {len(antes['issues'])} issues")
    print(f"Después: {despues['bugs']} bugs · {despues['vulnerabilities']} vulns · {despues['codeSmells']} smells · {len(despues['issues'])} issues")
    print(f"HTML generado en {RENDER}")


if __name__ == "__main__":
    main()
