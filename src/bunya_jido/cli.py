from __future__ import annotations

import argparse
import json
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

from . import __version__
from .blueprint import (
    activate_agent_guides,
    default_blueprint_path,
    default_agent_map_path,
    evaluate_map_freshness,
    generate_agent_context,
    graph_with_optional_blueprint,
    install_agent_guides,
    prepare_blueprint_workspace,
    validate_agent_map_file,
    validate_blueprint_file,
)
from .render import render_html, write_json
from .scanner import build_graph


def _add_common_scan_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--root", default=".", help="Repository root to scan. Default: current directory.")
    p.add_argument("--mode", choices=["auto", "code", "python", "docs", "runtime", "config", "llm", "full", "all"], default="auto", help="Scan mode. Default: auto. Aliases: code=python, full=all.")
    p.add_argument("--max-files", type=int, default=5000, help="Maximum files to inspect before truncating. Default: 5000.")
    p.add_argument("--max-nodes", type=int, default=700, help="Maximum nodes in rendered graph. Default: 700.")
    p.add_argument("--max-edges", type=int, default=1800, help="Maximum edges in rendered graph. Default: 1800.")
    p.add_argument("--include-hidden", action="store_true", help="Include hidden files/directories except heavy cache directories.")
    p.add_argument("--show-root", action="store_true", help="Show the synthetic repository root node. Hidden by default to avoid a central blueprint/root hub.")
    p.add_argument("--data-policy", choices=["summary", "sample", "full"], default="summary", help="How to handle dataset-like directories. summary=directory node only, sample=limited file nodes, full=all discovered data files within caps. Default: summary.")
    p.add_argument("--max-data-files", type=int, default=25, help="Maximum individual data file nodes when --data-policy=sample. Default: 25.")


def _blueprint_arg_value(value: str) -> str | bool:
    if value.lower() in {"none", "off", "false", "0"}:
        return "none"
    if value.lower() in {"auto", "on", "true", "1"}:
        return "auto"
    return value


def cmd_build(args: argparse.Namespace) -> int:
    graph, bp_path = graph_with_optional_blueprint(
        args.root,
        blueprint=args.blueprint,
        mode=args.mode,
        max_files=args.max_files,
        max_nodes=args.max_nodes,
        max_edges=args.max_edges,
        include_hidden=args.include_hidden,
        show_root=args.show_root,
        data_policy=args.data_policy,
        max_data_files=args.max_data_files,
        allow_draft=args.allow_draft,
    )
    html_path = render_html(graph, args.out, template=args.template)
    if args.write_json:
        write_json(graph, args.write_json)
    print(f"Bunya-Jido built: {html_path}")
    if bp_path:
        q = graph.get("blueprint_quality", {})
        print(f"artifact=semantic_blueprint grounding={q.get('grounding_status')} blueprint={bp_path}")
        print(f"quality nodes={q.get('node_count')} edges={q.get('edge_count')} grounded_edges={q.get('grounded_edge_ratio')} blockers={q.get('publish_blocker_count')}")
        if graph.get("agent_map_quality"):
            aq = graph["agent_map_quality"]
            print(f"agent_routes={aq.get('trusted_route_count')}/{aq.get('task_route_count')} validated")
    else:
        print("artifact=static_scan grounding=not_assessed blueprint=not found")
        print(f"hint: run `bunya-jido prepare --root {args.root}` or ask Codex to run it, then build again")
    print(f"nodes={graph['node_count']} edges={graph['edge_count']} mode={args.mode}")
    if getattr(args, "open", False):
        webbrowser.open(html_path.as_uri())
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    paths = prepare_blueprint_workspace(
        args.root,
        mode=args.mode,
        max_files=args.max_files,
        max_nodes=args.max_nodes,
        max_edges=args.max_edges,
        include_hidden=args.include_hidden,
        quiet=args.quiet,
        show_root=args.show_root,
        data_policy=args.data_policy,
        max_data_files=args.max_data_files,
    )
    if args.print_short_prompt:
        print(paths["short_prompt"].read_text(encoding="utf-8"), end="")
    elif args.quiet:
        print(paths["prompt"].as_posix())
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    graph = build_graph(args.root, mode=args.mode, max_files=args.max_files, max_nodes=args.max_nodes, max_edges=args.max_edges, include_hidden=args.include_hidden, show_root=args.show_root, data_policy=args.data_policy, max_data_files=args.max_data_files)
    if args.out:
        write_json(graph, args.out)
        print(f"Graph JSON written: {Path(args.out).resolve()}")
    else:
        print(json.dumps(graph, ensure_ascii=False, indent=2))
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    graph_path = Path(args.graph).resolve()
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    html_path = render_html(graph, args.out, template=args.template)
    print(f"Bunya-Jido rendered: {html_path}")
    if getattr(args, "open", False):
        webbrowser.open(html_path.as_uri())
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    nodes = {n.get("id") for n in graph.get("nodes", [])}
    errors = []
    for e in graph.get("edges", []):
        if e.get("source") not in nodes:
            errors.append(f"missing source: {e.get('source')} for edge {e.get('id')}")
        if e.get("target") not in nodes:
            errors.append(f"missing target: {e.get('target')} for edge {e.get('id')}")
    if errors:
        print("Graph validation failed:", file=sys.stderr)
        for err in errors[:50]:
            print(f"- {err}", file=sys.stderr)
        if len(errors) > 50:
            print(f"... {len(errors)-50} more", file=sys.stderr)
        return 2
    print(f"Graph validation passed: nodes={len(nodes)} edges={len(graph.get('edges', []))}")
    return 0


