# Judge Quick Test

## What this demonstrates

- One evidence-grounded semantic map shared by people and coding agents.
- Evidence-backed scenario playback and a validated coding-agent route.
- A Codex run receipt returned to the same offline atlas.
- Expected route versus exact evidence-linked changed paths.
- Honest context and token-use reporting without a single-run savings claim.

## 60-second test

1. Open the [live demo](https://jeong87.github.io/Bunya-Jido/demo.html).
2. Click **Scenarios**.
3. Play **Request Bounded Agent Context** at **2×**.
4. Exit playback, open **Filters**, and inspect **Validated Task Routes**.
5. Click **Load sample receipt**.
6. In **Run Evidence**, inspect the expected route, actual changed path,
   context/token receipt, and `passed` boundary verdict.

If the optional button is not present in the deployed build, download
[`judge-sample-run.json`](judge-sample-run.json), click **Open run.json**, and
select that file. Both paths use the same schema, route-fingerprint gate, and
overlay renderer.

## Credentials

None. The browser test does not require a Codex login, API key, installation,
or live Codex execution.

## Important evidence note

The sample is a sanitized demonstration fixture derived from the verified
Build Week run report. It is provided for UI evaluation and is not presented
as the raw live Codex execution artifact. A single run does not claim token
savings. Optional live `codex-run` use requires the judge's own authenticated
local Codex CLI and is not required for evaluation.

## Source and evidence

- [Submission source](https://github.com/jeong87/Bunya-Jido/tree/build-week-2026)
- [Build Week evidence boundary](../../BUILD_WEEK.md)
- [Testing record](TESTING.md)
- [Sample receipt](judge-sample-run.json)
- [Current demo](../demo.html)
