# Bunya-Jido No-Match Rejection 개선 제안서

## 0. 문서 목적

이 문서는 Bunya-Jido benchmark 과정에서 발견된 **no-match rejection 문제**를 상세히 기술하고, 이를 해결하기 위한 설계·구현 방향을 제안하기 위해 작성되었다.

이 문서는 Codex 또는 다른 coding agent에게 보여 주고, Bunya-Jido repository 업데이트 방향을 논의하기 위한 기술 제안서다.

핵심 요약:

> Bunya-Jido semantic map은 repository-scale bugfix 작업에서 탐색 토큰을 크게 줄이는 효과를 보였다.  
> 그러나 현재 router는 지원되지 않는 요청에도 가장 가까운 trusted route를 반환하는 경향이 있으며, 이로 인해 agent가 production file을 불필요하게 수정하는 문제가 발생했다.  
> 해결책은 route retrieval 이전에 repository responsibility boundary를 판단하고, route가 없을 때 명시적으로 `No matching trusted route`를 반환하는 것이다.

---

## 1. 배경

Bunya-Jido benchmark는 다음 세 단계를 거쳐 진행되었다.

1. **Curated route utility benchmark**  
   사전 작성된 route가 있을 때 coding agent의 탐색 비용이 줄어드는지 확인했다.

2. **Native generated-map benchmark**  
   clean repository에서 Codex + Bunya-Jido가 실제 map을 생성하고, 그 map을 freeze한 뒤 오류를 주입해 repair benchmark를 수행했다.

3. **Realistic / Enterprise-scale benchmark**  
   28.7K SLOC와 126.7K SLOC synthetic Python platform에서 native map의 효과를 측정했다.

결과적으로 Bunya-Jido map은 ordinary bugfix 작업에서 의미 있는 token 절감을 보였다.

예시:

```text
realistic_large_platform, 28.7K SLOC
- Medium map + Medium repair
- Bugfix paired token saving: 43.56% ± 17.84%

enterprise_xlarge_platform, 126.7K SLOC
- Medium map + Medium repair
- Bugfix cumulative token reduction: 40.48%
- Initial bugfix break-even excluding maintenance: ~13.12 tasks
```

그러나 같은 실험에서 **no-match request** 처리 문제가 반복적으로 관찰되었다.

---

## 2. 문제 정의

### 2.1 no-match란 무엇인가

`no-match`는 다음과 같은 요청을 의미한다.

```text
현재 repository의 책임 범위 밖에 있는 요청
```

예를 들어 repository가 Python 기반 enterprise control plane이라면 다음 요청은 no-match다.

```text
- native iOS application 추가
- Android / Gradle mobile app 추가
- Terraform Kubernetes deployment 환경 구축
- Electron desktop UI 구현
```

이들은 단순히 “어려운 bugfix”가 아니다. 해당 repository의 책임 경계 밖에 있는 product surface 또는 technology stack을 요구한다.

정상적인 Bunya-Jido 동작은 다음이어야 한다.

```text
No matching trusted route
```

즉, Bunya-Jido는 다음을 말할 수 있어야 한다.

```text
이 repository map 안에는 이 요청을 안전하게 수행할 trusted route가 없다.
```

---

## 3. 현재 관찰된 문제

### 3.1 핵심 증상

현재 Bunya-Jido context generation은 no-match request에도 trusted route를 반환하는 경향이 있다.

문제 흐름:

```text
unsupported request
  ↓
nearest route retrieval
  ↓
trusted route 반환
  ↓
agent가 route를 믿고 production file 수정
  ↓
불필요한 diff, boundary violation, no-match failure
```

### 3.2 benchmark에서 관찰된 사례

#### Enterprise XLarge Medium E2E

```text
repository: enterprise_xlarge_platform
scale: 126.7K SLOC
repair effort: medium
```

Strict no-match 결과:

```text
No-map + Medium:
edit-free success = 6 / 6

Medium-map + Medium:
edit-free success = 2 / 6
unexpected production edits = 15
route rejection score = 0 / 6
```

