# Bunya-Jido Benchmark Program 전체 실험 기록
## Curated route 실험부터 최신 dual-scale synchronized benchmark까지

**기록 기준일:** 2026-06-09
**대상:** Bunya-Jido semantic map의 coding-agent utility, safety, 경제성 검증
**주요 실행 환경:** Codex CLI, GPT-5.5, `medium` 및 `xhigh` reasoning effort
**주의:** 모든 성능 결과는 synthetic repository에서 얻었다. 실제 production repository 일반화는 별도 검증이 필요하다.

---

## 0. 이 문서가 다루는 범위

Bunya-Jido benchmark는 한 번에 설계된 단일 실험이 아니었다. 처음에는 작은 합성 repository와 수동 Codex extension으로 map의 탐색 효율을 확인했고, 이후 native map authoring, hidden test 격리, Codex CLI JSONL 계측, 대형 repository, XHigh replication, map-quality ablation, no-match hardening, decision-aware routing 순으로 실험을 확장했다.

정식 통계에 포함된 repair run은 총 **873개**, fresh native map authoring은 **14회**다. 여기에 smoke run, workspace probe, CLI compatibility test, 실패한 telemetry 계측과 폐기 run이 추가로 존재하지만 성능 통계에서는 제외했다.

### 정식 실험 계보

| 단계 | 실험 | Repo 규모 | Effort | Repair runs | 주요 질문 | 대표 결과 |
| --- | --- | --- | --- | --- | --- | --- |
| A | Curated route utility | 초기 synthetic 3종 | Medium | 108 | 좋은 route 자체가 탐색 비용을 줄이는가 | 누적 tokens 25.3% 감소 |
| B | Native generated-map pilot | 52~2,691 SLOC, 4종 | Medium | 144 | 실제 생성 map도 도움이 되는가 | Bugfix paired 15.86% ± 21.29% |
| C1 | Realistic Large E2E | 28,708 SLOC | Medium | 54 | 현실적 규모의 경제성 | Bugfix paired 43.56% ± 17.84% |
| C2 | Realistic Large replication | 28,708 SLOC | XHigh | 54 | 더 강한 effort가 더 좋은가 | Bugfix paired 36.53% ± 22.98% |
| D1 | Enterprise XLarge E2E | 126,731 SLOC | Medium | 90 | enterprise 규모의 효용과 안전성 | Bugfix 누적 40.48% 감소 |
| D2 | Enterprise XLarge replication | 126,731 SLOC | XHigh | 90 | hard-task 안정성 | Bugfix 누적 44.45% 감소 |
| E | XHigh-map + Medium-repair ablation | 126,731 SLOC | Medium repair | 45 | 비싼 map을 한 번 만들 가치가 있는가 | Medium map 대비 bugfix tokens 1.75% 증가 |
| F | Updated-map regression | 28.7K / 126.7K | Medium | 72 | no-match FP 수정의 부작용 | No-match 개선, Realistic recall 급락 |
| G | Updated-v2 regression | 28.7K / 126.7K | Medium | 72 | read-only·bounded discovery 시도 | No-match 성공, bugfix no-edit 실패 잔존 |
| H | 최신 synchronized dual-scale | 28.7K / 126.7K | Medium | 144 | 안전성과 utility를 동시 재검증 | Bugfix 63/63 유지, tokens 21.62% 감소 |

---

## 1. 공통 실험 원칙

### 1.1 Clean-first, freeze-first

Native-map 실험은 map이 결함의 정답을 미리 보지 못하도록 다음 순서를 지켰다.

```text
clean repository
→ Bunya-Jido prepare
→ Codex native map authoring
→ validation
→ map freeze 및 checksum
→ defect injection
→ baseline / mapped repair
```

### 1.2 Hidden test 격리

Repair agent의 workspace에는 public test만 있었다. Hidden test는 agent 종료 후 별도의 grading copy에 주입했다. 따라서 agent가 hidden test를 읽거나 수정해 통과할 수 없었다.

### 1.3 Paired comparison

같은 task, 같은 repetition, 같은 model effort를 가진 baseline과 mapped run을 한 pair로 묶었다. Paired saving은 다음과 같이 계산했다.

```text
saving = (baseline - mapped) / baseline × 100
```

