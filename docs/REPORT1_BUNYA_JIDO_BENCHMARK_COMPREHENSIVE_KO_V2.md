# Bunya-Jido Semantic Map Benchmark 종합 보고서

## 0. 문서 목적

이 문서는 Bunya-Jido의 semantic map이 coding agent의 repository-scale code repair 작업에 미치는 영향을 검증하기 위해 수행한 전체 벤치마크를 정리한다.

실험은 작은 합성 repository에서 시작해 126.7K SLOC enterprise-scale synthetic platform까지 확장했다. 단순한 토큰 절감뿐 아니라 다음 질문을 함께 추적했다.

1. 좋은 semantic route가 주어지면 coding agent의 탐색 비용이 줄어드는가?
2. Bunya-Jido가 clean repository에서 실제로 생성한 native map도 같은 효과를 내는가?
3. map authoring 비용을 포함하면 몇 회의 유사 작업 뒤에 초기 비용을 회수하는가?
4. repository 규모가 커질수록 map의 효용은 어떻게 달라지는가?
5. `gpt-5.5-medium`과 `gpt-5.5-xhigh` 중 어떤 operating point가 경제적인가?
6. XHigh로 비싼 map을 한 번 만든 뒤 Medium agent가 재사용하는 전략은 유효한가?
7. semantic router는 지원되지 않는 요청에 대해 침묵할 줄 아는가?

이 문서의 결과는 **synthetic repository benchmark**에 기반한다. 실제 공개 open-source issue replay와 production repository 검증은 아직 수행하지 않았다.

---

## 1. Executive summary

### 1.1 전체 결론

실험 결과는 다음 운영 전략을 지지한다.

```text
기본 운영:
Medium map authoring
+
Medium repair agent

workflow-heavy / decoy-heavy / 탐색 위험이 높은 작업:
기존 map을 유지한 채
repair agent만 XHigh로 선택적 승격

unsupported request:
router 단계에서 No matching trusted route로 차단
```

다음 전략은 현재 데이터에서 지지되지 않았다.

```text
처음부터 XHigh로 비싼 map을 만들고
이후 Medium agent가 계속 활용
```

XHigh-authored map을 Medium agent에게 제공했을 때 core bugfix 토큰 효율은 Medium-authored map과 사실상 동률이었고, 일부 decoy-heavy run에서는 안전성이 악화됐다.

### 1.2 주요 실험 요약

| 단계 | 성격 | Repository 규모 | Repair runs | 핵심 결과 |
| --- | --- | --- | ---: | --- |
| Curated route utility | 사전 작성 route의 메커니즘 검증 | 초기 synthetic repo 3종 | 108 | 누적 토큰 **25.3% 감소** |
| Native generated-map pilot | Bunya-Jido native map 검증 | micro-to-small synthetic repo 4종 | 144 | bugfix paired saving **15.86% ± 21.29%** |
| Realistic-large Medium E2E | 현실적인 규모의 native E2E | 28.7K SLOC | 54 | bugfix paired saving **43.56% ± 17.84%** |
| Realistic-large XHigh E2E | 동일 repo의 XHigh replication | 28.7K SLOC | 54 | bugfix paired saving **36.53% ± 22.98%** |
| Enterprise XLarge Medium E2E | enterprise-scale native E2E | 126.7K SLOC | 90 | bugfix 누적 토큰 **40.48% 감소** |
| Enterprise XLarge XHigh E2E | enterprise-scale XHigh replication | 126.7K SLOC | 90 | bugfix 누적 토큰 **44.45% 감소** |
| Enterprise map-quality ablation | Medium agent에 map 품질만 변경 | 126.7K SLOC | 45 추가 | XHigh map은 Medium map 대비 bugfix 토큰 **1.75% 증가** |

### 1.3 Wall-clock 핵심 관찰

| 실험 | 시간 결과 |
| --- | --- |
| Realistic-large Medium E2E | 전체 누적 시간 **22.07% 단축** |
| Enterprise Medium E2E | Core bugfix **19.99% 단축**, decoy-heavy outlier가 전체 이득 상쇄 |
| Enterprise XHigh E2E | 전체 누적 시간 **9.09% 증가**, 대신 decoy-heavy 안정성 개선 |

