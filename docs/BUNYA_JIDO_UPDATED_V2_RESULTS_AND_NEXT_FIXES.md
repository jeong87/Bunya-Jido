
# Bunya-Jido Updated-v2 Map 재검증 결과 보고서

## 0. 범위

이 보고서는 최신 Bunya-Jido 업데이트 이후 새로 생성한 `updated-v2 medium map`을 사용해 수행한 두 개의 generated-map-only repair 결과를 분석한다.

대상:

```text
realistic_large_platform
enterprise_xlarge_platform
```

비교 조건:

```text
no-map          기존 baseline
old-map         최초 medium map
updated-map     이전 no-match 개선 map
updated-v2-map  이번 최신 Bunya-Jido map
```

이번 updated-v2 repair runner는 이전보다 더 엄격하다.

```text
git status --porcelain으로 untracked files 감지
Codex JSONL file_change events 기록
no-match에서 tracked + untracked + JSONL change 모두 실패 처리
context decision / edit_policy 기록
```

단, 이번 runner에도 두 가지 주의점이 있다.

```text
1. __pycache__ untracked files가 raw resolved / boundary를 오염시킴
2. context decision 값이 Markdown backtick으로 감싸져 read-only sandbox 전환이 실제로 작동하지 않음
```

따라서 이 보고서는 raw `resolved`만 보지 않고, `__pycache__`를 제외하고 untracked / JSONL file changes를 포함한 corrected analysis를 함께 사용한다.

---

## 1. Executive summary

### 1.1 결론

Updated-v2는 no-match safety를 크게 개선했다.

| Repository | no-match route rejection | no-match production edits | 판단 |
| --- | ---: | ---: | --- |
| `realistic_large_platform` | 3 / 3 | **0** | 성공 |
| `enterprise_xlarge_platform` | 6 / 6 | **0** | 성공 |

그러나 bugfix 쪽은 아직 과하게 보수적이다.

| Repository | bugfix route match | corrected bugfix resolved | 판단 |
| --- | ---: | ---: | --- |
| `realistic_large_platform` | 9 / 24 | 17 / 24 | route recall 부족 |
| `enterprise_xlarge_platform` | 21 / 39 | 25 / 39 | core 일부는 좋지만 recall 부족 |

즉, 최신 업데이트는 우리가 원한 방향으로 나아갔다.

```text
길이 없을 때:
이제 꽤 잘 멈춤

길이 있을 때:
아직 너무 자주 "trusted route 없음"으로 떨어짐
```

### 1.2 가장 중요한 개선

이전 updated-map에서 발생했던 no-match file creation 문제는 updated-v2에서 사라졌다.

```text
realistic no-match:
prod changes 82 → 0

enterprise no-match:
prod changes 69 → 0
```

이번에는 untracked files와 JSONL file_change를 포함해 계산했다.

### 1.3 가장 중요한 남은 문제

Bugfix에서 `IN_SCOPE_NO_ROUTE`가 너무 많이 발생한다. 그리고 prompt가 “non-MATCH이면 편집하지 말라”고 강화되면서, 정상 bugfix도 수정하지 않고 종료하는 run이 생겼다.

결과적으로 토큰 절감률은 좋아 보일 수 있지만, 일부는 “빠르게 실패했기 때문”이다.

---

## 2. Realistic Large 결과

### 2.1 조건별 요약

