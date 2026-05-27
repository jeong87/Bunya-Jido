# Bunya-Jido

<p align="center">
  <a href="https://jeong87.github.io/Bunya-Jido/demo.html">
    <img src="docs/assets/bunyajido_preview.jpg" alt="Bunya-Jido preview" width="100%">
  </a>
</p>

<p align="center">
  <strong>EN</strong> | <a href="./README.ko.md">KR</a>
</p>

<p align="center">
  <a href="https://jeong87.github.io/Bunya-Jido/demo.html"><strong>Try the demo</strong></a>
</p>

<p align="center">
  <strong>A semantic repository atlas for humans and coding agents.</strong>
</p>

`Bunya-Jido` creates offline repository maps from deterministic evidence and reviewable coding-agent interpretation. It shows responsibilities, workflows, and change boundaries for humans, then derives bounded task-oriented navigation context for coding agents.

The project is inspired by Cheonsang Yeolcha Bunyajido, the Korean star map that reads the sky through regions and relationships. In the same spirit, Bunya-Jido gathers files, modules, docs, configuration, runtime artifacts, and coding-agent interpretation into one map of a codebase.

The goal is a grounded semantic map whose important claims can be inspected, not an automatic claim of architectural truth.

## What It Creates

Bunya-Jido creates two outputs.

1. A single HTML architecture map that opens directly in a browser.
2. A `.bunya-jido/` context pack that coding agents such as Codex, Claude Code, Cursor, and Cline can use as bounded handoff context for a task.

The HTML map works offline. It does not need a server, database, internet connection, or JavaScript build step.

## Why It Exists

Static analysis tools can tell that `foo.py` imports `bar.py`. They usually cannot tell which module owns control flow, which file is a runtime adapter, or which document is the contract to read before changing behavior.

Bunya-Jido fills that gap with a coding agent.

It first scans the repository to collect raw evidence. Then a coding agent reads the repository and writes component and workflow documents. Bunya-Jido validates those outputs and renders an interactive HTML map with evidence paths attached.

Bunya-Jido focuses on questions like these:

- What are the main responsibility areas in this repository?
- In what order do the important workflows move?
- Which files, docs, and tests should be read before changing a feature?
- Which boundaries should a coding agent avoid touching casually?
- What real evidence supports each graph node and edge?

## Two Map Modes

Bunya-Jido can produce two related, but different, map forms.

### Deterministic Scan Map

Without a semantic blueprint, Bunya-Jido renders repository structure and detected hints gathered from source files, documentation, configuration, and selected artifacts. This is useful discovery evidence, not an architectural judgment.

```bash
bunya-jido build --root . --blueprint none --out bunya-jido.html
```

### Semantic Blueprint Map

When `.bunya-jido/bunya-jido.blueprint.json` exists, Bunya-Jido renders an evidence-linked architectural interpretation written with a coding agent and checked by the tool. This is the recommended mode for responsibility areas, workflows, and agent handoff context.

Semantic maps with unresolved core grounding blockers are not built by default. To inspect a structurally valid but unfinished map explicitly as a draft, use:

```bash
bunya-jido build --root . --allow-draft --out bunya-jido.html
```

## Quick Start

1. Install: `python -m pip install git+https://github.com/jeong87/Bunya-Jido.git`
2. Prompt Codex: paste the Blueprint Mode prompt below to have it write docs, validate outputs, and build the HTML map.

Install with one command:

```bash
python -m pip install git+https://github.com/jeong87/Bunya-Jido.git
```

PyPI release is planned for later.

Check the command:

```bash
bunya-jido --version
```

### Blueprint Mode

Blueprint mode is the core Bunya-Jido workflow.

1. Bunya-Jido scans the repository deterministically.
2. A coding agent reads the repository and scan output.
3. The agent writes component docs, workflow docs, a blueprint, and an agent map.
4. Bunya-Jido validates those files.
5. The validated blueprint is rendered into a single HTML map.

From the repository root, ask your coding agent:

```text
Run `bunya-jido prepare --root . --quiet` if needed, then read and execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`. Create or refresh `.bunya-jido/COMPONENTS.md`, `.bunya-jido/WORKFLOWS.md`, `.bunya-jido/bunya-jido.blueprint.json`, and `.bunya-jido/bunya-jido.agent-map.json`; run `bunya-jido validate-blueprint --root .` and `bunya-jido validate-agent-map --root .`; fix errors and grounding blockers, and reduce classification warnings when practical; then run `bunya-jido build --root . --out bunya-jido.html`; confirm the HTML path and say `ready`.
```

This prompt builds `bunya-jido.html` at the end. If you edit the blueprint and want to rebuild the map yourself, run:

```bash
bunya-jido build --root . --out bunya-jido.html
```

Open `bunya-jido.html` in your browser.

## Generated Files

`bunya-jido prepare` creates these files:

```text
.bunya-jido/
  COMPONENTS.md
  WORKFLOWS.md
  bunya-jido.blueprint.json
  bunya-jido.agent-map.json
  bunya-jido-static-scan.json
  bunya-jido-blueprint.schema.json
  bunya-jido-agent-map.schema.json
  BUNYA_JIDO_BLUEPRINT_PROMPT.md
  CODEX_ONE_LINER.txt
