# OpenAI Build Week 2026

## Evidence Boundary

- Baseline commit: `a01d26bb9843252856f7fd2b952943c687d17641`
- Baseline commit date: July 2, 2026
- Build Week branch: `build-week-2026`
- Primary Codex session ID: `<PRIMARY_CODEX_SESSION_ID>`

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

HTML reporting, benchmark claims, package release, and live nested Codex proof
are not part of this MVP.

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

The Build Week protocol requires Codex and GPT-5.6 contributions to be
distinguished. Repository evidence can verify the Codex-authored changes and
test results, but it cannot independently prove the model identity of this
session. A verified GPT-5.6 contribution statement must be added from session
metadata before submission; local configuration must not be treated as proof.

## Installation and Judge Testing

From a clean checkout:

```bash
python -m pip install -e .
python -m unittest -v tests.test_codex_run
python -m compileall -q src tests
bunya-jido codex-run --root . --task "change guarded Codex run orchestration" --preview
```

The focused suite uses a fake executable and does not require Codex
authentication. To test a live run, use a separate disposable clean checkout
with a locally installed and authenticated Codex CLI:

```bash
bunya-jido codex-run --root . --task "inspect guarded Codex run documentation"
```

A live nested Codex run is a separate human approval gate. Fake-executable
evidence must not be described as proof of a live Codex OS sandbox.

For the full validation set and current results, see
[`docs/build-week/TESTING.md`](docs/build-week/TESTING.md). Product and
engineering decisions are recorded in
[`docs/build-week/DECISIONS.md`](docs/build-week/DECISIONS.md).
