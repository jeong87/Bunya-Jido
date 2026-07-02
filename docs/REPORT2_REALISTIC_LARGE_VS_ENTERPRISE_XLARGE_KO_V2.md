# Bunya-Jido 대형 Repository E2E 비교 보고서
## `realistic_large_platform` vs `enterprise_xlarge_platform`

## 0. 문서 범위

이 문서는 두 개의 대형 synthetic Python repository에서 수행한 Bunya-Jido native end-to-end benchmark만 비교한다.

포함하는 실험:

```text
realistic_large_platform:
Medium-authored map + Medium repair
XHigh-authored map + XHigh repair

enterprise_xlarge_platform:
Medium-authored map + Medium repair
XHigh-authored map + XHigh repair
```

의도적으로 제외한 실험:

```text
XHigh-authored map + Medium repair ablation
```

따라서 이 문서는 map-quality ablation이 아니라, repository 규모와 repair effort에 따른 E2E 비교 보고서다.

---

## 1. Executive summary

두 repository 모두 native map을 clean repo에서 먼저 authoring하고 freeze한 뒤, defect를 주입했다.

핵심 결과는 다음과 같다.

1. `realistic_large_platform`에서는 **Medium E2E가 경제적으로 우세**했다.
2. `enterprise_xlarge_platform`에서도 **기본 경제성은 Medium E2E가 우세**했다.
3. Enterprise 규모에서는 XHigh가 decoy-heavy task 안정성을 뚜렷하게 개선했다.
4. Repository 규모가 커져도 ordinary bugfix 토큰 절감 효과는 유지됐다.
5. 가장 큰 미해결 문제는 no-match route rejection이다.

시간 결과도 함께 읽어야 한다.

```text
Realistic-large Medium:
전체 누적 시간 22.07% 단축

Enterprise Medium:
Core bugfix 19.99% 단축
하지만 decoy-heavy outlier가 전체 개선을 상쇄

Enterprise XHigh:
전체 누적 시간 9.09% 증가
하지만 decoy-heavy boundary safety 개선
```

권장 운영 전략:

```text
기본:
Medium map authoring + Medium repair

복잡한 workflow-heavy / decoy-heavy task:
repair agent만 XHigh로 선택적 승격

unsupported request:
router 단계에서 No matching trusted route
```

---

## 2. Repository 규모

| 항목 | `realistic_large_platform` | `enterprise_xlarge_platform` | Enterprise 배율 |
| --- | ---: | ---: | ---: |
| Approximate SLOC | 28,708 | **126,731** | **4.41×** |
| src Python files | 1,432 | **5,926** | **4.14×** |
| Responsibility areas | 27 | **48** | 1.78× |
| Repair tasks | 9 | **15** | 1.67× |
| Repair runs per effort | 54 | **90** | 1.67× |

Enterprise repo는 파일 수만 늘린 구조가 아니다. queueing, lease, projection, reconciliation, ledger, billing, recovery, reporting 등 유사한 이름의 책임 영역과 decoy component를 의도적으로 포함한다.

---

## 3. Medium E2E 비교

### 3.1 Authoring과 repair

| 지표 | `realistic_large_platform` | `enterprise_xlarge_platform` |
| --- | ---: | ---: |
| Map authoring tokens | 1,748,486 | **1,527,492** |
| Map authoring seconds | 648.22 | 759.46 |
| Repair runs | 54 | 90 |
| 전체 누적 repair tokens: baseline | 5,670,720 | 12,596,826 |
| 전체 누적 repair tokens: generated-map | 3,276,162 | 8,840,991 |
| 전체 누적 토큰 절감률 | **42.23%** | 29.82% |
| Bugfix 누적 토큰 절감률 | 약 42% | **40.48%** |
| Bugfix paired 절감률 | **43.56% ± 17.84%** | 31.24% ± 53.39% |
| Core bugfix paired 절감률 | n/a | **45.85% ± 24.94%** |
| Bugfix 초기 손익분기점 | 18.06 tasks | **13.12 tasks** |

### 3.2 해석

Enterprise repo는 4.4배 크지만 Medium map authoring 토큰은 오히려 더 적었다.

```text
Map authoring cost
≠
LOC에 단순 비례
```

