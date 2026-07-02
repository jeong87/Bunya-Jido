# Bunya-Jido Semantic Map Benchmark: Comprehensive Report

## 0. Purpose

This report consolidates the full benchmark program used to evaluate whether Bunya-Jido semantic maps improve repository-scale code repair by coding agents.

The program started with small synthetic repositories and expanded to a 126.7K-SLOC enterprise-scale synthetic platform. It tracked more than token savings. The central questions were:

1. Does a bounded semantic route reduce repository exploration cost?
2. Do native maps authored from a clean repository deliver the same benefit?
3. How many similar repairs are needed to recover map-authoring cost?
4. How does map utility change as repository scale increases?
5. What is the more economical operating point: `gpt-5.5-medium` or `gpt-5.5-xhigh`?
6. Is it useful to author a premium XHigh map once and reuse it with a Medium repair agent?
7. Can the semantic router refuse unsupported requests instead of inventing a route?

All results in this document come from **synthetic repository benchmarks**. Public open-source issue replay and production-repository validation remain future work.

---

## 1. Executive summary

### 1.1 Recommended operating strategy

The current evidence supports:

```text
Default:
Medium map authoring
+
Medium repair agent

Workflow-heavy / decoy-heavy / high-risk navigation tasks:
Keep the existing map
+
selectively escalate the repair agent to XHigh

Unsupported requests:
reject at the router layer with No matching trusted route
```

The evidence does **not** support:

```text
Author an expensive XHigh map first
+
use a Medium repair agent for routine work
```

For Medium repair agents, XHigh-authored maps did not improve everyday bugfix economics over Medium-authored maps. Core bugfix results were effectively tied, while one decoy-heavy run regressed sharply in boundary safety.

### 1.2 Benchmark progression

| Stage | Purpose | Repository scale | Repair runs | Key result |
| --- | --- | --- | ---: | --- |
| Curated route utility | Mechanism test with pre-authored routes | 3 early synthetic repos | 108 | Cumulative tokens **-25.3%** |
| Native generated-map pilot | Native Bunya-Jido map validation | 4 micro-to-small repos | 144 | Bugfix paired saving **15.86% ± 21.29%** |
| Realistic-large Medium E2E | Native end-to-end benchmark | 28.7K SLOC | 54 | Bugfix paired saving **43.56% ± 17.84%** |
| Realistic-large XHigh E2E | XHigh replication | 28.7K SLOC | 54 | Bugfix paired saving **36.53% ± 22.98%** |
| Enterprise XLarge Medium E2E | Enterprise-scale native E2E | 126.7K SLOC | 90 | Bugfix cumulative tokens **-40.48%** |
| Enterprise XLarge XHigh E2E | Enterprise-scale XHigh replication | 126.7K SLOC | 90 | Bugfix cumulative tokens **-44.45%** |
| Enterprise map-quality ablation | Change map quality for a Medium repair agent | 126.7K SLOC | 45 additional | XHigh map used **1.75% more bugfix tokens** than Medium map |

### 1.3 Wall-clock highlights

| Experiment | Timing result |
| --- | --- |
| Realistic-large Medium E2E | Overall cumulative elapsed time **-22.07%** |
| Enterprise Medium E2E | Core-bugfix elapsed time **-19.99%**, offset by decoy-heavy outliers |
| Enterprise XHigh E2E | Overall cumulative elapsed time **+9.09%**, while decoy-heavy stability improved |

Token reduction does not automatically imply latency reduction.

### 1.4 Auditable token usage

The completed benchmark program contains at least:

```text
127,897,183 auditable raw tokens
```

Including dry runs, probes, smoke tests, and discarded attempts, practical consumption is reasonably estimated at:

```text
130M–145M raw tokens
```

---

## 2. Experimental principles

### 2.1 Clean-first, freeze-first

Every native-map benchmark followed this sequence:

```text
clean repository
  ↓
Bunya-Jido prepare
  ↓
Codex native map authoring
  ↓
validation
  ↓
freeze map + SHA-256
  ↓
inject defects only after freeze
  ↓
baseline / generated-map repair
```

This prevents answer leakage into the map.

### 2.2 Hidden-test isolation

Hidden tests were never exposed to the repair agent.

```text
Codex repair exits
  ↓
temporary grading clone
  ↓
inject hidden tests
  ↓
run public + hidden tests
```

### 2.3 Paired comparisons