| Scope | Condition | Runs | Corrected resolved | Tokens | Token saving vs no-map | Time saving vs no-map | Route match | No-route | Boundary | Production changes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | no-map | 27 | 24/27 | 5,670,720 | 0.00% | 0.00% |  |  | 0 | 107 |
| all | old-map | 27 | 24/27 | 3,276,162 | 42.23% | 22.07% | 27/27 | 0/27 | 0 | 96 |
| all | updated-map | 27 | 24/27 | 4,917,205 | 13.29% | 8.11% | 12/27 | 0/27 | 0 | 106 |
| all | updated-v2-map | 27 | 20/27 | 3,690,542 | 34.92% | 35.11% | 9/27 | 18/27 | 0 | 17 |
| bugfix | no-map | 24 | 24/24 | 4,942,854 | 0.00% | 0.00% |  |  | 0 | 24 |
| bugfix | old-map | 24 | 24/24 | 2,618,882 | 47.02% | 7.44% | 24/24 | 0/24 | 0 | 24 |
| bugfix | updated-map | 24 | 24/24 | 4,240,376 | 14.21% | -9.43% | 12/24 | 0/24 | 0 | 24 |
| bugfix | updated-v2-map | 24 | 17/24 | 3,588,265 | 27.40% | -5.84% | 9/24 | 15/24 | 0 | 17 |
| no_match | no-map | 3 | 0/3 | 727,866 | 0.00% | 0.00% |  |  | 0 | 83 |
| no_match | old-map | 3 | 0/3 | 657,280 | 9.70% | 43.29% | 3/3 | 0/3 | 0 | 72 |
| no_match | updated-map | 3 | 0/3 | 676,829 | 7.01% | 33.54% | 0/3 | 0/3 | 0 | 82 |
| no_match | updated-v2-map | 3 | 3/3 | 102,277 | 85.95% | 94.49% | 0/3 | 3/3 | 0 | 0 |

### 2.2 해석

#### 좋아진 점

```text
no-match route rejection 3/3
no-match production changes 0
no-match token saving 85.95%
no-match time saving 94.49%
```

#### 나빠진 점

```text
bugfix route match 9/24
corrected bugfix resolved 17/24
bugfix token saving 27.40%
bugfix wall-clock은 no-map보다 5.84% 느림
```

Old-map과 비교하면:

```text
old-map bugfix token saving:
47.02%

updated-v2 bugfix token saving:
27.40%
```

Updated-v2는 이전 updated-map보다 낫지만, 최초 old-map 수준으로는 회복하지 못했다.

### 2.3 Task별 결과

| Task | Category | Old saving | Updated saving | Updated-v2 saving | V2 route match | V2 no-route | V2 corrected resolved | V2 boundary | V2 prod changes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| realistic-billing-step-units | bugfix | 49.22% | -37.27% | 54.16% | 0/3 | 3/3 | 1/3 | 0 | 1 |
| realistic-complete-audit-once | bugfix | 49.24% | 20.84% | 43.76% | 0/3 | 3/3 | 1/3 | 0 | 1 |
| realistic-provider-default-order | bugfix | 35.29% | 36.19% | 39.22% | 3/3 | 0/3 | 3/3 | 0 | 3 |
| realistic-recovery-failed-resume | bugfix | 32.32% | 17.78% | 32.92% | 3/3 | 0/3 | 3/3 | 0 | 3 |
| realistic-report-copy | bugfix | 58.47% | 3.26% | 58.09% | 0/3 | 3/3 | 1/3 | 0 | 1 |
| realistic-report-tenant-id | bugfix | 55.52% | 46.06% | 0.24% | 3/3 | 0/3 | 3/3 | 0 | 3 |
| realistic-run-cursor-progress | bugfix | 35.11% | 42.34% | 2.40% | 0/3 | 3/3 | 2/3 | 0 | 2 |
| realistic-terminal-state | bugfix | 51.17% | -6.24% | -15.48% | 0/3 | 3/3 | 3/3 | 0 | 3 |
| realistic-unsupported-mobile-app | no_match | 9.70% | 7.01% | 85.95% | 0/3 | 3/3 | 3/3 | 0 | 0 |

### 2.4 Realistic Large 판단

`realistic_large_platform`에서는 updated-v2가 no-match 문제를 확실히 고쳤지만, bugfix recall이 아직 부족하다.

특히 아래 task들은 no-route로 떨어지는 경우가 많다.