누적 절감률과 pair별 평균은 함께 기록했다. 전자는 총비용을, 후자는 task 간 분산을 보여 준다.

### 1.4 Strict no-match

No-match는 “없는 버그를 억지로 찾게 하는 문제”가 아니다. 현재 repository의 product surface와 technology stack 밖의 요청을 router와 agent가 거절하는지 보는 안전성 시험이다.

```text
정상:
No matching trusted route / OUT_OF_SCOPE / UNCERTAIN
→ read-only
→ production file 변경 0

실패:
관련 없는 route를 trusted route로 반환
또는 unsupported 요청에 파일을 생성·수정
```

### 1.5 토큰과 시간의 분리

Semantic map은 repository 탐색과 context ingestion을 줄일 수 있지만, wall-clock에는 backend latency, shell command, test 실행, Windows I/O, agent의 도구 선택이 함께 영향을 준다. 따라서 token saving과 time saving은 별도 지표로 다뤘다.

---

## 2. 통계 이전 단계: 수동 prototype과 harness 구축

초기 benchmark는 Antigravity의 Codex extension, 수동 세션 기록, OpenTelemetry conversation usage를 이용했다. 이 단계에서 map이 첫 파일 탐색과 불필요한 read를 줄이는 신호는 보였지만, 정식 통계로 쓰기에는 문제가 많았다.

### 확인된 문제

- 창을 열어 둔 시간이 elapsed time에 포함됐다.
- 한 benchmark session 이후 여러 Codex conversation telemetry가 섞였다.
- 일부 run은 `elapsed_seconds=None`으로 기록돼 analyzer가 실패했다.
- usage event가 누락된 run이 0 tokens로 보였다.
- Windows 기본 `cp949`로 UTF-8 JSONL을 읽어 decode error가 났다.
- Codex CLI 0.135.0에서 `--ask-for-approval` 인자 형태가 달랐다.
- native sandbox가 workspace write를 막거나 recoverable policy warning을 infra failure로 오인했다.
- agent가 `tests/test_public.py`를 수정하는 경우가 있어 protected-file rule이 필요했다.
- 긴 Desktop 경로 아래 `.git/objects`와 hooks에서 Windows path-length 오류가 났다.

### 최종 조치

- `codex exec --json` 직접 실행
- `turn.completed.usage`가 없는 run은 infrastructure-invalid
- subprocess bytes를 UTF-8로 명시 디코딩
- `approval_policy="never"`와 Windows `unelevated` sandbox 사용
- clean Git baseline, protected-file violation, hidden-test grading copy 도입
- `%TEMP%`의 짧은 workspace와 `core.longpaths=true`
- tracked, untracked, JSONL `file_change`를 함께 감사
- `__pycache__`, `*.pyc`, `*.pyo`는 runtime noise로 제외

이 단계의 smoke와 실패 run은 제품·harness 개발 기록으로는 중요하지만 성능 수치에는 포함하지 않았다.

---

## 3. Experiment A: Curated Semantic Route Utility

### 목적

사람이 미리 만든 bounded route가 주어졌을 때 coding agent의 탐색 비용이 줄어드는지 확인한 mechanism test다. Bunya-Jido의 native authoring 품질이나 map 생성 비용은 측정하지 않았다.

### 구성

| 항목 | 값 |
| --- | --- |
| Synthetic repositories | 3 |
| Tasks | 18 |
| Conditions | baseline, curated mapped |
| Repetitions | 3 |
| Repair runs | 108 |
| Model / effort | GPT-5.5 / Medium |

### 결과

| 지표 | Baseline | Curated mapped | 변화 |
| --- | ---: | ---: | ---: |
| 해결 | 53/54 | 54/54 | +1 |
| 누적 tokens | 7,164,603 | 5,355,288 | **25.3% 감소** |
| 실행당 tokens | 132,678 ± 37,561 | 99,172 ± 37,961 | 감소 |
| Bugfix 누적 token 감소 |  |  | **29.8%** |

초기 수동 시간 기록에서는 small, medium, large 순으로 중앙값이 각각 40.67→22.47초, 42.15→26.74초, 44.65→36.23초로 줄었다. 다만 이 시간은 이후 subprocess 기반 elapsed와 동일한 계측이 아니므로 참고치로만 남긴다.

### 해석

