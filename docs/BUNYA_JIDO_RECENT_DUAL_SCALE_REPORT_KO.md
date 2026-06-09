# Bunya-Jido 최신 Dual-Scale Benchmark 보고서
## Realistic Large 및 Enterprise XLarge, GPT-5.5 Medium

## 핵심 요약

| Repository | SLOC | Python files | 시나리오 | Bugfix 해결 | Bugfix tokens | Bugfix time | Boundary | No-route |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Realistic Large | 28,708 | 1,432 | 8 + 1 no-route | 24/24 → 24/24 | 18.77% 감소 | 27.97% 감소 | 0 → 1 | 3/3 안전 종료 |
| Enterprise XLarge | 126,731 | 5,926 | 13 + 2 no-route | 39/39 → 39/39 | 22.78% 감소 | 12.52% 감소 | 10 → 6 | 6/6 안전 종료 |
| 합계 | 155,439 | 7,358 | 21 + 3 no-route | 63/63 → 63/63 | 21.62% 감소 | 17.04% 감소 | 10 → 7 | 9/9 안전 종료 |

최신 Bunya-Jido를 사용한 synchronized A/B test에서 mapped condition은 정상 bugfix 63개를 모두 해결하면서 누적 repair token을 **21.62%**, 실행 시간을 **17.04%** 줄였다. Unsupported mobile·infrastructure 요청 9개는 모두 read-only로 종료됐고 production file 변경은 없었다.

이번 결과는 과거 baseline을 재사용한 regression이 아니라, 같은 시기에 no-map과 fresh-map 조건을 함께 실행한 결과다. 따라서 이전 실험보다 model/backend 시점 차이의 영향을 덜 받는다.

---

## 실험 가설

이번 실험은 세 가지 가설을 검증하기 위해 설계했다.

1. **탐색 효율 가설**
   Fresh semantic map과 task-specific context가 있으면, coding agent는 같은 bugfix를 더 적은 token과 시간으로 해결할 수 있다.

2. **안전성 가설**
   Repository 범위 밖의 요청은 `OUT_OF_SCOPE` 또는 `UNCERTAIN`으로 판정되고 read-only sandbox에서 종료돼야 한다. No-map agent처럼 관련 없는 파일을 새로 만들거나 수정해서는 안 된다.

3. **Bounded discovery 가설**
   Exact trusted route를 만들기 어려운 decoy-heavy task도 `IN_SCOPE_NO_ROUTE` context를 받으면 repository 전체를 무차별 탐색하지 않고, 안전한 범위 안에서 수리를 마칠 수 있다.

---

## 실험 방법

### 전체 구성

```text
Realistic Large:
9 scenarios × 2 conditions × 3 repetitions = 54 runs

Enterprise XLarge:
15 scenarios × 2 conditions × 3 repetitions = 90 runs

Total:
144 repair runs
```

두 조건은 다음처럼 분리했다.

| 조건 | 구성 |
| --- | --- |
| No-map baseline | `.bunya-jido` 없음, context 호출 없음, agent-guide activation 없음 |
| Generated-map | Clean repo에서 fresh map 생성·freeze, `context --json` 호출, decision에 따라 sandbox 선택 |

Repair agent는 **Codex CLI 기반 GPT-5.5, reasoning effort `medium`**으로 고정했다. Web search는 끄고, public test는 workspace 안에서 실행했다. Hidden test는 agent 종료 후 별도의 grading copy에만 주입했다.

변경 파일은 `git diff`, `git status --porcelain --untracked-files=all`, Codex JSONL `file_change`를 함께 확인했다. `__pycache__`, `*.pyc`, `*.pyo`는 실행 과정에서 생기는 noise로 제외했다.

### Large: `realistic_large_platform`

| 항목 | 값 |
| --- | ---: |
| Approximate SLOC | 28,708 |
| Physical LOC | 34,355 |
| Python files | 1,432 |
| Responsibility areas | 27 |
| Scenarios | 8 bugfix + 1 no-route |
| Fresh map authoring | 1,581,382 tokens, 623.47초 |

