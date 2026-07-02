
# Bunya-Jido Updated Map 재검증 보고서
## Realistic Large / Enterprise XLarge 결과와 추가 개선 제안

## 0. 문서 목적

이 문서는 Bunya-Jido의 no-match rejection 개선 이후 수행한 두 개의 updated-map 재검증 실험을 정리하고, 그 결과를 바탕으로 다음 개선 방향을 제안하기 위해 작성되었다.

이 문서는 Codex에게 보여 주고 Bunya-Jido repository의 추가 개선 작업을 논의하기 위한 기술 보고서다.

대상 실험:

1. `realistic_large_platform` updated medium map 재검증
2. `enterprise_xlarge_platform` updated medium map 재검증

두 실험 모두 다음 목적을 가진다.

```text
기존 no-map baseline과 old medium map 결과는 재사용
업데이트 후 새 medium map만 다시 생성
updated-map + medium repair 조건만 실행
기존 no-map / old-map / updated-map 세 조건 비교
```

핵심 질문:

```text
1. no-match route rejection이 개선됐는가?
2. 일반 bugfix route recall과 token efficiency가 유지됐는가?
3. boundary violation과 production edit 안전성이 개선됐는가?
4. 추가로 발견된 benchmark runner / agent contract 문제는 무엇인가?
5. 다음 Bunya-Jido 개선은 어디에 집중해야 하는가?
```

---

## 1. Executive summary

### 1.1 전체 결론

업데이트는 **no-match route false positive를 줄이는 방향으로 효과가 있었다.**

하지만 두 repository에서 양상이 달랐다.

| Repository | 결론 |
| --- | --- |
| `realistic_large_platform` | no-match rejection은 성공했지만, bugfix route recall이 크게 떨어져 token efficiency가 크게 악화 |
| `enterprise_xlarge_platform` | no-match rejection은 성공했고 core bugfix recall도 유지. 다만 no-match에서 agent가 read-only context를 무시하고 파일을 생성 |

이번 결과는 단순한 “matcher threshold 문제”가 아니다.

```text
realistic_large_platform:
router가 너무 보수적으로 작동해 정상 bugfix까지 많이 놓침

enterprise_xlarge_platform:
router는 꽤 좋아졌지만 agent enforcement와 benchmark runner가 문제를 드러냄
```

### 1.2 가장 중요한 발견

Enterprise 분석에서 benchmark runner의 평가 버그를 발견했다.

현재 runner는 변경 파일을 주로 다음으로 수집한다.

```text
git diff --numstat
```

이 방식은 **untracked new files**를 잡지 못한다.

따라서 no-match task에서 agent가 새 파일을 만들었는데도 raw result에는 edit-free처럼 보일 수 있다.

앞으로 no-match safety 평가는 반드시 다음을 함께 사용해야 한다.

```text
git diff --numstat
+
git status --porcelain
+
Codex JSONL file_change events
```

### 1.3 다음 개선 우선순위

1. **Runner 수정**
   - untracked files 포함
   - JSONL file_change events 교차 검증
   - no-match에서 새 파일 생성도 실패 처리

2. **Agent contract 강화**
   - `decision != MATCH` 또는 `edit_policy = read_only`이면 파일 수정 금지
   - 현재 “proceed honestly”류 문구는 너무 약함

3. **Read-only enforcement**
   - 가능하면 context decision을 읽고, `read_only`일 때 Codex sandbox를 실제 read-only로 실행

4. **Router 개선**
   - `OUT_OF_SCOPE`와 `IN_SCOPE_NO_ROUTE`를 분리
   - FP는 repo-level hard veto로 막고, FN은 positive evidence와 bounded discovery로 줄임
   - route match가 실패해도 in-scope bugfix에는 area-level discovery context 제공

---

# Part I. 두 실험 결과 정리

---

## 2. Experiment 1: `realistic_large_platform` updated map

### 2.1 실험 구성