좋은 route가 이미 존재하면 agent가 repository를 덜 읽고 더 빠르게 관련 파일로 이동할 수 있다는 전제는 성립했다. 다음 단계는 이 route를 Bunya-Jido가 스스로 만들었을 때도 같은 효과가 나는지 확인하는 일이었다.

---

## 4. Experiment B: Native Generated-Map Pilot

### Repository 규모

역사적 이름은 `small`, `medium`, `large`, `xlarge`였지만 실제 규모는 훨씬 작았다.

| Historical ID | Approx. SLOC | src Python files | 현실적 분류 |
| --- | ---: | ---: | --- |
| `small_cli` | 52 | 11 | micro |
| `medium_service` | 123 | 32 | micro |
| `large_workflow` | 256 | 74 | micro |
| `xlarge_control_plane` | 2,691 | 248 | small |

### Map authoring 비용

| Repo | Tokens | Seconds | Retry |
| --- | ---: | ---: | ---: |
| `small_cli` | 780,751 | 409.03 | 0 |
| `medium_service` | 1,460,829 | 541.39 | 0 |
| `large_workflow` | 914,535 | 449.02 | 0 |
| `xlarge_control_plane` | 1,929,983 | 592.62 | 0 |
| **합계** | **5,086,098** | **1,992.06** |  |

### Repair 구성

```text
24 tasks × 2 conditions × 3 repetitions
= 144 raw runs
= 72 paired comparisons
```

초기 analyzer는 pair를 두 번 집계하는 오류가 있어 raw JSON에서 corrected analysis를 다시 계산했다.

### 결과

| 범위 | Pairs | Token saving 평균 ± SD | 누적 시간 변화 | Paired time saving 평균 ± SD |
| --- | ---: | ---: | ---: | ---: |
| 전체 | 72 | **4.81% ± 47.61%** | 8.23% 느림 | -4.67% ± 59.58% |
| Bugfix | 60 | **15.86% ± 21.29%** | **9.11% 빠름** | 4.18% ± 39.47% |
| No-match | 12 | **-50.45% ± 90.58%** | 43.06% 느림 | -48.92% ± 109.50% |

### 해석

- Native map도 ordinary bugfix에서는 평균적으로 이득이었다.
- 작은 repository에서는 authoring 비용이 수리 절감량보다 지나치게 컸다.
- No-match를 일반 bugfix와 섞으면 전체 결과를 왜곡했다.
- 가장 큰 `xlarge_control_plane`에서 map의 신호가 상대적으로 강했다.
- 이후 규모 taxonomy를 재설계하고 realistic large와 enterprise xlarge를 새로 만들게 된 직접적인 계기였다.

---

## 5. Experiment C1: Realistic Large, Medium E2E

### Repository

| 항목 | 값 |
| --- | ---: |
| SLOC | 28,708 |
| Physical LOC | 34,355 |
| src Python files | 1,432 |
| Responsibility areas | 27 |
| Tasks | 8 bugfix + 1 no-match |
| Repair runs | 54 |

### Authoring

| Model | Effort | Tokens | Seconds | Validation |
| --- | --- | ---: | ---: | --- |
| GPT-5.5 | Medium | 1,748,486 | 648.22 | pass |

### 결과

| 지표 | 결과 |
| --- | ---: |
| 해결 | 54/54 |
| 전체 누적 token 감소 | **42.23%** |
| 전체 paired saving | **39.52% ± 22.30%** |
| Bugfix paired saving | **43.56% ± 17.84%** |
| Bugfix token break-even | **18.06 tasks** |
| Boundary violations | 0 |
| Protected-file violations | 0 |
| 전체 시간 감소 | 22.07% |
| Bugfix 시간 감소 | 7.44% |

### 해석

초기 대형 실험에서 가장 강한 경제성 신호가 나왔다. 다만 당시 no-match route가 실제로 거절된 것인지, agent가 잘못된 route를 받았지만 우연히 편집하지 않은 것인지 구분하는 schema가 부족했다.

---

## 6. Experiment C2: Realistic Large, XHigh E2E

### Authoring 및 결과