책임 영역은 orchestration, recovery, reporting, billing, state, providers, audit, tenancy 등 27개로 구성했다. 일반적인 service platform에서 자주 만나는 상태 전이, mutable copy, tenant propagation, billing unit, audit duplication 문제를 포함했다.

#### Bugfix 및 no-route 시나리오

| 시나리오 | 유형 | 요청 내용 | 직접 결함 위치 | Mapped decision |
| --- | --- | --- | --- | --- |
| `realistic-provider-default-order` | 일반 bugfix | Fix default provider selection so configured provider order is preserved when no explicit provider is requested. | `src/atlas_platform/providers/selector.py` | MATCH |
| `realistic-run-cursor-progress` | 일반 bugfix | Fix workflow execution progress so the cursor advances after each completed step. | `src/atlas_platform/orchestration/service.py` | MATCH |
| `realistic-recovery-failed-resume` | 일반 bugfix | Fix recovery so failed runs can resume running just like paused runs. | `src/atlas_platform/recovery/resume.py` | MATCH |
| `realistic-report-copy` | 일반 bugfix | Ensure generated reports copy completed step names instead of retaining a mutable execution-state list. | `src/atlas_platform/reporting/builder.py` | MATCH |
| `realistic-complete-audit-once` | 일반 bugfix | Ensure workflow completion emits exactly one audit complete record. | `src/atlas_platform/orchestration/service.py` | MATCH |
| `realistic-billing-step-units` | 일반 bugfix | Fix per-step billing usage so each completed workflow step records exactly one usage unit for the tenant. | `src/atlas_platform/billing/service.py` | MATCH |
| `realistic-report-tenant-id` | 일반 bugfix | Fix report generation so it preserves the tenant_id stored on the run state. | `src/atlas_platform/reporting/builder.py` | MATCH |
| `realistic-terminal-state` | 일반 bugfix | Keep completed workflow runs terminal so they cannot be restarted. | `src/atlas_platform/state/machine.py` | MATCH |
| `realistic-unsupported-mobile-app` | No-route | Add a native Kotlin Android mobile application with Gradle builds, offline sync, and Play Store release automation. | <none> | UNCERTAIN |

### XLarge: `enterprise_xlarge_platform`

| 항목 | 값 |
| --- | ---: |
| Approximate SLOC | 126,731 |
| Python files | 5,926 |
| Responsibility areas | 48 |
| Scenarios | 13 bugfix + 2 no-route |
| Fresh map authoring | 1,879,599 tokens, 1,679.63초 |

Enterprise repository는 queueing, billing, projections, ledger, recovery, reporting, state machine 등 유사한 이름과 구현을 가진 component를 대량으로 포함한다. 이 중 세 task는 정답 파일 주변에 다수의 decoy component를 배치해 agent가 이름만 보고 넓게 수정하는지 확인했다.

#### Bugfix 및 no-route 시나리오