#### Enterprise XLarge XHigh E2E

```text
No-map + XHigh:
edit-free success = 5 / 6
unexpected production edits = 1

XHigh-map + XHigh:
edit-free success = 0 / 6
unexpected production edits = 37
route rejection score = 0 / 6
```

즉, map이 없을 때보다 map이 있을 때 no-match request 처리 품질이 악화되었다.

---

## 4. 실제 사용자에게 발생할 수 있는 문제

### 4.1 엉뚱한 production file 수정

사용자가 repository 범위 밖의 요청을 했을 때, Bunya-Jido가 관련 없어 보이는 route를 제공하면 agent는 해당 route를 기반으로 production code를 수정할 수 있다.

예:

```text
User request:
"Add a native iOS app with App Store signing."

Repository:
Python deployment control plane.

Wrong route:
notifications / deployment / webhooks / admin

Agent behavior:
existing Python modules modified to approximate an unsupported task
```

이는 실제 사용자에게 다음 피해를 줄 수 있다.

```text
- 불필요한 PR diff
- CI 비용 증가
- reviewer 시간 낭비
- revert 작업
- 기존 기능 regression
- agent와 map에 대한 신뢰 하락
```

### 4.2 잘못된 가능성 암시

`trusted route`가 반환되면 agent와 사용자는 다음 암시를 받는다.

```text
이 repository 안에 이 작업을 수행할 안전한 경로가 있다.
```

그러나 no-match에서는 이 전제가 거짓이다.

이것은 “길이 없는데 가장 가까운 길을 안내하는 navigation system”과 같다.

### 4.3 보안·컴플라이언스 위험

지원되지 않는 요청이 다음과 같은 형태일 경우 위험은 더 커진다.

```text
- admin override endpoint 추가
- auth 우회
- customer usage를 외부 webhook으로 전송
- compliance logging 변경
```

Router가 `auth`, `admin`, `webhooks`, `usage` 같은 route를 붙이면 agent가 민감한 production path를 수정할 수 있다.

---

## 5. 왜 map이 있을 때 문제가 더 심해지는가

### 5.1 nearest-neighbor retrieval의 함정

현재 문제는 route retrieval이 다음 질문에 먼저 답하기 때문이다.

```text
가장 가까운 route는 무엇인가?
```

그러나 no-match에서는 먼저 이 질문을 해야 한다.

```text
정말 route를 반환해도 되는 요청인가?
```

`nearest route`와 `valid route`는 다르다.

```text
nearest route ≠ trusted valid route
```

### 5.2 `trusted route` 라벨의 권위

`.bunya-jido/CONTEXT.md`에 trusted route가 있으면 agent는 이를 강한 prior로 받아들인다.

```text
Map says this route is trusted.
Therefore, this is probably the right area to edit.
```

No-map 상태에서는 agent가 repository를 살펴본 뒤 “이 작업은 이 repo의 범위를 벗어난다”고 판단할 가능성이 있다.

Map이 있으면 오히려 그 판단이 약해진다.

```text
No map:
agent may conclude "not in this repo"

Map present:
agent tries to make the suggested route work
```

### 5.3 map이 positive capability만 표현함

현재 map은 주로 다음을 표현한다.

```text
- 어떤 route가 있는가
- 어떤 file을 읽어야 하는가
- 어떤 workflow가 있는가
- 어떤 test가 관련되는가
- 어떤 path가 safe edit path인가
```

하지만 no-match를 처리하려면 다음 정보가 필요하다.

```text
- 이 repository가 하지 않는 일
- 이 route가 맡지 않는 일
- 이 technology stack 밖의 요청
- 이 product surface 밖의 요청
- 이 요청은 다른 repository가 필요하다는 사실
```

즉, map에는 positive capability뿐 아니라 **negative capability**가 있어야 한다.

### 5.4 route 설명의 과도한 폭

예를 들어 route 설명에 다음 단어가 있으면:

```text
deployment
notifications
webhooks
admin
runtime
integration
```

다음 요청과 어휘적으로 가까워질 수 있다.

