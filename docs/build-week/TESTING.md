# Build Week Testing

## Baseline

At commit `a01d26bb9843252856f7fd2b952943c687d17641`, before Guarded Codex
Run implementation:

- 97 unit tests passed.
- `python -m compileall -q src tests` passed.
- Blueprint validation passed.
- Agent-map validation passed.
- Grounded diagnostics passed.
- Agent utility passed 18 of 18 cases.
- Atlas quality validation passed.

## Focused Fake-Codex Coverage

`tests/test_codex_run.py` covers:

- `MATCH`, `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`, `UNCERTAIN`, and `DISABLED`
  sandbox mapping.
- Inability to raise a non-`MATCH` decision to writable.
- Dirty preview success and dirty actual-run blocking.
- Unicode, spaces, quotes, and command-injection-shaped task/root values.
- Successful `MATCH` writes within exact safe-edit boundaries.
- Read-only success for every non-`MATCH` decision.
- Unsafe paths, untracked files, renames, outside-workspace events, and
  write-then-revert attempts.
- Codex non-zero, missing executable, timeout, keyboard cancellation, malformed
  JSONL, empty JSONL, partial readable events, stderr, and last-message
  preservation.
- Schema v1 fields, status and exit-code priority, relative artifact paths, and
  deterministic injected run IDs and clocks.
- Shared route ID/fingerprint parity between run artifacts and HTML task-route
  presets.
- Context byte counts, exact single-event Codex token usage, unavailable and
  partial usage, rejection of negative token counts, and refusal to sum
  multiple usage events.
- Raw execution argv preservation alongside structured POSIX and Windows path
  redaction for human-facing previews, with task text left unchanged.
- Human Markdown rendering of a missing total as `unavailable`, without
  displaying Python `None`.
- Combined malformed JSONL and boundary violations preserve both reasons while
  failing with the contractually stronger `audit_incomplete` status.
- Single-run `tokens_saved` unavailability and the paired no-map requirement.

The viewer smoke coverage verifies the offline local-file import surface,
schema gate, route fingerprint gate, exact evidence-path mapping, overlay
legend, 5 MiB limit, and route-fragment support. Generated HTML also passes a
JavaScript syntax check. Interactive browser QA remains pending because no
controllable browser was connected during this work; no live Codex process is
needed for that future check.

The fake executable verifies Bunya-Jido's command construction, capture, policy,
and audit logic. It does not prove the behavior of a live Codex OS sandbox.

## Required Local Validation

The current CLI help was inspected on July 18, 2026. All commands and options
below are supported as written; no compatibility substitution is required.

```bash
python -m unittest -v tests.test_codex_run
python -m unittest discover -s tests -v
python -m compileall -q src tests
python -m bunya_jido validate-blueprint --root .
python -m bunya_jido validate-agent-map --root .
python -m bunya_jido diagnose --root . --require-grounded --json
python -m bunya_jido evaluate-agent-utility --root . --require-pass --json
python -m bunya_jido evaluate-atlas-quality --root . --require-pass --json
python -m bunya_jido check-stale --root . --git-diff "origin/main...HEAD" --require-reviewed
```

Run `bunya-jido refresh-context --root . --changed-file <path>` for every
changed file before the stale check.

## Shared Route And Receipt Slice

The strong visual submission slice was validated locally on July 19, 2026:

- A fresh Python 3.12 virtual environment installed the worktree with
  `python -m pip install -e .`.
- Focused fake-Codex suite: 15 of 15 passed.
- Full unit suite: 114 of 114 passed.
- `python -m compileall -q src tests`: passed.
- Blueprint: grounded, 15 nodes, 32 relationships, no warning or blocker.
- Agent map: 8 of 8 routes validated.
- Grounded diagnostics: passed.
- Agent utility: 20 of 20 cases passed.
- Atlas quality: passed with one explicit human-review warning and no
  deterministic warning or blocker.
- The committed demo was rebuilt; its semantic golden test and generated
  JavaScript syntax check passed.
- All 21 implementation, test, map, demo, and documentation files owned by
  this slice received a matched `refresh-context` result.
- Both the required `origin/main...HEAD` stale check and the supplemental
  working-diff stale check reported `review_recorded`.

No new CI run, live Codex run, cross-platform live behavior, or token-savings
claim is attached to this uncommitted slice. Interactive browser QA remains
pending for the reason recorded above.