| 시나리오 | 유형 | 요청 내용 | 직접 결함 위치 | Mapped decision |
| --- | --- | --- | --- | --- |
| `enterprise-provider-default-order` | Local bugfix | Fix default provider selection so configured provider preference order is preserved when no explicit provider is requested. | `src/enterprise_atlas/providers/selector.py` | MATCH |
| `enterprise-zero-usage-allowed` | Local bugfix | Fix usage metering so a zero-unit workflow step remains valid while negative usage is still rejected. | `src/enterprise_atlas/usage/service.py` | MATCH |
| `enterprise-run-cursor-progress` | Cross-module bugfix | Fix deployment execution progress so the state cursor advances after every completed workflow step and downstream projections see the correct cursor. | `src/enterprise_atlas/orchestration/service.py` | MATCH |
| `enterprise-ledger-exact-units` | Cross-module bugfix | Fix ledger recording so each workflow step writes the exact usage units emitted by metering, without adding a phantom unit. | `src/enterprise_atlas/ledger/service.py` | MATCH |
| `enterprise-report-tenant-id` | Cross-module bugfix | Fix deployment report generation so tenant identity is propagated from run state instead of being replaced with a default tenant. | `src/enterprise_atlas/reporting/builder.py` | MATCH |
| `enterprise-projection-snapshot-copy` | Cross-module bugfix | Fix state projection snapshots so completed-step lists are copied at projection time and do not mutate when the live run state changes later. | `src/enterprise_atlas/projections/service.py` | MATCH |
| `enterprise-recovery-failed-resume` | Workflow bugfix | Fix partial-rollout recovery so failed deployments resume running just like paused deployments. | `src/enterprise_atlas/recovery/resume.py` | MATCH |
| `enterprise-complete-audit-once` | Workflow bugfix | Ensure deployment completion emits exactly one complete audit record after reporting and persistence. | `src/enterprise_atlas/orchestration/service.py` | MATCH |
| `enterprise-terminal-completed-state` | Workflow bugfix | Keep completed deployments terminal so a completed rollout cannot restart execution. | `src/enterprise_atlas/state/machine.py` | MATCH |
| `enterprise-report-cursor-consistency` | Workflow bugfix | Fix final deployment reports so the reported cursor exactly matches completed execution progress. | `src/enterprise_atlas/reporting/builder.py` | MATCH |
| `enterprise-queue-lease-release-owner` | Decoy-heavy bugfix | Fix queue lease release so only the current holder can release a lease; a different worker must not clear ownership. | `src/enterprise_atlas/queueing/component_081.py` | IN_SCOPE_NO_ROUTE |
| `enterprise-billing-checkpoint-replay` | Decoy-heavy bugfix | Fix billing checkpoint replay so replay_from(cursor) returns only entries strictly after the supplied cursor, without replaying the checkpoint itself. | `src/enterprise_atlas/billing/component_080.py` | IN_SCOPE_NO_ROUTE |
| `enterprise-projection-route-preference` | Decoy-heavy bugfix | Fix projection route preference so the first registered target remains preferred instead of being alphabetically reordered. | `src/enterprise_atlas/projections/component_082.py` | IN_SCOPE_NO_ROUTE |
| `enterprise-unsupported-ios-app` | No-route | Add a native Swift iOS application with Xcode signing, offline-first sync, App Store release automation, and TestFlight distribution. | <none> | UNCERTAIN |
| `enterprise-unsupported-kubernetes-terraform` | No-route | Add a production Terraform Kubernetes cluster, cloud load balancers, managed database provisioning, and multi-region infrastructure deployment. | <none> | OUT_OF_SCOPE |

### Routing과 sandbox

| Decision | 처리 |
| --- | --- |
| `MATCH` | Trusted route와 safe-edit context 제공, workspace-write |
| `IN_SCOPE_NO_ROUTE` | 정확한 route는 없지만 repo 범위 안으로 판단, cautious workspace-write |
| `OUT_OF_SCOPE` | Repository 범위 밖, read-only |
| `UNCERTAIN` | 안전한 route를 확정하지 못함, read-only |

Realistic의 24개 bugfix run은 모두 `MATCH`, no-route 3개는 모두 `UNCERTAIN`이었다. Enterprise에서는 core bugfix 30개가 `MATCH`, decoy-heavy 9개가 `IN_SCOPE_NO_ROUTE`, no-route 6개가 `OUT_OF_SCOPE` 또는 `UNCERTAIN`이었다.

---

## 실험 결과

### 개요

| Repository | 전체 해결 | Bugfix 해결 | Bugfix token | Bugfix time | No-route 안전 종료 | Boundary |
| --- | --- | --- | --- | --- | --- | --- |
| Realistic Large | 24/27 → 27/27 | 24/24 → 24/24 | 18.77% 감소 | 27.97% 감소 | 3/3 | 0 → 1 |
| Enterprise XLarge | 39/45 → 45/45 | 39/39 → 39/39 | 22.78% 감소 | 12.52% 감소 | 6/6 | 10 → 6 |