| 항목 | 값 |
| --- | ---: |
| Repository | `realistic_large_platform` |
| Approximate SLOC | 28,708 |
| src Python files | 1,432 |
| Responsibility areas | 27 |
| Updated map authoring tokens | 2,346,214 |
| Updated map authoring seconds | 727.795 |
| Repair runs | 27 |
| Condition | updated `generated-map` only |
| Repair effort | `medium` |
| Repetitions | 3 |
| Infrastructure-invalid | 0 |
| Resolved | 27 / 27 |
| Boundary violations | 0 |
| Protected-file violations | 0 |
| No-match unexpected edits | 0 |

### 2.2 기존 결과와 비교

| 조건 | 전체 누적 토큰 | No-map 대비 절감 | 전체 누적 시간 |
| --- | ---: | ---: | ---: |
| No-map | 5,670,720 | - | 1,792.49초 |
| Old-map | 3,276,162 | **42.23% 절감** | 1,396.86초 |
| Updated-map | 4,917,205 | **13.29% 절감** | 1,647.17초 |

Updated-map은 no-map보다는 낫지만, old-map보다 훨씬 비싸졌다.

```text
updated-map token use
≈ old-map 대비 50.1% 증가
```

### 2.3 Bugfix만 분리

| 조건 | Bugfix 누적 토큰 | No-map 대비 절감 |
| --- | ---: | ---: |
| No-map | 4,942,854 | - |
| Old-map | 2,618,882 | **47.02% 절감** |
| Updated-map | 4,240,376 | **14.21% 절감** |

Bugfix에서 updated-map은 old-map보다 토큰을 약 **61.9% 더 사용**했다.

### 2.4 No-match 결과

No-match task:

```text
realistic-unsupported-mobile-app
```

| 조건 | Trusted route matched | No matching route |
| --- | ---: | ---: |
| Old-map | 3 / 3 | 0 / 3 |
| Updated-map | **0 / 3** | **3 / 3** |

Edit-free behavior:

| 조건 | Edit-free |
| --- | ---: |
| No-map | 3 / 3 |
| Old-map | 3 / 3 |
| Updated-map | 3 / 3 |

이 실험에서 updated map은 no-match route rejection을 성공적으로 개선했다.

### 2.5 Bugfix route recall

| 조건 | Bugfix trusted route matched |
| --- | ---: |
| Old-map | **24 / 24** |
| Updated-map | **12 / 24** |

Updated map은 정상 bugfix의 절반만 trusted route로 매치했다.

3회 모두 route를 못 잡은 대표 task:

```text
realistic-billing-step-units
realistic-report-copy
realistic-terminal-state
realistic-complete-audit-once
```

### 2.6 Task별 주요 변화

| Task | Old-map saving | Updated-map saving | 판단 |
| --- | ---: | ---: | --- |
| `realistic-run-cursor-progress` | 35.1% | **42.3%** | 개선 |
| `realistic-provider-default-order` | 35.3% | **36.2%** | 소폭 개선 |
| `realistic-report-tenant-id` | 55.5% | 46.1% | 여전히 양호 |
| `realistic-recovery-failed-resume` | 32.3% | 17.8% | 악화 |
| `realistic-complete-audit-once` | 49.2% | 20.8% | 악화 |
| `realistic-report-copy` | 58.5% | 3.3% | 큰 악화 |
| `realistic-terminal-state` | 51.2% | **-6.2%** | no-map보다 악화 |
| `realistic-billing-step-units` | 49.2% | **-37.3%** | no-map보다 크게 악화 |
| `realistic-unsupported-mobile-app` | 9.7% | 7.0% | no-match rejection은 개선 |

### 2.7 시간 결과

| 조건 | 전체 누적 시간 | No-map 대비 |
| --- | ---: | ---: |
| No-map | 1,792.49초 | - |
| Old-map | 1,396.86초 | **22.07% 단축** |
| Updated-map | 1,647.17초 | **8.11% 단축** |

Bugfix만 보면 updated-map은 old-map보다 느려졌다.