| 지표 | 값 |
| --- | ---: |
| XHigh map authoring tokens | 2,891,143 |
| Authoring seconds | 1,069.78 |
| Repair runs | 54 |
| 해결 | 54/54 |
| 전체 누적 token 감소 | **37.40%** |
| Bugfix paired saving | **36.53% ± 22.98%** |
| Bugfix token break-even | **28.36 tasks** |
| Boundary violations | 0 |
| 전체 시간 감소 | 4.70% |
| Bugfix 시간 변화 | **9.34% 느림** |

### 해석

XHigh가 항상 더 효율적이라는 가설은 지지되지 않았다. Medium보다 map authoring 비용이 65%가량 높았고 repair saving도 낮았다. Realistic 규모에서는 Medium이 명확한 기본값이었다.

---

## 7. Experiment D1: Enterprise XLarge, Medium E2E

### Repository

| 항목 | 값 |
| --- | ---: |
| SLOC | 126,731 |
| src Python files | 5,926 |
| Responsibility areas | 48 |
| Tasks | 13 bugfix + 2 no-match |
| Repair runs | 90 |

### Authoring 및 결과

| 지표 | 값 |
| --- | ---: |
| Map authoring tokens | 1,527,492 |
| Authoring seconds | 759.46 |
| 전체 누적 token 감소 | **29.82%** |
| Bugfix 누적 token 감소 | **40.48%** |
| Bugfix paired saving | **31.24% ± 53.39%** |
| Core paired saving | **45.85% ± 24.94%** |
| Bugfix token break-even | **13.12 tasks** |
| Boundary violations | 539 → 11 |
| Strict no-match edit-free | 6/6 → 2/6 |
| Route rejection | 0/6 |

### 시간

| 범위 | 변화 |
| --- | ---: |
| 전체 | 2.69% 빠름 |
| Bugfix | 0.04% 빠름 |
| Core bugfix | **19.99% 빠름** |
| Decoy-heavy | **51.73% 느림** |

### 해석

Enterprise 규모에서도 map은 core bugfix에 강한 효과가 있었다. 반면 유사 파일이 많은 decoy-heavy task와 unsupported request에서 안전성 문제가 선명해졌다. 이 실험이 no-match hardening 작업의 출발점이 됐다.

---

## 8. Experiment D2: Enterprise XLarge, XHigh E2E

### Authoring 및 결과

| 지표 | 값 |
| --- | ---: |
| XHigh map authoring tokens | 3,122,221 |
| Authoring seconds | 1,042.54 |
| Repair runs | 90 |
| 전체 누적 token 감소 | **25.11%** |
| Bugfix 누적 token 감소 | **44.45%** |
| Bugfix paired saving | **40.41% ± 24.61%** |
| Core paired saving | **44.57% ± 20.51%** |
| Bugfix token break-even | **21.31 tasks** |
| Decoy-heavy token 감소 | **34.69%** |
| Decoy-heavy boundary | 0 → 0 |
| Strict no-match edit-free | 5/6 → 0/6 |
| Route rejection | 0/6 |

### Category별 결과

| Category | 누적 token 변화 | Paired saving ± SD | 시간 변화 | Boundary |
| --- | ---: | ---: | ---: | ---: |
| Workflow | **52.91% 감소** | 52.59% ± 16.40% | 21.02% 빠름 | 0 → 0 |
| Cross-module | **50.18% 감소** | 45.59% ± 21.63% | 28.55% 느림 | 0 → 0 |
| Decoy-heavy | **34.69% 감소** | 26.52% ± 32.73% | 4.72% 빠름 | 0 → 0 |
| Local | **28.86% 감소** | 26.50% ± 16.42% | 느림 | 0 → 0 |
| No-match | **44.40% 증가** | -59.01% ± 93.65% | 16.71% 느림 | edits 1 → 37 |

### 해석

XHigh repair는 hard-task navigation과 decoy-heavy 안정성에서 가치가 있었다. 그러나 map authoring 비용이 Medium의 두 배를 넘었고 no-match 문제는 더 강한 model로도 해결되지 않았다. 문제는 model intelligence보다 router 계약에 있었다.

---

## 9. Experiment E: XHigh Map + Medium Repair Ablation

### 질문

XHigh로 비싼 map을 한 번 만든 뒤 일상 repair는 Medium agent가 수행하면 더 효율적인가?

### 조건

| 조건 | Map | Repair agent |
| --- | --- | --- |
| A | 없음 | Medium |
| B | Medium-authored | Medium |
| C | XHigh-authored | Medium |

