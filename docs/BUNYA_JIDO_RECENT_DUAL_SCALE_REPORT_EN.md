# Bunya-Jido Dual-Scale Benchmark Report
## Realistic Large and Enterprise XLarge with GPT-5.5 Medium

## Executive summary

| Repository | SLOC | Python files | Scenarios | Bugfix success | Bugfix tokens | Bugfix time | Boundary | No-route |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Realistic Large | 28,708 | 1,432 | 8 + 1 no-route | 24/24 → 24/24 | 18.77% lower | 27.97% lower | 0 → 1 | 3/3 safe |
| Enterprise XLarge | 126,731 | 5,926 | 13 + 2 no-route | 39/39 → 39/39 | 22.78% lower | 12.52% lower | 10 → 6 | 6/6 safe |
| Combined | 155,439 | 7,358 | 21 + 3 no-route | 63/63 → 63/63 | 21.62% lower | 17.04% lower | 10 → 7 | 9/9 safe |

In a synchronized A/B run using the latest Bunya-Jido, the mapped condition completed all 63 bugfix cases while using **21.62% fewer repair tokens** and **17.04% less cumulative wall-clock time**. All nine unsupported mobile or infrastructure requests ended in a read-only path with no production-file changes.

Unlike the earlier regression runs, this experiment reran no-map and fresh-map conditions during the same test window. That removes most of the timing and backend drift introduced when an old baseline is reused.

---

## Hypotheses

The experiment tested three claims.

1. **Navigation efficiency**
   A fresh semantic map and task-specific context should let the coding agent solve the same bug with less repository exploration, fewer tokens, and less elapsed time.

2. **Safe abstention**
   Requests outside the repository's product surface should be classified as `OUT_OF_SCOPE` or `UNCERTAIN`, executed in a read-only sandbox, and produce no repository changes.

3. **Bounded discovery**
   For decoy-heavy tasks where no exact trusted route is available, `IN_SCOPE_NO_ROUTE` should still narrow the search enough to complete the repair without broad edits.

---

## Method

### Overall design

```text
Realistic Large:
9 scenarios × 2 conditions × 3 repetitions = 54 runs

Enterprise XLarge:
15 scenarios × 2 conditions × 3 repetitions = 90 runs

Total:
144 repair runs
```

The two conditions were isolated as follows.

| Condition | Setup |
| --- | --- |
| No-map baseline | No `.bunya-jido` directory, no context call, no agent-guide activation |
| Generated map | Fresh map authored from the clean repo, frozen before defect injection, `context --json` used at repair time |

The repair agent was **GPT-5.5 with medium reasoning effort, invoked through Codex CLI**. Web search was disabled. Public tests ran inside the working copy; hidden tests were injected only into a separate grading copy after the agent had finished.

File accounting combined `git diff`, `git status --porcelain --untracked-files=all`, and Codex JSONL `file_change` events. Runtime artifacts such as `__pycache__`, `*.pyc`, and `*.pyo` were ignored.

### Large repository: `realistic_large_platform`

| Item | Value |
| --- | ---: |
| Approximate SLOC | 28,708 |
| Physical LOC | 34,355 |
| Python files | 1,432 |
| Responsibility areas | 27 |
| Scenarios | 8 bugfix + 1 no-route |
| Fresh map authoring | 1,581,382 tokens, 623.47 seconds |

The repository models a service platform with orchestration, recovery, reporting, billing, state, provider, audit, and tenancy responsibilities. The defects cover state transitions, mutable-list aliasing, tenant propagation, billing units, and duplicate audit events.

#### Bugfix and no-route scenarios