A pair consists of baseline and generated-map runs with the same repository, task, effort, and repetition index.

### 2.4 Strict no-match

No-match is not a fake bug. It is a router-safety test.

The request is deliberately outside the repository's responsibility boundary, such as asking a Python control-plane repository to add an iOS app or Terraform Kubernetes environment.

Expected behavior:

```text
No matching trusted route
```

Any production-file modification is recorded as a strict no-match failure.

---

## 3. Benchmark harness evolution

The initial telemetry-based workflow was not reliable enough for quantitative benchmarking. The harness evolved into a Codex CLI JSONL pipeline.

| Problem | Observation | Final mitigation |
| --- | --- | --- |
| Manual elapsed-time distortion | Idle UI time polluted timing | Use Codex subprocess elapsed time |
| OTel thread ambiguity | Multiple conversations mixed together | Measure `codex exec --json` directly |
| Missing usage events | Zero-token runs appeared valid | Require `turn.completed.usage` |
| Windows `cp949` decoding | UTF-8 JSONL failed under local defaults | Capture bytes and decode explicitly |
| Sandbox mismatch | Workspace writes failed | Use `--windows-sandbox unelevated` |
| CLI option mismatch | `--ask-for-approval` unsupported | Use config `approval_policy="never"` |
| Test modification | Agent edited grading material | Protected-file violation |
| Long Git paths | `.git\objects` hit Windows path limits | Short `%TEMP%` workspaces + `core.longpaths=true` |
| Grading-clone overhead | Copying `.git` became expensive | Exclude `.git` from grading clones |
| Reset bottleneck | Deleting many enterprise workspaces was slow | Separate fast result reset from workspace purge |
| Paired-stat double count | Early analyzer duplicated pairs | Recompute from raw JSON |

---

## 4. Experiment A: Curated Semantic Route Utility

This upper-bound mechanism test measured whether pre-authored bounded routes reduce exploration cost.

| Metric | Baseline | Curated mapped | Change |
| --- | ---: | ---: | ---: |
| Repair runs | 54 | 54 | equal |
| Resolved | 53 / 54 | 54 / 54 | +1 |
| Cumulative total tokens | 7,164,603 | 5,355,288 | **-25.3%** |
| Mean total tokens per run | 132,678 ± 37,561 | 99,172 ± 37,961 | **-25.3%** |
| Bugfix cumulative reduction |  |  | **29.8%** |

Interpretation: good routes can reduce repository exploration, but this does not measure native authoring cost.

---

## 5. Experiment B: Native Generated-Map Pilot

The pilot authored and froze native Bunya-Jido maps before injecting defects.

### 5.1 Repository scale

| Historical ID | Approx. SLOC | src Python files | Realistic band |
| --- | ---: | ---: | --- |
| `small_cli` | 52 | 11 | micro |
| `medium_service` | 123 | 32 | micro |
| `large_workflow` | 256 | 74 | micro |
| `xlarge_control_plane` | 2,691 | 248 | small |

### 5.2 Map-authoring cost

| Repo | Tokens | Seconds |
| --- | ---: | ---: |
| `small_cli` | 780,751 | 409.03 |
| `medium_service` | 1,460,829 | 541.39 |
| `large_workflow` | 914,535 | 449.02 |
| `xlarge_control_plane` | 1,929,983 | 592.62 |
| **Total** | **5,086,098** | **1,992.06** |

### 5.3 Repair results

```text
24 tasks × 2 conditions × 3 repetitions = 144 runs
72 paired comparisons
```

| Scope | Pairs | Token saving % ± SD | Time saving % ± SD |
| --- | ---: | ---: | ---: |
| All | 72 | **4.81% ± 47.61%** | -4.67% ± 59.58% |
| Bugfix | 60 | **15.86% ± 21.29%** | 4.18% ± 39.47% |
| No-match | 12 | **-50.45% ± 90.58%** | -48.92% ± 109.50% |

Takeaway: native maps helped ordinary bugfixes on average, but no-match required separate treatment.

---

## 6. Experiment C: `realistic_large_platform`

### 6.1 Repository

| Metric | Value |
| --- | ---: |
| Approximate SLOC | 28,708 |
| src Python files | 1,432 |
| Responsibility areas | 27 |
| Tasks | 9 |
| Repair runs per effort | 54 |

### 6.2 Medium E2E