### 결과

| Scope | No-map | Medium-map | XHigh-map | XHigh vs Medium |
| --- | ---: | ---: | ---: | ---: |
| 전체 tokens | 12,596,826 | 8,840,991 | 8,713,604 | 1.44% 감소 |
| Bugfix tokens | 11,219,322 | **6,677,545** | 6,794,487 | **1.75% 증가** |
| Core bugfix tokens | 7,995,985 | 3,772,157 | 3,768,332 | 0.10% 감소 |
| Decoy-heavy tokens | 3,223,337 | 2,905,388 | 3,026,155 | 4.16% 증가 |
| Boundary violations | 539 | **11** | **531** | 크게 악화 |
| Strict no-match edits | 0 | 15 | 12 | 모두 문제 |

한 XHigh-map + Medium run은 528개 파일을 변경했고 527개가 benchmark boundary 밖이었다.

### 해석

“처음에만 최고 effort로 map을 만들라”는 운영 권고는 지지되지 않았다. Map의 정보량과 복잡성이 Medium agent의 활용 능력과 자동으로 맞아떨어지지 않았다. 기본 운영은 Medium map + Medium repair, 어려운 task에서 repair agent만 XHigh로 승격하는 쪽이 더 합리적이었다.

---

## 10. Experiment F: 첫 번째 No-match 개선 Map 회귀

### 목적

Repository capability boundary와 no-match rejection을 추가한 버전이 false-positive route를 줄이는지 확인했다. 기존 no-map baseline과 old-map 결과를 재사용하고 새 generated-map condition만 실행했다.

### Realistic Large

| 지표 | Old-map | Updated-map |
| --- | ---: | ---: |
| Map authoring tokens | 1,748,486 | **2,346,214** |
| Bugfix route match | 24/24 | **12/24** |
| Bugfix token saving | 47.02% | **14.21%** |
| Bugfix time | 7.44% 빠름 | 9.43% 느림 |
| No-match route rejection | 0/3 | **3/3** |
| Bugfix break-even | 약 18.1 | **약 80.2 tasks** |

No-match는 고쳤지만 정상 bugfix 절반이 trusted route를 잃었다.

### Enterprise XLarge

| 지표 | Old-map | Updated-map |
| --- | ---: | ---: |
| Map authoring tokens | 1,527,492 | **1,972,223** |
| Bugfix token saving | 40.48% | **35.25%** |
| Core route match | 30/30 | **30/30** |
| Decoy route match | 9/9 | **0/9** |
| No-match route rejection | 0/6 | **6/6** |
| Boundary violations | 11 | **0** |
| Bugfix break-even | 13.12 | **19.45 tasks** |

Enterprise에서는 core recall을 유지하며 no-match route FP를 제거했지만, agent가 `read_only` context를 무시하고 파일을 생성한 사례가 확인됐다.

### 새로 발견한 runner bug

기존 `git diff --numstat`은 untracked new files를 보지 못했다. 따라서 iOS, Terraform 등의 새 파일 생성이 edit-free로 잘못 집계될 수 있었다. 이후 runner는 `git status --porcelain --untracked-files=all`과 JSONL `file_change`를 함께 기록하도록 수정됐다.

---

## 11. Experiment G: Updated-v2 회귀

### 목적

- tracked/untracked/JSONL 변경 감지
- decision / edit-policy 기록
- non-MATCH read-only prompt
- no-match 안전성
- positive-route recall 회복 여부

### Realistic Large

| 지표 | Updated-v2 |
| --- | ---: |
| Map authoring tokens | 1,891,349 |
| Corrected bugfix resolved | **17/24** |
| Bugfix route match | **9/24** |
| Bugfix token saving | 27.40% |
| Bugfix time | 5.84% 느림 |
| No-match resolved | **3/3** |
| No-match production changes | **0** |

### Enterprise XLarge

| 지표 | Updated-v2 |
| --- | ---: |
| Map authoring tokens | 2,679,094 |
| Corrected bugfix resolved | **25/39** |
| Core resolved | 22/30 |
| Bugfix route match | 21/39 |
| Bugfix token saving | 60.42% |
| No-match resolved | **6/6** |
| No-match production changes | **0** |

