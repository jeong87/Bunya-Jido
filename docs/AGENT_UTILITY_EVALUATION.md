# Agent Utility Evaluation

Bunya-Jido creates a bounded task handoff for coding agents. That handoff is
useful only if it exposes the intended first reading, tests, and boundaries
without inventing guidance for uncovered work.

This protocol keeps two claims separate:

- Automated evaluation checks what trusted context Bunya-Jido emits.
- Live-agent observation checks whether an agent actually reads and follows
  that context during work.

The first can be a deterministic CI gate. The second requires recorded
observation and is never implied by a passing CI run.

## Committed Acceptance Suite

A mapped repository may commit
`.bunya-jido/bunya-jido.agent-evaluation.json`. Each case supplies a task or
changed-file query and expected bounded-context output.

Run the strict suite from the repository root:

```bash
bunya-jido evaluate-agent-utility --root . --require-pass --json
```

The Bunya-Jido self-map currently covers:

| Dimension | Automated evidence |
|---|---|
| `first_read_accuracy` | A focused task selects its intended route and required reading. |
| `test_recall` | A focused task exposes the tests needed for the route. |
| `boundary_discipline` | A sensitive change exposes its contract and safe-edit boundary without unrelated guidance. |
| `honest_no_match` | Unsupported, weak-overlap, and in-scope-unmapped tasks emit no false trusted route and the expected decision. |
| `change_aware_refresh` | A changed source file selects only routes justified by mapped evidence. |

The report deliberately includes a limitation: it evaluates generated context,
not autonomous agent behavior.

## Writing Cases

Keep cases small and reviewable:

1. Choose task wording that identifies one authored route, unless multiple
   routes are intentionally expected.
2. Record only expectations that the agent handoff must expose, such as
   `decision`, `execution_policy`, `routes`, `must_read`, `tests`, `contracts`,
   and `safe_edit`.
3. Include multiple `not_found` tasks: reviewed `OUT_OF_SCOPE`, ambiguous
   `UNCERTAIN`, and `IN_SCOPE_NO_ROUTE` when the repository scope supports it.
4. Include adversarial wording that shares generic or broad terms with routes.
5. Include a changed-file case when `refresh-context` is part of the
   repository workflow.
6. Update the suite alongside agent-map changes and run the strict command.

The report includes a decision confusion matrix and deterministic P1 safety
metrics. Any expected non-`MATCH` case automatically fails if generated
context exposes a trusted route or safe-edit path. Expected execution policy
defaults from the decision when a case does not state it explicitly:
`MATCH=workspace_write`, `IN_SCOPE_NO_ROUTE=read_only_discovery`, and
`OUT_OF_SCOPE/UNCERTAIN=read_only`.

An ambiguous natural-language query should normally produce `UNCERTAIN`
instead of several trusted routes. Changed-file refresh may still return
multiple routes when each one is independently justified by file evidence.

## Live-Agent Observation

Use this layer only when making a behavioral claim about real coding agents:

1. Start from a clean checkout with activated native agent instructions.
2. Give the agent each committed evaluation task without separately naming the
   expected route.
3. Record whether it requested context first, which files it read before
   editing, which tests it chose, whether it crossed a guarded boundary, and
   how it responded to the no-match task.
4. For changed-file cases, record whether it requested refreshed context after
   its edits.
5. Store the observation date, agent/version, repository commit, task text,
   and deviations in the pull request or release evidence.
6. Record whether the integration enforced the reported execution policy and
   audit final production changes separately from JSONL write attempts.

Optionally repeat the same tasks without activated instructions as a baseline.
Do not combine results from different agent versions or prompts without
identifying them.

## Public Claim Boundary

A passing committed suite supports this claim:

> The mapped repository emits bounded agent context that satisfies its
> reviewed acceptance cases.

It does not support this stronger claim without live observation:

> Coding agents reliably follow the map during autonomous implementation.