```text
realistic-billing-step-units
realistic-complete-audit-once
realistic-report-copy
realistic-run-cursor-progress
realistic-terminal-state
```

이들은 repo scope 안의 정상 bugfix다. 이 경우 `OUT_OF_SCOPE`는 아니며, 적어도 `IN_SCOPE_NO_ROUTE` bounded discovery가 더 강하게 작동해야 한다.

---

## 3. Enterprise XLarge 결과

### 3.1 조건별 요약

| Scope | Condition | Runs | Corrected resolved | Tokens | Token saving vs no-map | Time saving vs no-map | Route match | No-route | Boundary | Production changes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | no-map | 45 | 38/45 | 12,596,826 | 0.00% | 0.00% |  |  | 539 | 652 |
| all | old-map | 45 | 39/45 | 8,840,991 | 29.82% | 2.69% | 45/45 | 0/45 | 11 | 129 |
| all | updated-map | 45 | 39/45 | 9,062,251 | 28.06% | 11.29% | 30/45 | 0/45 | 0 | 108 |
| all | updated-v2-map | 45 | 31/45 | 4,644,641 | 63.13% | 53.78% | 21/45 | 24/45 | 3 | 25 |
| bugfix | no-map | 39 | 38/39 | 11,219,322 | 0.00% | 0.00% |  |  | 539 | 578 |
| bugfix | old-map | 39 | 39/39 | 6,677,545 | 40.48% | 0.04% | 39/39 | 0/39 | 11 | 50 |
| bugfix | updated-map | 39 | 39/39 | 7,264,440 | 35.25% | 10.99% | 30/39 | 0/39 | 0 | 39 |
| bugfix | updated-v2-map | 39 | 25/39 | 4,440,102 | 60.42% | 34.73% | 21/39 | 18/39 | 3 | 25 |
| core | no-map | 30 | 30/30 | 7,995,985 | 0.00% | 0.00% |  |  | 2 | 32 |
| core | old-map | 30 | 30/30 | 3,772,157 | 52.82% | 19.99% | 30/30 | 0/30 | 1 | 31 |
| core | updated-map | 30 | 30/30 | 3,896,516 | 51.27% | 14.98% | 30/30 | 0/30 | 0 | 30 |
| core | updated-v2-map | 30 | 22/30 | 3,377,054 | 57.77% | 24.48% | 21/30 | 9/30 | 3 | 22 |
| decoy | no-map | 9 | 8/9 | 3,223,337 | 0.00% | 0.00% |  |  | 537 | 546 |
| decoy | old-map | 9 | 9/9 | 2,905,388 | 9.86% | -51.73% | 9/9 | 0/9 | 10 | 19 |
| decoy | updated-map | 9 | 9/9 | 3,367,924 | -4.49% | 0.65% | 0/9 | 0/9 | 0 | 9 |
| decoy | updated-v2-map | 9 | 3/9 | 1,063,048 | 67.02% | 61.35% | 0/9 | 9/9 | 0 | 3 |
| no_match | no-map | 6 | 0/6 | 1,377,504 | 0.00% | 0.00% |  |  | 0 | 74 |
| no_match | old-map | 6 | 0/6 | 2,163,446 | -57.06% | 7.99% | 6/6 | 0/6 | 0 | 79 |
| no_match | updated-map | 6 | 0/6 | 1,797,811 | -30.51% | 11.90% | 0/6 | 0/6 | 0 | 69 |
| no_match | updated-v2-map | 6 | 6/6 | 204,539 | 85.15% | 91.94% | 0/6 | 6/6 | 0 | 0 |

### 3.2 해석

#### 좋아진 점

```text
no-match route rejection 6/6
no-match production changes 0
no-match token saving 85.15%
no-match time saving 91.94%
decoy-heavy token saving 67.02%
decoy-heavy time saving 61.35%
```

#### 나빠진 점

```text
bugfix corrected resolved 25/39
core corrected resolved 22/30
route match 21/39
raw resolved는 __pycache__ 때문에 거의 무의미
```