```

### `COMPONENTS.md`

A responsibility-oriented document for the repository's main components.

Each component should include its role, evidence files, inputs, outputs, contracts, related tests, and the places a coding agent should read first. The point is not to mirror folder names, but to reveal real responsibilities and change boundaries.

### `WORKFLOWS.md`

A document that explains the repository's main flows in order.

For example, it can describe how a CLI entrypoint moves through scanning, blueprint validation, rendering, and HTML output. It should also leave a path for future feature work or debugging.

### `bunya-jido.blueprint.json`

The machine-readable graph used by the HTML map.

It contains nodes, edges, planes, groups, detail nodes, and evidence. Because it is derived from `COMPONENTS.md` and `WORKFLOWS.md`, it should be smaller and more semantic than a raw dependency graph.

Validate it with:

```bash
bunya-jido validate-blueprint --root .
```

### `bunya-jido.agent-map.json`

A task map for coding agents.

For tasks such as "modify provider behavior," "change the storage layer," or "debug runtime failure," it records what to read first, which tests matter, what is safe to edit, and which boundaries need care.

Its task routes must resolve against the semantic blueprint and repository-relative required reading and tests before they can be emitted as trusted agent context or shown as map paths.

Validate it with:

```bash
bunya-jido validate-agent-map --root .
```

### `bunya-jido-static-scan.json`

A deterministic scan result produced without an LLM.

It includes files, modules, imports, docs, configuration, runtime artifacts, and external API hints. The coding agent uses it as raw evidence while writing the blueprint.

## HTML Map

The generated HTML map includes:

- responsibility-oriented plane clusters
- node and edge filtering
- local graph focus around a selected node
- a trust panel showing `Static Scan`, `Grounded`, or explicit `Draft` status
- an evidence panel showing source paths, relation confidence, and recorded evidence
- labeled path presets for blueprint views, workflows, and validated agent-map task routes
- PNG and JSON export
- overview/detail switching when the blueprint provides detail nodes

The map is not the source of truth. The evidence remains in the repository's code, docs, configuration, tests, runtime artifacts, and validated blueprint files. Bunya-Jido projects that evidence into a form that is easier to inspect.

Validated agent-map task routes now appear both in generated context output and as `Task Route` path presets in the HTML map. Missing blueprint nodes, workflows, required reading, or tests block trusted context and normal semantic publication.

## Working With Coding Agents

Once a blueprint and agent map exist, Bunya-Jido can generate a focused handoff for a task.

```bash
bunya-jido context --root . --task "modify provider behavior" --out .bunya-jido/CONTEXT.md
```

You can also focus on a specific node:

```bash
bunya-jido context --root . --node component:llm_router --out .bunya-jido/CONTEXT.md
```

Or refresh context from changed files:

```bash
bunya-jido refresh-context --root . \
  --changed-file src/foo.py \
  --changed-file tests/test_foo.py \
  --out .bunya-jido/REFRESH_CONTEXT.md
```

These files are meant to be pasted or attached before handing work to a coding agent.

## Supported Scope

The current strongest fit is Python repositories with nontrivial workflows, especially developer tooling, research, automation, and agent-oriented projects.

- Python module/import and symbol scanning is the primary code-scanning surface today.
- Markdown documentation, common package/config files, selected runtime/data artifacts, and provider/API hints are used as discovery evidence.
- JavaScript and TypeScript files are scanned on a limited basis, but local module-resolution coverage is still developing.

Bunya-Jido does not yet claim equivalent semantic coverage across languages or automatic proof that an authored architecture map is correct.

## Agent Guide Snippets

Bunya-Jido can create instruction snippets for Codex, Claude Code, Cursor, and Cline style environments.

```bash
bunya-jido install-agent-guides --root . --agent all
```

Generated location:

```text
.bunya-jido/agent-guides/
```

It does not overwrite root-level `AGENTS.md`, `CLAUDE.md`, Cursor rules, or Cline rules. Move the snippets only when you want those tools to always reference Bunya-Jido guidance.

## Data-Heavy Repositories

By default, Bunya-Jido summarizes dataset-like directories as directory-level nodes. It does not turn thousands of data files into individual nodes.

```bash
bunya-jido build --root . --data-policy summary --out bunya-jido.html
```

Other options:

```bash
bunya-jido build --root . --data-policy sample --max-data-files 50 --out bunya-jido.html
bunya-jido build --root . --data-policy full --out bunya-jido.html
```

Use `summary` for most repositories. Use `sample` when the shape of a data directory matters, and `full` only for small example datasets or small artifact folders.

## Design Principles

- Prefer a small semantic architecture map over a giant raw dependency graph.
- Attach evidence paths to nodes and edges whenever possible.
- Let an LLM help author the blueprint, but let Bunya-Jido validate and render deterministically.
- Keep the final map openable offline.
- Treat the map as an inspectable projection, not the territory itself.

## Limitations

- Blueprint quality depends on the coding agent's analysis quality.
- Static scanning is fast, but it can become noisy on large repositories.
- Bunya-Jido does not call an LLM by itself.
- The HTML map does not prove architectural correctness. It makes assumptions and evidence easier to inspect.

## Roadmap

See [docs/CONTRIBUTION_PLAN.md](docs/CONTRIBUTION_PLAN.md) for the grounded-map roadmap, including validation status, human/agent parity, example maps, and measured scanner coverage.

## License

MIT.
