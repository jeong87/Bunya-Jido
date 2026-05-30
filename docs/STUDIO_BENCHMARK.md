# Studio Atlas Benchmark

This benchmark checks whether Studio atlas output can vary honestly across
repository shapes. It tests the contract and rendering surface; it does not
claim that an automated judge can select the best editorial interpretation.

## Executed Fixture Matrix

`tests/fixtures/studio_benchmark_cases.json` records rubric traits rather than
a single universal graph. `tests/test_studio_benchmark.py` constructs and
validates compact Studio v2 atlas outputs from those rubrics, evaluates atlas
quality, and renders each output through the offline viewer.

| Repository shape | Primary reading | Scenario expectation |
|---|---|---|
| Workflow/agent system | Decision to auditable record | Grounded behavioral playback |
| Semantic map tool | Trusted publication | Grounded behavioral playback |
| Web/state application | Interaction loop | Grounded behavioral playback |
| SDK/client | Public client contract | Structural tour only |
| Compiler/parser | Transformation stages | Grounded behavioral playback |
| Utility library | API reading route | `none_with_reason` |

The test enforces distinct theses and primary projection labels, accepts all
three scenario policies, and specifically prevents SDK or utility fixtures
from being presented as invented runtime lifecycles.

## Complex Workflow Review Policy

Auto-Researcher is treated as a difficult external review target, not a seed.
On May 30, 2026, the current public checkout was reviewed through its README,
package entrypoint, orchestration, backend, artifact, failure-routing, memory,
budget, and report-review surfaces. That source review supports the need for a
complex workflow case, but no Auto-Researcher atlas JSON, plane vocabulary, or
scenario name is copied into Bunya-Jido prompts or viewer defaults.

A future human review run may generate an Auto-Researcher Studio atlas from its
current repository evidence, then compare its thesis, landmarks, boundaries,
ordered flows, and first-screen readability with this rubric. The generated
atlas must remain an evaluation output, never a generation input.

## Running The Benchmark

```bash
python -m unittest tests.test_studio_benchmark
python -m bunya_jido evaluate-atlas-quality --root . --require-pass --json
```

The first command proves multi-domain contract and renderer behavior. The
second checks the committed Bunya-Jido Studio self-map after publication.