구조의 규칙성, 대표 흐름, agent 탐색 경로가 authoring 비용에 영향을 준다.

Ordinary bugfix 누적 절감률은 Enterprise 규모에서도 약 40%를 유지했다. 동시에 분산은 커졌다. 이는 대형 repo에서 task 난이도와 decoy ambiguity의 영향이 커졌다는 뜻이다.

---

## 4. XHigh E2E 비교

### 4.1 Authoring과 repair

| 지표 | `realistic_large_platform` | `enterprise_xlarge_platform` |
| --- | ---: | ---: |
| Map authoring tokens | 2,891,143 | **3,122,221** |
| Map authoring seconds | 1,069.78 | 1,042.54 |
| Repair runs | 54 | 90 |
| 전체 누적 토큰 절감률 | **37.40%** | 25.11% |
| Bugfix 누적 토큰 절감률 | n/a | **44.45%** |
| Bugfix paired 절감률 | 36.53% ± 22.98% | **40.41% ± 24.61%** |
| Core bugfix paired 절감률 | n/a | **44.57% ± 20.51%** |
| Bugfix 초기 손익분기점 | 28.36 tasks | **21.31 tasks** |

### 4.2 Enterprise XHigh category 결과

| Category | 누적 토큰 절감률 | Paired saving % ± SD | Boundary violations |
| --- | ---: | ---: | ---: |
| Workflow bugfix | **52.91%** | 52.59% ± 16.40% | 0 → 0 |
| Cross-module bugfix | **50.18%** | 45.59% ± 21.63% | 0 → 0 |
| Decoy-heavy bugfix | **34.69%** | 26.52% ± 32.73% | **0 → 0** |
| Local bugfix | **28.86%** | 26.50% ± 16.42% | 0 → 0 |
| Strict no-match | **-44.40%** | -59.01% ± 93.65% | 별도 안전성 실패 |

### 4.3 해석

Enterprise 규모에서는 XHigh의 가치가 단순 절감률뿐 아니라 안정성에서 드러났다.

Medium E2E에서는 decoy-heavy task에서 대규모 over-edit가 발생했다.

```text
enterprise-projection-route-preference
baseline repetition 1

changed files:       528
boundary violations: 527
```

반면 Enterprise XHigh E2E에서는 decoy-heavy boundary violation이 baseline과 mapped 조건 모두 0이었다.

```text
Medium:
더 경제적
하지만 일부 decoy-heavy task에서 폭주 가능

XHigh:
초기 비용이 큼
하지만 복잡한 탐색에서 더 안정적
```

---

## 5. Medium과 XHigh의 operating point

### 5.1 `realistic_large_platform`

| 지표 | Medium | XHigh | 우세 |
| --- | ---: | ---: | --- |
| Map authoring tokens | **1,748,486** | 2,891,143 | Medium |
| Bugfix paired 절감률 | **43.56%** | 36.53% | Medium |
| Bugfix 초기 손익분기점 | **18.06** | 28.36 | Medium |
| Boundary violations | 0 | 0 | 동률 |

28.7K SLOC에서는 Medium이 명확하게 더 경제적이다.

### 5.2 `enterprise_xlarge_platform`

| 지표 | Medium | XHigh | 우세 |
| --- | ---: | ---: | --- |
| Map authoring tokens | **1,527,492** | 3,122,221 | Medium |
| Bugfix 누적 토큰 절감률 | 40.48% | **44.45%** | XHigh |
| Bugfix paired 절감률 | 31.24% | **40.41%** | XHigh |
| Bugfix 초기 손익분기점 | **13.12** | 21.31 | Medium |
| Decoy-heavy boundary violations | 537 → 10 | **0 → 0** | XHigh |

Enterprise 규모에서는 선택이 단순하지 않다.

```text
경제성:
Medium

hard-task 안정성:
XHigh
```

따라서 XHigh는 기본 엔진보다 선택적 escalation 옵션에 가깝다.

---

## 6. No-match route rejection

No-match는 지원되지 않는 요청을 router가 거절할 수 있는지 보는 안전성 검사다.

```text
예:
Python control-plane repo에
iOS app 또는 Terraform Kubernetes 환경을 추가하라는 요청

기대:
No matching trusted route
```