| Metric | Value |
| --- | ---: |
| Map-authoring tokens | 1,748,486 |
| Map-authoring seconds | 648.22 |
| Resolved repair runs | 54 / 54 |
| Cumulative total-token reduction | **42.23%** |
| Mean paired total-token saving | **39.52% ± 22.30%** |
| Bugfix paired token saving | **43.56% ± 17.84%** |
| Initial bugfix break-even | **18.06 tasks** |
| Boundary violations | 0 |

### 6.3 XHigh E2E

| Metric | Value |
| --- | ---: |
| Map-authoring tokens | 2,891,143 |
| Map-authoring seconds | 1,069.78 |
| Resolved repair runs | 54 / 54 |
| Cumulative total-token reduction | **37.40%** |
| Bugfix paired token saving | **36.53% ± 22.98%** |
| Initial bugfix break-even | **28.36 tasks** |
| Boundary violations | 0 |

Interpretation: Medium was the better economic operating point at 28.7K SLOC.

---

## 7. Experiment D: `enterprise_xlarge_platform`

### 7.1 Repository

| Metric | Value |
| --- | ---: |
| Approximate SLOC | 126,731 |
| src Python files | 5,926 |
| Responsibility areas | 48 |
| Tasks | 15 |
| Repair runs per effort | 90 |

### 7.2 Medium E2E

| Metric | Value |
| --- | ---: |
| Map-authoring tokens | 1,527,492 |
| Map-authoring seconds | 759.46 |
| Cumulative total-token reduction | **29.82%** |
| Bugfix cumulative token reduction | **40.48%** |
| Bugfix paired token saving | **31.24% ± 53.39%** |
| Core-bugfix paired saving | **45.85% ± 24.94%** |
| Initial bugfix break-even | **13.12 tasks** |
| Boundary violations | 539 → 11 |
| Strict no-match edit-free runs | 6 / 6 → 2 / 6 |
| Router rejection score | **0 / 6** |

### 7.3 XHigh E2E

| Metric | Value |
| --- | ---: |
| Map-authoring tokens | 3,122,221 |
| Map-authoring seconds | 1,042.54 |
| Cumulative total-token reduction | **25.11%** |
| Bugfix cumulative token reduction | **44.45%** |
| Bugfix paired token saving | **40.41% ± 24.61%** |
| Core-bugfix paired saving | **44.57% ± 20.51%** |
| Initial bugfix break-even | **21.31 tasks** |
| Decoy-heavy boundary violations | **0 → 0** |
| Strict no-match edit-free runs | 5 / 6 → 0 / 6 |
| Router rejection score | **0 / 6** |

### 7.4 Interpretation

Medium remains the lower-cost default. XHigh is useful when navigation risk matters: it stabilized decoy-heavy repair. Neither effort fixed unsupported-request routing.

---

## 8. Experiment E: Map-quality ablation

Question:

```text
Can a premium XHigh-authored map improve a Medium repair agent?
```

### 8.1 Conditions

| Condition | Map | Repair agent |
| --- | --- | --- |
| A | none | Medium |
| B | Medium-authored | Medium |
| C | XHigh-authored | Medium |

### 8.2 Results

| Scope | No-map tokens | Medium-map tokens | XHigh-map tokens | XHigh vs Medium map |
| --- | ---: | ---: | ---: | ---: |
| All | 12,596,826 | 8,840,991 | 8,713,604 | 1.44% lower |
| Bugfix | 11,219,322 | **6,677,545** | 6,794,487 | **1.75% higher** |
| Core bugfix | 7,995,985 | 3,772,157 | 3,768,332 | 0.10% lower |
| Decoy-heavy | 3,223,337 | 2,905,388 | 3,026,155 | 4.16% higher |

| Condition | Boundary violations | Strict no-match edits |
| --- | ---: | ---: |
| No-map + Medium | 539 | 0 |
| Medium-map + Medium | **11** | 15 |
| XHigh-map + Medium | **531** | 12 |

Interpretation: premium map authoring did not improve Medium-agent economics or safety.

---

## 9. Cross-experiment conclusions

### 9.1 Scale

Semantic navigation becomes more useful as repository exploration cost grows, but larger repositories amplify route-precision and route-rejection requirements.

### 9.2 Medium vs XHigh

| Question | Answer |
| --- | --- |
| Default operating point | **Medium** |
| Is XHigh useless? | No. It is valuable for hard, decoy-heavy tasks |
| Should XHigh author every map by default? | No, not based on current data |
| When should XHigh be used? | Selectively for high-risk repair navigation |