| Scenario | Type | Request | Direct defect location | Mapped decision |
| --- | --- | --- | --- | --- |
| `realistic-provider-default-order` | bugfix | Fix default provider selection so configured provider order is preserved when no explicit provider is requested. | `src/atlas_platform/providers/selector.py` | MATCH |
| `realistic-run-cursor-progress` | bugfix | Fix workflow execution progress so the cursor advances after each completed step. | `src/atlas_platform/orchestration/service.py` | MATCH |
| `realistic-recovery-failed-resume` | bugfix | Fix recovery so failed runs can resume running just like paused runs. | `src/atlas_platform/recovery/resume.py` | MATCH |
| `realistic-report-copy` | bugfix | Ensure generated reports copy completed step names instead of retaining a mutable execution-state list. | `src/atlas_platform/reporting/builder.py` | MATCH |
| `realistic-complete-audit-once` | bugfix | Ensure workflow completion emits exactly one audit complete record. | `src/atlas_platform/orchestration/service.py` | MATCH |
| `realistic-billing-step-units` | bugfix | Fix per-step billing usage so each completed workflow step records exactly one usage unit for the tenant. | `src/atlas_platform/billing/service.py` | MATCH |
| `realistic-report-tenant-id` | bugfix | Fix report generation so it preserves the tenant_id stored on the run state. | `src/atlas_platform/reporting/builder.py` | MATCH |
| `realistic-terminal-state` | bugfix | Keep completed workflow runs terminal so they cannot be restarted. | `src/atlas_platform/state/machine.py` | MATCH |
| `realistic-unsupported-mobile-app` | no_match | Add a native Kotlin Android mobile application with Gradle builds, offline sync, and Play Store release automation. | <none> | UNCERTAIN |

### XLarge repository: `enterprise_xlarge_platform`

| Item | Value |
| --- | ---: |
| Approximate SLOC | 126,731 |
| Python files | 5,926 |
| Responsibility areas | 48 |
| Scenarios | 13 bugfix + 2 no-route |
| Fresh map authoring | 1,879,599 tokens, 1,679.63 seconds |

The enterprise repository contains many similarly named queueing, billing, projection, ledger, recovery, reporting, and state-machine components. Three scenarios deliberately place plausible decoys around the target file to measure whether the agent edits by name similarity rather than responsibility.

#### Bugfix and no-route scenarios

| Scenario | Type | Request | Direct defect location | Mapped decision |
| --- | --- | --- | --- | --- |
| `enterprise-provider-default-order` | local_bugfix | Fix default provider selection so configured provider preference order is preserved when no explicit provider is requested. | `src/enterprise_atlas/providers/selector.py` | MATCH |
| `enterprise-zero-usage-allowed` | local_bugfix | Fix usage metering so a zero-unit workflow step remains valid while negative usage is still rejected. | `src/enterprise_atlas/usage/service.py` | MATCH |
| `enterprise-run-cursor-progress` | cross_module_bugfix | Fix deployment execution progress so the state cursor advances after every completed workflow step and downstream projections see the correct cursor. | `src/enterprise_atlas/orchestration/service.py` | MATCH |
| `enterprise-ledger-exact-units` | cross_module_bugfix | Fix ledger recording so each workflow step writes the exact usage units emitted by metering, without adding a phantom unit. | `src/enterprise_atlas/ledger/service.py` | MATCH |
| `enterprise-report-tenant-id` | cross_module_bugfix | Fix deployment report generation so tenant identity is propagated from run state instead of being replaced with a default tenant. | `src/enterprise_atlas/reporting/builder.py` | MATCH |
| `enterprise-projection-snapshot-copy` | cross_module_bugfix | Fix state projection snapshots so completed-step lists are copied at projection time and do not mutate when the live run state changes later. | `src/enterprise_atlas/projections/service.py` | MATCH |
| `enterprise-recovery-failed-resume` | workflow_bugfix | Fix partial-rollout recovery so failed deployments resume running just like paused deployments. | `src/enterprise_atlas/recovery/resume.py` | MATCH |
| `enterprise-complete-audit-once` | workflow_bugfix | Ensure deployment completion emits exactly one complete audit record after reporting and persistence. | `src/enterprise_atlas/orchestration/service.py` | MATCH |
| `enterprise-terminal-completed-state` | workflow_bugfix | Keep completed deployments terminal so a completed rollout cannot restart execution. | `src/enterprise_atlas/state/machine.py` | MATCH |
| `enterprise-report-cursor-consistency` | workflow_bugfix | Fix final deployment reports so the reported cursor exactly matches completed execution progress. | `src/enterprise_atlas/reporting/builder.py` | MATCH |
| `enterprise-queue-lease-release-owner` | decoy_heavy_bugfix | Fix queue lease release so only the current holder can release a lease; a different worker must not clear ownership. | `src/enterprise_atlas/queueing/component_081.py` | IN_SCOPE_NO_ROUTE |
| `enterprise-billing-checkpoint-replay` | decoy_heavy_bugfix | Fix billing checkpoint replay so replay_from(cursor) returns only entries strictly after the supplied cursor, without replaying the checkpoint itself. | `src/enterprise_atlas/billing/component_080.py` | IN_SCOPE_NO_ROUTE |
| `enterprise-projection-route-preference` | decoy_heavy_bugfix | Fix projection route preference so the first registered target remains preferred instead of being alphabetically reordered. | `src/enterprise_atlas/projections/component_082.py` | IN_SCOPE_NO_ROUTE |
| `enterprise-unsupported-ios-app` | no_match | Add a native Swift iOS application with Xcode signing, offline-first sync, App Store release automation, and TestFlight distribution. | <none> | UNCERTAIN |
| `enterprise-unsupported-kubernetes-terraform` | no_match | Add a production Terraform Kubernetes cluster, cloud load balancers, managed database provisioning, and multi-region infrastructure deployment. | <none> | OUT_OF_SCOPE |