```text
Terraform Kubernetes deployment
iOS push notification app
Electron admin UI
external integration service
```

하지만 어휘 overlap이 route validity를 의미하지 않는다.

### 5.5 map이 탐색을 줄이는 만큼 반례 탐색도 줄인다

Map의 장점은 agent의 탐색 폭을 줄이는 것이다.

하지만 no-match에서는 그 장점이 단점이 될 수 있다.

```text
잘못된 route를 받음
  ↓
agent가 다른 증거를 덜 탐색
  ↓
"이 repo에는 없는 작업"이라는 결론에 도달할 기회가 줄어듦
```

---

## 6. 목표 동작

Bunya-Jido `context` command는 route를 반환하기 전에 다음 네 상태 중 하나를 결정해야 한다.

| Decision | 의미 | agent 행동 |
| --- | --- | --- |
| `MATCH` | trusted route가 충분히 있음 | route context 제공, edit 가능 |
| `IN_SCOPE_NO_ROUTE` | repository 책임 안이지만 map coverage 부족 | 낮은 신뢰 context 또는 일반 탐색 |
| `OUT_OF_SCOPE` | repository 책임 밖 | edit 금지, mismatch 설명 |
| `UNCERTAIN` | 판단 불충분 | 사용자 확인 또는 read-only 조사 |

현재의 단순 `route found / route not found`보다 이 네 상태가 제품적으로 더 유용하다.

---

## 7. 제안 해결책

## 7.1 Router pipeline 변경

현재 흐름이 다음과 같다면:

```text
task
  ↓
route retrieval
  ↓
best route 반환
```

다음처럼 바꾼다.

```text
task
  ↓
task intent parsing
  ↓
repository responsibility boundary check
  ↓
candidate route retrieval
  ↓
route sufficiency check
  ↓
decision:
  - MATCH
  - IN_SCOPE_NO_ROUTE
  - OUT_OF_SCOPE
  - UNCERTAIN
```

핵심은 retrieval보다 **scope gate**가 먼저 온다는 점이다.

---

## 7.2 Capability manifest 추가

Repository-level capability manifest를 도입한다.

예시:

```yaml
repository_capabilities:
  languages:
    - python

  supported_surfaces:
    - python_service_code
    - workflow_control_plane
    - provider_adapters
    - in_memory_storage
    - audit_reporting
    - billing_ledger
    - webhook_delivery

  unsupported_surfaces:
    - ios_application
    - android_application
    - electron_desktop_app
    - terraform_infrastructure
    - kubernetes_cluster_management
    - mobile_app_store_release
    - frontend_spa_ui

  supported_artifact_types:
    - python_module
    - unit_test
    - markdown_doc
    - html_atlas

  unsupported_artifact_types:
    - swift_project
    - kotlin_gradle_project
    - terraform_module
    - helm_chart
    - docker_compose_environment

  repository_non_goals:
    - native mobile app development
    - infrastructure provisioning
    - browser-rendered frontend implementation
```

이 manifest는 `.bunya-jido` 내부에 둘 수 있다.

예:

```text
.bunya-jido/capabilities.yaml
```

또는 blueprint에서 생성해도 된다.

---

## 7.3 Route schema에 negative boundaries 추가

각 route는 다음 정보를 가져야 한다.

```yaml
route_id: notification_delivery
summary: Handles notification delivery inside the Python control plane.

when_to_use:
  - existing notification channel behavior
  - webhook payload delivery
  - audit event notification
  - retry of in-repo delivery adapters

when_not_to_use:
  - native mobile app implementation
  - iOS or Android push notification SDK integration
  - App Store or Play Store release automation
  - Terraform or Kubernetes resource provisioning
  - browser frontend or Electron UI

allowed_technologies:
  - Python
  - in-memory adapters
  - local webhook contract

forbidden_technologies:
  - Swift
  - Kotlin
  - Gradle
  - Terraform
  - Kubernetes
  - Electron
  - React Native

supported_artifacts:
  - python_module
  - unit_test
  - markdown_doc

unsupported_artifacts:
  - ios_project
  - android_project
  - terraform_module
  - helm_chart

safe_edit_paths:
  - src/.../notifications/**
  - src/.../webhooks/**

forbidden_edit_paths:
  - mobile/**
  - ios/**
  - android/**
  - infra/**
  - terraform/**
  - frontend/**

requires_evidence:
  - request mentions an existing notification channel, webhook contract, audit event, or delivery adapter
```

