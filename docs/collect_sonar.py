"""Recolecta métricas e issues de SonarQube para el informe de LabTrack.

Uso:
    python collect_sonar.py baseline
    python collect_sonar.py final

La primera ejecución guarda docs/sonar-baseline.json; la segunda combina ambos
estados en docs/sonar-data.json, que alimenta el informe y la presentación.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
TOKEN_FILE = ROOT / "instance" / "sonar-token.txt"
HOST = "http://localhost:9000"
PROJECT = "labtrack"

METRICS = [
    "bugs",
    "vulnerabilities",
    "code_smells",
    "coverage",
    "duplicated_lines_density",
    "reliability_rating",
    "security_rating",
    "sqale_rating",
    "ncloc",
    "complexity",
    "cognitive_complexity",
]

RATING = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}


def token() -> str:
    value = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit("Falta instance/sonar-token.txt")
    return value


def api(path: str, params: dict | None = None) -> dict:
    query = ""
    if params:
        from urllib.parse import urlencode

        query = "?" + urlencode(params)
    request = urllib.request.Request(
        f"{HOST}{path}{query}",
        headers={"Authorization": f"Bearer {token()}"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def measures() -> dict:
    payload = api(
        "/api/measures/component",
        {"component": PROJECT, "metricKeys": ",".join(METRICS)},
    )
    values = {item["metric"]: item.get("value", "0") for item in payload["component"]["measures"]}

    def number(key: str, default: float = 0.0) -> float:
        try:
            return float(values.get(key, default))
        except (TypeError, ValueError):
            return default

    return {
        "linesOfCode": int(number("ncloc")),
        "bugs": int(number("bugs")),
        "vulnerabilities": int(number("vulnerabilities")),
        "codeSmells": int(number("code_smells")),
        "coverage": number("coverage"),
        "duplications": number("duplicated_lines_density"),
        "reliabilityRating": RATING.get(values.get("reliability_rating", ""), "A"),
        "securityRating": RATING.get(values.get("security_rating", ""), "A"),
        "maintainabilityRating": RATING.get(values.get("sqale_rating", ""), "A"),
        "complexity": int(number("complexity")),
        "cognitiveComplexity": int(number("cognitive_complexity")),
    }


def gate() -> dict:
    payload = api("/api/qualitygates/project_status", {"projectKey": PROJECT})
    status = payload["projectStatus"]
    return {
        "qualityGate": status["status"],
        "conditions": [
            {
                "metric": condition.get("metricKey", ""),
                "status": condition.get("status", ""),
                "actual": condition.get("actualValue", ""),
                "threshold": condition.get("errorThreshold", ""),
            }
            for condition in status.get("conditions", [])
        ],
    }


def issues() -> list[dict]:
    collected: list[dict] = []
    page = 1
    while True:
        payload = api(
            "/api/issues/search",
            {
                "componentKeys": PROJECT,
                "resolved": "false",
                "ps": 500,
                "p": page,
                "additionalFields": "rules",
            },
        )
        for issue in payload["issues"]:
            component = issue.get("component", "").split(":", 1)[-1]
            text_range = issue.get("textRange") or {}
            collected.append(
                {
                    "rule": issue.get("rule", ""),
                    "severity": issue.get("severity", "MAJOR"),
                    "type": issue.get("type", "CODE_SMELL"),
                    "component": component,
                    "line": text_range.get("startLine") or issue.get("line") or "",
                    "message": issue.get("message", ""),
                    "status": "Corregido",
                    "effort": issue.get("effort", ""),
                }
            )
        if page * 500 >= payload.get("total", 0):
            break
        page += 1
    collected.sort(key=lambda item: (item["type"], item["severity"], item["component"], item["rule"]))
    return collected


def snapshot() -> dict:
    data = measures()
    data.update(gate())
    data["issues"] = issues()
    return data


def main() -> None:
    stage = sys.argv[1].lower() if len(sys.argv) > 1 else "final"
    data = snapshot()
    print(
        f"{stage}: {data['bugs']} bugs · {data['vulnerabilities']} vulnerabilidades · "
        f"{data['codeSmells']} code smells · gate {data['qualityGate']} · "
        f"cobertura {data['coverage']:.1f} % ({len(data['issues'])} issues)"
    )

    if stage == "baseline":
        (BASE / "sonar-baseline.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return

    baseline_path = BASE / "sonar-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else data
    combined = {"baseline": baseline, "final": data}
    (BASE / "sonar-data.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Guardado docs/sonar-data.json")


if __name__ == "__main__":
    main()