### Routing and sandbox policy

| Decision | Execution policy |
| --- | --- |
| `MATCH` | Trusted route context, workspace-write |
| `IN_SCOPE_NO_ROUTE` | No exact route, cautious workspace-write with bounded discovery |
| `OUT_OF_SCOPE` | Read-only |
| `UNCERTAIN` | Read-only |

All 24 Realistic bugfix runs received `MATCH`; its three no-route runs received `UNCERTAIN`. In Enterprise, 30 core bugfix runs received `MATCH`, nine decoy-heavy runs received `IN_SCOPE_NO_ROUTE`, and six no-route runs received either `OUT_OF_SCOPE` or `UNCERTAIN`.

---

## Results

### Overview

| Repository | Overall success | Bugfix success | Bugfix tokens | Bugfix time | Safe no-route | Boundary |
| --- | --- | --- | --- | --- | --- | --- |
| Realistic Large | 24/27 → 27/27 | 24/24 → 24/24 | 18.77% lower | 27.97% lower | 3/3 | 0 → 1 |
| Enterprise XLarge | 39/45 → 45/45 | 39/39 → 39/39 | 22.78% lower | 12.52% lower | 6/6 | 10 → 6 |

The mapped condition preserved bugfix success in both repositories. The largest success-rate difference came from unsupported requests: the no-map baseline produced 169 production-file changes across nine no-route runs, while the mapped condition produced none.

### Token consumption

| Repository | Scope | Baseline tokens | Mapped tokens | Tokens saved | Cumulative change | Mean paired saving ± SD |
| --- | --- | --- | --- | --- | --- | --- |
| realistic_large | all | 4,209,841 | 3,005,556 | 1,204,285 | 28.61% lower | 22.21% ± 43.36% |
| realistic_large | bugfix | 3,636,555 | 2,953,976 | 682,579 | 18.77% lower | 13.65% ± 37.90% |
| realistic_large | core | 3,636,555 | 2,953,976 | 682,579 | 18.77% lower | 13.65% ± 37.90% |
| realistic_large | no_match | 573,286 | 51,580 | 521,706 | 91.00% lower | 90.69% ± 2.24% |
| enterprise_xlarge | all | 10,573,243 | 7,026,972 | 3,546,271 | 33.54% lower | 28.57% ± 39.25% |
| enterprise_xlarge | bugfix | 8,966,583 | 6,923,886 | 2,042,697 | 22.78% lower | 18.59% ± 31.88% |
| enterprise_xlarge | core | 6,052,151 | 4,815,951 | 1,236,200 | 20.43% lower | 17.97% ± 33.09% |
| enterprise_xlarge | decoy | 2,914,432 | 2,107,935 | 806,497 | 27.67% lower | 20.66% ± 29.21% |
| enterprise_xlarge | no_match | 1,606,660 | 103,086 | 1,503,574 | 93.58% lower | 93.45% ± 1.03% |

Across bugfixes only, the baseline used **12,603,138 tokens** and the mapped condition used **9,877,862**. The difference was **2,725,276 tokens**, or **21.62%**.

The greater than 90% reduction on no-route cases should not be read as ordinary repair efficiency. It reflects early abstention: the mapped agent recognized that the requested product surface did not belong in the repository and stopped in a read-only sandbox.

#### Per-scenario results