## Scenario Playback Visual Refinement

The uncommitted July 21 viewer refinement uses the actual
`scenario:agent_context` data and does not change any public schema.

- `tests.test_blueprint_v2`: 13 of 13 passed, including generated HTML hooks
  for full-route state, current-edge classification, clipped route marker,
  compact grounded card projection, viewport placement, reduced motion,
  run-overlay restoration, and one RAF loop.
- `tests.test_self_map`: 18 of 18 passed, including the actual
  `Request Bounded Agent Context` node, edge, narration, and evidence
  sequence.
- `tests.test_smoke`: 4 of 4 passed.
- Focused Guarded Codex Run suite: 16 of 16 passed.
- Full local unit suite: 117 of 117 passed.
- Compile, blueprint validation, agent-map validation, grounded diagnostics,
  20-case agent utility, and deterministic atlas-quality checks passed.
- The generated `docs/demo.html` contains the route-marker and step-card hooks
  and contains none of the visual-reference product identifiers.

Interactive browser QA is not claimed. The prescribed browser runtime exposed
no connected browser, so desktop and small-viewport interaction, console,
run-overlay restoration, and screenshot checks remain pending. No unrelated
browser automation backend was substituted, and video editing has not started.

## CI Incident at `b03f510`

GitHub Actions run `29635239405` failed at the `Run tests` step on Ubuntu
Python 3.10, 3.11, and 3.12, macOS Python 3.12, and Windows Python 3.12. All
five jobs reported the same two failures:

- `test_committed_self_map_and_routes_are_grounded`: the Guarded Codex Run
  route referenced ignored file `.bunya-jido/ATLAS_QUALITY_REPORT.md`.
- `test_published_demo_matches_stable_semantic_contract`: a clean rebuild
  included that missing-path warning while the committed demo, generated in a
  development worktree where the ignored file existed, did not.

A clean Python 3.12 virtual environment at `b03f510` reproduced 2 failures out
of 111 tests. A separate clean Python 3.12 environment at baseline
`a01d26bb9843252856f7fd2b952943c687d17641` passed 97 of 97 tests. This is a
Build Week regression, not a baseline failure.

The earlier local 111-of-111 result was valid only for the development
worktree state in which the ignored report existed. It was not clean-checkout
or cross-platform evidence. The corrective change removes that ignored path
from the route and adds a regression requiring safe-edit entries to resolve to
Git-tracked content.

## Stabilization Results

- A fresh Python 3.12 virtual environment installed the corrective worktree
  with `python -m pip install -e .`.
- Focused Guarded Codex Run suite: 13 of 13 passed in that environment.
- Full unit suite: 112 of 112 passed in that environment.
- `python -m compileall -q src tests`: passed.
- Blueprint: grounded, 15 nodes, 32 relationships, no warnings or blockers.
- Agent map: 8 of 8 routes validated with no warning or error.
- Grounded diagnostics: passed.
- Agent utility: 19 of 19 cases passed.
- Atlas quality: passed with one explicit human-review warning about primary
  projection choice and no deterministic warning or blocker.
- The self-map demo was rebuilt and its semantic golden test passed.
- Guarded preview reported `MATCH`, `workspace-write`,
  `execpolicy_rules_ignored=true`, `web_search_mode=disabled`, workspace
  network `false`, and `launched=false`.
- Every changed implementation, test, map, and documentation file received a
  matched `refresh-context` route after normalizing the Build Week
  documentation scope to the declared directory `docs/build-week/`.
- The required `origin/main...HEAD` stale-map check and a supplemental
  working-diff stale-map check both reported `review_recorded`.