### 6.1 `realistic_large_platform`

행동 자체는 edit-free였지만, trusted route가 과도하게 매치됐다.

```text
safe agent behavior
≠
correct route rejection
```

### 6.2 `enterprise_xlarge_platform`

문제가 더 선명해졌다.

#### Medium E2E

| 조건 | No-match edit-free |
| --- | ---: |
| No-map + Medium | **6 / 6** |
| Medium-map + Medium | **2 / 6** |

#### XHigh E2E

| 조건 | No-match edit-free |
| --- | ---: |
| No-map + XHigh | 5 / 6 |
| XHigh-map + XHigh | **0 / 6** |

모든 generated-map no-match run에서 trusted route가 매치됐다.

```text
Route rejection score:
0 / 6
```

근본 문제는 repair agent effort보다 semantic router의 responsibility-boundary 판단이다.

---

## 7. 경제성 비교

| Repository | Effort | Map authoring tokens | Bugfix initial break-even |
| --- | --- | ---: | ---: |
| `realistic_large_platform` | Medium | 1,748,486 | 18.06 tasks |
| `realistic_large_platform` | XHigh | 2,891,143 | 28.36 tasks |
| `enterprise_xlarge_platform` | Medium | **1,527,492** | **13.12 tasks** |
| `enterprise_xlarge_platform` | XHigh | 3,122,221 | 21.31 tasks |

Enterprise Medium이 가장 짧은 초기 손익분기점을 보였다.

단, 이 값은 다음을 포함하지 않는다.

```text
map maintenance cost
human review cost
cached-token monetary pricing
wrong-route risk cost
```

정확한 이름은 다음과 같다.

```text
Initial break-even excluding maintenance
```

---


## 8. Wall-clock 시간 비교

토큰 절감과 실제 작업 시간은 같은 방향으로 움직이지 않았다.

```text
semantic map
→ context ingestion 감소
→ token 절감

하지만
reasoning / command / test / filesystem 행동
→ wall-clock을 별도로 좌우
```

### 8.1 Medium E2E

| Repo | 범위 | Baseline 누적 시간 | Generated-map 누적 시간 | 절약 시간 | 누적 시간 변화 |
| --- | --- | ---: | ---: | ---: | ---: |
| `realistic_large_platform` | 전체 27 pairs | 1,792.49초 | 1,396.86초 | **395.63초** | **22.07% 단축** |
| `realistic_large_platform` | Bugfix 24 pairs | 1,060.75초 | 981.88초 | **78.87초** | **7.44% 단축** |
| `enterprise_xlarge_platform` | 전체 45 pairs | 3,697.31초 | 3,597.81초 | **99.50초** | **2.69% 단축** |
| `enterprise_xlarge_platform` | Bugfix 39 pairs | 2,466.19초 | 2,465.11초 | **1.08초** | **0.04% 단축** |
| `enterprise_xlarge_platform` | Core bugfix 30 pairs | 1,780.28초 | 1,424.40초 | **355.88초** | **19.99% 단축** |
| `enterprise_xlarge_platform` | Decoy-heavy 9 pairs | 685.92초 | 1,040.72초 | **-354.80초** | **51.73% 느려짐** |

Enterprise Medium의 core bugfix는 약 20% 빨라졌다. 그러나 decoy-heavy task의 over-edit outlier가 이득을 거의 지웠다.

### 8.2 XHigh E2E

| Repo | 범위 | Baseline 누적 시간 | Generated-map 누적 시간 | 절약 시간 | 누적 시간 변화 |
| --- | --- | ---: | ---: | ---: | ---: |
| `realistic_large_platform` | 전체 27 pairs | 3,056.01초 | 2,912.50초 | **143.51초** | **4.70% 단축** |
| `realistic_large_platform` | Bugfix 24 pairs | 1,536.47초 | 1,680.04초 | **-143.57초** | **9.34% 느려짐** |
| `enterprise_xlarge_platform` | 전체 45 pairs | 6,004.10초 | 6,549.97초 | **-545.87초** | **9.09% 느려짐** |
| `enterprise_xlarge_platform` | Bugfix 39 pairs | 3,162.72초 | 3,233.79초 | **-71.07초** | **2.25% 느려짐** |
| `enterprise_xlarge_platform` | Workflow bugfix 12 pairs | 992.50초 | 783.86초 | **208.64초** | **21.02% 단축** |
| `enterprise_xlarge_platform` | Decoy-heavy 9 pairs | 826.20초 | 787.19초 | **39.01초** | **4.72% 단축** |
| `enterprise_xlarge_platform` | Cross-module bugfix 12 pairs | 959.22초 | 1,233.04초 | **-273.83초** | **28.55% 느려짐** |