토큰 절감은 wall-clock 단축을 자동으로 보장하지 않는다.

### 1.4 감사 가능한 누적 사용량

정상 완료되어 raw log로 감사 가능한 본 실험 누적량은 다음과 같다.

```text
127,897,183 raw tokens
```

Dry run, smoke test, workspace probe, 폐기 run을 포함한 실제 체감 총량은 대략 다음 범위로 추정된다.

```text
130M–145M raw tokens
```

---

## 2. 실험 원칙

### 2.1 Clean-first, freeze-first

Native map 실험은 항상 다음 순서로 수행했다.

```text
clean repository
  ↓
Bunya-Jido prepare
  ↓
Codex native map authoring
  ↓
validation
  ↓
map freeze + SHA-256
  ↓
그 뒤에만 defect injection
  ↓
baseline / generated-map repair
```

이 순서를 지켜야 map이 정답을 미리 본다는 오염을 막을 수 있다.

### 2.2 Hidden test 격리

Hidden test는 Codex workspace에 포함하지 않았다.

```text
Codex repair 종료
  ↓
temporary grading clone 생성
  ↓
hidden test 주입
  ↓
public test + hidden test 실행
```

### 2.3 Pairing

각 paired comparison은 다음 조건이 동일한 baseline과 generated-map run을 묶는다.

```text
same repository
same task
same model effort
same repetition index
```

### 2.4 Strict no-match

No-match는 “존재하지 않는 버그를 억지로 고치게 하는 테스트”가 아니다.

현재 repository의 책임 범위를 벗어난 요청에 semantic router가 route를 붙이지 않고 거절할 수 있는지 본다.

```text
예:
Python control-plane repository에
iOS app 또는 Terraform Kubernetes 환경을 추가하라고 요청

기대:
No matching trusted route
```

Production file이 하나라도 수정되면 strict no-match 실패로 기록했다.

---

## 3. Benchmark harness의 진화

초기에는 Codex extension과 OpenTelemetry 기반 수동 측정을 시도했지만, 정량 benchmark로 쓰기 어려운 문제가 드러났다.

| 문제 | 관찰 | 최종 조치 |
| --- | --- | --- |
| 수동 시간 측정 왜곡 | 창을 열어 둔 시간까지 포함 | Codex subprocess elapsed time 사용 |
| OTel conversation ambiguity | 여러 Codex thread telemetry가 섞임 | `codex exec --json` 직접 측정 |
| usage event 누락 | 토큰 0 run이 정상처럼 집계 | `turn.completed.usage` 필수화 |
| Windows `cp949` decode 오류 | JSONL UTF-8을 기본 문자셋으로 읽음 | bytes capture 후 UTF-8 디코딩 |
| sandbox 정책 차이 | workspace write 실패 | `--windows-sandbox unelevated` |
| CLI option mismatch | `--ask-for-approval` 미지원 | config `approval_policy="never"` |
| test 수정 | agent가 시험지를 수정 | protected-file violation 처리 |
| 긴 Git 경로 | `.git\objects`에서 `Filename too long` | 짧은 `%TEMP%` workspace와 `core.longpaths=true` |
| grading clone 복사 비용 | 대형 repo의 `.git` 복사 병목 | grading clone에서 `.git` 제외 |
| reset 삭제 병목 | 수십 개 대형 workspace 삭제 | 결과만 지우는 fast reset, workspace purge 분리 |
| pair 중복 계산 | 초기 analyzer가 pair를 두 번 집계 | raw JSON 기준 corrected analyzer |

이 과정은 단순한 설치 troubleshooting이 아니라, benchmark의 신뢰도를 높이는 측정 장비 제작 과정이었다.

---

## 4. Experiment A: Curated Semantic Route Utility

### 4.1 목적

사전 작성된 bounded semantic route가 있을 때 agent 탐색 비용이 줄어드는지 확인하는 upper-bound mechanism test다.

이 실험은 Bunya-Jido native map 품질을 측정하지 않는다.

### 4.2 구성과 결과

