from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

PLACEHOLDER = "__BUNYA_JIDO_DATA__"


def _safe_json_for_script(data: dict[str, Any]) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render_html(graph: dict[str, Any], out: str | Path, template: str | Path | None = None) -> Path:
    out_path = Path(out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if template:
        html = Path(template).read_text(encoding="utf-8")
    else:
        html = resources.files("bunya_jido.viewer").joinpath("index.template.html").read_text(encoding="utf-8")
    payload = _safe_json_for_script(graph)
    if PLACEHOLDER not in html:
        raise ValueError(f"viewer template is missing {PLACEHOLDER} placeholder")
    html = html.replace(PLACEHOLDER, payload)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def write_json(graph: dict[str, Any], out: str | Path) -> Path:
    out_path = Path(out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