### 9.3 No-match rejection

A good router must know when to remain silent.

```text
route useful work
+
reject unsupported work
```

At enterprise scale, unsupported requests still received trusted routes. This is the highest-priority hardening area.

---

## 10. Economics

| Repository / Effort | Map-authoring tokens | Initial bugfix break-even |
| --- | ---: | ---: |
| Realistic-large Medium | 1,748,486 | 18.06 tasks |
| Realistic-large XHigh | 2,891,143 | 28.36 tasks |
| Enterprise XLarge Medium | **1,527,492** | **13.12 tasks** |
| Enterprise XLarge XHigh | 3,122,221 | 21.31 tasks |

Map-authoring cost did not scale linearly with LOC.

---


## 11. Wall-clock analysis

Token savings and wall-clock savings must be interpreted separately.

Semantic maps reduce repeated repository exploration and context ingestion. Actual elapsed time also depends on model reasoning, shell commands, tests, filesystem work, and nondeterministic agent behavior.

```text
token efficiency
≠
wall-clock latency
```

### 11.1 Native generated-map pilot

| Scope | Baseline cumulative time | Generated-map cumulative time | Time saved | Cumulative time change | Mean paired time saving ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| All 72 pairs | 3,969.26s | 4,296.10s | **-326.84s** | **8.23% slower** | -4.67% ± 59.58% |
| Bugfix 60 pairs | 2,649.77s | 2,408.38s | **241.39s** | **9.11% faster** | 4.18% ± 39.47% |
| No-match 12 pairs | 1,319.49s | 1,887.72s | **-568.23s** | **43.06% slower** | -48.92% ± 109.50% |

Ordinary bugfixes became faster in the pilot, while no-match outliers dominated the aggregate.

### 11.2 `realistic_large_platform`

#### Medium E2E

| Scope | Baseline cumulative time | Generated-map cumulative time | Time saved | Cumulative time change | Mean paired time saving ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| All 27 pairs | 1,792.49s | 1,396.86s | **395.63s** | **22.07% faster** | 7.50% ± 41.24% |
| Bugfix 24 pairs | 1,060.75s | 981.88s | **78.87s** | **7.44% faster** | 4.63% ± 41.81% |

#### XHigh E2E

| Scope | Baseline cumulative time | Generated-map cumulative time | Time saved | Cumulative time change | Mean paired time saving ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| All 27 pairs | 3,056.01s | 2,912.50s | **143.51s** | **4.70% faster** | -9.77% ± 29.65% |
| Bugfix 24 pairs | 1,536.47s | 1,680.04s | **-143.57s** | **9.34% slower** | -13.30% ± 29.44% |

### 11.3 `enterprise_xlarge_platform`

#### Medium E2E

| Scope | Baseline cumulative time | Generated-map cumulative time | Time saved | Cumulative time change | Mean paired time saving ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| All 45 pairs | 3,697.31s | 3,597.81s | **99.50s** | **2.69% faster** | -5.57% ± 102.21% |
| Bugfix 39 pairs | 2,466.19s | 2,465.11s | **1.08s** | **0.04% faster** | -7.53% ± 109.75% |
| Core bugfix 30 pairs | 1,780.28s | 1,424.40s | **355.88s** | **19.99% faster** | see category mix |
| Decoy-heavy 9 pairs | 685.92s | 1,040.72s | **-354.80s** | **51.73% slower** | -84.93% ± 213.19% |

#### XHigh E2E

| Scope | Baseline cumulative time | Generated-map cumulative time | Time saved | Cumulative time change | Mean paired time saving ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| All 45 pairs | 6,004.10s | 6,549.97s | **-545.87s** | **9.09% slower** | -6.57% ± 64.66% |
| Bugfix 39 pairs | 3,162.72s | 3,233.79s | **-71.07s** | **2.25% slower** | -4.88% ± 68.02% |
| Workflow bugfix 12 pairs | 992.50s | 783.86s | **208.64s** | **21.02% faster** | 19.76% ± 20.20% |
| Decoy-heavy 9 pairs | 826.20s | 787.19s | **39.01s** | **4.72% faster** | 1.78% ± 17.94% |
| Cross-module bugfix 12 pairs | 959.22s | 1,233.04s | **-273.83s** | **28.55% slower** | -30.40% ± 117.24% |
| No-match 6 pairs | 2,841.37s | 3,316.17s | **-474.80s** | **16.71% slower** | -17.54% ± 38.20% |