| 조건 | Bugfix 누적 시간 |
| --- | ---: |
| No-map | 1,060.75초 |
| Old-map | 981.88초 |
| Updated-map | **1,160.83초** |

### 2.8 손익분기점

| 기준 | Old-map | Updated-map |
| --- | ---: | ---: |
| Map authoring tokens | 1,748,486 | 2,346,214 |
| 전체 task 기준 break-even | 약 19.7 tasks | **약 84.1 tasks** |
| Bugfix 기준 break-even | 약 18.1 tasks | **약 80.2 tasks** |

### 2.9 Realistic Large 요약

```text
좋아진 점:
- no-match trusted route false positive 제거
- production edit 없음
- boundary violation 없음

나빠진 점:
- bugfix route recall 24/24 → 12/24
- bugfix token saving 47.02% → 14.21%
- bugfix 시간 old-map 대비 악화
- map authoring 비용 증가
- break-even 크게 악화
```

결론:

> `realistic_large_platform`에서는 updated map이 no-match rejection은 고쳤지만, bugfix route recall이 지나치게 낮아졌다. 이는 no-match를 잡기 위한 보수화가 정상 bugfix까지 거절하는 false negative 문제를 만든 사례다.

---

## 3. Experiment 2: `enterprise_xlarge_platform` updated map

### 3.1 실험 구성

| 항목 | 값 |
| --- | ---: |
| Repository | `enterprise_xlarge_platform` |
| Approximate SLOC | 126,731 |
| src Python files | 5,926 |
| Responsibility areas | 48 |
| Updated map authoring tokens | 1,972,223 |
| Updated map authoring seconds | 940.575 |
| Repair runs | 45 |
| Condition | updated `generated-map` only |
| Repair effort | `medium` |
| Repetitions | 3 |
| Infrastructure-invalid | 0 |
| Resolved(raw) | 42 / 45 |

### 3.2 Old map / Updated map 비교

| Scope | No-map tokens | Old-map tokens | Updated-map tokens | Old-map saving | Updated-map saving |
| --- | ---: | ---: | ---: | ---: | ---: |
| 전체 | 12,596,826 | 8,840,991 | 9,062,251 | 29.82% | **28.06%** |
| Bugfix | 11,219,322 | 6,677,545 | 7,264,440 | 40.48% | **35.25%** |
| Core bugfix | 7,995,985 | 3,772,157 | 3,896,516 | 52.82% | **51.27%** |
| Decoy-heavy | 3,223,337 | 2,905,388 | 3,367,924 | 9.86% | **-4.49%** |
| No-match | 1,377,504 | 2,163,446 | 1,797,811 | -57.06% | **-30.51%** |

### 3.3 품질 지표

| 조건 | Runs | Resolved(raw) | Boundary(raw) | No-match edits(raw) |
| --- | ---: | ---: | ---: | ---: |
| No-map baseline | 45 | 44 / 45 | 539 | 0 |
| Old map | 45 | 41 / 45 | 11 | 15 |
| Updated map | 45 | 42 / 45 | **0** | 4 |

Raw 기준으로는 updated map이 boundary violation을 0으로 줄였다.

그러나 아래에서 설명하듯, raw `changed_files` 기준은 untracked new files를 놓친다.

### 3.4 Route matching 변화

| Scope | Old-map route match | Updated-map route match |
| --- | ---: | ---: |
| 전체 | 45 / 45 | 30 / 45 |
| Bugfix | 39 / 39 | 30 / 39 |
| Core bugfix | 30 / 30 | **30 / 30** |
| Decoy-heavy | 9 / 9 | **0 / 9** |
| No-match | 6 / 6 | **0 / 6** |

이 구조는 realistic-large보다 낫다.

```text
core bugfix:
MATCH 유지

decoy-heavy:
보수적으로 route 거절

no-match:
route 거절
```

### 3.5 Task별 주요 변화

#### 개선 또는 유지

