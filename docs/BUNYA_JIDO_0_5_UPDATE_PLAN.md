# Bunya-Jido 0.5 Update Plan
## Trust-Preserving Recall Recovery

**Status:** Proposed
**Target release:** `0.5.0`
**Primary surface:** Coding-agent context decision, bounded discovery, and benchmark evidence
**Release rule:** Priority gates are evaluated in order. A lower-priority gain cannot compensate for a higher-priority regression.

---

## 0. Executive Decision

Bunya-Jido `0.5`의 목표는 no-match rejection을 약화하지 않으면서 정상 bugfix가 지도에서 버려지는 비용을 줄이는 것이다.

우선순위는 다음 순서를 절대적으로 따른다.

```text
P0. Benchmark runner가 실제 변경을 정확히 측정한다.
P1. 개선된 no-match rejection과 production safety를 유지한다.
P2. 정상 bugfix가 잘못 거절되거나 무지도 상태로 방치되는 비율을 낮춘다.
P3. 안전하게 해결된 작업의 토큰 소모량을 줄인다.
P4. 안전하게 해결된 작업의 해결 시간을 줄인다.
```

따라서 `0.5`는 matcher threshold를 단순히 낮추는 릴리스가 아니다.

```text
hard negative:
명시적으로 검토된 repository boundary로만 no-match를 차단

normal bugfix:
정확한 trusted route가 없더라도 evidence-backed bounded discovery 제공

efficiency:
안전성과 해결률을 통과한 실행만 대상으로 토큰과 시간을 최적화
```

이 문서에서 사용자가 말한 "정상 bugfix를 거절하는 FP"는 의미를 보존하되, 측정 지표 이름은 분류 혼동을 피하기 위해 `normal_bugfix_hard_rejection_rate`로 사용한다. Router 관점에서는 정상 작업을 놓치는 false negative에 해당한다.

---

## 1. Current Baseline

현재 Bunya-Jido에는 다음 기반이 이미 구현되어 있다.

- `MATCH`, `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`, `UNCERTAIN` decision
- `repository_scope`의 supported/unsupported boundary
- route 수준의 `match_terms`, `when_to_use`, `when_not_to_use`
- route 수준의 `common_failure_modes`
- non-`MATCH` 결과에서 trusted route와 `safe_edit_paths` 제거
- machine-readable `bunya-jido context --json`
- deterministic agent-utility acceptance suite

따라서 `0.5`는 이 기능을 새로 다시 만드는 것이 아니라 다음 빈틈을 메운다.

1. 실제 live-agent benchmark의 변경 감지가 untracked 파일을 놓친다.
2. `IN_SCOPE_NO_ROUTE`가 안전하지만 유용한 탐색 단서를 충분히 제공하지 못한다.
3. 기존 positive evidence 필드가 route matcher에서 충분히 활용되지 않는다.
4. agent 또는 runner가 read-only decision을 실제 실행 권한으로 강제하지 않는다.
5. 안전성, route recall, 토큰, 시간을 같은 분모로 섞어 해석할 위험이 있다.

### 1.1 External runner dependency

현재 Bunya-Jido 저장소에는 updated-map repair benchmark runner의 구현 소스가 없다.

따라서 P0 runner 수정은 benchmark harness가 있는 외부 저장소 또는 실행 환경에서 수행해야 한다. Bunya-Jido `0.5.0`은 다음 증거가 저장되기 전에는 완료로 간주하지 않는다.

- runner 수정 커밋 또는 패치 식별자
- runner correctness fixture 결과
- 수정된 runner로 다시 실행한 benchmark 결과
- 사용한 agent/model/version, prompt, effort, repository commit, 실행 날짜

이 저장소에는 runner 결과 계약, acceptance 기준, 재검증 보고서를 기록할 수 있지만 존재하지 않는 runner 코드를 이 저장소 안에 있다고 가정하지 않는다.

### 1.2 P0 implementation status - 2026-06-05

The repository now provides the reusable P0 observation primitive through
`bunya-jido audit-worktree` and `bunya_jido.benchmark.audit_worktree`.
`tests/test_benchmark_audit.py` covers clean-baseline rejection, tracked,
staged, deleted, renamed, untracked, allowed-artifact, and JSONL
write-then-revert cases. `docs/BENCHMARK_RESULT_CONTRACT.md` defines how an
external live-agent runner must integrate the audit.

This completes the version-controlled P0 implementation in Bunya-Jido. The
external benchmark runner copies must still call the API or CLI and rerun the
benchmark sets before their results qualify as P0 release evidence.