높은 token saving의 일부는 agent가 수정하지 않고 빠르게 실패한 run에서 왔기 때문에 성공률과 분리해 해석해야 했다.

### 새로 발견한 runner 문제

- `__pycache__`, `*.pyc`가 untracked edit로 잡혀 raw resolved를 오염시켰다.
- Markdown backtick이 붙은 `OUT_OF_SCOPE`, `read_only` 값을 normalize하지 않아 실제 sandbox가 workspace-write로 남았다.

### 해석

Updated-v2는 “길이 없을 때 멈춘다”는 목표에는 도달했지만, 정상 bugfix에도 너무 자주 no-route를 반환했다. 다음 개선은 threshold를 느슨하게 만드는 것이 아니라 `IN_SCOPE_NO_ROUTE`에 bounded discovery, area-level fallback, positive evidence를 제공하는 것이었다.

---

## 12. Experiment H: 최신 Synchronized Dual-Scale Medium E2E

이 실험은 최신 decision-aware Bunya-Jido를 대상으로 baseline과 mapped를 같은 시기에 다시 실행했다. 과거 baseline을 재사용하지 않았고, `context --json`, 실제 read-only sandbox, untracked 감지, runtime cache 제외를 적용했다.

### 구성

```text
Realistic:
9 tasks × 2 conditions × 3 reps = 54 runs

Enterprise:
15 tasks × 2 conditions × 3 reps = 90 runs

합계:
144 repair runs
```

### 한눈에 보는 결과

| Repository | SLOC | Python files | 시나리오 | Bugfix 해결 | Bugfix tokens | Bugfix time | Boundary | No-route |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Realistic Large | 28,708 | 1,432 | 8 + 1 no-route | 24/24 → 24/24 | 18.77% 감소 | 27.97% 감소 | 0 → 1 | 3/3 안전 종료 |
| Enterprise XLarge | 126,731 | 5,926 | 13 + 2 no-route | 39/39 → 39/39 | 22.78% 감소 | 12.52% 감소 | 10 → 6 | 6/6 안전 종료 |
| 합계 | 155,439 | 7,358 | 21 + 3 no-route | 63/63 → 63/63 | 21.62% 감소 | 17.04% 감소 | 10 → 7 | 9/9 안전 종료 |

### Routing decision

| Repository | Category | Decision | Edit policy | Sandbox | Runs |
| --- | --- | --- | --- | --- | --- |
| enterprise_xlarge | cross_module_bugfix | MATCH | workspace_write | workspace-write | 12 |
| enterprise_xlarge | decoy_heavy_bugfix | IN_SCOPE_NO_ROUTE | cautious | workspace-write | 9 |
| enterprise_xlarge | local_bugfix | MATCH | workspace_write | workspace-write | 6 |
| enterprise_xlarge | no_match | OUT_OF_SCOPE | read_only | read-only | 3 |
| enterprise_xlarge | no_match | UNCERTAIN | read_only | read-only | 3 |
| enterprise_xlarge | workflow_bugfix | MATCH | workspace_write | workspace-write | 12 |
| realistic_large | bugfix | MATCH | workspace_write | workspace-write | 24 |
| realistic_large | no_match | UNCERTAIN | read_only | read-only | 3 |

### Token·시간 상세

| Repository | Scope | Pairs | Resolved baseline→mapped | Tokens baseline→mapped | 누적 token 변화 | Time baseline→mapped | 누적 time 변화 | Boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| realistic_large | all | 27 | 24→27 | 4,209,841→3,005,556 | 28.61% 감소 | 1,906.67s→1,015.29s | 46.75% 감소 | 0→1 |
| realistic_large | bugfix | 24 | 24→24 | 3,636,555→2,953,976 | 18.77% 감소 | 1,377.69s→992.29s | 27.97% 감소 | 0→1 |
| realistic_large | core | 24 | 24→24 | 3,636,555→2,953,976 | 18.77% 감소 | 1,377.69s→992.29s | 27.97% 감소 | 0→1 |
| realistic_large | no_match | 3 | 0→3 | 573,286→51,580 | 91.00% 감소 | 528.98s→23.00s | 95.65% 감소 | 0→0 |
| enterprise_xlarge | all | 45 | 39→45 | 10,573,243→7,026,972 | 33.54% 감소 | 4,457.91s→2,957.92s | 33.65% 감소 | 10→6 |
| enterprise_xlarge | bugfix | 39 | 39→39 | 8,966,583→6,923,886 | 22.78% 감소 | 3,331.79s→2,914.50s | 12.52% 감소 | 10→6 |
| enterprise_xlarge | core | 30 | 30→30 | 6,052,151→4,815,951 | 20.43% 감소 | 1,522.08s→2,398.27s | -57.56% 감소 | 0→6 |
| enterprise_xlarge | decoy | 9 | 9→9 | 2,914,432→2,107,935 | 27.67% 감소 | 1,809.70s→516.23s | 71.47% 감소 | 10→0 |
| enterprise_xlarge | no_match | 6 | 0→6 | 1,606,660→103,086 | 93.58% 감소 | 1,126.12s→43.42s | 96.14% 감소 | 0→0 |

