from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from . import __version__
from .blueprint import (
    default_blueprint_path,
    default_agent_map_path,
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
    )
    html_path = render_html(graph, args.out, template=args.template)
    if args.write_json:
        write_json(graph, args.write_json)
    print(f"Bunya-Jido built: {html_path}")
    if bp_path:
        q = graph.get("blueprint_quality", {})
        print(f"blueprint={bp_path} quality nodes={q.get('node_count')} edges={q.get('edge_count')} grounded_edges={q.get('grounded_edge_ratio')}")
    else:
        print("blueprint=not found; used deterministic static scan")
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
    print(f"Blueprint validation passed: {bp_path}")
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
    print(f"Agent map validation passed: {am_path}")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    if warnings:
        print("Warnings:")
        for warn in warnings[:40]:
            print(f"- {warn}")
        if len(warnings) > 40:
            print(f"... {len(warnings)-40} more")
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
        if cf.exists():
            changed.extend([x.strip() for x in cf.read_text(encoding="utf-8").splitlines() if x.strip()])
    text = generate_agent_context(args.root, task=args.task or "refresh context for changed files", changed_files=changed)
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Refresh context written: {out}")
    else:
        print(text, end="")
    return 0


def cmd_install_agent_guides(args: argparse.Namespace) -> int:
    paths = install_agent_guides(args.root, agent=args.agent, overwrite=args.overwrite)
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bunya-jido", description="Generate a single-file interactive graph atlas for a local repository.")
    parser.add_argument("--version", action="version", version=f"bunya-jido {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_build = sub.add_parser("build", help="Scan a repo and write an offline HTML graph. Uses .bunya-jido/bunya-jido.blueprint.json if present.")
    _add_common_scan_args(p_build)
    p_build.add_argument("--out", default="bunya-jido.html", help="Output HTML path. Default: bunya-jido.html")
    p_build.add_argument("--write-json", "--json-out", dest="write_json", default=None, help="Optional path to also write graph JSON.")
    p_build.add_argument("--template", default=None, help="Optional custom viewer template path.")
    p_build.add_argument("--blueprint", default="auto", type=_blueprint_arg_value, help="Blueprint path, 'auto' (default), or 'none'.")
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
    p_vbp.set_defaults(func=cmd_validate_blueprint)

    p_vam = sub.add_parser("validate-agent-map", help="Validate .bunya-jido/bunya-jido.agent-map.json.")
    p_vam.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_vam.add_argument("--agent-map", default=None, help="Agent map JSON path. Default: .bunya-jido/bunya-jido.agent-map.json")
    p_vam.add_argument("--blueprint", default=None, help="Optional blueprint JSON path for node-reference validation.")
    p_vam.set_defaults(func=cmd_validate_agent_map)

    p_ctx = sub.add_parser("context", help="Print or write a coding-agent context pack from blueprint + agent map.")
    p_ctx.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_ctx.add_argument("--node", default=None, help="Optional blueprint node id to focus.")
    p_ctx.add_argument("--workflow", default=None, help="Optional workflow id to focus.")
    p_ctx.add_argument("--task", default=None, help="Natural language task to match against agent-map routes.")
    p_ctx.add_argument("--changed-file", action="append", default=[], help="Changed file path or comma-separated list. Repeatable.")
    p_ctx.add_argument("--out", default=None, help="Optional output markdown path.")
    p_ctx.set_defaults(func=cmd_context)

    p_refresh = sub.add_parser("refresh-context", help="Generate agent context for changed files, useful after a PR/diff or stale blueprint warning.")
    p_refresh.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_refresh.add_argument("--changed-file", action="append", default=[], help="Changed file path or comma-separated list. Repeatable.")
    p_refresh.add_argument("--changed-files-from", default=None, help="File containing changed paths, one per line.")
    p_refresh.add_argument("--task", default=None, help="Optional task text to route context.")
    p_refresh.add_argument("--out", default=None, help="Optional output markdown path.")
    p_refresh.set_defaults(func=cmd_refresh_context)

    p_guides = sub.add_parser("install-agent-guides", help="Write Codex/Claude/Cursor/Cline instruction snippets under .bunya-jido/agent-guides.")
    p_guides.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    p_guides.add_argument("--agent", choices=["all", "codex", "claude", "cursor", "cline"], default="all", help="Which guide to write. Default: all.")
    p_guides.add_argument("--overwrite", action="store_true", help="Overwrite existing guide files.")
    p_guides.set_defaults(func=cmd_install_agent_guides)
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    subcommands = {"build", "prepare", "scan", "render", "validate", "validate-blueprint", "validate-agent-map", "context", "refresh-context", "install-agent-guides"}
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