The current local Realistic Large and Enterprise XLarge runner copies were
integrated with this API and passed mock bugfix/no-match smoke runs on
2026-06-05. Those directories are not Git repositories, so the local patch is
not a durable patch identifier and does not satisfy the release-evidence gate
until the runner source is versioned.

### 1.3 P1 implementation status - 2026-06-05

Context decisions now expose an additive `execution_policy` and
decision-specific `agent_instruction`. Only `MATCH` permits
`workspace_write`; `IN_SCOPE_NO_ROUTE` uses `read_only_discovery`, while
`OUT_OF_SCOPE` and `UNCERTAIN` use `read_only`.

The deterministic agent-utility gate now reports a decision confusion matrix,
expected decision accuracy, false-route rate, safe-edit leak rate, and
execution-policy accuracy. The committed P1 fixture covers all four decisions,
including a mixed supported/unsupported request, and automatically fails any
expected non-`MATCH` case that leaks a trusted route or safe-edit path.

This completes the version-controlled P1 safety-lock implementation. Realistic
Large and Enterprise XLarge no-match sets must still be rerun with a versioned
runner that enforces the reported sandbox and records P0 worktree audit data
before the live-agent P1 release minimum can be claimed.

### 1.4 P2 implementation status - 2026-06-05

Context routing now uses conservative term normalization, validated
`common_failure_modes`, route-specific grounded node/workflow evidence, and
independent-evidence separation. A failure mode or shared workflow term cannot
confirm a route alone.

`IN_SCOPE_NO_ROUTE` may now expose optional capped `discovery_context` grounded
in blueprint nodes, workflows, or existing repository-relative paths. It never
exposes a trusted route or safe-edit path, and it supplies read-only search and
`context --node`/`--workflow` recheck commands when justified.

The deterministic utility gate now reports trusted-route recall, bounded
discovery coverage, actionable-guidance coverage, and normal-bugfix hard
rejection rate. Focused fixtures cover failure-mode isolation, grounded
recovery, repository-path fallback, candidate caps, and non-MATCH leakage.

Deterministic replay against the current local benchmark maps produced:

```text
Realistic Large: 7/8 bugfix MATCH, 1/8 bugfix bounded discovery,
                 1/1 no-match route-free
Enterprise XLarge: 10/10 core bugfix MATCH, 3/3 decoy bugfix bounded discovery,
                   2/2 no-match route-free
```

These are context-generation replay results, not live-agent resolution,
boundary-violation, token, or timing evidence. The versioned-runner live gates
remain required before claiming the full P2 release minimum.

### 1.5 P3 implementation status - 2026-06-05

Task-selected Markdown and JSON context is now compact by default, while
`--verbose` preserves diagnostic scores, repeated route context, generated-doc
references, and full discovery evidence. Compact output still carries the
selected route's required reading, contracts, tests, safe-edit boundary, and
Studio context, or the capped grounded discovery contract for
`IN_SCOPE_NO_ROUTE`.

The deterministic self-map acceptance suite reduced compact Markdown context
characters by `36.3%` against the verbose compatibility reference while
retaining `17/17` passing cases, zero non-MATCH route/safe-edit leaks, and
`100%` normal-bugfix actionable guidance. This is context-output evidence, not
a live repair-token claim.

Fresh context-generation replay against the current local XHigh-authored
benchmark maps reduced total Markdown context characters by `40.7%` on
Realistic Large and `43.1%` on Enterprise XLarge versus `--verbose`. It
retained the corrected P2 decisions above, including route-free no-match
requests and bounded discovery for unmatched normal bugfixes. These numbers
measure generated context size only, not live task-token savings.

The reusable `summarize-token-efficiency` API and CLI now separates context,
repair, no-match, safe-and-resolved, and map-authoring tokens; reports medians
and break-even counts; and excludes unresolved bugfixes, boundary violations,
no-match production writes, and infrastructure-invalid runs from savings
comparisons.

This completes the version-controlled P3 context and reporting implementation.
The Realistic Large and Enterprise XLarge live token gates remain open until
compatible runner results are collected and summarized.

---

## 2. 0.5 Product Contract

### 2.1 Decision behavior

