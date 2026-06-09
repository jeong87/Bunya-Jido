# Bunya-Jido Benchmarks

This page summarizes the public benchmark evidence for the `0.5.0a1` alpha.
It is intentionally short; detailed reports are linked at the end.

## Recent Dual-Scale Synthetic Benchmark

The latest benchmark reran no-map and generated-map conditions in the same
test window on two synthetic Python repositories. The repair agent was
GPT-5.5 Medium through Codex CLI, with web search disabled and three
repetitions per scenario.

| Synthetic repository | Scale | Bugfix scenarios | No-route scenarios | Bugfix success | Bugfix token change | Bugfix time change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Realistic Large | 28.7K SLOC, 1,432 Python files | 8 | 1 | 24/24 -> 24/24 | -18.8% | -28.0% |
| Enterprise XLarge | 126.7K SLOC, 5,926 Python files | 13 | 2 | 39/39 -> 39/39 | -22.8% | -12.5% |

Across both repositories, the mapped condition preserved all 63 bugfix
successes while reducing repair tokens by 21.6% and cumulative bugfix
wall-clock time by 17.0%. All nine unsupported mobile or infrastructure
requests ended in read-only paths with no production-file changes.

These are synthetic benchmark results. They do not prove equivalent gains on
production repositories.

## Method Summary

- Conditions: no-map baseline vs. fresh generated Bunya-Jido map.
- Map timing: authored from the clean repository, frozen before defect
  injection, and queried with `bunya-jido context --json` during repair.
- Agent: GPT-5.5 Medium via Codex CLI.
- Repetitions: three per scenario.
- Tests: public tests ran during the repair; hidden tests ran only in a
  separate grading copy after the agent finished.
- File accounting: combined `git diff`, `git status --porcelain
  --untracked-files=all`, and Codex JSONL `file_change` events.
- Generated noise: runtime/cache artifacts such as `__pycache__`, `*.pyc`,
  and `*.pyo` were excluded from production-change accounting.

## Interpretation

The strongest supported claim is navigation efficiency on the measured
synthetic Python suites: Bunya-Jido preserved bugfix success while reducing
repair tokens and cumulative time.

The no-route savings should be read as safe abstention evidence, not ordinary
repair efficiency. The mapped agent recognized that unsupported requests were
outside the repository's product surface and stopped without production
changes.

`IN_SCOPE_NO_ROUTE` evidence is promising but narrower: in the Enterprise
XLarge decoy-heavy tasks, bounded discovery completed all nine runs and
reduced token use by 27.7%. The full integration pattern should still enforce
read-only discovery before any later edit approval or rematched context.

## Limitations

- Both benchmark repositories are synthetic.
- The benchmark covers Codex CLI and GPT-5.5 Medium only.
- The suite contains 21 bugfix scenarios and three no-route scenarios, each
  repeated three times.
- The no-route tasks are relatively clear product-surface mismatches; more
  ambiguous scope boundaries need separate tests.
- Hidden tests check functional behavior, not long-term maintainability.
- Boundary accounting uses the direct mutation target; a different defensible
  implementation may still be counted as a boundary violation.
- Break-even estimates exclude map refresh, review, and maintenance after
  repository changes.
- Raw token counts do not equal API billing because cached-input pricing and
  subscription economics differ.
- Wall-clock time is sensitive to backend latency and local I/O.

## Detailed Reports

- [Recent dual-scale report, English](BUNYA_JIDO_RECENT_DUAL_SCALE_REPORT_EN.md)
- [Recent dual-scale report, Korean](BUNYA_JIDO_RECENT_DUAL_SCALE_REPORT_KO.md)
- [Complete benchmark chronicle, Korean](BUNYA_JIDO_COMPLETE_BENCHMARK_CHRONICLE_KO.md)
