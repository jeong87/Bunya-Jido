# OpenAI Build Week 2026

Bunya-Jido predates Build Week: it turns a repository into a reviewed semantic
map that people and coding agents share. What Build Week added is the
execution half of that idea — a guarded way to hand one validated map route to
Codex, and receipts that show exactly what Codex did with it.

## Evidence boundary

Judging a pre-existing project needs a clear line between old and new work.

| | |
| --- | --- |
| Baseline commit (pre-Build Week) | `a01d26bb9843252856f7fd2b952943c687d17641` — July 2, 2026 |
| Build Week branch | `build-week-2026`, first commit July 18, 2026 |
| Primary Codex session | `019f73d5-d0c4-7633-8f08-fd8fb5933b3b` |
| Session model (local rollout metadata) | `turn_context.model` = `gpt-5.6-sol`, July 18, 2026 |
| Approved live observations | one read-only boundary smoke from `3544c198f7c1279fb96084790f109cd5ac38b34b`; one bounded workspace-write integration smoke recorded July 20 |
| Cross-platform CI | [run 29641266678](https://github.com/jeong87/Bunya-Jido/actions/runs/29641266678), green at `f10182c97d5f139703063ad60876c3ccb9d64547` |

Everything in the baseline — repository scanning, blueprint generation, the
offline atlas, task-aware context decisions, execution-policy recommendations,
worktree auditing, agent-utility evaluation, benchmarks, guide generation, and
stale-map checks — predates Build Week. So do the GPT-5.5 benchmark numbers in
the README. None of it is claimed as Build Week work. The baseline passed 97
unit tests plus blueprint, agent-map, diagnostics, and atlas-quality
validation before the first Build Week commit.

## What Build Week added

```bash
bunya-jido codex-run --root ROOT --task TASK
```

One command that turns a map route into a guarded Codex execution.

The route decision picks the sandbox. Only a confident `MATCH` gets
`workspace-write`; `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`, `UNCERTAIN`, and
`DISABLED` all run read-only, and no CLI flag can escalate that. An actual run
requires a clean worktree; `--preview` shows the decision, sandbox, scoped
context, and exact argv without launching anything.

After the run, a boundary audit combines the final git state with every write
attempt seen in the Codex JSONL stream — so writing outside the declared
safe-edit paths counts as a violation even if the file was reverted before the
end. A malformed or incomplete stream fails the run as `audit_incomplete`
rather than pretending the audit passed.

Each run ends with two additive receipts in `run.json` (schema
`bunya-jido-codex-run-v1`): a route receipt (route ID and fingerprint shared
with the atlas, first reads, tests, edit boundaries) and an efficiency receipt
(compact-context bytes, actual Codex token usage, elapsed time, changed-file
count, boundary verdict). The offline atlas opens a local `run.json` and
overlays the expected route, the actual changes, and any violations on the
same map people already use — the overlay only activates when route ID and
fingerprint match.

Scenario playback now makes evidence-backed routes easier to follow with
focused dimming, a moving route marker, and compact step explanations.

Plumbing choices that matter for safety: the prompt travels as UTF-8 over
stdin with argv execution (`shell=False`); Codex web search and
workspace-shell network access are both explicitly disabled; user and
trusted-project execpolicy `.rules` are ignored so automation behaves the same
on every machine (administrator-managed requirements are not bypassed).

## What this doesn't prove

The current 117-test suite drives a deterministic fake Codex executable
through success, boundary violations, write-then-revert,
renames, malformed and empty JSONL, cancellation, timeout, and
injection-shaped input. That proves the orchestration contract, not the
behavior of a live Codex OS sandbox. Two separately approved observations are
recorded in [docs/build-week/TESTING.md](docs/build-week/TESTING.md): one
read-only boundary smoke and one bounded workspace-write integration smoke.
Neither is cross-platform, exhaustive sandbox, or performance evidence. There
is no new GPT-5.6 benchmark. A single run never reports tokens saved — that
number only exists in paired map-vs-no-map comparisons — and token usage
missing from the stream is recorded as unavailable, never estimated.

## How Codex and I split the work

Codex (GPT-5.6, session above) inspected the baseline, then wrote the runner
(`src/bunya_jido/codex_run.py`, ~900 lines), the tests (~800 lines), the atlas
overlay, and the documentation and map updates, and ran the local validators.
The calls I made, recorded in
[docs/build-week/DECISIONS.md](docs/build-week/DECISIONS.md): keep the
reviewed semantic map as the product; implement `codex-run` as an isolated
module that reuses the existing context and audit contracts; require a clean
baseline before any actual run; never let a non-`MATCH` decision become
writable; and extend the existing offline viewer instead of inventing a new
report format.

## Try it

From a clean checkout — the test suite needs no Codex authentication:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m bunya_jido codex-run --root . --task "Implement guarded Codex run orchestration and boundary reporting." --preview
```

Full validation results are in
[docs/build-week/TESTING.md](docs/build-week/TESTING.md), the decision log in
[docs/build-week/DECISIONS.md](docs/build-week/DECISIONS.md), and the complete
command contract in [docs/GUARDED_CODEX_RUN.md](docs/GUARDED_CODEX_RUN.md).
Live nested Codex runs remain an explicit human approval gate.
