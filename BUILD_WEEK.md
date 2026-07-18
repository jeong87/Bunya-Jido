# OpenAI Build Week 2026

## Evidence Boundary

- Baseline commit: `a01d26bb9843252856f7fd2b952943c687d17641`
- Baseline commit date: July 2, 2026
- Build Week branch: `build-week-2026`
- Primary Codex session ID: `019f73d5-d0c4-7633-8f08-fd8fb5933b3b`
- Verified session model metadata: the local Codex rollout for that session
  records `turn_context.model` as `gpt-5.6-sol` on July 18, 2026.
- Approved live smoke source commit:
  `3544c198f7c1279fb96084790f109cd5ac38b34b`
- Corrective cross-platform CI:
  [run 29641266678](https://github.com/jeong87/Bunya-Jido/actions/runs/29641266678),
  successful at `f10182c97d5f139703063ad60876c3ccb9d64547`

The baseline was verified before implementation with 97 unit tests, Python
compileall, blueprint and agent-map validation, grounded diagnostics, 18 agent
utility cases, and atlas-quality validation.

## Features Before July 13, 2026

The baseline already included repository scanning, semantic blueprint
generation, offline and Studio visualization, task-aware context decisions,
execution-policy recommendations, worktree auditing, deterministic agent
utility evaluation, benchmark support, native guide generation, and stale-map
checks.

Those baseline capabilities must not be presented as Build Week additions.

## Features Added During Build Week

The Build Week extension keeps the semantic map as the product and adds a
measurable map-guided execution loop:

1. A canonical task-route identity and fingerprint shared by the compact agent
   context, run artifacts, and offline human atlas.
2. Additive route and context-efficiency receipts in schema v1, including
   first reads, tests, semantic edit boundaries, compact-context bytes, actual
   Codex token usage when available, elapsed time, changed-file counts, and the
   boundary verdict.
3. Offline `run.json` import in the HTML atlas, with expected-route,
   exact evidence-linked actual-change, and violation overlays.
4. An honest measurement boundary: a single run never reports tokens saved,
   and unavailable model usage is recorded as unavailable rather than
   estimated.
5. Public `bunya-jido codex-run --root ROOT --task TASK` orchestration.
6. A non-mutating preview and clean-baseline enforcement before an actual
   nested process starts.
7. Supporting non-escalating sandbox selection: only `MATCH` is
   `workspace-write`; every other decision is `read-only`.
8. UTF-8 prompt delivery through standard input with argv execution and
   `shell=False`.
9. JSONL capture, final Git audit, write-attempt auditing, and exact/glob/
   declared-directory safe-edit evaluation.
10. Schema `bunya-jido-codex-run-v1`, Markdown reporting, preserved stderr and
   last message, and intentional exit codes.
11. Deterministic fake-Codex tests for success, policy failures, malformed
   streams, cancellation, timeout, and command-injection-shaped input.
12. Independent explicit controls for disabled Codex web search and disabled
   workspace-shell network access.
13. Deterministic automation that ignores user and trusted-project execpolicy
    `.rules` without claiming to bypass administrator-managed requirements.

This is not a new Build Week savings benchmark. One separately approved
disposable read-only live smoke is recorded as narrow execution evidence; it
does not establish workspace-write, cross-platform, general safety, or token
savings.

## Contributions and Decisions

Codex inspected the baseline, designed and implemented the shared route
identity, receipts, atlas overlay, isolated runner, tests, documentation, and
repository-map updates, and ran local validators.

Human decisions are separated as follows:

- Product: keep the evidence-grounded semantic map as the core, expose it as a
  human atlas and compact agent route, and use `codex-run` as a measured
  map-guided extension.
- Engineering: use an independent module, require a clean actual-run baseline,
  and prevent non-`MATCH` sandbox escalation.
- Design: add optional schema-v1 receipts and a small local-file overlay to the
  existing offline viewer instead of creating a separate HTML report.

The session metadata above identifies the model recorded for this engineering
session. Separately, one live Codex CLI smoke exercised the read-only guarded
path. The smoke did not independently report or verify a model identity and
must not be presented as a GPT-5.6 benchmark.

The benchmark snapshot and reports already present at the baseline use
GPT-5.5 Medium and are pre-Build-Week evidence. Guarded Codex Run is new
Build Week functionality tested with a deterministic fake executable. No new
GPT-5.6 benchmark, performance number, or cross-platform live-agent claim is
made.

## Installation and Judge Testing

From a clean checkout:

```bash
python -m pip install -e .
python -m unittest -v tests.test_codex_run
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m bunya_jido codex-run --root . --task "Implement guarded Codex run orchestration and boundary reporting." --preview
```

The focused suite uses a fake executable and does not require Codex
authentication. The separately approved live smoke and its exact limitations
are documented in
[`docs/build-week/TESTING.md`](docs/build-week/TESTING.md). Future live nested
Codex runs remain a separate human approval gate. Fake-executable evidence must
not be described as proof of a live Codex OS sandbox.

For the full validation set and current results, see
[`docs/build-week/TESTING.md`](docs/build-week/TESTING.md). Product and
engineering decisions are recorded in
[`docs/build-week/DECISIONS.md`](docs/build-week/DECISIONS.md).