### 11.4 XHigh-map + Medium-repair ablation timing

| Scope | No-map + Medium | Medium-map + Medium | XHigh-map + Medium | XHigh map vs Medium map |
| --- | ---: | ---: | ---: | ---: |
| All 45 runs | 3,697.31s | 3,597.81s | 3,621.35s | **0.65% slower** |
| Bugfix 39 runs | 2,466.19s | 2,465.11s | **2,136.61s** | **13.33% faster** |
| Core bugfix 30 runs | 1,780.28s | **1,424.40s** | 1,459.69s | 2.48% slower |
| Decoy-heavy 9 runs | 685.92s | 1,040.72s | **676.92s** | 34.96% faster |
| No-match 6 runs | 1,231.11s | **1,132.70s** | 1,484.74s | 31.08% slower |

This ablation was not an interleaved replication, so timing differences should be treated as preliminary observations.

### 11.5 Timing conclusions

1. **Token savings are the more consistent primary signal.**
2. **Wall-clock savings are sensitive to task mix and outliers.**
3. Medium maps reduced overall elapsed time by 22.07% on `realistic_large_platform`.
4. Enterprise Medium improved core-bugfix latency by 19.99%, but decoy-heavy outliers erased most of the aggregate benefit.
5. Enterprise XHigh improved decoy-heavy stability but made total elapsed time 9.09% worse.
6. Public messaging should emphasize reduced exploration tokens and context ingestion, not guaranteed speedups.

### 11.6 Caution on latency break-even

Latency break-even is substantially noisier than token break-even.

| Experiment | Map-authoring time | Mean bugfix time saved per task | Initial latency break-even |
| --- | ---: | ---: | ---: |
| `realistic_large_platform` Medium | 648.22s | 3.29s | about **197 tasks** |
| `realistic_large_platform` XHigh | 1,069.78s | negative | no break-even |
| `enterprise_xlarge_platform` Medium | 759.46s | 0.03s | unstable |
| `enterprise_xlarge_platform` XHigh | 1,042.54s | negative | no break-even |

For Enterprise Medium core bugfixes alone, average saving was about 11.86 seconds per task, implying an authoring-time break-even near 64 tasks. The full bugfix mix erased that benefit through decoy-heavy outliers.


## 12. Defensible public statement

> Synthetic benchmarks suggest that Bunya-Jido semantic maps can materially reduce repository-scale code-repair token usage. On a 126.7K-SLOC synthetic Python platform, Medium-authored maps reduced cumulative Medium-effort bugfix tokens by 40.48%, with an initial authoring break-even of approximately 13 similar bugfix tasks excluding maintenance. XHigh repair agents improved decoy-heavy stability, but XHigh-authored maps did not improve Medium-agent economics. Unsupported-request routing remains the highest-priority hardening area.

---

## 13. Limitations

Do not claim that:

- production repositories will reproduce the same saving rates;
- maps benefit every task type;
- wall-clock time always improves;
- XHigh-authored maps are universally better;
- no-match routing is production-ready;
- raw-token break-even equals monetary break-even;
- synthetic benchmarks prove industrial generalization.

---

## 14. Next priorities

1. No-match route rejection hardening
2. Responsibility-boundary pre-checks
3. Allowed / forbidden boundaries for decoy-heavy routes
4. Structural-change map-maintenance benchmark
5. Public open-source issue replay
6. Optional interleaved map-quality replication

---

## Appendix A. Auditable raw-token usage

| Stage | Tokens |
| --- | ---: |
| Curated route utility | 12,519,891 |
| Native pilot map authoring | 5,086,098 |
| Native pilot repair | 20,427,656 |
| Realistic-large Medium map authoring | 1,748,486 |
| Realistic-large Medium repair | 8,946,882 |
| Realistic-large XHigh map authoring | 2,891,143 |
| Realistic-large XHigh repair | 12,746,252 |
| Enterprise XLarge Medium map authoring | 1,527,492 |
| Enterprise XLarge Medium repair | 21,437,817 |
| Enterprise XLarge XHigh map authoring | 3,122,221 |
| Enterprise XLarge XHigh repair | 28,729,641 |
| Enterprise XHigh-map + Medium-repair ablation | 8,713,604 |
| **Total** | **127,897,183** |