- Corrective cross-platform CI:
  [run `29641266678`](https://github.com/jeong87/Bunya-Jido/actions/runs/29641266678)
  completed successfully at
  `f10182c97d5f139703063ad60876c3ccb9d64547`.
- Successful jobs: Ubuntu Python 3.10, 3.11, and 3.12; macOS Python 3.12;
  Windows Python 3.12; and semantic-map review.
- A disposable clean clone at corrective commit
  `3544c198f7c1279fb96084790f109cd5ac38b34b` passed the documented preview and
  live read-only smoke.
- Cross-platform success is limited to the fake-executable and repository
  validation exercised by that CI matrix. It is not cross-platform live Codex
  sandbox evidence.
- Live nested Codex validation: one explicitly approved read-only smoke
  succeeded; details and limitations are recorded below.
- The fake executable verifies Bunya-Jido's command construction, capture,
  policy, and audit logic. It does not prove the behavior of a live Codex OS
  sandbox.

## Disposable Live Smoke Protocol

This protocol was approved and run once on July 18, 2026. Future live runs
still require a new product-owner approval. Use a disposable clean clone, a
separately installed and authenticated Codex CLI, and the exact corrective
commit selected for submission.

1. Clone the approved `build-week-2026` revision into a temporary directory,
   install it with `python -m pip install -e .`, and confirm
   `git status --porcelain` is empty.
2. Run preview with the bounded out-of-scope task below and confirm the decision
   is `OUT_OF_SCOPE`, the sandbox is `read-only`, and execution is not launched:

   ```bash
   python -m bunya_jido codex-run --root . --task "Add a native iOS app with App Store signing." --preview --json
   ```

3. Only after immediate human approval, run the same command without
   `--preview`. Do not add a sandbox override, network flag, dirty-worktree
   bypass, or arbitrary Codex argument.
4. Confirm the final Git audit reports no production changes or write attempts.
   Remove the disposable clone after preserving the reviewed run artifacts.

Expected `.bunya-jido/runs/<run-id>/` artifacts are `run.json`, `report.md`,
`events.jsonl`, `stderr.log`, and `last-message.txt`. For a successful smoke,
`run.json` should record schema `bunya-jido-codex-run-v1`, decision
`OUT_OF_SCOPE`, sandbox `read-only`, `web_search_mode` `disabled`,
`execpolicy_rules_ignored` `true`, `workspace_network_access` `false`, a
launched process with return code `0`, complete JSONL, no production boundary
violation, status `succeeded`, and exit code `0`.

One successful smoke is evidence for the observed installed Codex version and
that disposable environment only. It is not an exhaustive safety,
cross-platform, or workspace-write proof.

## Approved Live Smoke Result

- Date: July 18, 2026.
- Source commit: `3544c198f7c1279fb96084790f109cd5ac38b34b`.
- Environment: disposable clean Windows clone, Python 3.12, Codex CLI
  `0.144.5`.
- Run ID: `20260718T103801Z-8885b3dd`.
- Task decision: `OUT_OF_SCOPE`.
- Codex sandbox: `read-only`.
- Invocation controls: approval `never`, user config ignored, user/project
  execpolicy rules ignored, web search `disabled`, workspace-shell network
  `false`, ephemeral JSONL execution.
- Process: launched, return code `0`, no timeout or cancellation.
- Audit: four valid JSONL events, complete stream, production-clean worktree,
  no production write attempts, outside-workspace attempts, or boundary
  violations.
- Result: schema `bunya-jido-codex-run-v1`, status `succeeded`, exit code `0`,
  and all five expected artifacts present.
- Artifact hashes:
  - `run.json`:
    `ca8f9826ff19a8807e2a99b4baec9b8817373560c0931154b0559f60f729f3e3`
  - `events.jsonl`:
    `992f3027e4efa261d44f753f51bd32e0fea9761ec3d55c45c293dfe66c9e1245`
  - `last-message.txt`:
    `fb7329f9552e81e859166b18f21cfbf41d07d928b118f14fe0cca000e7e52425`
- Stderr contained one non-fatal Codex warning that PowerShell shell snapshots
  are not yet supported. It did not change the return code, JSONL
  completeness, worktree audit, or boundary result.

The live process returned the reviewed repository-boundary explanation and
made no file changes. This result validates only the observed read-only path
for the versions and environment above. It does not prove `workspace-write`
enforcement, other operating systems, other Codex versions, performance, or
the model identity used by the provider.

## Second Approved Live Run — July 20, 2026 (workspace-write)

Product-owner approved, run for the Build Week demo video. Disposable clean
clone of `build-week-2026`, Linux Codex CLI under WSL Ubuntu, task
`Change guarded Codex run orchestration: clarify the route receipt
explanation in the codex_run.py module docstring with one short sentence.
Make exactly one small docstring edit.`

- Run ID `20260720T062213Z-bd704b40`, decision `MATCH`, sandbox
  `workspace-write`, status `succeeded`, exit code `0`.
- Exactly one changed file (`src/bunya_jido/codex_run.py`, one docstring
  sentence), inside the declared safe-edit boundary; boundary result
  `passed`.
- Recorded usage from the single complete `turn.completed` event: input
  182,823 · cached input 159,232 · output 1,652 · reasoning 367. Elapsed
  54.9 s. Compact context 3,095 UTF-8 bytes.
- Run artifacts are retained locally for the demo video and are not
  committed.

A first attempt on native Windows (run `20260720T…` earlier the same day) is
recorded as a platform observation: Codex reported its OS sandbox as
effectively read-only despite the requested `workspace-write`, made no file
changes, and the run finished `succeeded` with zero changed files. The
guarded contract held in the restrictive direction. Neither run is
performance or cross-platform enforcement evidence; each validates only the
observed environment.

## Final Demo Revision QA — July 20, 2026

The final demo revision reused the approved workspace-write smoke above. It did
not launch another live Codex process or claim new benchmark evidence.

- Original and backup SHA-256:
  `8edb417610cfcf8040f506e2174feb66c448b2fcc96ca0c197ea18b7f90b2b93`.
- Revised video:
  `openai_build_week_demo/bunya-jido-demo-narrated-final-revised.mp4`,
  SHA-256
  `fb8ee7ec5af07fd98cc729c8fffd89608cf9aa67e1e9a84cddac3f1a290701df`.
- Media contract: 168.033333 seconds, H.264, 1920 x 1080, 30 fps,
  `yuv420p`, AAC stereo at 48 kHz.
- Audio measurement: -16.01 LUFS integrated, -1.50 dBTP true peak, and
  4.70 LU loudness range.
- OpenAI transcription QA: passed, word error rate 0.012539, no missing
  required phrase.
- Focused runner suite: 16 of 16 passed. Full unit suite: 115 of 115 passed.
  Compile, blueprint, agent-map, grounded diagnostics, 20-case agent utility,
  atlas quality, changed-file context refresh, and stale-map review passed.
- Revised render fixtures contained no private home path,
  `codex_executable_not_found`, Python `None` token rendering, or the retired
  `real token usage` caption.
- The final contact sheet and explicit OUT_OF_SCOPE frame are retained under
  `openai_build_week_demo/audio/revision-20260720/qa/`.

## In-App Browser Demo Revision QA — July 21, 2026

This revision did not launch a new nested Codex process or change the spoken
narration. It replaced a static atlas interval with actual
`Request Bounded Agent Context` playback captured from the ChatGPT in-app
Browser.

- Browser behavior verified at 1920 x 1080: four authored steps, route
  dimming and emphasis, pause/play, previous/next, 2x playback, explicit exit,
  and Escape restoration.
- At 820 x 720, the measured narration card remained within the viewport.
- The tested flow produced zero browser console warnings or errors.
- Local run evidence import and post-scenario overlay restoration passed. The
  original July 20 `run.json` is no longer available, so this UI-only check
  used an explicitly marked QA fixture derived from the verified report. The
  fixture is not raw execution evidence.
- Approved browser-revised official video:
  `openai_build_week_demo/bunya-jido-demo-narrated-final.mp4`,
  SHA-256
  `26c3e0b6c01bdf6b08bb49942882ad6cbab4fdc2a9455b459ff83d88d9e61fc4`.
- Media contract: 165.933333 seconds, H.264, 1920 x 1080, 30 fps,
  `yuv420p`, AAC stereo at 48 kHz.
- Audio measurement: -16.00 LUFS integrated, -1.50 dBTP true peak, and
  4.90 LU loudness range.
- Retimed subtitle: 22 sequential, non-overlapping cues ending at
  165.380 seconds; the original wording is unchanged.
- No new transcription was run because no spoken cue content changed. The
  prior revised narration transcription remains the evidence for the voice
  content, while this revision separately validates the new SRT and media
  timing.
- Full unit suite: 117 of 117 passed after the browser/video revision.
- Detailed browser measurements, preservation hashes, media metadata, and
  artifact paths are recorded in
  `openai_build_week_demo/qa/browser-revision-qa-report.json`.

The browser motion is a 10 fps screenshot capture of the actual in-app
playback encoded into a 30 fps video segment, not a native screen recording.
The product owner approved replacing the official MP4/SRT with the verified
browser revision and delivering the reviewed changes to the
`build-week-2026` branch on July 21, 2026.