def cmd_validate_blueprint(args: argparse.Namespace) -> int:
    bp_path = Path(args.blueprint).resolve() if args.blueprint else default_blueprint_path(args.root)
    if not bp_path.exists():
        print(f"Blueprint not found: {bp_path}", file=sys.stderr)
        print("Run `bunya-jido prepare --root .` and ask Codex/Claude Code to execute the generated prompt.", file=sys.stderr)
        return 2
    errors, warnings, metrics = validate_blueprint_file(bp_path, root=args.root)
    if errors:
        print("Blueprint validation failed:", file=sys.stderr)
        for err in errors[:60]:
            print(f"- {err}", file=sys.stderr)
        return 2
    blockers = list(metrics.get("publish_blockers") or [])
    if blockers and not args.allow_draft:
        print("Blueprint publication blocked:", file=sys.stderr)
        for blocker in blockers[:60]:
            print(f"- {blocker}", file=sys.stderr)
        print("Use `--allow-draft` only when an explicitly marked draft output is acceptable.", file=sys.stderr)
        return 2
    status = "draft" if blockers else "grounded"
    metrics = {**metrics, "grounding_status": status}
    print(f"Blueprint validation passed: {bp_path}")
    print(f"Artifact mode: semantic_blueprint; grounding: {status}")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    if warnings:
        print("Warnings:")
        for warn in warnings[:40]:
            print(f"- {warn}")
        if len(warnings) > 40:
            print(f"... {len(warnings)-40} more")
    return 0


def cmd_validate_agent_map(args: argparse.Namespace) -> int:
    am_path = Path(args.agent_map).resolve() if args.agent_map else default_agent_map_path(args.root)
    if not am_path.exists():
        print(f"Agent map not found: {am_path}", file=sys.stderr)
        print("Run `bunya-jido prepare --root .` and ask Codex/Claude Code to execute the generated prompt.", file=sys.stderr)
        return 2
    errors, warnings, metrics = validate_agent_map_file(am_path, root=args.root, blueprint_path=args.blueprint)
    if errors:
        print("Agent map validation failed:", file=sys.stderr)
        for err in errors[:60]:
            print(f"- {err}", file=sys.stderr)
        return 2
    blockers = list(metrics.get("publish_blockers") or [])
    if blockers:
        print("Agent-map trusted context blocked:", file=sys.stderr)
        for blocker in blockers[:60]:
            print(f"- {blocker}", file=sys.stderr)
        return 2
    print(f"Agent map validation passed: {am_path}")
    print("Agent-map route references: validated")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    if warnings:
        print("Warnings:")
        for warn in warnings[:40]:
            print(f"- {warn}")
        if len(warnings) > 40:
            print(f"... {len(warnings)-40} more")
    return 0