| Decision | 의미 | 0.5 기본 실행 정책 | Trusted route | Safe edit paths |
|---|---|---|---|---|
| `MATCH` | 충분한 route evidence와 분리도 확보 | `workspace_write` | 제공 | 제공 |
| `IN_SCOPE_NO_ROUTE` | 저장소 책임 범위 안이지만 정확한 route 없음 | `read_only_discovery` 후 재평가 | 제공하지 않음 | 제공하지 않음 |
| `OUT_OF_SCOPE` | 검토된 repository boundary 밖 | `read_only` 강제 | 제공하지 않음 | 제공하지 않음 |
| `UNCERTAIN` | 범위 또는 route 충분성 판단 불가 | `read_only` 강제 후 사용자 확인 | 제공하지 않음 | 제공하지 않음 |

### 2.2 No-match safety invariant

명시적으로 unsupported인 요청은 다음 조건을 모두 만족해야 한다.

```text
decision = OUT_OF_SCOPE
trusted route = 없음
safe edit paths = 없음
production write attempt = 없음
final production change = 없음
```

`MATCH` 비율을 높이기 위해 이 invariant를 약화해서는 안 된다.

### 2.3 Normal bugfix recovery invariant

검증된 정상 bugfix는 다음 중 하나를 받아야 한다.

```text
A. 정확한 MATCH
또는
B. IN_SCOPE_NO_ROUTE + evidence-backed bounded discovery
```

정상 bugfix가 `OUT_OF_SCOPE`, 근거 없는 `UNCERTAIN`, 또는 아무 탐색 단서도 없는 route-free 상태로 끝나는 것은 회귀로 본다.

### 2.4 Bounded discovery is not a trusted route

Bounded discovery는 route match 실패를 숨기는 장치가 아니다.

- 반드시 `IN_SCOPE_NO_ROUTE`로 표시한다.
- candidate마다 blueprint node, workflow, 또는 repository-relative evidence 근거를 제공한다.
- `safe_edit_paths`를 제공하지 않는다.
- 읽기 후보와 테스트 후보를 소수로 제한한다.
- agent는 discovery 후 새 evidence로 context를 다시 평가하거나 사용자 승인을 받아야 한다.

---

## 3. Release Gates

모든 gate는 순서대로 평가한다. 앞 gate가 실패하면 뒤 gate의 개선 수치를 릴리스 근거로 사용하지 않는다.

### Gate P0: Runner correctness

#### Required change observation

Runner는 실행 전 clean baseline과 실행 후 상태를 비교하여 다음을 구분해 기록해야 한다.

```text
tracked modified files
staged files
deleted files
renamed files
untracked files
production file changes
allowed harness artifacts
Codex JSONL production write attempts
```

권장 workspace truth source:

```text
git status --porcelain=v1 -z --untracked-files=all
git diff --numstat HEAD
git diff --cached --numstat HEAD
```

JSONL `file_change` 이벤트는 최종 workspace truth를 대체하지 않는다. 최종 변경과 별도로 "production write attempt"를 검출하는 감사 신호로 사용한다.

#### Required runner fixtures

다음 fixture를 모두 정확히 판정해야 한다.

| Fixture | 기대 결과 |
|---|---|
| 기존 production 파일 수정 | production change 감지 |
| 새 `ios/` 파일 생성 | untracked production change 감지 |
| 새 `infra/terraform/` 파일 생성 | untracked production change 감지 |
| 새 `src/.../infrastructure/` 패키지 생성 | untracked production change 감지 |
| production 파일 삭제 또는 rename | production change 감지 |
| write 후 revert하여 최종 diff 없음 | final change 없음, JSONL write attempt 있음 |
| 허용된 runner log 생성 | harness artifact로 분리 |
| 실행 전 dirty worktree | benchmark invalid 처리 |

#### Required result fields

```json
{
  "baseline_clean": true,
  "changed_files_tracked": [],
  "staged_files": [],
  "deleted_files": [],
  "renamed_files": [],
  "untracked_files": [],
  "production_file_changes": [],
  "jsonl_production_write_attempts": [],
  "context_decision": "OUT_OF_SCOPE",
  "context_edit_policy": "read_only",
  "context_execution_policy": "read_only"
}
```

#### P0 pass condition

```text
runner correctness fixtures = 100% pass
untracked production files = 반드시 감지
dirty baseline = 반드시 invalid
```

P0가 통과하기 전의 기존 no-match edit-free 및 boundary 결과는 참고 자료로만 취급한다.

---

### Gate P1: Preserve improved no-match

No-match 평가는 단순히 `decision != MATCH`인지 확인하는 데서 끝나지 않는다. 기대 decision과 실제 실행 행동을 함께 평가한다.

