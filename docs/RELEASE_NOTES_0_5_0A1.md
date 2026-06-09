# Bunya-Jido 0.5.0 Alpha 1

This is Bunya-Jido's first public alpha release.

## What Bunya-Jido Is

Bunya-Jido creates offline semantic repository maps for humans and bounded
task context for coding agents. It combines deterministic repository evidence
with reviewable coding-agent interpretation, then validates and renders the
result as a single HTML map plus `.bunya-jido/` agent-context artifacts.

## Who This Alpha Is For

This alpha is best for maintainers and coding-agent users who want to test
semantic repository maps on Python-heavy projects with nontrivial workflows.
It is especially relevant for developer tools, automation, research, and
agent-oriented repositories.

## 5-Minute Quick Start

```bash
python -m pip install --pre bunya-jido
bunya-jido --version
```

Then, from the repository you want to map, ask a coding agent:

```text
Run `bunya-jido prepare --root . --atlas-mode studio --quiet`, then read and execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`; validate the blueprint and agent map; run `bunya-jido build --root . --out bunya-jido.html`; confirm the HTML path and say `ready`.
```

Open `bunya-jido.html` in a browser.

## What Is New

- Studio semantic atlas mode with projections, scenario policy, narrated
  scenario playback, and atlas-quality checks.
- Decision-aware agent context: `MATCH`, `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`,
  `UNCERTAIN`, and `DISABLED`.
- Native agent activation for Codex, Claude Code, Cursor, and Cline, with
  persistent deactivation via `install-agent-guides --deactivate`.
- Worktree auditing for live-agent benchmark runners, including untracked
  files, generated/cache noise, and Codex JSONL write attempts.
- Token and time efficiency summarizers that compare only paired
  safe-and-resolved benchmark runs.
- Runtime no-map opt-out with `BUNYA_JIDO_CONTEXT=off` or
  `BUNYA_JIDO_DISABLE_CONTEXT=1`.
- Benchmark provenance fields for Bunya-Jido version, git commit SHA, and
  agent-map SHA-256.

## Benchmark Evidence

In two synchronized synthetic Python benchmark repositories, Bunya-Jido
preserved bugfix success while reducing GPT-5.5 Medium repair tokens:

| Synthetic repo | Bugfix success | Token change | Time change |
| --- | ---: | ---: | ---: |
| 28.7K SLOC | 24/24 -> 24/24 | -18.8% | -28.0% |
| 126.7K SLOC | 39/39 -> 39/39 | -22.8% | -12.5% |

Synthetic benchmark; GPT-5.5 Medium; three repetitions per scenario. These
results do not prove equivalent gains on production repositories. See
`docs/BENCHMARKS.md` for methodology and limitations.

## Known Limitations

- Python repositories are currently the strongest supported target.
- Semantic map authoring requires a capable coding agent and a meaningful
  initial token budget.
- Small repositories may not recover the authoring cost.
- A trusted route can still point to a downstream compensation path rather
  than the root-cause owner.
- `IN_SCOPE_NO_ROUTE` two-stage discovery depends on integrations honoring
  the read-only discovery contract.
- Synthetic benchmark results do not prove production generalization.

## Feedback

Please report issues with:

- repository type and approximate size;
- Bunya-Jido version and git commit SHA;
- whether the task was `MATCH`, `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`,
  `UNCERTAIN`, or `DISABLED`;
- the generated context output when it is safe to share;
- whether the HTML map, agent context, or benchmark/audit behavior was wrong.