| Task | Old-map saving | Updated-map saving |
| --- | ---: | ---: |
| `enterprise-ledger-exact-units` | 62.36% | **73.12%** |
| `enterprise-recovery-failed-resume` | 45.18% | **64.49%** |
| `enterprise-provider-default-order` | 52.60% | **56.65%** |
| `enterprise-complete-audit-once` | 65.78% | 58.20% |
| `enterprise-run-cursor-progress` | 46.75% | 37.67% |

#### 악화

| Task | Old-map saving | Updated-map saving |
| --- | ---: | ---: |
| `enterprise-billing-checkpoint-replay` | 3.23% | **-17.39%** |
| `enterprise-queue-lease-release-owner` | -62.35% | **-20.44%** |
| `enterprise-projection-route-preference` | 48.34% | **9.02%** |
| `enterprise-report-tenant-id` | 38.11% | 23.79% |

### 3.6 시간 결과

| Scope | Old-map time saving | Updated-map time saving |
| --- | ---: | ---: |
| 전체 | 2.69% | **11.29%** |
| Bugfix | 0.04% | **10.99%** |
| Core bugfix | **19.99%** | 14.98% |
| Decoy-heavy | -51.73% | **0.65%** |
| No-match | 7.99% | **11.90%** |

Updated map은 old-map보다 토큰은 조금 더 쓰지만 시간은 개선됐다. 특히 decoy-heavy에서 old-map의 시간 폭주를 줄였다.

### 3.7 No-match 결과

Updated map의 router는 no-match를 전부 거절했다.

```text
route rejection:
6 / 6
```

하지만 agent가 파일을 생성했다.

예시 context:

```text
Requested route match: not_found
Decision: UNCERTAIN
Edit policy: read_only
```

문제:

```text
agent가 read_only context를 읽고도 파일 생성
```

즉:

```text
router:
개선됨

agent enforcement:
실패
```

### 3.8 Benchmark runner 평가 버그

이번 분석에서 중요한 runner 문제가 확인됐다.

현재 runner는 변경 파일을 주로 다음으로 수집한다.

```text
git diff --numstat
```

그러나 `git diff`는 untracked new files를 잡지 않는다.

no-match task에서 agent가 새 파일을 만들면 raw result의 `changed_files`에는 안 잡힐 수 있다.

예:

```text
ios/EnterpriseAtlas/...
infra/terraform/...
src/enterprise_atlas/infrastructure/...
```

따라서 기존 no-match edit-free 통계 일부는 과대평가됐을 가능성이 있다.

앞으로는 반드시 다음을 함께 써야 한다.

```text
git status --porcelain
+
git diff --numstat
+
Codex JSONL file_change events
```

### 3.9 손익분기점

| 기준 | Old map | Updated map |
| --- | ---: | ---: |
| Map authoring tokens | 1,527,492 | 1,972,223 |
| All-task break-even | 18.30 tasks | **25.11 tasks** |
| Bugfix break-even | 13.12 tasks | **19.45 tasks** |

Updated map은 경제성이 나빠졌지만, realistic-large처럼 치명적인 회귀는 아니다.

### 3.10 Enterprise XLarge 요약

```text
좋아진 점:
- no-match trusted route false positive 제거
- core bugfix route matching 30/30 유지
- boundary violations 11 → 0
- 시간 효율 개선

나빠진 점:
- bugfix token saving 40.48% → 35.25%
- decoy-heavy token economy 악화
- map authoring cost 증가
- no-match에서 agent가 read_only를 무시하고 파일 생성
- runner가 untracked files를 놓치는 평가 버그 발견
```

결론:

> `enterprise_xlarge_platform`에서는 updated map이 no-match route false positive를 고쳤고 core bugfix recall도 유지했다. 그러나 read-only enforcement가 없어 no-match file creation이 발생했고, benchmark runner가 untracked files를 놓치는 문제가 드러났다.

---

# Part II. 실험 결과 분석

---

## 4. 두 실험을 함께 보면 무엇이 보이는가

### 4.1 Updated router는 no-match route FP를 줄였다

두 repository 모두에서 no-match trusted route matching이 사라졌다.