#### Required metrics

```text
expected_decision_accuracy
false_route_rate
safe_edit_leak_rate
production_write_attempt_free_rate
final_edit_free_rate
wrong_edit_count
boundary_violation_count
```

#### P1 release minimum

| Dataset | Required result |
|---|---|
| Realistic Large no-match | route match `0/3`, production write attempt `0`, production edit `0` |
| Enterprise XLarge no-match | route match `0/6`, production write attempt `0`, production edit `0` |
| Holdout no-match set | expected decision accuracy `100%`, false route `0`, production edit `0` |
| All non-`MATCH` results | trusted route `0`, safe-edit path `0` |

명시적으로 검토된 unsupported task는 `OUT_OF_SCOPE`여야 한다. 단순히 `UNCERTAIN`으로 보내서 route rejection 수치만 맞추는 것은 통과로 보지 않는다.

#### Enforcement rule

- `OUT_OF_SCOPE`와 `UNCERTAIN`: runner 또는 integration이 실제 read-only sandbox를 사용한다.
- `IN_SCOPE_NO_ROUTE`: 첫 단계는 read-only discovery로 실행한다.
- read-only 상태에서 production write attempt가 발생하면 최종 diff가 없어도 policy failure로 기록한다.

---

### Gate P2: Reduce normal bugfix hard rejection

P2의 목적은 no-match safety를 유지한 채 정상 bugfix가 버려지는 비용을 낮추는 것이다.

#### Required metrics

```text
trusted_route_recall
normal_bugfix_hard_rejection_rate
actionable_guidance_coverage
bounded_discovery_coverage
boundary_violation_count
resolved_rate
```

정의:

```text
normal_bugfix_hard_rejection
=
정상 bugfix가 OUT_OF_SCOPE, 근거 없는 UNCERTAIN,
또는 read-first 후보 없는 IN_SCOPE_NO_ROUTE로 끝난 경우

actionable_guidance
=
MATCH 또는 evidence-backed bounded discovery
```

#### P2 release minimum

| Dataset | Required result |
|---|---|
| Realistic Large bugfix | trusted route match `>= 20/24` |
| Realistic Large bugfix | actionable guidance `24/24` |
| Enterprise core bugfix | trusted route match `30/30` |
| Enterprise all bugfix | actionable guidance `39/39` |
| Normal bugfix overall | `OUT_OF_SCOPE = 0`, empty guidance `= 0` |
| All bugfix runs | boundary violation `= 0` |

Enterprise decoy-heavy 작업은 안전 근거가 부족하면 억지로 `MATCH`할 필요가 없다. 대신 정상 bugfix임이 확인되면 `IN_SCOPE_NO_ROUTE`와 bounded discovery를 제공해야 한다.

#### Stretch target

```text
Realistic Large trusted route match >= 22/24
Enterprise all-bugfix trusted route match >= 36/39
normal_bugfix_hard_rejection_rate = 0%
```

---

### Gate P3: Reduce token use

토큰 효율은 안전하고 해결된 실행끼리만 비교한다.

다음 실행은 token-saving 계산의 성공 분모에 넣지 않는다.

- 잘못 거절되어 작업을 수행하지 않은 bugfix
- boundary violation이 발생한 실행
- no-match에서 production write가 발생한 실행
- infrastructure-invalid 실행

#### Required token reports

```text
map authoring tokens
context output tokens
repair task tokens
safe-and-resolved task tokens
no-match tokens
break-even task count
```

#### Context output budget

- `MATCH`: 선택된 route만 제공하며 unrelated route catalog를 포함하지 않는다.
- `IN_SCOPE_NO_ROUTE`: 최대 3개 likely area, 최대 5개 read-first path, 최대 3개 likely test를 제공한다.
- 중복된 contract, path, reason은 제거한다.
- discovery candidate는 근거가 없는 경우 포함하지 않는다.

#### P3 release minimum

| Dataset | Required result |
|---|---|
| Realistic Large bugfix | no-map 대비 token saving `>= 35%` |
| Enterprise bugfix | no-map 대비 token saving `>= 35%` |
| Enterprise core bugfix | no-map 대비 token saving `>= 45%` |
| No-match | median tokens가 no-map보다 높지 않음 |
| Map authoring | updated-map baseline 대비 증가 없음, 증가 시 명시적 승인 필요 |

#### Stretch target

```text
Realistic Large bugfix break-even <= 40 tasks
Enterprise bugfix break-even <= 20 tasks
```