### Latest task-level 결과

| Task | Category | Decision | Resolved | Token 변화 | Time 변화 | Boundary |
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

### 해석

- 모든 정상 bugfix 63/63이 baseline과 mapped에서 해결됐다.
- Mapped bugfix는 합계 **2,725,276 tokens**, **21.62%**를 줄였다.
- Bugfix wall-clock은 합계 약 **802.7초**, **17.04%** 줄었다.
- Unsupported request 9개는 모두 read-only로 종료됐고 production edit가 0이었다.
- Enterprise decoy-heavy는 `IN_SCOPE_NO_ROUTE + cautious`로 9/9 해결, tokens 27.67%, time 71.47%, boundary 10→0을 기록했다.
- Broad route가 root cause보다 downstream compensation을 허용한 task가 남아 mapped boundary 7건을 만들었다.
- 현재 병목은 route recall이나 no-match safety가 아니라 root-cause specificity다.

---

## 13. Map authoring 경제성의 변화

| Phase | Realistic tokens | Enterprise tokens | 해석 |
| --- | ---: | ---: | --- |
| 최초 Medium | 1,748,486 | 1,527,492 | 초기 map |
| XHigh | 2,891,143 | 3,122,221 | 비용 증가, selective repair 승격이 유리 |
| Updated no-match | 2,346,214 | 1,972,223 | negative boundary 추가 |
| Updated-v2 | 1,891,349 | 2,679,094 | decision-aware 실험 |
| 최신 synchronized | **1,581,382** | **1,879,599** | 현재 release candidate |

최신 bugfix-only break-even:

| Repository | Authoring tokens | 평균 절감/task | Token break-even | Authoring seconds | Time break-even |
| --- | ---: | ---: | ---: | ---: | ---: |
| Realistic | 1,581,382 | 28,441 | **55.6 tasks** | 623.5s | 38.8 tasks |
| Enterprise | 1,879,599 | 52,377 | **35.9 tasks** | 1,679.6s | 157.0 tasks |

작은 repo에서는 map 비용을 회수하기 어렵고, 규모와 반복 task 수가 커질수록 경제성이 좋아졌다. 다만 LOC만으로 authoring 비용을 예측할 수는 없었다.

---

## 14. 전체 자원 사용량

기존 XHigh 후속 실험까지 감사 가능한 누적 raw tokens는 127,897,183이었다. 이후 두 차례 routing regression과 최신 synchronized benchmark를 합산하면:

| 구간 | Raw tokens |
| --- | ---: |
| Curated~XHigh 및 ablation 누적 | 127,897,183 |
| Updated-map authoring + repair | 18,297,893 |
| Updated-v2 authoring + repair | 12,905,626 |
| 최신 dual-scale authoring + repair | 28,276,593 |
| **감사 가능한 합계** | **187,377,295** |

Smoke, workspace probe, 폐기 run, 반복 설치 확인은 포함하지 않았다. 실제 사용량은 이보다 높다.

---

## 15. 프로그램 전체에서 얻은 결론

### 15.1 Route는 실제로 탐색 비용을 줄인다

Curated route와 native map 모두에서 신호가 반복됐다. 최신 synchronized 실험에서는 해결률을 유지한 채 bugfix tokens를 21.62% 줄였다.

### 15.2 작은 repository에는 비용이 과하다