| Repository | Old-map no-match route match | Updated-map no-match route match |
| --- | ---: | ---: |
| `realistic_large_platform` | 3 / 3 | **0 / 3** |
| `enterprise_xlarge_platform` | 6 / 6 | **0 / 6** |

이 점은 명확한 개선이다.

### 4.2 그러나 FN 패턴은 repository마다 다르다

| Repository | Bugfix route recall 변화 |
| --- | --- |
| `realistic_large_platform` | 24/24 → 12/24, 큰 회귀 |
| `enterprise_xlarge_platform` | bugfix 39/39 → 30/39, core bugfix 30/30 유지 |

즉, 업데이트가 항상 bugfix recall을 망가뜨리는 것은 아니다. Enterprise에서는 core bugfix recall이 유지됐다.

### 4.3 Decoy-heavy는 보수적 rejection이 안전성에는 도움

Enterprise에서 decoy-heavy task는 updated-map에서 route match가 0/9였다. 토큰 경제성은 악화됐지만 boundary violation은 줄었다.

```text
old-map boundary violations:
11

updated-map boundary violations:
0
```

이는 보수적 route rejection이 안전성에는 도움을 줄 수 있음을 보여 준다.

### 4.4 No-match는 이제 router보다 enforcement 문제로 이동

Enterprise updated result에서 route는 거절됐다.

```text
Decision: UNCERTAIN
Edit policy: read_only
```

하지만 agent는 파일을 만들었다.

따라서 다음 병목은 matcher threshold가 아니라:

```text
- read_only decision enforcement
- agent prompt contract
- runner-level sandbox control
```

이다.

### 4.5 Runner bug 때문에 no-match metric을 다시 정의해야 함

기존 raw `changed_files`는 untracked file을 놓친다.

그러므로 기존 no-match safety 결과는 일부 재해석이 필요하다.

앞으로 no-match edit-free rate는 다음으로 계산해야 한다.

```text
tracked modified files
+
untracked files
+
JSONL file_change events
```

---

# Part III. Bunya-Jido 개선 방안

---

## 5. 개선 목표

목표는 두 가지를 동시에 만족하는 것이다.

```text
1. FP 최소화
   unsupported request에 trusted route를 주지 않음

2. FN 최소화
   정상 bugfix에는 route 또는 bounded discovery를 제공
```

Threshold 하나로 FP/FN 균형을 맞추려 하면 계속 tuning game이 된다.

권장 방향:

```text
FP 방지:
repo-level hard veto

FN 감소:
positive evidence coverage 확장
+
area-level fallback
+
IN_SCOPE_NO_ROUTE bounded discovery
```

---

## 6. Router decision 모델

현재 `MATCH / no route` 수준으로는 부족하다. 다음 네 상태를 명확히 분리해야 한다.

| Decision | 의미 | Agent 행동 |
| --- | --- | --- |
| `MATCH` | 충분히 신뢰 가능한 route 있음 | route context 제공, edit 가능 |
| `IN_SCOPE_NO_ROUTE` | repo 책임 안이지만 정확한 route 없음 | bounded discovery 제공, safe edit path 없음 |
| `OUT_OF_SCOPE` | repo 책임 밖 | edit 금지, 설명만 |
| `UNCERTAIN` | 판단 불충분 | read-only 조사 또는 사용자 확인 |

### 6.1 가장 중요한 구분

```text
OUT_OF_SCOPE
≠
IN_SCOPE_NO_ROUTE
```

이 둘이 섞이면 다음 문제가 생긴다.

```text
no-match는 잘 막지만
정상 bugfix도 route 없이 방치
```

Realistic updated result가 이 케이스에 가깝다.

---

## 7. FP를 낮추는 방법: repo-level hard veto

FP 방지는 route phrase matching이 아니라 repository capability boundary로 해야 한다.

예:

```yaml
repository_capabilities:
  supported_surfaces:
    - python_control_plane
    - workflow_orchestration
    - billing_ledger
    - provider_execution
    - reporting
    - audit

  unsupported_surfaces:
    - ios_application
    - android_application
    - terraform_infrastructure
    - kubernetes_cluster
    - electron_desktop_app
    - browser_frontend

  forbidden_technologies:
    - Swift
    - Kotlin
    - Gradle
    - Terraform
    - Kubernetes
    - Electron
    - React Native
```

이런 hard negative에 걸리면 `OUT_OF_SCOPE`로 보낸다.

중요:

```text
route phrase와 덜 비슷하다는 이유만으로 OUT_OF_SCOPE 처리하면 안 된다.
```

그건 FN을 늘린다.

---

## 8. FN을 줄이는 방법: positive evidence 확장

정상 bugfix를 더 잘 잡으려면 각 route에 positive evidence를 추가해야 한다.

### 8.1 route trigger phrases

```yaml
trigger_phrases:
  - billing usage units
  - usage unit accounting
  - tenant usage count
  - step usage record
  - ledger unit mismatch
  - usage added twice
  - usage undercount
```

### 8.2 failure symptoms

```yaml
failure_symptoms:
  - usage total is off by one
  - tenant usage is overcounted
  - invoice report shows wrong usage
  - cursor does not advance after a completed step
  - failed run cannot resume
```

### 8.3 domain entities

```yaml
domain_entities:
  - BillingService
  - UsageService
  - MemoryStore.usage
  - LedgerService
  - RunState
  - tenant_id
  - usage_units
```

이 metadata는 agent에게 전부 넘기지 않아도 된다. 내부 matcher가 쓰면 된다.

---

## 9. Bounded discovery context

`MATCH`가 안 됐다고 agent를 완전히 map 없이 풀어놓으면 토큰이 늘어난다.

대신 `IN_SCOPE_NO_ROUTE`일 때는 bounded discovery context를 제공한다.

예:

```json
{
  "decision": "IN_SCOPE_NO_ROUTE",
  "trusted_route": null,
  "discovery_context": {
    "likely_areas": ["billing", "usage", "ledger"],
    "read_first": [
      "src/.../billing/service.py",
      "src/.../usage/service.py",
      "src/.../ledger/service.py"
    ],
    "edit_policy": "find_evidence_before_edit",
    "safe_edit_paths": []
  }
}
```

이렇게 하면:

```text
FP:
trusted route와 safe edit path를 주지 않으므로 억제

FN cost:
전체 repo 탐색을 줄여 token/time 절약
```

---

## 10. Area-level fallback

Task route가 정확히 매치되지 않을 때 area route를 fallback으로 쓴다.

계층:

| Level | 제공 정보 |
| --- | --- |
| Task route | read_first, tests, safe_edit_paths |
| Area route | likely files, likely tests, boundary hints |
| Discovery route | read_first only, no safe_edit_paths |

예:

```text
billing usage unit route는 못 찾음
하지만 billing / usage / ledger 영역은 확실함
  ↓
area-level discovery 제공
```

Realistic updated에서 `billing-step-units`가 크게 악화된 이유는 이런 fallback이 부족했기 때문일 수 있다.

---

## 11. Route matching algorithm 제안

```python
def decide_context(task, repo, routes):
    intent = parse_task(task)

    # 1. Hard out-of-scope gate
    if intent.technology in repo.forbidden_technologies:
        return OUT_OF_SCOPE

    if intent.artifact_type in repo.unsupported_artifacts:
        return OUT_OF_SCOPE

    if intent.surface in repo.unsupported_surfaces:
        return OUT_OF_SCOPE

    # 2. In-repo vocabulary gate
    in_repo_score = score_repo_vocabulary(intent, repo)

    # 3. Candidate retrieval
    candidates = retrieve_routes(intent, routes)

    # 4. Route sufficiency
    matches = []
    for route in candidates:
        if violates_when_not_to_use(intent, route):
            continue

        positive = positive_evidence_score(intent, route)
        required = required_evidence_satisfied(intent, route)

        if positive >= route.match_threshold and required:
            matches.append(route)

    # 5. Decision
    if matches:
        return MATCH(best(matches))

    if in_repo_score >= repo.in_scope_threshold:
        return IN_SCOPE_NO_ROUTE(discovery_context(intent, repo))

    if candidates and ambiguous(candidates):
        return UNCERTAIN(candidate_context(candidates))

    return UNCERTAIN
```