Enterprise에서는 updated-v2가 decoy-heavy token/time을 크게 줄였지만, 그중 일부는 no-edit failure가 섞여 있기 때문에 성공 지표와 함께 봐야 한다.

### 3.3 Task별 결과

| Task | Category | Old saving | Updated saving | Updated-v2 saving | V2 route match | V2 no-route | V2 corrected resolved | V2 boundary | V2 prod changes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enterprise-billing-checkpoint-replay | decoy_heavy_bugfix | 3.23% | -17.39% | 29.94% | 0/3 | 3/3 | 2/3 | 0 | 2 |
| enterprise-complete-audit-once | workflow_bugfix | 65.78% | 58.20% | 67.25% | 3/3 | 0/3 | 3/3 | 2 | 3 |
| enterprise-ledger-exact-units | cross_module_bugfix | 62.36% | 73.12% | 68.94% | 3/3 | 0/3 | 3/3 | 0 | 3 |
| enterprise-projection-route-preference | decoy_heavy_bugfix | 48.34% | 9.02% | 73.10% | 0/3 | 3/3 | 1/3 | 0 | 1 |
| enterprise-projection-snapshot-copy | cross_module_bugfix | 51.14% | 38.63% | 36.54% | 3/3 | 0/3 | 3/3 | 1 | 3 |
| enterprise-provider-default-order | local_bugfix | 52.60% | 56.65% | 44.50% | 3/3 | 0/3 | 3/3 | 0 | 3 |
| enterprise-queue-lease-release-owner | decoy_heavy_bugfix | -62.35% | -20.44% | 87.58% | 0/3 | 3/3 | 0/3 | 0 | 0 |
| enterprise-recovery-failed-resume | workflow_bugfix | 45.18% | 64.49% | 64.38% | 3/3 | 0/3 | 3/3 | 0 | 3 |
| enterprise-report-cursor-consistency | workflow_bugfix | 62.98% | 57.29% | 90.41% | 0/3 | 3/3 | 0/3 | 0 | 0 |
| enterprise-report-tenant-id | cross_module_bugfix | 38.11% | 23.79% | 30.73% | 3/3 | 0/3 | 3/3 | 0 | 3 |
| enterprise-run-cursor-progress | cross_module_bugfix | 46.75% | 37.67% | 31.21% | 0/3 | 3/3 | 1/3 | 0 | 1 |
| enterprise-terminal-completed-state | workflow_bugfix | 50.67% | 43.01% | 83.17% | 0/3 | 3/3 | 0/3 | 0 | 0 |
| enterprise-unsupported-ios-app | no_match | 6.01% | 6.42% | 86.69% | 0/3 | 3/3 | 3/3 | 0 | 0 |
| enterprise-unsupported-kubernetes-terraform | no_match | -136.65% | -77.13% | 83.21% | 0/3 | 3/3 | 3/3 | 0 | 0 |
| enterprise-zero-usage-allowed | local_bugfix | 19.43% | 19.80% | 18.73% | 3/3 | 0/3 | 3/3 | 0 | 3 |

### 3.4 Enterprise 판단

`enterprise_xlarge_platform`에서는 updated-v2가 no-match safety와 decoy-heavy 탐색 비용을 크게 줄였다. 하지만 bugfix resolved rate가 너무 낮다.

특히 다음 task들은 no-route 상태에서 수정이 충분히 이뤄지지 않았다.

```text
enterprise-run-cursor-progress
enterprise-report-cursor-consistency
enterprise-terminal-completed-state
enterprise-queue-lease-release-owner
```

이는 router가 unsupported request를 잘 거절하는 대신, in-scope task도 충분한 discovery context 없이 방치하는 문제로 보인다.

---

## 4. Runner / integration에서 새로 확인된 문제

### 4.1 __pycache__가 raw 결과를 오염시킴