| 항목 | 값 |
| --- | ---: |
| Synthetic repositories | 3 |
| Tasks | 18 |
| Conditions | baseline, curated mapped |
| Repetitions | 3 |
| Repair runs | 108 |
| Model effort | `medium` |

| 지표 | Baseline | Curated mapped | 변화 |
| --- | ---: | ---: | ---: |
| 해결 성공 | 53 / 54 | 54 / 54 | +1 |
| 누적 총 토큰 | 7,164,603 | 5,355,288 | **-25.3%** |
| 실행당 평균 총 토큰 | 132,678 ± 37,561 | 99,172 ± 37,961 | **-25.3%** |
| Bugfix 누적 토큰 절감 |  |  | **29.8%** |

### 4.3 해석

좋은 route가 이미 존재하면 agent의 repository exploration 비용을 줄일 수 있다는 메커니즘은 확인됐다. 그러나 curated route는 제품의 native map authoring 비용을 포함하지 않는다.

---

## 5. Experiment B: Native Generated-Map Pilot

### 5.1 목적

Bunya-Jido가 clean repository에서 실제 생성한 map의 효용을 검증한다.

### 5.2 Repository 규모

| Historical repo ID | Approx. SLOC | src Python files | 현실적 scale band |
| --- | ---: | ---: | --- |
| `small_cli` | 52 | 11 | micro |
| `medium_service` | 123 | 32 | micro |
| `large_workflow` | 256 | 74 | micro |
| `xlarge_control_plane` | 2,691 | 248 | small |

### 5.3 Native map authoring 비용

| Repo | Tokens | Seconds |
| --- | ---: | ---: |
| `small_cli` | 780,751 | 409.03 |
| `medium_service` | 1,460,829 | 541.39 |
| `large_workflow` | 914,535 | 449.02 |
| `xlarge_control_plane` | 1,929,983 | 592.62 |
| **합계** | **5,086,098** | **1,992.06** |

### 5.4 Repair 결과

```text
24 tasks × 2 conditions × 3 repetitions = 144 runs
72 paired comparisons
```

| 범위 | Pairs | Token saving % ± SD | Time saving % ± SD |
| --- | ---: | ---: | ---: |
| 전체 | 72 | **4.81% ± 47.61%** | -4.67% ± 59.58% |
| Bugfix | 60 | **15.86% ± 21.29%** | 4.18% ± 39.47% |
| No-match | 12 | **-50.45% ± 90.58%** | -48.92% ± 109.50% |

### 5.5 교훈

- 작은 repo에서는 map authoring 비용을 회수하기 어렵다.
- ordinary bugfix에서는 native generated map이 평균적으로 이득이다.
- no-match는 별도 품질 지표로 분리해야 한다.
- 토큰 효율과 wall-clock 효율은 같은 지표가 아니다.

---

## 6. Experiment C: `realistic_large_platform`

### 6.1 Repository

| 항목 | 값 |
| --- | ---: |
| Approximate SLOC | 28,708 |
| src Python files | 1,432 |
| Responsibility areas | 27 |
| Tasks | 9 |
| Conditions | baseline, generated-map |
| Repetitions | 3 |

### 6.2 Medium E2E

| 지표 | 값 |
| --- | ---: |
| Map authoring tokens | 1,748,486 |
| Map authoring seconds | 648.22 |
| Repair runs | 54 |
| 해결 성공 | 54 / 54 |
| 전체 누적 토큰 절감률 | **42.23%** |
| 전체 paired 절감률 | **39.52% ± 22.30%** |
| Bugfix paired 절감률 | **43.56% ± 17.84%** |
| Bugfix 초기 손익분기점 | **18.06 tasks** |
| Boundary violations | 0 |
| Protected-file violations | 0 |

### 6.3 XHigh E2E

| 지표 | 값 |
| --- | ---: |
| Map authoring tokens | 2,891,143 |
| Map authoring seconds | 1,069.78 |
| Repair runs | 54 |
| 해결 성공 | 54 / 54 |
| 전체 누적 토큰 절감률 | **37.40%** |
| Bugfix paired 절감률 | **36.53% ± 22.98%** |
| Bugfix 초기 손익분기점 | **28.36 tasks** |
| Boundary violations | 0 |
| Protected-file violations | 0 |