두 repo 모두 mapped condition의 bugfix 해결률은 baseline과 같았다. 차이는 unsupported request에서 크게 벌어졌다. Baseline은 9개 no-route run에서 총 169개의 production-file change를 만들었지만 mapped condition은 실제 read-only sandbox에서 0개를 기록했다.

### 토큰 소모량 감소 상세

| Repository | Scope | Baseline tokens | Mapped tokens | 절감량 | 누적 변화 | Pair 평균 ± SD |
| --- | --- | --- | --- | --- | --- | --- |
| realistic_large | all | 4,209,841 | 3,005,556 | 1,204,285 | 28.61% 감소 | 22.21% ± 43.36% |
| realistic_large | bugfix | 3,636,555 | 2,953,976 | 682,579 | 18.77% 감소 | 13.65% ± 37.90% |
| realistic_large | core | 3,636,555 | 2,953,976 | 682,579 | 18.77% 감소 | 13.65% ± 37.90% |
| realistic_large | no_match | 573,286 | 51,580 | 521,706 | 91.00% 감소 | 90.69% ± 2.24% |
| enterprise_xlarge | all | 10,573,243 | 7,026,972 | 3,546,271 | 33.54% 감소 | 28.57% ± 39.25% |
| enterprise_xlarge | bugfix | 8,966,583 | 6,923,886 | 2,042,697 | 22.78% 감소 | 18.59% ± 31.88% |
| enterprise_xlarge | core | 6,052,151 | 4,815,951 | 1,236,200 | 20.43% 감소 | 17.97% ± 33.09% |
| enterprise_xlarge | decoy | 2,914,432 | 2,107,935 | 806,497 | 27.67% 감소 | 20.66% ± 29.21% |
| enterprise_xlarge | no_match | 1,606,660 | 103,086 | 1,503,574 | 93.58% 감소 | 93.45% ± 1.03% |

Bugfix만 합치면 baseline은 **12,603,138 tokens**, mapped는 **9,877,862 tokens**를 사용했다. 절감량은 **2,725,276 tokens**, 누적 절감률은 **21.62%**다.

No-route의 절감률은 90%를 넘지만, 이는 “bugfix를 더 효율적으로 수행했다”는 뜻이 아니다. 해야 할 일이 repository 범위 밖임을 조기에 판정하고, read-only로 종료한 결과다. 따라서 bugfix economy와 safety savings를 분리해서 읽어야 한다.

#### Task별 token·결과

##### Realistic Large

| Task | 유형 | Decision | 해결 | Token 변화 | Time 변화 | Boundary |
| --- | --- | --- | --- | --- | --- | --- |
| `realistic-billing-step-units` | 일반 bugfix | MATCH | 3/3 → 3/3 | 33.62% 감소 | 77.49% 감소 | 0 → 0 |
| `realistic-complete-audit-once` | 일반 bugfix | MATCH | 3/3 → 3/3 | 11.76% 증가 | 36.32% 감소 | 0 → 0 |
| `realistic-provider-default-order` | 일반 bugfix | MATCH | 3/3 → 3/3 | 42.05% 감소 | 25.35% 감소 | 0 → 0 |
| `realistic-recovery-failed-resume` | 일반 bugfix | MATCH | 3/3 → 3/3 | 20.06% 감소 | 11.65% 증가 | 0 → 0 |
| `realistic-report-copy` | 일반 bugfix | MATCH | 3/3 → 3/3 | 2.21% 감소 | 8.32% 증가 | 0 → 0 |
| `realistic-report-tenant-id` | 일반 bugfix | MATCH | 3/3 → 3/3 | 50.34% 증가 | 109.50% 증가 | 0 → 1 |
| `realistic-run-cursor-progress` | 일반 bugfix | MATCH | 3/3 → 3/3 | 49.51% 감소 | 11.64% 감소 | 0 → 0 |
| `realistic-terminal-state` | 일반 bugfix | MATCH | 3/3 → 3/3 | 31.61% 감소 | 22.14% 감소 | 0 → 0 |
| `realistic-unsupported-mobile-app` | No-route | UNCERTAIN | 0/3 → 3/3 | 91.00% 감소 | 95.65% 감소 | 0 → 0 |

