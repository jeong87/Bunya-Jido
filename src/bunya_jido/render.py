from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

PLACEHOLDER = "__BUNYA_JIDO_DATA__"
SAMPLE_RUN_PLACEHOLDER = "__BUNYA_JIDO_SAMPLE_RUN__"


def _safe_json_for_script(data: dict[str, Any]) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    return text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _render_html(
    graph: dict[str, Any],
    out: str | Path,
    *,
    template: str | Path | None = None,
    sample_run: dict[str, Any] | None = None,
) -> Path:
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
    if SAMPLE_RUN_PLACEHOLDER in html:
        sample_payload = "null" if sample_run is None else _safe_json_for_script(sample_run)
        html = html.replace(SAMPLE_RUN_PLACEHOLDER, sample_payload)
    elif sample_run is not None:
        raise ValueError(
            f"viewer template is missing {SAMPLE_RUN_PLACEHOLDER} placeholder"
        )
    out_path.write_text(html, encoding="utf-8")
    return out_path


def render_html(graph: dict[str, Any], out: str | Path, template: str | Path | None = None) -> Path:
    return _render_html(graph, out, template=template)


def _render_html_with_sample_run(
    graph: dict[str, Any],
    sample_run: dict[str, Any],
    out: str | Path,
    template: str | Path | None = None,
) -> Path:
    """Render a repository-owned demo with an optional offline receipt fixture."""

    return _render_html(graph, out, template=template, sample_run=sample_run)


def write_json(graph: dict[str, Any], out: str | Path) -> Path:
    out_path = Path(out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
