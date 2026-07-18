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

Guarded Codex Run adds:

1. Public `bunya-jido codex-run --root ROOT --task TASK` orchestration.
2. A non-mutating preview that works with a dirty worktree.
3. Clean-baseline enforcement before any actual nested process starts.
4. Non-escalating context-to-Codex sandbox mapping: only `MATCH` is
   `workspace-write`; every other decision is `read-only`.
5. UTF-8 prompt delivery through standard input with argv execution and
   `shell=False`.
6. JSONL capture, final Git audit, write-attempt auditing, and exact/glob/
   declared-directory safe-edit evaluation.
7. Schema `bunya-jido-codex-run-v1`, Markdown reporting, preserved stderr and
   last message, and intentional exit codes.
8. Deterministic fake-Codex tests for success, policy failures, malformed
   streams, cancellation, timeout, and command-injection-shaped input.
9. Independent explicit controls for disabled Codex web search and disabled
   workspace-shell network access.
10. Deterministic automation that ignores user and trusted-project execpolicy
    `.rules` without claiming to bypass administrator-managed requirements.

HTML reporting, benchmark claims, and package release are not part of this MVP.
One separately approved disposable read-only live smoke is recorded as narrow
validation evidence; it does not establish workspace-write, cross-platform, or
general safety behavior.

## Contributions and Decisions

Codex inspected the baseline, designed and implemented the isolated runner,
added tests and documentation, updated the repository map, and ran local
validators.

Human decisions are separated as follows:

- Product: expose one public `bunya-jido codex-run` command and keep live
  nested validation, benchmark claims, release, and publication outside MVP.
- Engineering: use an independent module, require a clean actual-run baseline,
  and prevent non-`MATCH` sandbox escalation.
- Design: use a compact JSON plus Markdown result contract and defer an HTML
  report while preserving the existing viewer design.

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