##### Realistic Large

| Task | Type | Decision | Success | Token change | Time change | Boundary |
| --- | --- | --- | --- | --- | --- | --- |
| `realistic-billing-step-units` | bugfix | MATCH | 3/3 → 3/3 | 33.62% lower | 77.49% lower | 0 → 0 |
| `realistic-complete-audit-once` | bugfix | MATCH | 3/3 → 3/3 | 11.76% higher | 36.32% lower | 0 → 0 |
| `realistic-provider-default-order` | bugfix | MATCH | 3/3 → 3/3 | 42.05% lower | 25.35% lower | 0 → 0 |
| `realistic-recovery-failed-resume` | bugfix | MATCH | 3/3 → 3/3 | 20.06% lower | 11.65% higher | 0 → 0 |
| `realistic-report-copy` | bugfix | MATCH | 3/3 → 3/3 | 2.21% lower | 8.32% higher | 0 → 0 |
| `realistic-report-tenant-id` | bugfix | MATCH | 3/3 → 3/3 | 50.34% higher | 109.50% higher | 0 → 1 |
| `realistic-run-cursor-progress` | bugfix | MATCH | 3/3 → 3/3 | 49.51% lower | 11.64% lower | 0 → 0 |
| `realistic-terminal-state` | bugfix | MATCH | 3/3 → 3/3 | 31.61% lower | 22.14% lower | 0 → 0 |
| `realistic-unsupported-mobile-app` | no_match | UNCERTAIN | 0/3 → 3/3 | 91.00% lower | 95.65% lower | 0 → 0 |

##### Enterprise XLarge

| Task | Type | Decision | Success | Token change | Time change | Boundary |
| --- | --- | --- | --- | --- | --- | --- |
| `enterprise-billing-checkpoint-replay` | decoy_heavy_bugfix | IN_SCOPE_NO_ROUTE | 3/3 → 3/3 | 0.27% higher | 73.59% lower | 0 → 0 |
| `enterprise-complete-audit-once` | workflow_bugfix | MATCH | 3/3 → 3/3 | 18.88% higher | 60.54% higher | 0 → 3 |
| `enterprise-ledger-exact-units` | cross_module_bugfix | MATCH | 3/3 → 3/3 | 0.53% higher | 323.76% higher | 0 → 0 |
| `enterprise-projection-route-preference` | decoy_heavy_bugfix | IN_SCOPE_NO_ROUTE | 3/3 → 3/3 | 19.56% lower | 2.99% lower | 0 → 0 |
| `enterprise-projection-snapshot-copy` | cross_module_bugfix | MATCH | 3/3 → 3/3 | 49.61% lower | 17.89% lower | 0 → 0 |
| `enterprise-provider-default-order` | local_bugfix | MATCH | 3/3 → 3/3 | 8.18% lower | 2.99% lower | 0 → 0 |
| `enterprise-queue-lease-release-owner` | decoy_heavy_bugfix | IN_SCOPE_NO_ROUTE | 3/3 → 3/3 | 50.18% lower | 85.12% lower | 10 → 0 |
| `enterprise-recovery-failed-resume` | workflow_bugfix | MATCH | 3/3 → 3/3 | 50.71% lower | 4.20% lower | 0 → 0 |
| `enterprise-report-cursor-consistency` | workflow_bugfix | MATCH | 3/3 → 3/3 | 7.56% lower | 2.41% higher | 0 → 0 |
| `enterprise-report-tenant-id` | cross_module_bugfix | MATCH | 3/3 → 3/3 | 30.65% lower | 269.39% higher | 0 → 0 |
| `enterprise-run-cursor-progress` | cross_module_bugfix | MATCH | 3/3 → 3/3 | 16.55% lower | 23.18% higher | 0 → 3 |
| `enterprise-terminal-completed-state` | workflow_bugfix | MATCH | 3/3 → 3/3 | 44.17% lower | 28.13% lower | 0 → 0 |
| `enterprise-unsupported-ios-app` | no_match | UNCERTAIN | 0/3 → 3/3 | 92.96% lower | 96.65% lower | 0 → 0 |
| `enterprise-unsupported-kubernetes-terraform` | no_match | OUT_OF_SCOPE | 0/3 → 3/3 | 94.10% lower | 95.45% lower | 0 → 0 |
| `enterprise-zero-usage-allowed` | local_bugfix | MATCH | 3/3 → 3/3 | 13.67% lower | 7.07% lower | 0 → 0 |