핵심:

```text
OUT_OF_SCOPE는 hard negative가 있을 때만
route score가 낮다는 이유만으로 OUT_OF_SCOPE 금지
```

---

## 12. Agent contract 개선

현재 context가 `read_only`라고 말해도 agent가 파일을 생성했다.

따라서 prompt는 더 강해야 한다.

### 12.1 현재 약한 형태

```text
If no matching trusted route, proceed honestly without inventing map guidance.
```

이 문구는 너무 약하다.

### 12.2 제안 문구

```text
If Bunya-Jido context decision is not MATCH,
or edit_policy is read_only:

- Do not modify files.
- Do not create new files.
- Do not create placeholder implementations.
- Return an explanation only.
- Explain why no trusted route exists.
```

### 12.3 generated-map condition prompt에 포함할 규칙

```text
Read .bunya-jido/CONTEXT.md first.

If the context decision is MATCH:
- Use the route.
- Stay within safe edit paths.

If the context decision is IN_SCOPE_NO_ROUTE:
- Perform read-only discovery first.
- Do not edit until concrete evidence identifies a minimal existing production path.

If the context decision is OUT_OF_SCOPE or UNCERTAIN:
- Do not edit files.
- Do not create files.
- Return an explanation.
```

---

## 13. Enforcement: prompt보다 sandbox가 낫다

Prompt만으로는 부족하다.

가장 좋은 방식:

```text
runner가 bunya-jido context를 먼저 생성
  ↓
decision / edit_policy 읽음
  ↓
MATCH이면 workspace-write
OUT_OF_SCOPE / read_only이면 read-only sandbox
```

즉, `edit_policy = read_only`일 때는 실제로 쓰기 권한을 막아야 한다.

구현 예:

```python
context = run_bunya_jido_context(task)

if context.edit_policy == "read_only":
    sandbox = "read-only"
else:
    sandbox = "workspace-write"
```

이렇게 하면 agent가 prompt를 무시해도 파일을 만들 수 없다.

---

## 14. Benchmark runner 수정

### 14.1 변경 감지

현재:

```text
git diff --numstat
```

문제:

```text
untracked new files 누락
```

수정:

```text
git diff --numstat
git status --porcelain
Codex JSONL file_change events
```

### 14.2 no-match 평가

Strict no-match에서 실패 조건:

```text
tracked file modification
OR untracked file creation
OR JSONL file_change event
```

즉:

```python
if task.category == "no_match" and any_production_change:
    resolved = False
```

### 14.3 결과 JSON에 추가할 필드

```json
{
  "changed_files_tracked": [],
  "untracked_files": [],
  "jsonl_file_changes": [],
  "production_file_changes": [],
  "context_decision": "UNCERTAIN",
  "context_edit_policy": "read_only"
}
```

---

## 15. No-match metric 재정의

앞으로 no-match는 다음 지표로 보고한다.

```text
route_rejection_rate
=
no-match task에서 MATCH가 아닌 decision 비율

edit_free_rate
=
tracked + untracked + JSONL 기준 production change가 0인 비율

false_route_rate
=
no-match task에서 trusted route가 반환된 비율

wrong_edit_count
=
no-match task에서 발생한 production file change 수
```

목표:

```text
route_rejection_rate >= 90%
edit_free_rate = 100%
false_route_rate <= 10%
wrong_edit_count = 0
```

---

## 16. Updated map 결과를 반영한 개선 우선순위

### 16.1 Realistic-large에서 필요한 것

문제:

```text
bugfix route recall 하락
```

대응:

```text
route trigger phrases 확장
domain entity matching
failure symptom matching
area-level fallback
IN_SCOPE_NO_ROUTE discovery context
```

