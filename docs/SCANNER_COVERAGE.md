# Scanner Coverage Matrix

This document records what the deterministic `static_scan` artifact actually
discovers today. It is a fit guide for users and a change gate for future
scanner claims. A static scan supplies discovery evidence for blueprint
authoring; it is not a reviewed architectural interpretation.

The committed fixture is [`examples/coverage/`](../examples/coverage/). Its
observable behavior is covered by
[`tests/test_scanner_coverage.py`](../tests/test_scanner_coverage.py).

## Current Coverage

The matrix describes the default `auto` mode unless a row says otherwise.

| Area | Status | Fixture Evidence | Current Output | Important Limit |
|---|---|---|---|---|
| Python modules, imports, and top-level symbols | Primary supported scanner surface | `src/coverage_app/core.py`, `worker.py` | Module nodes; `uses_module` edges for resolved package imports; `defines` nodes for classes/functions; local-call edges within one module | Not a whole-program call graph; dynamic imports and runtime dispatch are not resolved |
| JavaScript / TypeScript source | Limited discovery support | `web/main.ts`, `web/local.ts` | Module, class/function, external-package, and provider-hint discovery | Relative imports are recorded only as inferred unresolved structure; they do not resolve to the local target module |
| Markdown / RST documents | Supported evidence discovery | `README.md`, `docs/contract.md` | Document nodes and `documents` edges for local Markdown/RST links | Does not infer contract meaning from prose |
| Python package metadata | Supported selected format | `pyproject.toml` | Dependency nodes and script entrypoints | Reads project dependencies, optional dependencies, and scripts only |
| JavaScript package metadata | Supported selected format | `package.json` | Dependency nodes and npm script entrypoints | Reads dependency groups and scripts only; does not execute tooling |
| Requirements files | Supported selected format | `requirements.txt` | Dependency nodes from non-option requirement lines | No recursive resolution, lockfile interpretation, or environment solve |
| Runtime artifacts | Supported selected artifacts | `runs/events.jsonl`, `runs/status.json` | Runtime file nodes; JSONL event nodes; selected JSON key nodes | Reads bounded samples and selected keys; not runtime truth or telemetry ingestion |
| Data artifacts | Policy-controlled discovery | `data/sample.csv` | Directory summary by default; file nodes with `--data-policy sample` or `full` | Defaults to omitting individual dataset files for privacy and scale |
| Provider / API hints | Heuristic discovery only | `worker.py`, `hint_text.py` | `api_provider` nodes and `api_calls` edges with source evidence | Token text can be a false positive; it does not prove a live integration |
| Other languages and artifact formats | Not claimed | None | None | Requires an adapter proposal and fixtures before any support claim |

## Measured Fixture Commands

Run the fixture scan directly when evaluating scanner behavior:

```bash
python -m bunya_jido scan --root examples/coverage --out coverage.json
python -m bunya_jido scan --root examples/coverage --data-policy sample --out coverage-sample.json
python -m unittest tests.test_scanner_coverage
```

In the default scan, `data/` is represented as a summarized directory and
`data/sample.csv` is deliberately absent. With `--data-policy sample`, the CSV
appears as a data node. The JS/TS fixture intentionally demonstrates the
current unresolved relative-import behavior rather than implying target
resolution.

## JavaScript / TypeScript Decision

Local JavaScript and TypeScript import resolution is intentionally documented
as limited in this milestone. Today a relative import such as `./local` is
detected with inferred evidence, but it is not linked to `web/local.ts`.
Claiming local module topology would therefore be misleading.

A later implementation may add local resolution only after it covers, with
fixtures, extension variants, `index` resolution, common alias configuration,
test-file behavior, missing-target handling, and evidence output. Until then,
JS/TS support means file, symbol, dependency, and provider-hint discovery.

## Extension Policy

A new language or artifact adapter must land with all of the following:

1. A small committed fixture containing supported cases and at least one
   deliberately unsupported or ambiguous case.
2. Regression tests asserting node/edge types, evidence kind and path,
   confidence for inferred behavior, and bounded behavior for missing or large
   inputs.
3. Documentation updates to this matrix that state exact formats, resolution
   rules, and limits without promising semantic architecture inference.
4. Output hygiene checks: no secret value capture, repository-relative
   evidence paths, controlled file/record limits, and no publication as
   grounded semantic truth without blueprint validation.
5. A before/after example or generated artifact when the new output materially
   changes what a user sees.

Provider detectors also require false-positive fixtures; runtime and data
adapters additionally require privacy and scale fixtures before expanding
their default collection behavior.

## Detection Boundaries

- Config files recognized as file-level evidence include `pyproject.toml`,
  `setup.py`, `setup.cfg`, `requirements.txt`, `requirements-dev.txt`,
  `Pipfile`, common lockfiles, `package.json`, Docker/Compose files,
  `Makefile`, `tox.ini`, `noxfile.py`, pre-commit config, and MkDocs config.
  Structured dependency or entrypoint extraction currently occurs only for
  `pyproject.toml`, `package.json`, and files whose names start with
  `requirements`.
- Runtime classification occurs for files in runtime-like directories such as
  `runs`, `logs`, `state`, `artifacts`, and `outputs`, or for `.log` and
  `.jsonl` files. JSONL event extraction reads a bounded prefix; JSON key
  extraction is applied when a runtime-classified file has a `.json` suffix.
- Data classification covers data-like directories including `data`,
  `datasets`, `notebooks`, `assets`, and `static`, plus `.csv`, `.tsv`,
  `.parquet`, `.npy`, `.npz`, and `.ipynb` files. Heavy data-like directories
  are not walked under the default `summary` policy.
- Provider/API hint scanning reads imports plus token-like text in recognized
  config, Python, and JS/TS files. It records the source path and token name,
  never a credential value, but remains heuristic evidence only.