Six of the eight Realistic bugfix scenarios used fewer cumulative tokens. `report-tenant-id` regressed because the selected route was broader than the direct reporting defect. In Enterprise, the three decoy-heavy tasks were handled as `IN_SCOPE_NO_ROUTE`; together they reduced token use by 27.67% and removed ten baseline boundary violations.

### Wall-clock time

| Repository | Scope | Baseline seconds | Mapped seconds | Seconds saved | Cumulative change | Mean paired saving ± SD |
| --- | --- | --- | --- | --- | --- | --- |
| realistic_large | all | 1,906.668 | 1,015.286 | 891.382 | 46.75% lower | 8.99% ± 57.79% |
| realistic_large | bugfix | 1,377.693 | 992.285 | 385.408 | 27.97% lower | -1.82% ± 51.75% |
| realistic_large | core | 1,377.693 | 992.285 | 385.408 | 27.97% lower | -1.82% ± 51.75% |
| realistic_large | no_match | 528.975 | 23.001 | 505.974 | 95.65% lower | 95.44% ± 1.51% |
| enterprise_xlarge | all | 4,457.912 | 2,957.920 | 1,499.992 | 33.65% lower | -28.86% ± 222.41% |
| enterprise_xlarge | bugfix | 3,331.788 | 2,914.495 | 417.293 | 12.52% lower | -48.07% ± 233.32% |
| enterprise_xlarge | core | 1,522.085 | 2,398.268 | -876.183 | -57.56% lower | -71.10% ± 261.61% |
| enterprise_xlarge | decoy | 1,809.703 | 516.227 | 1,293.476 | 71.47% lower | 28.70% ± 43.23% |
| enterprise_xlarge | no_match | 1,126.124 | 43.425 | 1,082.699 | 96.14% lower | 96.02% ± 0.83% |

For bugfixes, cumulative elapsed time fell from **4,709.481 seconds** to **3,906.780 seconds**, a saving of **802.701 seconds**, or about **13 minutes 23 seconds**.

Paired time means were much noisier than the cumulative totals. A small number of long tool or backend latency outliers made the mean paired time saving negative for both bugfix suites even though total elapsed time went down. Wall-clock therefore remains a secondary metric; token use is the cleaner measure of navigation efficiency.

---

## Limitations

1. Both repositories are synthetic rather than production codebases.
2. The experiment covers Codex CLI and GPT-5.5 Medium only.
3. Each task was repeated three times, but the suite contains only 21 bugfix scenarios and three no-route scenarios.
4. The no-route requests are relatively clear product-surface mismatches. More ambiguous scope boundaries need separate tests.
5. Hidden tests establish functional behavior, not long-term maintainability or architectural quality.
6. Boundary accounting is based on the direct mutation target. A different but defensible implementation may still be counted as a boundary violation.
7. `IN_SCOPE_NO_ROUTE` was executed as cautious workspace-write in a single session. The full two-stage flow, with read-only discovery followed by a new decision or approval, was not tested here.
8. Break-even estimates exclude map refresh, review, and maintenance after repository changes.
9. Raw token counts do not equal API billing because cached-input pricing and subscription economics differ.
10. Wall-clock time is sensitive to backend latency and local Windows I/O.

---

## Conclusion

The latest Bunya-Jido map reduced repair cost without reducing bugfix success. Token use fell by 18.77% on the Realistic Large repository and 22.78% on Enterprise XLarge, while every mapped bugfix still passed public and hidden tests. The routing policy also prevented the failure mode that mattered most in earlier versions: unsupported requests no longer received actionable edit guidance or produced repository changes.

The next improvement is not broader matching. A few tasks still show that a route can be semantically relevant yet too broad, encouraging a downstream compensation rather than a repair at the owning component. Route metadata should therefore become more explicit about owner precedence, upstream invariants, and the preferred repair locus.

A defensible public summary is:

> In two synthetic large-repository benchmarks, Bunya-Jido preserved a 100% bugfix success rate while reducing GPT-5.5 Medium repair tokens by 18.8% and 22.8%. All nine out-of-scope requests completed without production-file changes.