### 6.4 해석

28.7K SLOC에서는 Medium이 더 경제적이었다. XHigh도 토큰을 줄였지만 map authoring 비용이 증가했고 상대 절감률은 낮았다.

---

## 7. Experiment D: `enterprise_xlarge_platform`

### 7.1 Repository

| 항목 | 값 |
| --- | ---: |
| Approximate SLOC | 126,731 |
| src Python files | 5,926 |
| Responsibility areas | 48 |
| Tasks | 15 |
| Conditions | baseline, generated-map |
| Repetitions | 3 |

### 7.2 Medium E2E

| 지표 | 값 |
| --- | ---: |
| Map authoring tokens | 1,527,492 |
| Map authoring seconds | 759.46 |
| Repair runs | 90 |
| 전체 누적 토큰 절감률 | **29.82%** |
| Bugfix 누적 토큰 절감률 | **40.48%** |
| Bugfix paired 절감률 | **31.24% ± 53.39%** |
| Core bugfix paired 절감률 | **45.85% ± 24.94%** |
| Bugfix 초기 손익분기점 | **13.12 tasks** |
| Boundary violations | 539 → 11 |
| Strict no-match edit-free | 6 / 6 → 2 / 6 |
| Route rejection score | **0 / 6** |

### 7.3 XHigh E2E

| 지표 | 값 |
| --- | ---: |
| Map authoring tokens | 3,122,221 |
| Map authoring seconds | 1,042.54 |
| Repair runs | 90 |
| 전체 누적 토큰 절감률 | **25.11%** |
| Bugfix 누적 토큰 절감률 | **44.45%** |
| Bugfix paired 절감률 | **40.41% ± 24.61%** |
| Core bugfix paired 절감률 | **44.57% ± 20.51%** |
| Bugfix 초기 손익분기점 | **21.31 tasks** |
| Decoy-heavy boundary violations | **0 → 0** |
| Strict no-match edit-free | 5 / 6 → 0 / 6 |
| Route rejection score | **0 / 6** |

### 7.4 Medium map과 XHigh map authoring 비용

| 지표 | Medium map | XHigh map | XHigh 변화 |
| --- | ---: | ---: | ---: |
| Total tokens | 1,527,492 | 3,122,221 | +104.57% |
| Authoring seconds | 759.46 | 1,042.54 | +37.27% |

### 7.5 해석

- Medium은 초기 비용과 손익분기점에서 우세하다.
- XHigh는 decoy-heavy task의 탐색 안정성에서 강하다.
- no-match router 문제는 XHigh에서도 해결되지 않았다.
- 더 강한 repair agent가 hard task에 도움을 줄 수 있지만, 더 비싼 map이 항상 더 좋은 것은 아니다.

---

## 8. Experiment E: Map-quality ablation

### 8.1 질문

```text
초기에만 XHigh로 좋은 map을 만들고,
일상 수리는 Medium agent가 수행하면 더 효율적인가?
```

### 8.2 세 조건

| 조건 | Map | Repair agent |
| --- | --- | --- |
| A | 없음 | Medium |
| B | Medium-authored map | Medium |
| C | XHigh-authored map | Medium |

### 8.3 결과

| Scope | No-map tokens | Medium-map tokens | XHigh-map tokens | XHigh map vs Medium map |
| --- | ---: | ---: | ---: | ---: |
| 전체 | 12,596,826 | 8,840,991 | 8,713,604 | 1.44% 감소 |
| Bugfix | 11,219,322 | **6,677,545** | 6,794,487 | **1.75% 증가** |
| Core bugfix | 7,995,985 | 3,772,157 | 3,768,332 | 0.10% 감소 |
| Decoy-heavy | 3,223,337 | 2,905,388 | 3,026,155 | 4.16% 증가 |

| 조건 | Boundary violations | Strict no-match edits |
| --- | ---: | ---: |
| No-map + Medium | 539 | 0 |
| Medium-map + Medium | **11** | 15 |
| XHigh-map + Medium | **531** | 12 |

### 8.4 해석