핵심 추가 요소:

```text
when_not_to_use
forbidden_technologies
unsupported_artifacts
forbidden_edit_paths
requires_evidence
```

---

## 7.4 `bunya-jido context` output schema 개선

현재 context output은 human-readable Markdown 중심이다.

앞으로는 Markdown과 함께 machine-readable decision block을 포함하는 것이 좋다.

예:

```json
{
  "decision": "OUT_OF_SCOPE",
  "confidence": 0.91,
  "matched_route_id": null,
  "reason": "The request asks for a native iOS application. This repository contains a Python workflow control plane and no mobile app surface.",
  "edit_policy": "read_only",
  "agent_instruction": "Do not modify files. Explain that no trusted route exists and ask for the appropriate repository.",
  "evidence": {
    "requested_surface": "ios_application",
    "repository_supported_surfaces": ["python_service_code", "workflow_control_plane"],
    "violated_boundaries": ["unsupported_surfaces.ios_application"]
  }
}
```

Markdown output 예:

```markdown
# Bunya-Jido Context Decision

Decision: OUT_OF_SCOPE
Confidence: 0.91

No matching trusted route.

Reason:
The request asks for a native iOS application. This repository contains a Python workflow control plane and no mobile app surface.

Edit policy:
Do not modify production files.

Suggested response:
Explain that this request requires a different repository or a new product surface outside the current map.
```

---

## 7.5 Confidence threshold와 margin threshold

Route를 반환하기 위해 다음 조건을 모두 만족해야 한다.

```text
top_score >= threshold
top_score - second_score >= margin
requested_surface not in unsupported_surfaces
requested_artifact_type not in unsupported_artifacts
requested_technology not in forbidden_technologies
route.when_not_to_use와 충돌 없음
route.requires_evidence 충족
```

예시:

```python
if requested_surface in repo.unsupported_surfaces:
    return OUT_OF_SCOPE

if requested_technology in route.forbidden_technologies:
    return OUT_OF_SCOPE

if top_score < 0.72:
    return UNCERTAIN

if top_score - second_score < 0.10:
    return UNCERTAIN

if not route.required_evidence_satisfied(task):
    return IN_SCOPE_NO_ROUTE
```

정확한 threshold는 benchmark로 calibration한다.

---

## 7.6 Edit policy를 integration layer에서 강제

Prompt instruction만으로는 부족하다.

가능하면 `decision`에 따라 agent sandbox를 바꾸는 것이 좋다.

```text
MATCH:
workspace-write 허용

IN_SCOPE_NO_ROUTE:
workspace-write 허용하되 low-confidence 경고

UNCERTAIN:
read-only 또는 사용자 확인

OUT_OF_SCOPE:
read-only
```

최소한 `OUT_OF_SCOPE`일 때는 다음 contract를 강제해야 한다.

```text
Do not modify files.
Return explanation only.
```

Runner 또는 IDE extension에서 `OUT_OF_SCOPE` decision이면 write tool을 막는 방식을 검토할 수 있다.

---

## 7.7 Agent prompt contract 개선

Generated context를 읽은 agent에게 다음 규칙을 명시한다.

```text
If Bunya-Jido context decision is OUT_OF_SCOPE:
- Do not edit files.
- Do not create placeholder implementations.
- Explain that no trusted route exists.
- Suggest the likely missing repository or product surface.

If decision is UNCERTAIN:
- Prefer read-only inspection.
- Ask for confirmation if interactive.
- Do not perform broad refactors.

If decision is MATCH:
- Use the route and stay within safe edit paths.
```