XHigh는 Enterprise decoy-heavy 안정성을 높였지만 전체 latency를 개선하지는 못했다.

### 8.3 시간 기준 해석

| 질문 | 답 |
| --- | --- |
| Semantic map은 항상 더 빠른가? | 아니다 |
| 가장 명확한 시간 이득은? | `realistic_large_platform` Medium 전체 **22.07% 단축** |
| Enterprise Medium은 시간 이득이 없는가? | Core bugfix는 **19.99% 단축**, decoy-heavy outlier가 상쇄 |
| Enterprise XHigh는 왜 쓰는가? | 평균 속도보다 hard-task 안정성과 boundary safety |
| 공개 문구의 중심은? | “속도 보장”보다 “탐색 토큰과 context ingestion 감소” |

### 8.4 시간 기준 초기 회수점

| Repo | Effort | Map authoring 시간 | Bugfix당 평균 절약 시간 | 시간 기준 회수점 |
| --- | --- | ---: | ---: | ---: |
| `realistic_large_platform` | Medium | 648.22초 | 3.29초 | 약 **197 tasks** |
| `realistic_large_platform` | XHigh | 1,069.78초 | 음수 | 회수 불가 |
| `enterprise_xlarge_platform` | Medium | 759.46초 | 0.03초 | 불안정 |
| `enterprise_xlarge_platform` | XHigh | 1,042.54초 | 음수 | 회수 불가 |

Token break-even과 latency break-even은 반드시 분리해야 한다.


## 9. Scaling insight

두 repo의 비교가 보여 주는 핵심은 다음과 같다.

### 8.1 Semantic navigation은 대형 repo에서도 유효하다

Ordinary bugfix 토큰 절감은 Enterprise 규모에서도 유지됐다.

### 8.2 단순 LOC보다 구조가 중요하다

Enterprise repo는 SLOC가 4.4배 컸지만 Medium map authoring 비용은 오히려 낮았다.

### 8.3 규모가 커질수록 route precision이 중요하다

Decoy-heavy task와 no-match 요청에서 route의 경계 품질이 중요해졌다.

### 8.4 Medium은 예상보다 강한 기본값이다

Medium은 큰 repo에서도 경쟁력 있는 token economy를 보였다.

### 8.5 XHigh는 선택적 증강 옵션이다

XHigh는 enterprise decoy-heavy 안정성을 개선했다. 그러나 map authoring 비용과 break-even을 고려하면 상시 기본값보다는 hard-task escalation에 적합하다.

---

## 10. 공개 가능한 요약

> Two native end-to-end synthetic benchmarks suggest that Bunya-Jido semantic maps can reduce repository-scale code-repair token usage at both 28.7K and 126.7K SLOC. On the 126.7K-SLOC enterprise-scale platform, Medium-authored maps reduced cumulative Medium-effort bugfix tokens by 40.48%, with an initial break-even of approximately 13 similar bugfix tasks excluding maintenance. XHigh improved decoy-heavy stability but remained more expensive. Unsupported-request routing still needs hardening.

---

## 11. 현재 권장안

```text
기본 운영:
Medium map authoring + Medium repair

복잡한 workflow-heavy / decoy-heavy 작업:
repair agent만 XHigh로 선택적 승격

제품 개선 최우선:
No matching trusted route
responsibility-boundary pre-check
```

---

## 12. 한계

- 두 repository는 synthetic이다.
- 실제 production repository 재현성은 아직 검증하지 않았다.
- Wall-clock time은 외부 noise와 agent 행동 차이에 민감하다.
- Raw token break-even은 금액 break-even과 다르다.
- No-match route rejection은 아직 production-ready가 아니다.