XHigh-authored map은 Medium agent의 일상 bugfix 경제성을 개선하지 않았다. Core bugfix에서는 사실상 동률이었고, 한 decoy-heavy run에서는 527개의 boundary violation이 발생했다.

현재 데이터는 다음 권장안을 지지하지 않는다.

```text
XHigh map authoring + Medium repair agent
```

---

## 9. Cross-experiment 해석

### 9.1 Repo 규모와 semantic map 가치

| 규모 | 관찰 |
| --- | --- |
| Micro-to-small | native map은 평균적으로 이득이지만 authoring 비용 회수가 어려움 |
| 28.7K SLOC | 약 40%대 bugfix 절감, 안정적 품질 |
| 126.7K SLOC | core bugfix 절감 유지, decoy-heavy와 no-match 품질 문제가 선명해짐 |

Repository가 커지면 semantic navigation의 가치는 커질 수 있다. 하지만 큰 repo에서는 route precision과 rejection 능력도 더 중요해진다.

### 9.2 Medium과 XHigh

| 질문 | 결론 |
| --- | --- |
| 기본 operating point는? | **Medium** |
| XHigh는 쓸모가 없는가? | 아니다. hard task 안정성에 가치가 있음 |
| XHigh map을 기본으로 만들 것인가? | 현재 데이터에서는 아니다 |
| 언제 XHigh를 사용할 것인가? | workflow-heavy, decoy-heavy, 위험한 탐색 작업 |

### 9.3 No-match rejection

Map이 빠른 길찾기를 제공하는 것만으로는 충분하지 않다.

```text
좋은 router:
길을 안내한다
+
길이 없을 때 거절한다
```

Enterprise-scale 실험에서는 unsupported 요청에도 trusted route가 매치됐다. 이는 다음 개발 우선순위를 제시한다.

1. 책임 경계 검사
2. matcher confidence threshold
3. `No matching trusted route`
4. no-match 회귀 테스트

---

## 10. 경제성 요약

| Repository / Effort | Map authoring tokens | Bugfix initial break-even |
| --- | ---: | ---: |
| Realistic-large Medium | 1,748,486 | 18.06 tasks |
| Realistic-large XHigh | 2,891,143 | 28.36 tasks |
| Enterprise XLarge Medium | **1,527,492** | **13.12 tasks** |
| Enterprise XLarge XHigh | 3,122,221 | 21.31 tasks |

Map authoring 비용은 LOC에 단순 비례하지 않았다. Enterprise repo는 더 컸지만 Medium authoring tokens는 realistic-large보다 오히려 작았다. 구조의 규칙성, 탐색 경로, authoring agent의 행동이 비용에 영향을 준다.

---


## 11. Wall-clock 시간 분석

토큰 절감과 wall-clock 시간 절감은 분리해서 읽어야 한다.

Semantic map은 반복적인 repository exploration과 context ingestion을 줄인다. 그러나 실제 실행 시간에는 model reasoning, shell command 수, test 실행, 파일 복사, 비결정적인 agent 행동이 함께 영향을 준다.

```text
token efficiency
≠
wall-clock latency
```

### 11.1 Native generated-map pilot

| 범위 | Baseline 누적 시간 | Generated-map 누적 시간 | 절약 시간 | 누적 시간 변화 | Paired 시간 절감률 평균 ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 전체 72 pairs | 3,969.26초 | 4,296.10초 | **-326.84초** | **8.23% 느려짐** | -4.67% ± 59.58% |
| Bugfix 60 pairs | 2,649.77초 | 2,408.38초 | **241.39초** | **9.11% 단축** | 4.18% ± 39.47% |
| No-match 12 pairs | 1,319.49초 | 1,887.72초 | **-568.23초** | **43.06% 느려짐** | -48.92% ± 109.50% |

Pilot에서는 ordinary bugfix 시간이 줄었지만, no-match outlier가 전체 시간을 끌어올렸다.

### 11.2 `realistic_large_platform`

#### Medium E2E