---

### Gate P4: Reduce resolution time

시간 평가는 안전성과 해결률을 먼저 통과한 실행만 대상으로 한다.

#### Required time reports

```text
cumulative seconds
per-task median
per-task p90
context generation seconds
discovery-to-first-edit seconds
total resolution seconds
```

#### P4 release minimum

| Dataset | Required result |
|---|---|
| Realistic Large bugfix | no-map보다 느리지 않음 |
| Enterprise bugfix | no-map 대비 time saving `>= 10%` |
| No-match | no-map보다 느리지 않음 |
| Context decision | 기존 `0.4` 대비 유의미한 지연 회귀 없음 |

#### Stretch target

```text
Realistic Large bugfix time saving >= 10%
Enterprise bugfix time saving >= 15%
```

---

## 4. Implementation Strategy

### 4.1 Preserve hard negative boundaries

`OUT_OF_SCOPE`는 다음과 같은 검토된 hard negative가 있을 때만 선택한다.

- repository `unsupported_surfaces`
- repository `unsupported_technologies`
- repository `unsupported_artifact_types`
- repository `repository_non_goals`

규칙:

- route score가 낮다는 이유만으로 `OUT_OF_SCOPE`를 선택하지 않는다.
- supported와 unsupported evidence가 동시에 있으면 `UNCERTAIN`으로 보낸다.
- 기술명이 문서나 예시로 언급되었다는 이유만으로 unsupported task로 판단하지 않는다.

### 4.2 Use existing positive evidence before adding schema

먼저 기존 agent-map 필드를 matcher에 충분히 연결한다.

```text
task
intent
match_terms
when_to_use
common_failure_modes
when_not_to_use
```

`common_failure_modes`는 정상 bugfix의 symptom matching에 사용하되, 그 자체만으로 broad route를 확정하지 않는다.

Optional `domain_entities` 같은 새 필드는 기존 필드와 evidence-backed discovery만으로 목표 recall을 달성하지 못했을 때 추가한다. 새 필드를 추가한다면 blueprint node, evidence symbol, 또는 repository-relative source evidence와 연결할 수 있어야 한다.

### 4.3 Match with independent evidence, not one global threshold

권장 decision 순서:

```text
1. Explicit repository hard-negative boundary 확인
2. Route-level when_not_to_use 및 negative boundary 적용
3. Candidate route retrieval
4. 독립적인 positive evidence 종류 확인
5. Route separation 확인
6. MATCH가 아니면 in-scope evidence로 bounded discovery 생성
7. 근거가 부족하거나 충돌하면 UNCERTAIN
```

Positive evidence 예:

- exact multi-word `match_terms`
- `when_to_use` phrase
- task/intent meaningful-term overlap
- `common_failure_modes` symptom
- grounded node/workflow/evidence candidate

한 개의 일반 단어만으로 `MATCH`하지 않는다. 반대로 exact route phrase, symptom, grounded area evidence가 함께 있는 정상 bugfix를 단순 threshold 부족으로 버리지 않는다.

### 4.4 Add evidence-backed bounded discovery

`IN_SCOPE_NO_ROUTE`의 machine-readable report에 optional `discovery_context`를 추가한다.

예:

```json
{
  "decision": "IN_SCOPE_NO_ROUTE",
  "route_status": "not_found",
  "edit_policy": "cautious",
  "execution_policy": "read_only_discovery",
  "safe_edit_paths": [],
  "discovery_context": {
    "likely_areas": [
      {
        "node_id": "domain:billing",
        "label": "Billing",
        "reason": "task terms overlap grounded node responsibility"
      }
    ],
    "read_first": [
      {
        "path": "src/.../billing/service.py",
        "reason": "evidence for domain:billing"
      }
    ],
    "likely_tests": [
      {
        "path": "tests/.../test_billing.py",
        "reason": "grounded test evidence"
      }
    ]
  }
}
```

Discovery candidate는 다음 소스에서만 가져온다.

- blueprint node labels, descriptions, inspector summaries
- blueprint workflow steps
- resolving repository-relative node or edge evidence
- validated route의 start node 또는 workflow와 독립적으로 연결되는 grounded
  reading/test evidence

선택되지 않은 route의 `must_read`, `tests`, 또는 `safe_edit` 목록을 그대로
discovery output에 복사해서는 안 된다. Candidate는 route가 아니라 grounded
node/workflow evidence로 정당화되어야 한다.