Benchmark runner에도 이 규칙을 넣어야 한다.

---

## 7.8 no-match benchmark를 first-class test로 유지

No-match는 일반 resolved rate와 섞으면 안 된다.

별도 지표:

```text
route_rejection_rate
=
no-match task에서 OUT_OF_SCOPE 또는 No matching trusted route가 나온 비율

edit_free_rate
=
no-match task에서 production file 변경이 0인 비율

false_route_rate
=
no-match task에서 trusted route가 반환된 비율

wrong_edit_count
=
no-match task에서 수정된 production file 수
```

현재 enterprise benchmark 기준:

```text
route_rejection_rate:
0 / 6

edit_free_rate:
Medium-map + Medium repair = 2 / 6
XHigh-map + XHigh repair   = 0 / 6
```

목표:

```text
route_rejection_rate >= 90%
edit_free_rate = 100%
false_route_rate <= 10%
wrong_edit_count = 0
```

초기 목표는 conservative하게 잡되, 최종적으로 no-match edit는 0이어야 한다.

---

## 8. 구현 계획

### Phase 1: Instrumentation and schema

1. `bunya-jido context`에 decision metadata를 추가한다.
2. agent-map route schema에 `when_not_to_use` 필드를 추가한다.
3. repo-level capability manifest를 생성하거나 수동 정의할 수 있게 한다.
4. context output에 JSON decision block을 포함한다.
5. 기존 Markdown output과 backward compatibility를 유지한다.

### Phase 2: Conservative rejection

1. unsupported technologies와 artifact types를 감지한다.
2. route score가 낮거나 margin이 좁으면 `UNCERTAIN` 처리한다.
3. 명백한 unsupported request는 `OUT_OF_SCOPE` 처리한다.
4. `OUT_OF_SCOPE`인 경우 safe edit paths를 제공하지 않는다.

### Phase 3: Agent and CLI integration

1. Codex handoff prompt에 decision-specific instruction을 추가한다.
2. benchmark runner에서 `OUT_OF_SCOPE`이면 edit-free expectation을 적용한다.
3. 가능하면 read-only sandbox enforcement를 붙인다.
4. `bunya-jido context --json` 옵션을 추가해 machine-readable decision을 출력한다.

### Phase 4: Benchmark and calibration

1. 기존 enterprise no-match tasks로 regression test를 만든다.
2. positive bugfix route matching recall이 너무 낮아지지 않는지 확인한다.
3. threshold를 조정한다.
4. 다음 metric을 보고한다.

```text
bugfix route recall
bugfix repair token saving
no-match rejection rate
no-match edit-free rate
false route rate
```

---

## 9. Acceptance criteria

### 9.1 Functional

다음 요청은 `OUT_OF_SCOPE` 또는 equivalent no-match decision을 반환해야 한다.

```text
- Add a native iOS app
- Add an Android Gradle app
- Add Terraform Kubernetes deployment
- Add Electron desktop UI
- Add React Native mobile client
```

다음 요청은 기존 route와 정상 매치되어야 한다.

```text
- Fix provider default order
- Fix workflow cursor progress
- Fix recovery from failed state
- Fix billing ledger unit accounting
- Fix report tenant_id propagation
```

### 9.2 Safety

No-match context에서 agent가 production file을 수정하면 실패다.

```text
strict no-match edit-free rate = 100%
```

### 9.3 Utility preservation

No-match rejection을 강화한 뒤에도 ordinary bugfix에서 map 효용이 크게 떨어지면 안 된다.

예시 목표:

```text
bugfix token saving degradation <= 5 percentage points
bugfix resolved rate degradation = 0
```

### 9.4 Explainability

No-match decision은 사용자가 납득할 수 있어야 한다.

나쁜 설명:

```text
No route found.
```

좋은 설명:

```text
This repository contains a Python workflow control plane and no iOS application surface.
The request requires a native mobile repository or a new product surface outside this map.
```

---

## 10. 테스트 fixture 제안

### 10.1 OUT_OF_SCOPE