| 범위 | Baseline 누적 시간 | Generated-map 누적 시간 | 절약 시간 | 누적 시간 변화 | Paired 시간 절감률 평균 ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 전체 27 pairs | 1,792.49초 | 1,396.86초 | **395.63초** | **22.07% 단축** | 7.50% ± 41.24% |
| Bugfix 24 pairs | 1,060.75초 | 981.88초 | **78.87초** | **7.44% 단축** | 4.63% ± 41.81% |

#### XHigh E2E

| 범위 | Baseline 누적 시간 | Generated-map 누적 시간 | 절약 시간 | 누적 시간 변화 | Paired 시간 절감률 평균 ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 전체 27 pairs | 3,056.01초 | 2,912.50초 | **143.51초** | **4.70% 단축** | -9.77% ± 29.65% |
| Bugfix 24 pairs | 1,536.47초 | 1,680.04초 | **-143.57초** | **9.34% 느려짐** | -13.30% ± 29.44% |

XHigh에서는 전체 누적 시간은 소폭 줄었지만 ordinary bugfix만 보면 오히려 느려졌다. No-match task의 상대적으로 큰 시간 감소가 전체 수치를 뒤집었다.

### 11.3 `enterprise_xlarge_platform`

#### Medium E2E

| 범위 | Baseline 누적 시간 | Generated-map 누적 시간 | 절약 시간 | 누적 시간 변화 | Paired 시간 절감률 평균 ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 전체 45 pairs | 3,697.31초 | 3,597.81초 | **99.50초** | **2.69% 단축** | -5.57% ± 102.21% |
| Bugfix 39 pairs | 2,466.19초 | 2,465.11초 | **1.08초** | **0.04% 단축** | -7.53% ± 109.75% |
| Core bugfix 30 pairs | 1,780.28초 | 1,424.40초 | **355.88초** | **19.99% 단축** | category mix 참고 |
| Decoy-heavy 9 pairs | 685.92초 | 1,040.72초 | **-354.80초** | **51.73% 느려짐** | -84.93% ± 213.19% |

Enterprise Medium의 core bugfix에서는 의미 있는 시간 절감이 있었다. 그러나 decoy-heavy run의 폭주가 이 효과를 거의 상쇄했다.

#### XHigh E2E

| 범위 | Baseline 누적 시간 | Generated-map 누적 시간 | 절약 시간 | 누적 시간 변화 | Paired 시간 절감률 평균 ± SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 전체 45 pairs | 6,004.10초 | 6,549.97초 | **-545.87초** | **9.09% 느려짐** | -6.57% ± 64.66% |
| Bugfix 39 pairs | 3,162.72초 | 3,233.79초 | **-71.07초** | **2.25% 느려짐** | -4.88% ± 68.02% |
| Workflow bugfix 12 pairs | 992.50초 | 783.86초 | **208.64초** | **21.02% 단축** | 19.76% ± 20.20% |
| Decoy-heavy 9 pairs | 826.20초 | 787.19초 | **39.01초** | **4.72% 단축** | 1.78% ± 17.94% |
| Cross-module bugfix 12 pairs | 959.22초 | 1,233.04초 | **-273.83초** | **28.55% 느려짐** | -30.40% ± 117.24% |
| No-match 6 pairs | 2,841.37초 | 3,316.17초 | **-474.80초** | **16.71% 느려짐** | -17.54% ± 38.20% |

Enterprise XHigh는 decoy-heavy 안정성을 개선했지만 전체 latency를 줄이지는 못했다. 토큰 절감과 안전성 개선이 wall-clock 단축으로 자동 연결되지는 않았다.

### 11.4 XHigh map + Medium repair ablation 시간

| 범위 | No-map + Medium | Medium-map + Medium | XHigh-map + Medium | XHigh map vs Medium map |
| --- | ---: | ---: | ---: | ---: |
| 전체 45 runs | 3,697.31초 | 3,597.81초 | 3,621.35초 | **0.65% 느림** |
| Bugfix 39 runs | 2,466.19초 | 2,465.11초 | **2,136.61초** | **13.33% 빠름** |
| Core bugfix 30 runs | 1,780.28초 | **1,424.40초** | 1,459.69초 | 2.48% 느림 |
| Decoy-heavy 9 runs | 685.92초 | 1,040.72초 | **676.92초** | 34.96% 빠름 |
| No-match 6 runs | 1,231.11초 | **1,132.70초** | 1,484.74초 | 31.08% 느림 |