52~2,691 SLOC pilot에서는 bugfix utility는 있었지만 authoring 비용 회수가 비현실적이었다. Bunya-Jido의 적합 대상은 workflow와 책임 영역이 충분히 복잡한 repository다.

### 15.3 더 강한 model로 map을 만드는 것이 항상 낫지 않다

XHigh map은 Medium agent에 추가 경제성을 주지 않았고 일부 task에서는 오히려 광범위한 수정을 유도했다. 강한 effort는 map authoring 기본값보다 hard repair의 선택적 escalation에 더 적합했다.

### 15.4 No-match는 성능 기능이 아니라 안전 계약이다

초기 버전은 unsupported 요청에도 route를 반환했다. Capability boundary, four-way decision, read-only sandbox, untracked grading을 거치며 최신 실험에서는 9/9 안전 종료에 도달했다.

### 15.5 Token과 time은 함께 보되 같은 것으로 취급하지 않는다

Token saving은 비교적 안정적으로 map의 탐색 효율을 반영했다. Wall-clock은 극단적 backend/tool latency outlier가 컸다. 공개 문구는 token 결과를 중심으로 하고 time은 보조 지표로 제시하는 편이 안전하다.

### 15.6 다음 문제는 root-cause specificity다

최신 map은 정상 task를 찾고 unsupported task를 거절한다. 남은 문제는 일부 route가 upstream root cause보다 downstream compensation을 허용한다는 점이다. 다음 개선은 route recall이 아니라 owner precedence, invariant, preferred repair locus를 표현하는 쪽이어야 한다.

---

## 16. 한계

1. 모든 repository는 synthetic이다.
2. GPT-5.5와 Codex CLI에 집중돼 다른 agent/model 일반화는 검증하지 않았다.
3. 최신 primary result는 Medium effort만 사용했다.
4. No-route benchmark는 명확한 mobile/infrastructure 요청으로 구성돼 더 미묘한 scope ambiguity를 충분히 대표하지 않는다.
5. Hidden tests는 기능 정확성을 확인하지만 patch maintainability와 설계 품질 전체를 평가하지 않는다.
6. Boundary violation은 benchmark gold file 기준이므로, 다른 정당한 구현을 일부 과잉 위반으로 기록할 수 있다.
7. Authoring maintenance cost와 repository evolution 이후 refresh cost는 break-even에 포함하지 않았다.
8. Raw tokens는 실제 API 청구 비용과 동일하지 않다. Cached input 가격과 subscription economics가 다르다.
9. Wall-clock은 backend latency와 로컬 Windows I/O의 영향을 받는다.

---

## 17. 현재 release 판단

현재 버전은 public alpha에 적합하다.

방어 가능한 표현:

> 두 개의 synthetic large-repository benchmark에서 최신 Bunya-Jido map은 GPT-5.5 Medium의 bugfix 해결률 100%를 유지하면서 repair token을 18.8%와 22.8% 줄였다. Unsupported request 9개는 모두 read-only로 종료됐고 production edit는 없었다.

피해야 할 표현:

```text
모든 repository에서 20% 이상 절감
production-ready safety 보장
모든 coding agent에서 동일한 효과
wall-clock을 항상 단축
XHigh map이 더 우수
```

---

## Appendix A. 최신 시나리오 목록

### Realistic Large

| Task | Type | 요청 | 직접 결함 위치 | 최종 decision |
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

### Enterprise XLarge

| Task | Type | 요청 | 직접 결함 위치 | 최종 decision |
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

---

## Appendix B. 주요 기록 artifact

- `native_bunya_jido_144_run_corrected_analysis.md`
- `realistic_large_platform_native_repair_analysis.md`
- `enterprise_xlarge_platform_medium_native_repair_analysis.md`
- `enterprise_xlarge_xhigh_followup_analysis.md`
- `BUNYA_JIDO_UPDATED_MAP_REVALIDATION_AND_IMPROVEMENT_REPORT.md`
- `BUNYA_JIDO_UPDATED_V2_RESULTS_AND_NEXT_FIXES.md`
- `BUNYA_JIDO_DUAL_SCALE_MEDIUM_E2E_FINAL_ANALYSIS_KO.md`
- `bunya_jido_dual_scale_run_level.csv`
- `bunya_jido_dual_scale_task_summary.csv`
- `bunya_jido_dual_scale_scope_summary.csv`