def _diagnostic_blueprint_path(root: Path, blueprint: str | bool) -> Path | None:
    if blueprint is False or blueprint == "none":
        return None
    if blueprint is True or blueprint == "auto":
        candidate = default_blueprint_path(root)
        return candidate if candidate.exists() else None
    candidate = Path(str(blueprint)).resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"blueprint file not found: {candidate}")
    return candidate


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _diagnostic_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    bp_path = _diagnostic_blueprint_path(root, args.blueprint)
    if not bp_path:
        graph = build_graph(
            root,
            mode=args.mode,
            max_files=args.max_files,
            max_nodes=args.max_nodes,
            max_edges=args.max_edges,
            include_hidden=args.include_hidden,
            show_root=args.show_root,
            data_policy=args.data_policy,
            max_data_files=args.max_data_files,
        )
        return {
            "root": root.as_posix(),
            "artifact_mode": "static_scan",
            "grounding_status": "not_assessed",
            "semantic_publication_allowed": False,
            "blueprint_path": None,
            "agent_map_path": None,
            "node_count": graph["node_count"],
            "edge_count": graph["edge_count"],
            "publish_blockers": [],
            "warnings": [],
            "agent_routes": {"status": "not_assessed", "trusted": 0, "total": 0},
        }

    bp_errors, bp_warnings, bp_metrics = validate_blueprint_file(bp_path, root=root)
    blockers = list(bp_metrics.get("publish_blockers") or [])
    errors = list(bp_errors)
    warnings = list(bp_warnings)
    agent_path = default_agent_map_path(root)
    agent_routes = {"status": "not_provided", "trusted": 0, "total": 0}
    if agent_path.exists():
        agent_errors, agent_warnings, agent_metrics = validate_agent_map_file(
            agent_path, root=root, blueprint_path=bp_path
        )
        errors.extend(f"agent map: {error}" for error in agent_errors)
        warnings.extend(f"agent map: {warning}" for warning in agent_warnings)
        blockers.extend(
            f"agent map: {blocker}"
            for blocker in agent_metrics.get("publish_blockers") or []
        )
        trusted = int(agent_metrics.get("trusted_route_count") or 0)
        total = int(agent_metrics.get("task_route_count") or 0)
        agent_routes = {
            "status": "validated"
            if not agent_errors and not agent_metrics.get("publish_blockers")
            else "blocked",
            "trusted": trusted,
            "total": total,
        }
    blockers = list(dict.fromkeys(blockers))
    grounding_status = "blocked" if errors or blockers else "grounded"
    return {
        "root": root.as_posix(),
        "artifact_mode": "semantic_blueprint",
        "grounding_status": grounding_status,
        "semantic_publication_allowed": grounding_status == "grounded",
        "blueprint_path": _display_path(bp_path, root),
        "agent_map_path": _display_path(agent_path, root) if agent_path.exists() else None,
        "node_count": int(bp_metrics.get("node_count") or 0),
        "edge_count": int(bp_metrics.get("edge_count") or 0),
        "grounded_core_node_ratio": bp_metrics.get("grounded_core_node_ratio"),
        "grounded_critical_edge_ratio": bp_metrics.get("grounded_critical_edge_ratio"),
        "publish_blockers": blockers,
        "warnings": warnings,
        "errors": errors,
        "agent_routes": agent_routes,
    }