이 ablation은 interleaved replication이 아니다. 따라서 시간 차이는 1차 관찰로만 해석해야 한다. 특히 decoy-heavy run의 큰 분산이 전체 수치를 흔든다.

### 11.5 시간 기준 결론

1. **토큰 절감은 일관된 핵심 신호**다.
2. **시간 절감은 task mix와 outlier에 민감**하다.
3. Medium map은 `realistic_large_platform`에서 전체 wall-clock을 22.07% 줄였다.
4. Enterprise Medium은 core bugfix에서 19.99% 빨라졌지만 decoy-heavy 폭주가 전체 개선을 상쇄했다.
5. Enterprise XHigh는 decoy-heavy 안정성을 높였지만 전체 wall-clock은 9.09% 악화됐다.
6. 따라서 제품 문구는 “더 빠르다”보다 “탐색 토큰과 context ingestion을 줄인다”를 중심으로 써야 한다.

### 11.6 시간 기준 손익분기점에 대한 주의

Map authoring 시간까지 포함한 latency break-even은 token break-even보다 훨씬 불안정하다.

| 실험 | Map authoring 시간 | Bugfix당 평균 절약 시간 | 시간 기준 초기 회수점 |
| --- | ---: | ---: | ---: |
| `realistic_large_platform` Medium | 648.22초 | 3.29초 | 약 **197 tasks** |
| `realistic_large_platform` XHigh | 1,069.78초 | 음수 | 회수 불가 |
| `enterprise_xlarge_platform` Medium | 759.46초 | 0.03초 | 사실상 불안정 |
| `enterprise_xlarge_platform` XHigh | 1,042.54초 | 음수 | 회수 불가 |

Enterprise Medium의 core bugfix만 별도로 보면 평균 약 11.86초를 절약해 약 64개 task 뒤 authoring 시간을 회수한다. 그러나 전체 bugfix mix에서는 decoy-heavy outlier가 이득을 지웠다.

시간 기준 경제성은 task 분포와 실행 환경에 크게 좌우되므로, 공개 문구에서는 token break-even과 분리해야 한다.


## 12. 현재까지 방어 가능한 공개 문구

> Synthetic benchmarks suggest that Bunya-Jido semantic maps can materially reduce repository-scale code repair token usage. On a 126.7K-SLOC synthetic Python platform, medium-authored maps reduced cumulative medium-effort bugfix tokens by 40.48%, with an initial authoring break-even of approximately 13 similar bugfix tasks excluding maintenance. XHigh repair agents improved decoy-heavy stability, but XHigh-authored maps did not improve medium-agent economics. Unsupported-request routing remains the highest-priority hardening area.

---

## 13. 아직 주장하면 안 되는 것

- 실제 상용 repository에서도 동일한 절감률이 재현된다.
- 모든 task 유형에서 map이 이득이다.
- wall-clock 시간이 항상 줄어든다.
- XHigh map이 항상 더 좋다.
- no-match router가 production-ready다.
- raw token break-even이 금액 break-even과 같다.
- synthetic benchmark만으로 산업 일반화가 증명됐다.

---

## 14. 다음 우선순위

1. no-match route rejection hardening
2. responsibility-boundary pre-check
3. decoy-heavy route에 allowed / forbidden boundary 표현
4. 구조 변경 이후 map maintenance 비용 측정
5. 실제 공개 open-source issue replay
6. 필요하면 interleaved map-quality replication

---

## Appendix A. 감사 가능한 raw token 사용량

| 단계 | Tokens |
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
| **합계** | **127,897,183** |

---

## Appendix B. 주요 source artifacts

- `curated_semantic_route_utility_benchmark_detailed_report_v2.md`
- `native_bunya_jido_144_run_corrected_analysis.md`
- `realistic_large_platform_native_repair_analysis.md`
- `realistic_large_platform_xhigh_native_repair_analysis.md`
- `enterprise_xlarge_platform_medium_native_repair_analysis.md`
- `enterprise_xlarge_xhigh_followup_analysis.md`