Discovery 출력은 trusted route처럼 표시하지 않으며 edit permission을 부여하지 않는다.
Discovery가 grounded node 또는 workflow를 찾으면 agent는 파일을 수정하기 전에
`bunya-jido context --node <id>` 또는 `--workflow <id>`로 route decision을 다시
평가한다.

### 4.5 Add an explicit execution policy for integrations

기존 `edit_policy`를 호환성 때문에 유지하고, integration을 위한 additive field를 검토한다.

```text
workspace_write
read_only_discovery
read_only
```

Runner는 이 값을 읽어 sandbox를 선택한다. Bunya-Jido CLI가 외부 agent runtime의 권한을 직접 제어할 수 있다고 주장하지 않는다.

### 4.6 Strengthen native agent instructions without contradiction

Agent activation 문구는 다음 의미를 가져야 한다.

```text
MATCH:
route guidance를 사용해 작업 가능

IN_SCOPE_NO_ROUTE:
먼저 읽기 전용 discovery 수행
근거를 확보한 후 context 재평가 또는 사용자 승인 전에는 수정 금지

OUT_OF_SCOPE:
수정 금지, 검토된 boundary 설명

UNCERTAIN:
수정 금지, 사용자 확인 요청
```

`decision != MATCH이면 무조건 설명만 반환` 같은 규칙은 사용하지 않는다. 그 규칙은 정상 bugfix를 복구하기 위한 `IN_SCOPE_NO_ROUTE` discovery를 막는다.

---

## 5. Delivery Sequence

### Work Package 0: Benchmark Truth

**Priority:** P0 blocker
**Location:** Bunya-Jido audit primitive and result-contract documentation,
plus external benchmark runner integration

Scope:

- untracked-aware workspace observation
- staged/deleted/renamed file observation
- JSONL production write-attempt audit
- clean baseline enforcement
- production/harness artifact classification
- context decision and execution policy capture
- runner correctness fixtures

Exit criteria:

- P0 runner fixtures 100% pass
- updated runner로 모든 release benchmark를 재실행할 수 있음

### Work Package 1: Safety Lock

**Priority:** P1 blocker
**Primary files:** `src/bunya_jido/blueprint.py`, `tests/test_blueprint.py`, agent activation guidance

Scope:

- 현재 repository hard-negative behavior characterization 강화
- non-`MATCH` trusted route 및 safe-edit leak regression 강화
- optional `execution_policy` 출력
- `OUT_OF_SCOPE`/`UNCERTAIN` read-only integration contract 문서화
- expected decision confusion-matrix fixture 추가

Exit criteria:

- P1 no-match gates 모두 통과
- no-match holdout에서도 false route와 production write 없음

### Work Package 2: Safe Bounded Discovery

**Priority:** P2 prerequisite
**Primary files:** `src/bunya_jido/blueprint.py`, `src/bunya_jido/cli.py`, `tests/test_blueprint.py`

Scope:

- `IN_SCOPE_NO_ROUTE`용 evidence-backed `discovery_context`
- bounded candidate ranking과 출력 cap
- discovery reason과 source evidence 표시
- safe-edit path 비노출 보장
- discovery 후 `context --node` 또는 `context --workflow` 재평가 workflow 문서화

Exit criteria:

- 정상 bugfix actionable guidance coverage 목표 달성
- no-match safety gate 무회귀

### Work Package 3: Recall Recovery

**Priority:** P2
**Primary files:** `src/bunya_jido/blueprint.py`, agent-map schema/validation, evaluation fixtures

Scope:

- `common_failure_modes` symptom evidence 활용
- existing `match_terms`와 `when_to_use` calibration
- route-level negative boundary 우선 적용
- independent positive evidence와 route separation
- realistic/enterprise missed bugfix task 회귀 fixture
- holdout task로 benchmark phrase 과적합 방지

Exit criteria:

- P2 release minimum 달성
- P1 gate 유지

구현 초기에는 대규모 matcher 모듈 분리를 하지 않는다. 행동과 테스트가 안정된 후 `blueprint.py`의 matcher 책임이 실제 유지보수 병목이면 별도 리팩터링한다.

### Work Package 4: Token Efficiency

**Priority:** P3
**Primary files:** context rendering and benchmark reporting

Scope:

- selected route 외 unrelated context 제거
- discovery context cap과 deduplication
- read-first 후보 precision 개선
- no-match 즉시 종료 경로
- task token과 map authoring token 분리 보고
- break-even 재계산

Exit criteria:

- P3 release minimum 달성
- P0-P2 gate 유지

### Work Package 5: Resolution Time

**Priority:** P4
**Primary files:** routing/discovery hot path and runner timing report

Scope:

- context decision latency 측정
- discovery-to-first-edit 시간 측정
- 불필요한 반복 탐색 제거
- no-match 즉시 종료 시간 개선
- task별 median/p90 보고

Exit criteria:

- P4 release minimum 달성
- P0-P3 gate 유지

### Work Package 6: 0.5 Release Evidence

Scope:

- updated runner로 no-map, old-map, `0.5` map 조건을 동일 환경에서 재실행
- `0.5` benchmark report 작성
- agent-utility suite와 self-map 업데이트
- `CHANGELOG.md`, 버전 선언, release guide 업데이트
- 전체 release gate 실행

---

## 6. Benchmark Methodology

Runner 버그가 발견되었으므로 `0.5` release evidence에서는 기존 baseline을 재사용하지 않는다.

### 6.1 Required controls

각 비교 실행은 다음을 고정하고 기록한다.

```text
agent/model/version
repair effort
system and repository instructions
task text
repository commit
map commit
runner commit
execution environment
repetition count
observation date
```

### 6.2 Required comparison

```text
no-map
old-map
0.5-map
```

세 조건을 수정된 runner와 동일 agent 환경에서 다시 실행한다.

### 6.3 Tuning and holdout split

Realistic Large와 Enterprise XLarge의 기존 실패 task만 반복해서 최적화하면 benchmark phrase에 과적합될 수 있다.

따라서 task를 다음으로 분리한다.

- calibration set: matcher와 discovery 개선에 사용
- holdout set: release 직전에만 평가
- adversarial no-match set: route phrase와 겹치는 unsupported 요청
- ambiguous in-scope set: `IN_SCOPE_NO_ROUTE`가 적합한 정상 작업

### 6.4 Reporting rules

- cumulative 값과 task별 median/p90을 함께 보고한다.
- 안전성 실패와 해결 실패를 숨긴 token/time saving을 인정하지 않는다.
- `MATCH`, `IN_SCOPE_NO_ROUTE`, `OUT_OF_SCOPE`, `UNCERTAIN` confusion matrix를 제공한다.
- final workspace change와 JSONL write attempt를 별도 보고한다.
- map authoring cost와 task execution cost를 분리한다.

---

## 7. Tests And Artifacts

### 7.1 In-repository tests

권장 테스트 추가 또는 확장:

```text
tests/test_blueprint.py
  - expected decision confusion matrix
  - common_failure_modes matching
  - hard negative precedence
  - mixed supported/unsupported => UNCERTAIN
  - IN_SCOPE_NO_ROUTE discovery context
  - non-MATCH safe-edit leak prevention

tests/test_self_map.py
  - committed self-map decision/discovery contract

.bunya-jido/bunya-jido.agent-evaluation.json
  - known MATCH tasks
  - supported no-route tasks
  - reviewed OUT_OF_SCOPE tasks
  - ambiguous UNCERTAIN tasks
  - adversarial overlap tasks
```

Runner fixture tests는 runner가 실제로 위치한 저장소에 추가한다.

### 7.2 Suggested artifacts

```text
docs/BUNYA_JIDO_0_5_UPDATE_PLAN.md
docs/BUNYA_JIDO_0_5_BENCHMARK_REPORT.md
docs/BENCHMARK_RESULT_CONTRACT.md
.bunya-jido/bunya-jido.agent-evaluation.json
```

새 `context.py`, `matcher.py`, `capabilities.py` 모듈은 행동 안정화 후 책임 분리가 실제로 필요할 때만 도입한다.

---

## 8. Compatibility

`0.5`는 alpha minor release다.

- 기존 `context --json` 필드는 유지한다.
- `discovery_context`와 `execution_policy`는 additive optional field로 설계한다.
- non-`MATCH`에서 trusted route와 safe-edit path를 노출하지 않는 기존 계약을 유지한다.
- classic blueprint와 Studio blueprint의 publication contract를 변경하지 않는다.
- human-facing HTML viewer redesign은 `0.5` 범위가 아니다.

Schema version을 바꿀 필요가 있는지는 실제 JSON contract 변경 범위를 확인한 후 결정한다. Optional additive field만 추가한다면 기존 consumer 호환성을 우선한다.

---

## 9. Risks And Mitigations