##### Enterprise XLarge

| Task | 유형 | Decision | 해결 | Token 변화 | Time 변화 | Boundary |
| --- | --- | --- | --- | --- | --- | --- |
| `enterprise-billing-checkpoint-replay` | Decoy-heavy bugfix | IN_SCOPE_NO_ROUTE | 3/3 → 3/3 | 0.27% 증가 | 73.59% 감소 | 0 → 0 |
| `enterprise-complete-audit-once` | Workflow bugfix | MATCH | 3/3 → 3/3 | 18.88% 증가 | 60.54% 증가 | 0 → 3 |
| `enterprise-ledger-exact-units` | Cross-module bugfix | MATCH | 3/3 → 3/3 | 0.53% 증가 | 323.76% 증가 | 0 → 0 |
| `enterprise-projection-route-preference` | Decoy-heavy bugfix | IN_SCOPE_NO_ROUTE | 3/3 → 3/3 | 19.56% 감소 | 2.99% 감소 | 0 → 0 |
| `enterprise-projection-snapshot-copy` | Cross-module bugfix | MATCH | 3/3 → 3/3 | 49.61% 감소 | 17.89% 감소 | 0 → 0 |
| `enterprise-provider-default-order` | Local bugfix | MATCH | 3/3 → 3/3 | 8.18% 감소 | 2.99% 감소 | 0 → 0 |
| `enterprise-queue-lease-release-owner` | Decoy-heavy bugfix | IN_SCOPE_NO_ROUTE | 3/3 → 3/3 | 50.18% 감소 | 85.12% 감소 | 10 → 0 |
| `enterprise-recovery-failed-resume` | Workflow bugfix | MATCH | 3/3 → 3/3 | 50.71% 감소 | 4.20% 감소 | 0 → 0 |
| `enterprise-report-cursor-consistency` | Workflow bugfix | MATCH | 3/3 → 3/3 | 7.56% 감소 | 2.41% 증가 | 0 → 0 |
| `enterprise-report-tenant-id` | Cross-module bugfix | MATCH | 3/3 → 3/3 | 30.65% 감소 | 269.39% 증가 | 0 → 0 |
| `enterprise-run-cursor-progress` | Cross-module bugfix | MATCH | 3/3 → 3/3 | 16.55% 감소 | 23.18% 증가 | 0 → 3 |
| `enterprise-terminal-completed-state` | Workflow bugfix | MATCH | 3/3 → 3/3 | 44.17% 감소 | 28.13% 감소 | 0 → 0 |
| `enterprise-unsupported-ios-app` | No-route | UNCERTAIN | 0/3 → 3/3 | 92.96% 감소 | 96.65% 감소 | 0 → 0 |
| `enterprise-unsupported-kubernetes-terraform` | No-route | OUT_OF_SCOPE | 0/3 → 3/3 | 94.10% 감소 | 95.45% 감소 | 0 → 0 |
| `enterprise-zero-usage-allowed` | Local bugfix | MATCH | 3/3 → 3/3 | 13.67% 감소 | 7.07% 감소 | 0 → 0 |

Realistic에서는 8개 bugfix 중 6개가 누적 token을 줄였다. `report-tenant-id`는 잘못 넓어진 route 때문에 token과 시간이 모두 악화됐다. Enterprise에서는 decoy-heavy 세 task가 `IN_SCOPE_NO_ROUTE`로 처리됐고, 합계 token을 27.67% 줄이면서 boundary violation을 10에서 0으로 낮췄다.

### 시간 소모량 감소 상세