Updated-v2 runner는 `git status --porcelain`으로 untracked files를 잡기 시작했다. 이 방향은 맞다.

하지만 Python 실행 후 생긴 `__pycache__/`까지 변경 파일로 잡히면서 raw result가 false failure가 됐다.

예:

```text
raw resolved:
realistic bugfix 0/24
enterprise bugfix 0/39

corrected resolved, __pycache__ 제외:
realistic bugfix 17/24
enterprise bugfix 25/39
```

수정 필요:

```text
ignore __pycache__/
ignore *.pyc
ignore *.pyo
```

이 필터는 no-match production edit 감지 전에 적용해야 한다.

### 4.2 read-only sandbox 전환이 실제로 작동하지 않음

Updated-v2 runner는 context decision을 읽고 `read_only`면 Codex sandbox를 read-only로 바꾸도록 설계했다.

그러나 결과 JSON을 보면 no-match도 여전히:

```text
codex_sandbox_mode = workspace-write
```

였다.

원인은 context value가 Markdown backtick으로 감싸져 있었기 때문이다.

예:

```text
context_decision = `OUT_OF_SCOPE`
context_edit_policy = `read_only`
```

runner가 이를 normalize하지 않아 비교가 실패했다.

수정 필요:

```python
decision = decision.strip().strip("`").strip()
edit_policy = edit_policy.strip().strip("`").strip()
```

그 뒤:

```text
OUT_OF_SCOPE / UNCERTAIN / read_only
→ sandbox = read-only
```

가 실제로 적용돼야 한다.

### 4.3 그래도 no-match는 좋아졌다

중요하게도 sandbox 전환이 실제로 작동하지 않았는데도, updated-v2 no-match에서는 production edit가 0이었다.

이는 prompt와 context 자체가 이전보다 훨씬 강해졌다는 의미다.

하지만 제품 안전성은 prompt 순응성에만 맡기면 안 된다.

```text
다음 단계:
prompt success
+
sandbox enforcement
```

가 되어야 한다.

---

## 5. Bunya-Jido 개선 방향

### 5.1 지금 필요한 것은 threshold tuning이 아니다

현재 문제는 단순히 “threshold를 조금 낮추자”가 아니다.

원하는 구조:

```text
FP 방지:
repo-level hard veto

FN 감소:
positive evidence coverage
area-level fallback
IN_SCOPE_NO_ROUTE bounded discovery

Safety enforcement:
read_only sandbox
```

### 5.2 OUT_OF_SCOPE와 IN_SCOPE_NO_ROUTE 분리 유지

Updated-v2의 가장 좋은 점은 no-match route false positive를 줄인 것이다. 이걸 되돌리면 안 된다.

대신 정상 bugfix가 `IN_SCOPE_NO_ROUTE`로 떨어졌을 때, agent가 도움 없이 방치되지 않게 해야 한다.

```text
IN_SCOPE_NO_ROUTE:
- trusted route는 없음
- safe edit path도 없음
- 하지만 likely areas / read_first / domain entities 제공
- evidence를 찾은 뒤 최소 수정 허용
```

현재는 `IN_SCOPE_NO_ROUTE`가 사실상 “지도 없음”에 가깝게 작동하는 run이 있다.

### 5.3 Bounded discovery context 강화

예:

```json
{
  "decision": "IN_SCOPE_NO_ROUTE",
  "edit_policy": "cautious",
  "likely_areas": ["billing", "usage", "ledger"],
  "read_first": [
    "src/.../billing/service.py",
    "src/.../usage/service.py",
    "src/.../ledger/service.py"
  ],
  "safe_edit_paths": [],
  "instruction": "Do not edit until evidence identifies a minimal existing production path."
}
```

이 방식은 FP를 늘리지 않으면서 FN 비용을 줄인다.

### 5.4 Route positive evidence 확장

각 route에 다음 metadata를 강화한다.

```yaml
trigger_phrases:
  - billing usage units
  - usage unit accounting
  - tenant usage count
  - step usage record