def cmd_diagnose(args: argparse.Namespace) -> int:
    report = _diagnostic_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Bunya-Jido diagnostics: {report['root']}")
        print(f"Artifact mode: {report['artifact_mode']}")
        print(f"Grounding status: {report['grounding_status']}")
        allowed = "allowed" if report["semantic_publication_allowed"] else "not allowed"
        print(f"Normal semantic publication: {allowed}")
        print(f"Blueprint: {report['blueprint_path'] or 'not found'}")
        print(f"Graph quality: nodes={report['node_count']} edges={report['edge_count']}")
        routes = report["agent_routes"]
        print(f"Agent-map routes: {routes['status']} ({routes['trusted']}/{routes['total']} trusted)")
        print(f"Warnings: {len(report.get('warnings') or [])}")
        print(f"Blockers: {len(report.get('publish_blockers') or [])}")
        for blocker in (report.get("publish_blockers") or [])[:10]:
            print(f"- {blocker}")
        for error in (report.get("errors") or [])[:10]:
            print(f"- error: {error}")
    if args.require_grounded and (
        report["artifact_mode"] != "semantic_blueprint"
        or report["grounding_status"] != "grounded"
    ):
        return 2
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    changed = []
    for v in args.changed_file or []:
        changed.extend([x.strip() for x in v.split(",") if x.strip()])
    text = generate_agent_context(args.root, node=args.node, workflow=args.workflow, task=args.task, changed_files=changed)
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Agent context written: {out}")
    else:
        print(text, end="")
    return 0


def cmd_refresh_context(args: argparse.Namespace) -> int:
    changed = []
    for v in args.changed_file or []:
        changed.extend([x.strip() for x in v.split(",") if x.strip()])
    if args.changed_files_from:
        cf = Path(args.changed_files_from)
        if not cf.exists():
            print(f"Changed-files input not found: {cf}", file=sys.stderr)
            return 2
        changed.extend([x.strip() for x in cf.read_text(encoding="utf-8").splitlines() if x.strip()])
    if not changed:
        print("refresh-context requires at least one --changed-file or --changed-files-from entry.", file=sys.stderr)
        return 2
    text = generate_agent_context(args.root, task=args.task, changed_files=changed)
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Refresh context written: {out}")
    else:
        print(text, end="")
    return 0


def cmd_check_stale(args: argparse.Namespace) -> int:
    changed = []
    for value in args.changed_file or []:
        changed.extend([path.strip() for path in value.split(",") if path.strip()])
    if args.changed_files_from:
        changed_file_path = Path(args.changed_files_from)
        if not changed_file_path.exists():
            print(f"Changed-files input not found: {changed_file_path}", file=sys.stderr)
            return 2
        changed.extend(
            path.strip()
            for path in changed_file_path.read_text(encoding="utf-8").splitlines()
            if path.strip()
        )
    if args.git_diff is not None:
        root = Path(args.root).resolve()
        revision = args.git_diff or "HEAD"
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "diff", "--name-only", revision, "--"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Could not collect git diff paths: {exc}", file=sys.stderr)
            return 2
        changed.extend(path.strip() for path in completed.stdout.splitlines() if path.strip())
    if not changed:
        print("check-stale requires changed files from --changed-file, --changed-files-from, or --git-diff.", file=sys.stderr)
        return 2
    report = evaluate_map_freshness(args.root, changed)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Map freshness status: {report['status']}")
        print(f"Reason: {report['reason']}")
        for path in report.get("triggering_files") or []:
            print(f"- requires review: {path}")
        for path in report.get("review_artifacts") or []:
            print(f"- review artifact updated: {path}")
        if report["status"] == "stale":
            print("Run `bunya-jido prepare --root . --quiet`, have a coding agent refresh the semantic map, then commit the updated map artifact.")
        elif report["status"] == "review_recorded":
            print("A map update or review note is present; validation still checks trust, not architectural completeness.")
    if args.require_reviewed and report["status"] not in {"current", "review_recorded"}:
        return 2
    return 0