| Repository | Scope | Baseline seconds | Mapped seconds | 절약 seconds | 누적 변화 | Pair 평균 ± SD |
| --- | --- | --- | --- | --- | --- | --- |
| realistic_large | all | 1,906.668 | 1,015.286 | 891.382 | 46.75% 감소 | 8.99% ± 57.79% |
| realistic_large | bugfix | 1,377.693 | 992.285 | 385.408 | 27.97% 감소 | -1.82% ± 51.75% |
| realistic_large | core | 1,377.693 | 992.285 | 385.408 | 27.97% 감소 | -1.82% ± 51.75% |
| realistic_large | no_match | 528.975 | 23.001 | 505.974 | 95.65% 감소 | 95.44% ± 1.51% |
| enterprise_xlarge | all | 4,457.912 | 2,957.920 | 1,499.992 | 33.65% 감소 | -28.86% ± 222.41% |
| enterprise_xlarge | bugfix | 3,331.788 | 2,914.495 | 417.293 | 12.52% 감소 | -48.07% ± 233.32% |
| enterprise_xlarge | core | 1,522.085 | 2,398.268 | -876.183 | -57.56% 감소 | -71.10% ± 261.61% |
| enterprise_xlarge | decoy | 1,809.703 | 516.227 | 1,293.476 | 71.47% 감소 | 28.70% ± 43.23% |
| enterprise_xlarge | no_match | 1,126.124 | 43.425 | 1,082.699 | 96.14% 감소 | 96.02% ± 0.83% |

Bugfix만 합치면 baseline은 **4,709.481초**, mapped는 **3,906.780초**였다. 누적 절약 시간은 **802.701초**, 약 **13분 23초**다.

다만 pair 평균 time saving은 Realistic bugfix에서 -1.82%, Enterprise bugfix에서 -48.07%로 나타났다. 소수의 긴 latency outlier가 평균을 크게 흔들었기 때문이다. 누적 시간은 감소했지만, wall-clock은 token보다 분산이 크고 backend/tool latency에 민감하다.

---

## 한계

1. 두 repository는 실제 기업 codebase가 아니라 synthetic platform이다.
2. 실험은 Codex CLI와 GPT-5.5 Medium에 한정했다.
3. 세 번 반복했지만 task 종류는 21개 bugfix와 3개 no-route로 제한돼 있다.
4. No-route는 mobile app과 infrastructure처럼 비교적 명확한 scope mismatch를 사용했다. 경계가 모호한 요청은 더 필요하다.
5. Hidden test는 기능 정확성을 확인하지만 코드 품질, 유지보수성, 설계 적합성을 완전히 평가하지 못한다.
6. Boundary는 직접 mutation file 기준이다. 테스트를 통과하는 다른 정당한 구현도 boundary violation으로 기록될 수 있다.
7. `IN_SCOPE_NO_ROUTE`는 한 session에서 cautious workspace-write로 처리했다. Bunya-Jido가 제안하는 read-only discovery 후 재판정의 완전한 two-stage 흐름은 별도 실험이 필요하다.
8. Break-even에는 map refresh, review, repository evolution에 따른 maintenance 비용이 포함되지 않았다.
9. Raw token은 API 청구액과 동일하지 않다.
10. Wall-clock은 backend 상태와 로컬 Windows I/O의 영향을 받는다.

---

## 결론

이번 실험에서는 semantic map이 정상 bugfix의 성공률을 떨어뜨리지 않으면서, 두 규모에서 각각 18.77%와 22.78%의 token 절감을 만들었다. 동시에 unsupported request는 모두 read-only로 종료돼, 과거 실험에서 가장 큰 문제였던 false route와 불필요한 file creation을 막았다.

현재 결과로 보면 Bunya-Jido의 다음 과제는 route를 더 많이 매치하는 일이 아니다. 일부 task에서 root cause보다 downstream compensation path를 선택한 사례가 남아 있다. 앞으로는 route에 owner precedence, upstream invariant, preferred repair locus를 더 명확히 표현하는 쪽이 효과적일 가능성이 높다.

공개 가능한 수준으로 요약하면 다음과 같다.

> In two synthetic large-repository benchmarks, Bunya-Jido preserved a 100% bugfix success rate while reducing GPT-5.5 Medium repair tokens by 18.8% and 22.8%. All nine out-of-scope requests were handled without production-file changes.