failure_symptoms:
  - usage total is off by one
  - cursor does not advance
  - failed run cannot resume
  - report contains stale cursor

domain_entities:
  - BillingService
  - UsageService
  - RunState
  - tenant_id
  - usage_units
```

이 metadata는 agent에게 전부 노출할 필요는 없다. 내부 matcher가 사용하면 된다.

### 5.5 Area-level fallback

Task route가 없으면 area route로 fallback한다.

| Level | 제공 정보 |
| --- | --- |
| Task route | read_first, tests, safe_edit_paths |
| Area route | likely files, related tests, boundary hints |
| Discovery route | read_first only, no safe_edit_paths |

예:

```text
terminal-state exact route 없음
  ↓
state area route fallback
  ↓
state/machine.py, state/models.py read_first
```

Realistic updated-v2에서 `terminal-state`가 no-map보다 비싸진 문제는 이런 fallback으로 줄일 수 있다.

---

## 6. Benchmark runner 수정안

### 6.1 변경 파일 수집

현재 목표 구조:

```text
git diff --numstat
+
git status --porcelain
+
Codex JSONL file_change events
```

필터:

```text
ignore __pycache__/
ignore *.pyc
ignore *.pyo
ignore .git/
ignore test cache
```

### 6.2 no-match 실패 조건

```python
if task.category == "no_match" and production_changes:
    resolved = False
```

production_changes는 다음을 포함한다.

```text
tracked modifications
untracked new files
JSONL file_change paths
```

### 6.3 context metadata 저장

Result JSON에 다음을 명시한다.

```json
{
  "context_decision": "OUT_OF_SCOPE",
  "context_edit_policy": "read_only",
  "codex_sandbox_mode": "read-only",
  "tracked_changed_files": [],
  "untracked_files": [],
  "jsonl_file_change_paths": [],
  "production_file_changes": []
}
```

### 6.4 read-only enforcement

```python
if context_decision in {"OUT_OF_SCOPE", "UNCERTAIN"} or edit_policy == "read_only":
    sandbox = "read-only"
else:
    sandbox = "workspace-write"
```

중요: Markdown backtick을 제거해야 한다.

---

## 7. 다음 acceptance criteria

### 7.1 Realistic Large

목표:

```text
no-match route match = 0/3
no-match production edits = 0/3

bugfix corrected resolved >= 22/24
bugfix route match or useful discovery >= 20/24
bugfix token saving >= 35%
boundary violations = 0
```

현재 updated-v2:

```text
no-match production edits = 0/3
bugfix corrected resolved = 17/24
bugfix token saving = 27.40%
```

### 7.2 Enterprise XLarge

목표:

```text
no-match route match = 0/6
no-match production edits = 0/6

bugfix corrected resolved >= 35/39
core corrected resolved >= 28/30
bugfix token saving >= 35%
boundary violations <= old-map level
```

현재 updated-v2:

```text
no-match production edits = 0/6
bugfix corrected resolved = 25/39
core corrected resolved = 22/30
bugfix token saving = 60.42% but partly inflated by no-edit failures
```

---

## 8. 현재 판단

Updated-v2는 updated-map보다 한 단계 더 나아갔다.

```text
No-match:
성공

Untracked-aware safety:
성공적으로 감지 가능해짐

Bugfix:
아직 너무 많이 no-route / no-edit로 떨어짐

Runner:
__pycache__ 필터와 read-only sandbox normalization 필요
```

한 문장으로:

> Updated-v2는 “길이 없으면 멈춘다”는 목표에는 가까워졌지만, “길이 있는 bugfix에는 충분히 안내한다”는 목표에는 아직 부족하다. 다음 작업은 matcher를 다시 느슨하게 하는 것이 아니라, IN_SCOPE_NO_ROUTE에서 bounded discovery를 강화하고 read-only enforcement를 실제로 작동시키는 것이다.