| Risk | Mitigation |
|---|---|
| No-match 안전성을 지키려다 정상 bugfix를 다시 과도하게 거절 | hard veto와 route score를 분리하고 bounded discovery 제공 |
| Recall을 올리려다 false route 재발 | P1 gate를 P2보다 먼저 실행하고 holdout no-match 유지 |
| Bounded discovery가 사실상 untrusted safe-edit route가 됨 | safe-edit 미제공, evidence와 reason 표시, read-only discovery 강제 |
| 특정 benchmark phrase에 과적합 | calibration/holdout 분리, adversarial wording 추가 |
| JSONL 이벤트 누락 또는 과잉 신뢰 | workspace truth와 write-attempt audit를 별도 처리 |
| 토큰 절감이 작업 거절로 만들어짐 | safe-and-resolved 실행만 효율 계산 |
| 외부 runner가 수정되지 않은 채 0.5가 릴리스됨 | P0 runner evidence를 release blocker로 지정 |
| 리팩터링이 behavior change를 가림 | 먼저 characterization test와 작은 행동 변경, 모듈 분리는 후속 |

---

## 10. Explicit Non-Goals

`0.5`에서 하지 않는 것:

- 모든 non-`MATCH`를 `OUT_OF_SCOPE`로 처리
- global threshold 하나만 낮춰 route recall 개선
- non-`MATCH`에 trusted route 또는 safe-edit path 제공
- benchmark 결과를 근거 없이 일반적인 live-agent 성능으로 확대 해석
- human-facing HTML viewer의 대규모 UI redesign
- runner source가 없는 상태에서 runner bug가 해결되었다고 주장
- map authoring 전체를 자동화하거나 semantic interpretation을 자동 진실로 취급

---

## 11. Release Checklist

### P0 Runner truth

- [ ] External runner patch 식별자 기록
- [x] untracked/staged/deleted/renamed fixture 통과
- [x] JSONL production write-attempt fixture 통과
- [x] dirty baseline invalid 처리
- [x] result JSON contract 검증

### P1 No-match safety

- [x] context execution-policy contract and agent activation guidance
- [x] deterministic decision confusion matrix
- [x] committed non-`MATCH` false-route and safe-edit leak `0`
- [x] committed expected decision and execution-policy accuracy `100%`
- [ ] Realistic no-match route match `0/3`
- [ ] Enterprise no-match route match `0/6`
- [ ] no-match production write attempt `0`
- [ ] no-match final production edit `0`
- [ ] non-`MATCH` safe-edit leak `0`
- [ ] holdout no-match expected decision accuracy `100%`

### P2 Normal bugfix recovery

- [ ] Realistic trusted route match `>= 20/24`
- [ ] Realistic actionable guidance `24/24`
- [ ] Enterprise core trusted route match `30/30`
- [ ] Enterprise all-bugfix actionable guidance `39/39`
- [ ] normal bugfix `OUT_OF_SCOPE = 0`
- [ ] bugfix boundary violation `0`

### P3 Token efficiency

- [ ] Realistic bugfix token saving `>= 35%`
- [ ] Enterprise bugfix token saving `>= 35%`
- [ ] Enterprise core bugfix token saving `>= 45%`
- [ ] no-match median token use가 no-map보다 높지 않음
- [ ] map authoring token 변화와 break-even 보고

### P4 Resolution time

- [ ] Realistic bugfix가 no-map보다 느리지 않음
- [ ] Enterprise bugfix time saving `>= 10%`
- [ ] no-match가 no-map보다 느리지 않음
- [ ] median/p90과 context latency 보고

### Repository release gate

- [ ] full unit suite
- [ ] blueprint validation
- [ ] agent-map validation
- [ ] grounded diagnostic
- [ ] agent-utility evaluation
- [ ] atlas-quality evaluation
- [ ] stale-map review
- [ ] `0.5` benchmark report
- [ ] version declarations and changelog aligned

---

## 12. Definition Of Done

Bunya-Jido `0.5`는 다음 문장을 증거와 함께 말할 수 있을 때 완료된다.

> 수정된 benchmark runner는 tracked와 untracked production changes 및 write attempts를 정확히 관찰한다. Bunya-Jido는 unsupported no-match 요청에 trusted route나 쓰기 권한을 주지 않으며, 정상 bugfix에는 정확한 trusted route 또는 evidence-backed bounded discovery를 제공한다. 이 안전성과 해결률을 유지한 상태에서 `0.4` updated-map보다 토큰과 해결 시간이 개선되었다.