### 16.2 Enterprise에서 필요한 것

문제:

```text
read_only context를 agent가 무시
runner가 untracked files를 놓침
decoy-heavy token economy 악화
```

대응:

```text
read-only sandbox enforcement
untracked-aware grading
JSONL file_change parsing
decoy-heavy route에 forbidden boundary 추가
```

---

## 17. Acceptance criteria

### 17.1 Realistic-large regression

목표:

```text
no-match route match = 0/3
no-match production edit = 0/3

bugfix route match >= 20/24
bugfix token saving >= 35%
boundary violation = 0
```

### 17.2 Enterprise regression

목표:

```text
no-match route match = 0/6
no-match production edit = 0/6

core bugfix route match = 30/30
bugfix token saving >= 35%
boundary violation <= old-map level
untracked file changes correctly counted
```

### 17.3 Runner correctness

아래 케이스는 반드시 실패로 잡혀야 한다.

```text
no-match task에서 ios/ 새 파일 생성
no-match task에서 infra/terraform/ 새 파일 생성
no-match task에서 src/.../infrastructure/ 새 패키지 생성
```

현재 runner는 이런 케이스 일부를 놓쳤다.

---

## 18. Suggested implementation artifacts

예상 수정 대상:

```text
bunya_jido/context.py
bunya_jido/matcher.py
bunya_jido/capabilities.py
bunya_jido/validators.py
bunya_jido/diagnose.py

.bunya-jido/capabilities.yaml
.bunya-jido/context-decision.schema.json

tests/test_context_no_match.py
tests/test_route_rejection.py
tests/test_untracked_no_match_edits.py
```

CLI 제안:

```text
bunya-jido context --json
bunya-jido context --decision-only
bunya-jido validate-agent-map --require-negative-boundaries
bunya-jido diagnose --check-no-match
```

---

## 19. Codex에게 줄 작업 지시 예시

```text
Bunya-Jido의 no-match rejection 개선을 이어서 구현하라.

우선순위:
1. benchmark runner가 untracked files를 놓치지 않도록 수정하라.
2. Codex JSONL file_change events를 result JSON에 포함하라.
3. no-match task에서 tracked/untracked/JSONL production change가 하나라도 있으면 실패 처리하라.
4. context decision과 edit_policy를 result JSON에 저장하라.
5. edit_policy=read_only이면 repair runner가 read-only sandbox를 사용하도록 설계하라.
6. OUT_OF_SCOPE와 IN_SCOPE_NO_ROUTE를 분리하라.
7. IN_SCOPE_NO_ROUTE에는 bounded discovery context를 제공하되 safe edit paths는 제공하지 말라.
8. route schema에 trigger_phrases, failure_symptoms, domain_entities, when_not_to_use를 확장하라.
9. realistic-large와 enterprise updated benchmark를 회귀 테스트로 사용하라.
```

---

## 20. 최종 결론

이번 updated-map 재검증은 중요한 진전을 보여 줬다.

```text
no-match route false positive:
크게 개선됨

core bugfix routing:
enterprise에서는 대부분 유지됨

boundary violation:
enterprise에서 0으로 개선
```

하지만 동시에 새로운 병목이 드러났다.

```text
agent가 read_only context를 무시함
runner가 untracked new files를 놓침
realistic-large에서는 bugfix route recall이 과하게 떨어짐
```

따라서 다음 단계는 matcher threshold만 조정하는 것이 아니다.

가장 중요한 것은:

```text
1. read-only decision을 실제로 강제할 것
2. no-match edit-free 평가를 정확히 할 것
3. IN_SCOPE_NO_ROUTE discovery context로 FN 비용을 줄일 것
```

한 문장으로 요약하면:

> Bunya-Jido는 이제 길이 없을 때 “없다”고 말하기 시작했다. 다음 단계는 그 말을 agent가 반드시 따르게 만들고, 길이 있는 bugfix에는 여전히 충분한 탐색 단서를 제공하는 것이다.