```text
Add a native iOS app with App Store signing.
Add a Kotlin Android app with Gradle build.
Add Terraform Kubernetes deployment manifests.
Add an Electron desktop dashboard.
```

Expected:

```text
decision = OUT_OF_SCOPE
trusted route = null
edit policy = read_only
```

### 10.2 IN_SCOPE_NO_ROUTE

```text
Add a new audit event for a workflow state not yet represented in the map.
Add a new provider adapter similar to existing providers but without exact route coverage.
```

Expected:

```text
decision = IN_SCOPE_NO_ROUTE
trusted route = null or low-confidence context
edit policy = cautious
```

### 10.3 MATCH

```text
Fix provider default order.
Fix report cursor consistency.
Fix failed-state recovery.
Fix billing usage units.
```

Expected:

```text
decision = MATCH
trusted route present
safe edit paths present
```

### 10.4 UNCERTAIN

```text
Add external deployment support.
```

This could mean internal deployment workflow or external infrastructure provisioning.

Expected:

```text
decision = UNCERTAIN
ask for clarification or provide read-only diagnostic
```

---

## 11. Risks and tradeoffs

### 11.1 False rejection

If rejection is too strict, Bunya-Jido may reject valid in-scope work.

Mitigation:

```text
Use IN_SCOPE_NO_ROUTE distinct from OUT_OF_SCOPE.
Allow cautious mode for in-scope but unmapped requests.
```

### 11.2 Extra authoring burden

Adding `when_not_to_use` increases map authoring complexity.

Mitigation:

```text
Generate initial negative boundaries from repository languages, file surfaces, and docs.
Allow route-level defaults inherited from repo capabilities.
```

### 11.3 Threshold brittleness

Hard thresholds can be brittle across repositories.

Mitigation:

```text
Expose configurable thresholds.
Benchmark route rejection separately.
Use confidence bands: MATCH / UNCERTAIN / OUT_OF_SCOPE.
```

### 11.4 Agent noncompliance

Even if context says `OUT_OF_SCOPE`, agent may still edit files.

Mitigation:

```text
Use sandbox-level enforcement where possible.
Do not provide safe edit paths on OUT_OF_SCOPE.
Add benchmark tests that fail on any production edit.
```

---

## 12. Suggested implementation artifacts

Potential files to add or modify:

```text
.bunya-jido/capabilities.yaml
.bunya-jido/agent-map.json
.bunya-jido/context-decision.schema.json

bunya_jido/context.py
bunya_jido/matcher.py
bunya_jido/capabilities.py
bunya_jido/diagnose.py
bunya_jido/validators.py

tests/test_context_no_match.py
tests/test_route_rejection.py
tests/fixtures/no_match/
```

Potential CLI additions:

```text
bunya-jido context --json
bunya-jido context --decision-only
bunya-jido validate-agent-map --require-negative-boundaries
bunya-jido diagnose --check-no-match
```

Potential JSON decision schema:

```json
{
  "decision": "MATCH | IN_SCOPE_NO_ROUTE | OUT_OF_SCOPE | UNCERTAIN",
  "confidence": 0.0,
  "matched_route_id": null,
  "reason": "",
  "edit_policy": "workspace_write | cautious | read_only",
  "safe_edit_paths": [],
  "forbidden_edit_paths": [],
  "requested_surface": "",
  "requested_technologies": [],
  "evidence": []
}
```

---

## 13. Summary

The benchmark shows that Bunya-Jido maps can substantially reduce repository-scale bugfix token usage, especially in large repositories.

However, the same map can be harmful when it returns a trusted route for an unsupported request.

The next product-quality milestone should be:

```text
Bunya-Jido must know when not to route.
```

In practical terms:

```text
- add repository responsibility boundaries
- add route negative boundaries
- add MATCH / IN_SCOPE_NO_ROUTE / OUT_OF_SCOPE / UNCERTAIN decisions
- make OUT_OF_SCOPE edit-free
- report no-match rejection as a first-class metric
```

The goal is not merely a faster map.

The goal is a map that is fast, grounded, and honest.