def cmd_install_agent_guides(args: argparse.Namespace) -> int:
    if args.dry_run and not args.activate:
        print("--dry-run requires --activate.", file=sys.stderr)
        return 2
    if args.activate:
        actions = activate_agent_guides(args.root, agent=args.agent, dry_run=args.dry_run)
        for name, action in actions.items():
            print(f"{name}: {action['status']} {action['path']}")
            if args.dry_run:
                print(action["content"].rstrip())
                print()
        return 0
    paths = install_agent_guides(args.root, agent=args.agent, overwrite=args.overwrite)
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bunya-jido", description="Create offline semantic repository maps and bounded coding-agent context.")
    parser.add_argument("--version", action="version", version=f"bunya-jido {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_build = sub.add_parser("build", help="Write an offline HTML map from a semantic blueprint when present, or from a deterministic scan otherwise.")
    _add_common_scan_args(p_build)
    p_build.add_argument("--out", default="bunya-jido.html", help="Output HTML path. Default: bunya-jido.html")
    p_build.add_argument("--write-json", "--json-out", dest="write_json", default=None, help="Optional path to also write graph JSON.")
    p_build.add_argument("--template", default=None, help="Optional custom viewer template path.")
    p_build.add_argument("--blueprint", default="auto", type=_blueprint_arg_value, help="Blueprint path, 'auto' (default), or 'none'.")
    p_build.add_argument("--allow-draft", action="store_true", help="Render a structurally valid semantic blueprint with grounding blockers as an explicit draft.")
    p_build.add_argument("--open", action="store_true", help="Open the generated HTML in your default browser.")
    p_build.set_defaults(func=cmd_build)

    p_prepare = sub.add_parser("prepare", help="Create .bunya-jido prompt/schema/static scan for Codex, Claude Code, or another coding agent.")
    _add_common_scan_args(p_prepare)
    p_prepare.add_argument("--quiet", action="store_true", help="Only print the generated prompt path.")
    p_prepare.add_argument("--print-short-prompt", action="store_true", help="Print the one-line instruction for coding agents.")
    p_prepare.set_defaults(func=cmd_prepare)

    p_scan = sub.add_parser("scan", help="Scan a repo and print/write graph JSON.")
    _add_common_scan_args(p_scan)
    p_scan.add_argument("--out", default=None, help="Optional output JSON path. If omitted, JSON prints to stdout.")
    p_scan.set_defaults(func=cmd_scan)

    p_render = sub.add_parser("render", help="Render an existing graph JSON into HTML.")
    p_render.add_argument("--graph", required=True, help="Input graph JSON path.")
    p_render.add_argument("--out", default="bunya-jido.html", help="Output HTML path.")
    p_render.add_argument("--template", default=None, help="Optional custom viewer template path.")
    p_render.add_argument("--open", action="store_true", help="Open the generated HTML in your default browser.")
    p_render.set_defaults(func=cmd_render)

    p_validate = sub.add_parser("validate", help="Validate graph JSON references.")
    p_validate.add_argument("--graph", required=True, help="Input graph JSON path.")
    p_validate.set_defaults(func=cmd_validate)

    p_vbp = sub.add_parser("validate-blueprint", help="Validate .bunya-jido/bunya-jido.blueprint.json.")
    p_vbp.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_vbp.add_argument("--blueprint", default=None, help="Blueprint JSON path. Default: .bunya-jido/bunya-jido.blueprint.json")
    p_vbp.add_argument("--allow-draft", action="store_true", help="Accept grounding blockers for an explicitly marked draft review.")
    p_vbp.set_defaults(func=cmd_validate_blueprint)

    p_vam = sub.add_parser("validate-agent-map", help="Validate .bunya-jido/bunya-jido.agent-map.json.")
    p_vam.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_vam.add_argument("--agent-map", default=None, help="Agent map JSON path. Default: .bunya-jido/bunya-jido.agent-map.json")
    p_vam.add_argument("--blueprint", default=None, help="Optional blueprint JSON path for node-reference validation.")
    p_vam.set_defaults(func=cmd_validate_agent_map)

    p_diag = sub.add_parser("diagnose", help="Report actual artifact mode, grounding status, and validated agent-route readiness.")
    _add_common_scan_args(p_diag)
    p_diag.add_argument("--blueprint", default="auto", type=_blueprint_arg_value, help="Blueprint path, 'auto' (default), or 'none'.")
    p_diag.add_argument("--require-grounded", action="store_true", help="Exit with status 2 unless a publishable grounded semantic blueprint is present.")
    p_diag.add_argument("--json", action="store_true", help="Print a machine-readable diagnostics report.")
    p_diag.set_defaults(func=cmd_diagnose)

    p_ctx = sub.add_parser("context", help="Print or write a coding-agent context pack from blueprint + agent map.")
    p_ctx.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_ctx.add_argument("--node", default=None, help="Optional blueprint node id to focus.")
    p_ctx.add_argument("--workflow", default=None, help="Optional workflow id to focus.")
    p_ctx.add_argument("--task", default=None, help="Natural language task to match against agent-map routes.")
    p_ctx.add_argument("--changed-file", action="append", default=[], help="Changed file path or comma-separated list. Repeatable.")
    p_ctx.add_argument("--out", default=None, help="Optional output markdown path.")
    p_ctx.set_defaults(func=cmd_context)

    p_refresh = sub.add_parser("refresh-context", help="Recommend trusted routes justified by changed-file evidence after an edit or diff.")
    p_refresh.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_refresh.add_argument("--changed-file", action="append", default=[], help="Changed file path used as route evidence, or a comma-separated list. Repeatable.")
    p_refresh.add_argument("--changed-files-from", default=None, help="File containing changed paths used as route evidence, one per line.")
    p_refresh.add_argument("--task", default=None, help="Optional task text to route context.")
    p_refresh.add_argument("--out", default=None, help="Optional output markdown path.")
    p_refresh.set_defaults(func=cmd_refresh_context)

    p_stale = sub.add_parser("check-stale", help="Check whether changed files require a reviewed semantic map update.")
    p_stale.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_stale.add_argument("--changed-file", action="append", default=[], help="Changed file path, or a comma-separated list. Repeatable.")
    p_stale.add_argument("--changed-files-from", default=None, help="File containing changed paths, one per line.")
    p_stale.add_argument("--git-diff", nargs="?", const="", default=None, metavar="REVISION", help="Read tracked changed paths from git diff against REVISION; without a value, compare the working tree to HEAD.")
    p_stale.add_argument("--require-reviewed", action="store_true", help="Exit with status 2 when policy-triggering changes have no semantic map artifact update.")
    p_stale.add_argument("--json", action="store_true", help="Print a machine-readable freshness report.")
    p_stale.set_defaults(func=cmd_check_stale)

    p_guides = sub.add_parser("install-agent-guides", help="Write Bunya-Jido agent guidance snippets or activate managed project instructions.")
    p_guides.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_guides.add_argument("--agent", choices=["all", "codex", "claude", "cursor", "cline"], default="all", help="Which guide to write. Default: all.")
    p_guides.add_argument("--overwrite", action="store_true", help="Overwrite existing snippet files in default snippet mode.")
    p_guides.add_argument("--activate", action="store_true", help="Install or update a managed task-context block in each agent's native project instructions file.")
    p_guides.add_argument("--dry-run", action="store_true", help="With --activate, show planned native instruction writes without changing files.")
    p_guides.set_defaults(func=cmd_install_agent_guides)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    subcommands = {"build", "prepare", "scan", "render", "validate", "validate-blueprint", "validate-agent-map", "diagnose", "context", "refresh-context", "check-stale", "install-agent-guides"}
    if not raw or (raw[0] not in subcommands and raw[0] not in {"-h", "--help", "--version"}):
        raw = ["build"] + raw
    parser = build_parser()
    args = parser.parse_args(raw)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"bunya-jido error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
