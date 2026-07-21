# Bunya-Jido

<p align="center">
  <a href="https://jeong87.github.io/Bunya-Jido/demo.html">
    <img src="https://jeong87.github.io/Bunya-Jido/assets/self-map-grounded.png" alt="Grounded Bunya-Jido constellation map preview with semantic role glyphs" width="100%">
  </a>
</p>

<p align="center">
  <a href="./README.md">EN</a> | <strong>KR</strong>
</p>

<p align="center">
  <a href="https://jeong87.github.io/Bunya-Jido/demo.html"><strong>데모 체험하기</strong></a>
</p>

<p align="center">
  <strong>사람과 코딩 에이전트를 위한 시맨틱 저장소 지도입니다.</strong>
</p>

`Bunya-Jido`는 저장소를 재사용 가능한 시맨틱 지도로 만듭니다. 이후 유지보수 작업에서 코딩 에이전트가 먼저 읽을 곳, 확인할 테스트, 넘지 말아야 할 변경 경계를 좁히는 데 쓰입니다. 같은 지도는 사람이 탐색할 수 있는 HTML atlas로도 렌더링되어, 폴더와 import 목록만 보고 시작하지 않아도 코드베이스의 흐름을 잡을 수 있게 돕습니다.

시나리오 재생에는 경로 밖 구조를 흐리게 보여 주는 포커스, 움직이는 route marker, 간결한 단계 설명이 추가되어 근거 기반 경로를 더 쉽게 따라갈 수 있습니다.

이름은 하늘을 구역과 관계로 읽어낸 한국의 별자리 지도, 천상열차분야지도에서 따왔습니다. Bunya-Jido는 그 방식을 코드에 옮겨 파일, 문서, 워크플로우, 런타임 산출물, 검토된 해석을 하나의 살펴볼 수 있는 지도로 묶습니다.

## Build Week 2026: 지도 기반 Codex 실행

OpenAI Build Week에서 추가된 기능입니다. 이제 지도는 읽기 안내를 넘어 실행을
직접 통제합니다. `codex-run`은 검증된 작업 경로 하나를 로컬 Codex CLI에
넘기고, 경로 판정으로 샌드박스를 정하고, Codex가 한 일을 선언된 편집 경계와
대조해 감사합니다.

```bash
bunya-jido codex-run --root . --task "Implement guarded Codex run orchestration and boundary reporting." --preview
```

확실한 경로 `MATCH`만 `workspace-write`를 받습니다. 나머지는 — "애매함"까지
포함해 — 전부 read-only로 돌고, 이를 우회하는 플래그는 없습니다. 실행마다
영수증(`run.json`)이 남습니다: 경로 ID와 fingerprint, compact context 크기,
실제 Codex 토큰 사용량, 실행 시간, 변경 파일, 경계 판정. 이 파일을 오프라인
atlas에서 열면 같은 지도 위에 예상 경로, 실제 변경, 위반이 겹쳐 보입니다.

정직성 규칙 두 가지가 내장돼 있습니다. 스트림에 없는 토큰 사용량은 추정하지
않고 unavailable로 기록하며, 단일 실행으로는 "토큰 절감"을 주장하지 않습니다
— 그 숫자는 지도 유무를 짝지은 비교에서만 나옵니다.

**Codex와 GPT-5.6의 역할.** 이 기능 자체가 GPT-5.6 기반 Codex로 만들어졌습니다
(세션 `019f73d5-d0c4-7633-8f08-fd8fb5933b3b`, 모델 메타데이터는 리포에 기록).
Bunya-Jido 자신의 작업 경로 — 무엇을 먼저 읽고, 어떤 테스트를 만족시키고,
어디를 수정해도 되는지 — 의 안내를 받아 Codex가 약 900줄의 러너와 800줄의
테스트, atlas 오버레이를 작성했습니다. 동시에 Codex는 이 기능이 오케스트레이션
하는 대상이기도 합니다: `codex-run`은 로컬 Codex CLI를 매핑된 샌드박스로 띄우고
그 작업을 감사합니다. 사람의 결정 기록은
[docs/build-week/DECISIONS.md](docs/build-week/DECISIONS.md), 협업 전체 기록과
근거 경계는 [BUILD_WEEK.md](BUILD_WEEK.md), 명령 계약은
[docs/GUARDED_CODEX_RUN.md](docs/GUARDED_CODEX_RUN.md)를 참고하세요.

## 벤치마크 요약

최근 동기화된 synthetic benchmark에서는 Bunya-Jido가 bugfix 성공률을
유지하면서 대형 저장소 수리 비용을 줄일 수 있음을 보였습니다.

<div align="center">
<table align="center">
  <thead>
    <tr>
      <th>저장소 규모</th>
      <th align="center">Bugfix 성공</th>
      <th align="center">Tokens</th>
      <th align="center">Time</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>28.7K SLOC</td>
      <td align="center">bugfix 24개 중 24개 성공</td>
      <td align="center">total -18.8%<br><small>(paired 13.7% ± 37.9%)</small></td>
      <td align="center">total -28.0%<br><small>(paired -1.8% ± 51.8%)</small></td>
    </tr>
    <tr>
      <td>126.7K SLOC</td>
      <td align="center">bugfix 39개 중 39개 성공</td>
      <td align="center">total -22.8%<br><small>(paired 18.6% ± 31.9%)</small></td>
      <td align="center">total -12.5%<br><small>(paired -48.1% ± 233.3%)</small></td>
    </tr>
  </tbody>
</table>
</div>

- Synthetic benchmark, GPT-5.5 Medium, scenario별 3회 반복 결과입니다.
- `total`: bugfix suite 전체의 누적 변화입니다.
- `paired`: scenario별 saving 평균 ± 표준편차입니다.
- Wall-clock time은 노이즈가 커서 누적 시간이 줄어도 paired time 평균은
  음수일 수 있습니다.
- Production 저장소에서도 같은 개선을 보장한다는 뜻은 아닙니다.
  방법론, 제한사항, 상세 보고서는 [docs/BENCHMARKS.md](docs/BENCHMARKS.md)에
  정리했습니다.

## 빠른 시작

1. 지도를 만들 저장소에서 PyPI public alpha를 설치합니다.

```bash
python -m pip install --pre bunya-jido
bunya-jido --version
```

최신 릴리스가 alpha인 동안에는 `--pre` 옵션이 필요합니다. 오래된
`pip` 환경이라면 먼저 `python -m pip install --upgrade pip`를 실행하세요.

2. 그 저장소 루트에서 코딩 에이전트에게 (GPT-5.5 Medium 권장) 다음 문장을 그대로 지시합니다.

```text
Run `bunya-jido prepare --root . --atlas-mode studio --quiet`, then read and execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`. Use `.bunya-jido/ATLAS_INTERVIEW.md` as an internal checklist while creating or refreshing `.bunya-jido/COMPONENTS.md`, `.bunya-jido/WORKFLOWS.md`, `.bunya-jido/REPOSITORY_THESIS.md`, `.bunya-jido/PROJECTIONS.md`, `.bunya-jido/SCENARIOS.md`, `.bunya-jido/bunya-jido.blueprint.json`, and `.bunya-jido/bunya-jido.agent-map.json`; run `bunya-jido validate-blueprint --root .`, `bunya-jido validate-agent-map --root .`, and `bunya-jido evaluate-atlas-quality --root . --require-pass --json`; fix errors and grounding blockers; then run `bunya-jido build --root . --out bunya-jido.html`; confirm the HTML path and say `ready`.
```

완료되면 브라우저에서 `bunya-jido.html`을 엽니다.

## 어떻게 쓰나요?

Bunya-Jido를 설치하는 것만으로는 저장소 파일이 바뀌지 않습니다. 빠른
시작 프롬프트를 실행하면 `.bunya-jido/` 시맨틱 산출물과
`bunya-jido.html` 지도가 만들어집니다.

코딩 에이전트가 구현, 디버깅, 리뷰 전에 지도를 먼저 보게 하려면 생성된
context 지침을 활성화합니다.

```bash
bunya-jido install-agent-guides --root . --agent all --activate
```

이 명령은 `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/bunya-jido.mdc`,
`.clinerules/bunya-jido.md` 같은 파일에 Bunya-Jido 관리 블록을 추가하거나
갱신합니다. 나중에 끄려면 다음 명령을 사용합니다.

```bash
bunya-jido install-agent-guides --root . --agent all --deactivate
```

한 번만 지도 없는 실행을 하고 싶다면 `BUNYA_JIDO_CONTEXT=off` 또는
`BUNYA_JIDO_DISABLE_CONTEXT=1`을 설정합니다.

사람은 `bunya-jido.html`을 브라우저에서 바로 열면 됩니다. 먼저 overview를
보고, 필요하면 projection이나 workflow를 바꾸고, 노드를 눌러 목적과
근거를 확인합니다. 지도가 narrated scenario를 게시한 경우에는 scenario
playback으로 흐름을 따라갈 수 있습니다.

## 무엇을 만드나요?

Bunya-Jido는 두 가지 결과물을 만듭니다.

1. 브라우저에서 바로 열 수 있는 단일 HTML 아키텍처 지도
2. Codex, Claude Code, Cursor, Cline 같은 코딩 에이전트가 특정 작업의 제한된 handoff 문맥으로 사용할 수 있는 `.bunya-jido/` 컨텍스트 팩

HTML 지도는 오프라인에서 동작합니다. 별도의 서버, 데이터베이스, 인터넷 연결, JavaScript 빌드 과정이 필요하지 않습니다.

## 왜 필요한가요?

정적 분석 도구는 `foo.py`가 `bar.py`를 import한다는 사실을 잘 찾습니다. 하지만 어떤 모듈이 제어 흐름을 담당하는지, 어떤 파일이 런타임 어댑터인지, 어떤 문서가 실제 변경 전에 읽어야 할 계약인지까지는 보통 알기 어렵습니다.

Bunya-Jido는 이 빈틈을 코딩 에이전트와 함께 메웁니다.

먼저 저장소를 빠르게 스캔해 raw evidence를 모읍니다. 그 다음 코딩 에이전트가 저장소를 읽고 구성요소 문서와 워크플로우 문서를 작성합니다. Bunya-Jido는 그 결과를 검증하고, 근거 경로가 붙은 인터랙티브 HTML 지도로 렌더링합니다.

결과적으로 Bunya-Jido는 다음 질문에 답하는 데 집중합니다.

- 이 저장소의 주요 책임 영역은 무엇인가?
- 중요한 워크플로우는 어떤 순서로 흐르는가?
- 특정 기능을 바꾸기 전에 어떤 파일, 문서, 테스트를 먼저 봐야 하는가?
- 코딩 에이전트가 함부로 건드리지 말아야 할 경계는 어디인가?
- 그래프의 노드와 엣지는 어떤 실제 근거에 기반하는가?

## 두 가지 지도 모드

Bunya-Jido는 서로 관련되어 있지만 의미가 다른 두 형태의 지도를 만들 수 있습니다.

### 결정적 스캔 지도

semantic blueprint 없이 실행하면, Bunya-Jido는 소스 파일, 문서, 설정, 선택된 산출물에서 수집한 저장소 구조와 탐지 힌트를 렌더링합니다. 이는 탐색에 유용한 근거이지, 아키텍처에 대한 판단 자체는 아닙니다.

```bash
bunya-jido build --root . --blueprint none --out bunya-jido.html
```

### 시맨틱 Blueprint 지도

`.bunya-jido/bunya-jido.blueprint.json`이 있으면, Bunya-Jido는 코딩 에이전트와 함께 작성하고 도구가 검사한, 근거가 연결된 아키텍처 해석을 렌더링합니다. 책임 영역, 워크플로우, 에이전트 handoff 문맥에는 이 모드를 권장합니다.

핵심 grounding blocker가 해결되지 않은 시맨틱 지도는 기본적으로 빌드되지 않습니다. 구조적으로는 유효하지만 아직 완성되지 않은 지도를 명시적으로 draft로 검토하려면 다음 명령을 사용합니다.

```bash
bunya-jido build --root . --allow-draft --out bunya-jido.html
```

## 설치와 모드 상세

필요 환경:

- `pip`을 사용할 수 있는 Python 3.10 이상.
- 현재 GitHub 설치 명령을 위한 Git.
- Blueprint 모드에서는 저장소를 읽고 쓰며 터미널 명령을 실행할 수
  있는 코딩 에이전트(Codex, Claude Code 등).
- 생성된 오프라인 HTML 지도를 확인할 때만 브라우저가 필요합니다.

CLI는 Windows, macOS, Linux에서 사용할 수 있도록 설계되어 있습니다.
CI는 Ubuntu에서 Python 3.10-3.12를, Windows와 macOS에서 Python 3.12를
검증합니다.

PyPI public alpha 설치는 한 줄이면 됩니다.

```bash
python -m pip install --pre bunya-jido
```

`--pre`는 `0.5.0a2` 같은 alpha 릴리스를 설치하기 위한 옵션입니다.
Bunya-Jido에 stable 릴리스가 생기면 `python -m pip install bunya-jido`만으로
충분해집니다. 아직 릴리스되지 않은 `main`을 테스트하려면 GitHub에서
직접 설치할 수 있습니다.

```bash
python -m pip install git+https://github.com/jeong87/Bunya-Jido.git
```

설치가 끝나면 명령어를 확인합니다.

```bash
bunya-jido --version
```

### 운영체제별 설치

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --pre bunya-jido
bunya-jido --version
```

macOS 또는 Linux (`bash` / `zsh`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --pre bunya-jido
bunya-jido --version
```

Python 3.10 이상이면 사용할 수 있습니다. Windows 예시에서 `3.12`를
사용한 것은 세 CI 운영체제 모두에서 검증하는 버전이기 때문입니다.

### Blueprint 모드

Blueprint 모드는 기본 시맨틱 워크플로우입니다. 위 빠른 시작은 더 풍부한
Studio atlas 확장을 선택합니다. authored projection과 narrated
scenario가 필요하지 않다면 이 기본 경로를 사용할 수 있습니다.

1. Bunya-Jido가 저장소를 정적으로 스캔합니다.
2. 코딩 에이전트가 저장소와 스캔 결과를 읽습니다.
3. 에이전트가 구성요소 문서, 워크플로우 문서, blueprint, agent map을 작성합니다.
4. Bunya-Jido가 작성된 파일을 검증합니다.
5. 검증된 blueprint를 단일 HTML 지도로 렌더링합니다.

저장소 루트에서 코딩 에이전트에게 다음 지시를 줍니다.

```text
Run `bunya-jido prepare --root . --quiet` if needed, then read and execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`. Create or refresh `.bunya-jido/COMPONENTS.md`, `.bunya-jido/WORKFLOWS.md`, `.bunya-jido/bunya-jido.blueprint.json`, and `.bunya-jido/bunya-jido.agent-map.json`; run `bunya-jido validate-blueprint --root .` and `bunya-jido validate-agent-map --root .`; fix errors and grounding blockers, and reduce classification warnings when practical; then run `bunya-jido build --root . --out bunya-jido.html`; confirm the HTML path and say `ready`.
```

이 프롬프트는 마지막에 `bunya-jido.html`까지 생성합니다. Blueprint를 고친 뒤 직접 다시 만들고 싶으면 다음 명령을 실행하면 됩니다.

```bash
bunya-jido build --root . --out bunya-jido.html
```

그 다음 `bunya-jido.html`을 브라우저에서 열면 됩니다.

#### Studio Atlas 모드

위 빠른 시작에서 권장하는 경로가 Studio 모드입니다. narrated atlas를
게시하기에 앞서 코딩 에이전트가 저장소에 맞는 설명 관점을 비교하도록
합니다.

```bash
bunya-jido prepare --root . --atlas-mode studio --quiet
```

Studio 준비는 내부 체크리스트인 `ATLAS_INTERVIEW.md`와
`REPOSITORY_THESIS.md`, `PROJECTIONS.md`, `SCENARIOS.md`도 추가로
생성합니다. 코딩 에이전트는 역할별 pass를 거쳐 primary projection과
정직한 scenario 정책(`required`, `optional`, `none_with_reason`)을
검토합니다. 새로 작성하는 Studio blueprint는 선택된 projection, 비교한
대안, 과도한 중심화 위험을 다시 검토할 수 있도록 선택적인
`atlas.decision_record`도 기록합니다. 이 필드가 없는 기존 v2 산출물도
계속 호환됩니다.
Studio 준비는 이제 additive `bunya-jido-blueprint-v2` schema를 생성하며,
`validate-blueprint`, `build`, `diagnose`는 vocabulary, projection, scenario
계약을 처리합니다. 오프라인 viewer는 이제 map-local node/relation
family를 렌더링하고 primary projection에서 시작하며, projection
preset과 선택 노드의 contextual 이웃 표시를 제공합니다. 검증된 Studio
atlas가 scenario를 게시한 경우 viewer는 근거 basis badge가 표시되는
narrated playback도 제공합니다. behavioral path는 token으로 재생할 수
있고, structural tour는 runtime 순서를 암시하지 않는 단계 강조로
보여줍니다. 재생을 종료하면 이전 view와 filter가 복원됩니다. Classic
모드와 `none_with_reason` atlas에는 scenario launcher가 나타나지 않습니다.
검증된 task route는 선택적으로 Studio projection 하나와 연관 scenario를
제한된 읽기 문맥으로 연결할 수 있습니다. viewer에서는 선택한 노드와
관련된 신뢰 route를 보여주고 그 coding-agent context를 바로 복사할 수
있습니다.

Studio v2 blueprint의 첫 화면 가독성과 scenario 정책 신호는 다음
명령으로 평가할 수 있습니다.

```bash
bunya-jido evaluate-atlas-quality --root . --require-pass --json
```

이 quality gate는 결정적으로 확인할 수 있는 계약 위반을 차단하고,
overview 과밀이나 약한 core inspection 같은 가독성 신호를 경고합니다.
또한 structural tour가 실제 실행처럼 서술되는 경우, playback 문장이
너무 짧거나 긴 경우, 선택된 projection의 landmark를 방문하지 않는
경우를 검토 신호로 보고합니다. projection 선택과 narration 의미는 자동
증명으로 가장하지 않고 명시적인 검토 항목으로 남기며, 검토 전용
신호만으로 `status: "passed"`나 `--require-pass` 의미는 바뀌지
않습니다. 선택적으로 사람이 읽는 요약을 쓰려면 다음을 실행합니다.

```bash
bunya-jido evaluate-atlas-quality --root . --require-pass --write-report
```

이 명령은 로컬 작업공간의 `.bunya-jido/ATLAS_QUALITY_REPORT.md`를 씁니다.

이 저장소의 커밋된 self-map은 이제 Studio v2를 사용합니다. primary
projection은 `Trusted Publication`이며, machine-readable editorial
decision record와 근거 badge가 붙은 behavioral scenario 두 개를
게시합니다. 도구가 자기 소스 트리에만 맞춰지는 것을
막기 위해 Studio benchmark는 워크플로우 시스템, 웹 애플리케이션, SDK,
변환 파이프라인, runtime scenario를 꾸며내지 않는 utility를 포함한
서로 다른 여섯 저장소 형태를 렌더링하고 검증합니다. 자세한 내용은
[docs/STUDIO_BENCHMARK.md](docs/STUDIO_BENCHMARK.md)와
[docs/gallery.md](docs/gallery.md)를 참고하세요. 공개 gallery에는 이
self-map, provenance 중심 coverage fixture, 그리고 근거가 있는 SDK,
web-state, compiler, utility miniature가 함께 게시됩니다. 이 사례들은
모든 저장소에 같은 lifecycle을 강제하지 않으면서 structural tour,
grounded behavioral playback, 정직한 `none_with_reason` 결과를 보여줍니다.

## 생성되는 파일

`bunya-jido prepare`를 실행하면 다음 파일들이 만들어집니다.

```text
.bunya-jido/
  COMPONENTS.md
  WORKFLOWS.md
  bunya-jido.blueprint.json
  bunya-jido.agent-map.json
  bunya-jido-static-scan.json
  bunya-jido-blueprint.schema.json
  bunya-jido-agent-map.schema.json
  BUNYA_JIDO_BLUEPRINT_PROMPT.md
  CODEX_ONE_LINER.txt
```

지도 저장소는 `check-stale`에서 구조 변경이 필요 없다고 검토한 결정을
남기기 위해 `.bunya-jido/MAP_REVIEW.md`를 추가로 추적할 수 있습니다.
`--atlas-mode studio`를 사용하면 내부 체크리스트인 `ATLAS_INTERVIEW.md`,
편집 입력인 `REPOSITORY_THESIS.md`, `PROJECTIONS.md`, `SCENARIOS.md`, 그리고
Studio v2 blueprint schema도 생성됩니다. `evaluate-atlas-quality --write-report`를
실행하면 선택적인 로컬 검토 요약인
`ATLAS_QUALITY_REPORT.md`도 작성됩니다.

### `COMPONENTS.md`

저장소의 주요 구성요소를 책임 기준으로 정리하는 문서입니다.

각 구성요소에는 역할, 근거 파일, 입력, 출력, 계약, 관련 테스트, 코딩 에이전트가 먼저 읽어야 할 위치를 적습니다. 폴더 이름을 그대로 옮기는 대신, 실제 책임과 변경 경계를 드러내는 것이 목적입니다.

### `WORKFLOWS.md`

저장소의 주요 흐름을 순서대로 설명하는 문서입니다.

예를 들어 CLI 진입점에서 시작해 스캐너, blueprint 검증기, 렌더러, HTML 출력까지 어떤 흐름으로 이어지는지 적습니다. 기능 변경이나 디버깅을 시작할 때 어떤 경로를 따라가야 하는지도 함께 남깁니다.

### `bunya-jido.blueprint.json`

HTML 지도가 사용하는 machine-readable graph입니다.

노드, 엣지, plane, group, detail node, evidence를 담습니다. 사람이 읽는 `COMPONENTS.md`와 `WORKFLOWS.md`에서 도출된 구조이므로, raw dependency graph보다 작고 의미 중심적이어야 합니다.

검증:

```bash
bunya-jido validate-blueprint --root .
```

### `bunya-jido.agent-map.json`

코딩 에이전트용 작업 지도입니다.

예를 들어 "provider 동작 수정", "저장 계층 변경", "런타임 실패 디버깅" 같은 작업마다 먼저 읽을 파일, 관련 테스트, 안전하게 수정할 수 있는 영역, 조심해야 할 경계를 기록합니다.

task route는 신뢰된 에이전트 context로 출력되거나 지도 경로로 표시되기 전에 semantic blueprint 및 저장소 상대 경로의 필수 읽기 파일·테스트와의 연결이 검증되어야 합니다. Studio 지도에서는 검증된 `projection_context`와 `scenario_context` ID를 추가해 제한된 읽기 관점을 전달할 수도 있습니다.

검증:

```bash
bunya-jido validate-agent-map --root .
```

### `bunya-jido-static-scan.json`

LLM 없이 결정적으로 생성되는 정적 스캔 결과입니다.

파일, 모듈, import, 문서, 설정, 런타임 산출물, 외부 API 힌트를 담습니다. provider hint evidence에는 출처와 종류 metadata가 붙고, 생성 prompt, schema 또는 viewer template 안의 token 예시는 Studio overlay 노드로 승격되지 않습니다. 코딩 에이전트가 blueprint를 만들 때 남은 관찰값을 raw evidence로 사용합니다.

## 진단

현재 어떤 artifact mode가 존재하는지, semantic 지도가 실제로 grounded
게시 조건을 충족하는지 확인할 수 있습니다.

```bash
bunya-jido diagnose --root .
bunya-jido diagnose --root . --require-grounded --json
bunya-jido evaluate-atlas-quality --root . --require-pass --json  # Studio v2
bunya-jido evaluate-atlas-quality --root . --require-pass --write-report  # 선택적인 검토 요약
```

`--require-grounded`는 정적 스캔이거나 차단된 semantic blueprint이면
실패 상태로 종료합니다. 릴리스 자동화도 생성 결과를 신뢰한다고
가정하지 않고 이 검증 조건을 그대로 사용합니다.
`evaluate-atlas-quality`는 Studio v2 blueprint에 적용되며, 측정 가능한
경고와 편집 관점의 검토 항목을 분리해 보고합니다. 자동화가 게시를
막지 않으면서 사람의 후속 검토를 표시할 수 있도록 additive
`review_required` 및 warning count 필드도 제공합니다.

## HTML 지도

생성된 HTML 지도에는 다음 기능이 들어갑니다.

- 시맨틱 역할 표식과 워크플로우 launcher bar가 있는 canvas-first 별자리 overview
- guided-tour 진입점과 키보드로 탐색 가능한 repository outline을 포함한 간결한 저장소 요약
- 책임 영역별 plane cluster
- 작성된 plane 목적 설명과 화면용 노드·관계 family
- Studio v2의 map-local glyph/line vocabulary, primary projection tab, contextual direct-neighbor reveal
- Studio v2 narrated scenario playback, basis badge, 일시정지/단계/속도 조작, 종료 시 view 복원
- 작성된 목적, 입력, 출력, 제약을 보여주는 semantic inspector card
- 별자리 layout을 유지하면서 관계 방향과 workflow 순서를 보여주는 미묘한 화살표와 단계 번호
- 선택한 노드의 관련 신뢰 task route와 coding-agent context 복사 동작
- 노드 family, 관계 family, confidence 필터링
- 선택한 노드 주변만 보는 local graph focus
- `Static Scan`, `Grounded`, 명시적 `Draft` 상태를 보여주는 trust panel
- source path, 관계 confidence, 기록된 근거를 보여주는 evidence panel
- 명시적인 `Overview`, `Inspect Evidence`, `Implementation Detail` 탐색 모드
- blueprint view, 워크플로우, 검증된 agent-map task route를 구분해 보여주는 path preset
- PNG와 JSON export
- blueprint가 제공하는 경우 implementation detail 확장
- 좁은 화면에서 가로 탐색 가능한 compact control과 drawer 기반 outline 접근

지도의 근거는 저장소의 코드, 문서, 설정, 테스트, 런타임 산출물, 검증된 blueprint 파일에 있습니다. Bunya-Jido는 그 근거를 보기 좋은 형태로 투영합니다.

검증된 agent map의 task route는 생성되는 context 출력과 HTML 지도의 `Task Route` path preset 양쪽에 나타납니다. route가 검증된 Studio projection/scenario 문맥을 선언하면 CLI handoff와 viewer 복사 동작은 해당 관점과 시작 노드 책임도 함께 제공합니다. blueprint 노드, 워크플로우, 필수 읽기 파일, 테스트 또는 선언된 Studio 문맥 참조가 끊긴 route는 신뢰된 context와 일반 semantic 게시를 차단합니다.

## 코딩 에이전트와 함께 쓰기

Blueprint와 agent map이 있으면 특정 작업에 맞는 handoff를 만들 수 있습니다.

```bash
bunya-jido context --root . --task "modify provider behavior" --out .bunya-jido/CONTEXT.md
```

요청이 검증된 task route와 일치하면 생성된 context는 일치 이유와 함께
읽어야 할 파일, 계약, 테스트 안내를 제공합니다. route가 검증된 Studio
읽기 문맥을 선언한 경우 관련 projection 질문, 성격이 표시된 scenario,
시작 노드의 책임도 함께 제공합니다. 일치하는 route가 없으면
무관한 준비 경로를 안내하는 대신 `No matching trusted route`라고 명시합니다.
`IN_SCOPE_NO_ROUTE`인 정상 수정 작업에는 likely area, 먼저 읽을 경로,
테스트, 읽기 전용 검색 명령, node/workflow 재평가 명령을 상한 내에서
근거와 함께 제공할 수 있습니다.

Context 선택은 다음 결정을 구분합니다.

| Decision | 의미 | 편집 정책 | 실행 정책 |
|---|---|---|---|
| `MATCH` | 하나의 trusted route가 충분한 근거와 구분도를 가짐 | `workspace_write` | `workspace_write` |
| `IN_SCOPE_NO_ROUTE` | 저장소 책임 범위 안이지만 충분한 route가 없음 | `cautious` | `read_only_discovery` |
| `OUT_OF_SCOPE` | 검토된 저장소 경계와 요청이 충돌함 | `read_only` | `read_only` |
| `UNCERTAIN` | 범위 또는 route 충분성을 안전하게 판단할 수 없음 | `read_only` | `read_only` |

Agent map은 선택적으로 repository scope와 route별 negative boundary를
선언할 수 있습니다. Matching은 의미 있는 정확한 단어, 명시적 route 사용
문구, common failure mode, route 고유의 grounded node/workflow 근거,
보수적인 route 간 점수 차이를 사용합니다. failure mode나 공유 workflow
단어 하나만으로 route를 확정하지 않으며, `MATCH`가 아닌 결정은 trusted
route나 safe-edit 경로를 노출하지 않습니다.

통합 도구는 machine-readable 결정을 받을 수 있습니다.

```bash
bunya-jido context --root . --task "modify provider behavior" --json
```

JSON 보고서는 `execution_policy`, `agent_instruction`, 그리고 근거가 있는
`IN_SCOPE_NO_ROUTE`에만 선택적으로 `discovery_context`를 제공합니다.
통합 도구는 에이전트를 실행하기 전에 `read_only` 또는
`read_only_discovery` sandbox를 강제해야 합니다. Bunya-Jido는 정책을
보고하지만 다른 프로세스의 sandbox를 직접 제어하지는 않습니다. 자세한
계약은 [docs/CONTEXT_EXECUTION_POLICY.md](docs/CONTEXT_EXECUTION_POLICY.md)에
있습니다.

### 보호된 Codex 실행

`codex-run`은 context 결정을 권한 상승이 없는 Codex 실행 계획으로
바꿉니다. Preview는 작업 트리가 dirty여도 사용할 수 있고, Codex를
실행하거나 run 산출물을 만들지 않습니다.

```bash
bunya-jido codex-run --root . --task "Implement guarded Codex run orchestration and boundary reporting." --preview
```

실제 실행에는 clean Git 작업 트리와 별도로 설치·인증된 Codex CLI가
필요합니다.

```bash
bunya-jido codex-run --root . --task "Implement guarded Codex run orchestration and boundary reporting."
```

`MATCH`만 Codex의 `workspace-write` OS sandbox를 받습니다. 나머지 context
결정은 모두 `read-only`이며, CLI 옵션으로 권한을 높일 수 없습니다.
safe-edit 경로는 의미적 안내와 실행 후 감사 경계일 뿐 OS sandbox를
확장하지 않습니다. Codex 웹 검색은 `disabled`로 명시하고, workspace
shell의 네트워크 접근도 별도의 설정으로 비활성화합니다. 보고서와 프로세스 출력은
`.bunya-jido/runs/<run-id>/` 아래에 저장됩니다. 결정적인 자동화를 위해
사용자 및 trusted project의 execpolicy `.rules`는 무시하며, 관리자 강제
요구사항은 별도 제약으로 남습니다. 전체 계약은
[docs/GUARDED_CODEX_RUN.md](docs/GUARDED_CODEX_RUN.md)를 참고하세요.

작업이 선택된 Markdown과 JSON context는 기본적으로 compact 출력입니다.
선택된 route 또는 bounded discovery 계약은 유지하되 반복 진단과 무관한
생성 문서 참조를 제거합니다. route 점수나 전체 discovery evidence를
진단할 때는 `--verbose`를 사용합니다.

특정 노드를 중심으로 만들 수도 있습니다.

```bash
bunya-jido context --root . --node component:llm_router --out .bunya-jido/CONTEXT.md
```

변경된 파일 기준으로 context를 새로 만들 수도 있습니다.

```bash
bunya-jido refresh-context --root . \
  --changed-file src/foo.py \
  --changed-file tests/test_foo.py \
  --out .bunya-jido/REFRESH_CONTEXT.md
```

`refresh-context`는 전달된 변경 파일이 route의 읽기/테스트/편집 경로
또는 route 시작 노드의 grounded evidence와 연결될 때만 route를
추천합니다. 출력에는 파일이 일치한 이유가 표시되며, 무관한 변경이면
`No matching trusted route`를 반환합니다.

### 지도를 최신으로 유지하기

Bunya-Jido는 소스 코드가 바뀔 때 semantic map을 검토 없이 자동으로
다시 쓰지 않습니다. semantic 갱신은 여전히 코딩 에이전트가 읽고
작성해야 합니다. 대신 지도 저장소는
`.bunya-jido/bunya-jido.agent-map.json`에 `stale_map_policy`를 정의하고
다음 명령으로 재검토 필요 여부를 자동 확인할 수 있습니다.

```bash
bunya-jido check-stale --root . --git-diff --require-reviewed
```

브랜치를 기준 브랜치와 비교하려면 revision range를 전달합니다.

```bash
bunya-jido check-stale --root . --git-diff origin/main...HEAD --require-reviewed
```

policy 대상 파일이 바뀌었는데 blueprint, agent map 또는
`.bunya-jido/MAP_REVIEW.md` 검토 메모 갱신이 함께 없으면 명령은
`stale`을 보고하고 strict 모드에서 실패합니다. 아키텍처가 바뀌었으면
Blueprint 모드 프롬프트로 지도를 갱신하고, 바뀌지 않았다고 검토했으면
결정을 `MAP_REVIEW.md`에 남깁니다. 어느 경우든 `review_recorded`는
검토 작업의 존재를 기록하는 것이지, 작성된 아키텍처가 완전하다는 자동
증명은 아닙니다. CI에서도 pull request나 push마다 같은 gate를 실행할 수 있습니다. 로컬의
`--git-diff`는 Git이 추적하는 변경만 읽으므로, 아직 추적하지 않는 새
파일은 `--changed-file`로 직접 전달합니다.

### 에이전트 효용 평가하기

지도를 사용하는 저장소는 제한된 context의 acceptance case를
`.bunya-jido/bunya-jido.agent-evaluation.json`에 커밋하고 다음 명령을
실행할 수 있습니다.

```bash
bunya-jido evaluate-agent-utility --root . --require-pass --json
```

이 suite는 예상 첫 읽기 파일, 관련 테스트 회상, 계약/편집 경계,
정직한 no-match 처리, 정상 bugfix의 route/discovery 회수, 변경 근거 기반
refresh 출력을 검사합니다. trusted-route recall, bounded-discovery coverage,
actionable-guidance coverage, normal-bugfix hard-rejection rate도 보고합니다. 이는
생성된 handoff의 결정적 계약 검사이지, 실제 코딩 에이전트가 내용을
읽고 따랐다는 증명은 아닙니다. 평가 형식과 선택적인 실제 에이전트
관찰 절차는
[docs/AGENT_UTILITY_EVALUATION.md](docs/AGENT_UTILITY_EVALUATION.md)에
정리되어 있습니다.
보고서는 compact와 verbose context 출력 크기도 추정하지만, 이는 실제
에이전트 작업 토큰 측정을 대신하지 않습니다.

### Live-agent benchmark 변경 감사하기

Live-agent benchmark runner는 dirty baseline을 거절하고 tracked, staged,
deleted, renamed, untracked, Codex JSONL write activity를 관찰할 수
있습니다.

```bash
bunya-jido audit-worktree --root workspace --require-clean --json
bunya-jido audit-worktree --root workspace --jsonl task.codex.jsonl --allow-artifact "results/**" --require-jsonl --json
```

Audit은 최종 workspace 변경과 write-then-revert 시도를 분리합니다. 또한
Python bytecode cache, test cache, coverage output, OS/editor temp file 같은
일반 generated/cache noise를 분류해 no-match production edit 검사가 환경
artifact에 오염되지 않게 합니다. Runner가 소유한 결과물은 여전히 명시적인
`--allow-artifact` glob으로 허용해야 합니다.

호환되는 live benchmark 결과를 모은 뒤에는 안전하고 해결된 동일 task만
다음 명령으로 비교할 수 있습니다.

```bash
bunya-jido summarize-token-efficiency \
  --results results/token-runs.json \
  --baseline no-map \
  --candidate 0.5-map \
  --require-comparable \
  --json
```

요약은 context 출력, repair, no-match, map authoring, safe-and-resolved
task 토큰을 분리하고 median과 break-even task 수를 보고합니다.

동일한 안전 필터와 명시적인 반복 실행 pairing으로 해결 시간도 측정할
수 있습니다.

```bash
bunya-jido summarize-time-efficiency \
  --results results/time-runs.json \
  --baseline no-map \
  --candidate 0.5-map \
  --require-comparable \
  --json
```

시간 요약은 누적 시간, median, nearest-rank p90, context 생성,
discovery-to-first-edit, 전체 해결 시간, task별 결과, 선택적 authoring 시간
break-even을 보고합니다. 이는 측정 전용 기능이며 benchmark 시나리오에
맞춰 routing 동작을 튜닝하지 않습니다.

이 파일들은 코딩 에이전트에게 작업을 맡기기 전에 붙여넣거나 첨부하기 좋습니다.

## Alpha 제한사항

Bunya-Jido는 public alpha 소프트웨어입니다. 현재 가장 중요한 제한은
다음과 같습니다.

- Python 저장소가 현재 가장 강하게 지원되는 대상입니다.
- 시맨틱 지도 authoring에는 충분히 강한 코딩 에이전트와 의미 있는 초기
  token budget이 필요합니다.
- 작은 저장소에서는 authoring 비용을 회수하지 못할 수 있습니다.
- trusted route가 root-cause owner 대신 downstream compensation path를
  제안할 수 있으므로, 편집 전에 근거를 검토해야 합니다.
- `IN_SCOPE_NO_ROUTE` two-stage discovery는 integration이 read-only
  discovery 계약을 지키는지에 따라 효과가 달라집니다.
- Synthetic benchmark 결과가 production 저장소에서 같은 개선을 보장하지
  않습니다.

## 현재 지원 범위

현재 가장 적합한 대상은 워크플로우가 복잡한 Python 저장소이며, 특히 개발 도구, 연구, 자동화, 에이전트 기반 프로젝트에 잘 맞습니다.

- Python 모듈/import 및 심볼 스캔이 현재 코드 분석의 주된 표면입니다.
- Markdown 문서, 일반적인 패키지/설정 파일, 일부 런타임/데이터 산출물, provenance가 표시된 provider/API 힌트를 탐색 근거로 활용하며, 생성 prompt/schema/template 예시는 Studio overlay에서 걸러집니다.
- JavaScript와 TypeScript 파일도 제한적으로 스캔하지만, 로컬 모듈 해석 범위는 아직 발전 중입니다.

Bunya-Jido는 아직 언어별로 동등한 시맨틱 분석 범위나, 작성된 아키텍처 지도의 정확성을 자동으로 증명한다고 주장하지 않습니다.

현재의 정확한 동작, 대표 fixture, JS/TS 로컬 해석 제한, 새 지원 범위 주장을 추가하기 위한 근거 조건은 [scanner coverage matrix](docs/SCANNER_COVERAGE.md)에서 확인할 수 있습니다.

## 에이전트 활성화

Bunya-Jido는 Codex, Claude Code, Cursor, Cline이 구현, 디버깅, 리뷰
작업 전에 검증된 지도를 먼저 확인하도록 task-context 지침을 활성화할 수 있습니다.

```bash
bunya-jido install-agent-guides --root . --agent all --activate --dry-run
bunya-jido install-agent-guides --root . --agent all --activate
```

활성화 대상 파일:

```text
Codex       AGENTS.md
Claude Code CLAUDE.md
Cursor      .cursor/rules/bunya-jido.mdc
Cline       .clinerules/bunya-jido.md
```

활성화는 기존 프로젝트 지침을 덮어쓰지 않고, 표시된 Bunya-Jido 관리
블록만 추가하거나 갱신합니다. 이 블록은 에이전트에게 `bunya-jido
context --root . --task "<user request>"`를 먼저 실행하고, 일치한 route의
읽기 파일, 계약, 테스트를 따르며, `OUT_OF_SCOPE`와 `UNCERTAIN`은
read-only로 유지하고, `IN_SCOPE_NO_ROUTE`에서는 route를 추측하지 않은 채
초기 탐색도 read-only로 진행한 뒤 정당화된 node/workflow focus로 context를
다시 평가하며, 수정 후에는 실제 변경 파일로
`refresh-context`를 실행하라고 지시합니다. 저장소에 stale-map policy가 정의되어 있으면
`check-stale`도 실행하고, 지도 갱신 또는 구조 변경 없음 검토 기록 중
맞는 조치를 남기도록 안내합니다.

native 지침 파일을 수정하지 않고 일시적으로 no-map 실행을 강제하려면
`bunya-jido context` 또는 `refresh-context` 실행 전에
`BUNYA_JIDO_CONTEXT=off` 또는 `BUNYA_JIDO_DISABLE_CONTEXT=1`을 설정합니다.
그러면 명령은 `decision=DISABLED`, trusted route 없음, safe-edit path 없음,
read-only sandbox 권장을 반환합니다.

native 활성화를 지속적으로 끄려면 표시된 Bunya-Jido 관리 블록만 제거합니다.

```bash
bunya-jido install-agent-guides --root . --agent all --deactivate --dry-run
bunya-jido install-agent-guides --root . --agent all --deactivate
```

비활성화는 관리 블록 밖의 프로젝트 지침을 보존합니다. native 지침 파일이
Bunya-Jido 활성화만을 위해 생성되었고 다른 내용이 없으면 그 파일은
삭제됩니다. 이 작업은 `.bunya-jido/` 지도 artifact나 생성된 HTML 지도는
삭제하지 않습니다.

native 지침 파일을 건드리지 않고 복사 가능한 snippet만 만들려면
`--activate`를 생략합니다.

```bash
bunya-jido install-agent-guides --root . --agent all
```

snippet은 `.bunya-jido/agent-guides/` 아래 생성됩니다.

## 데이터가 많은 저장소

기본적으로 Bunya-Jido는 dataset처럼 보이는 디렉터리를 요약 노드로만 표시합니다. 데이터 파일 수천 개를 전부 노드로 만들지 않습니다.

```bash
bunya-jido build --root . --data-policy summary --out bunya-jido.html
```

다른 옵션:

```bash
bunya-jido build --root . --data-policy sample --max-data-files 50 --out bunya-jido.html
bunya-jido build --root . --data-policy full --out bunya-jido.html
```

대부분의 저장소에는 `summary`를 권장합니다. 데이터 디렉터리의 형태를 조금 보고 싶다면 `sample`, 작은 예제 데이터나 작은 artifact 폴더라면 `full`을 사용할 수 있습니다.

## 설계 원칙

- 거대한 raw dependency graph보다 작은 semantic architecture map을 우선합니다.
- 노드와 엣지에는 가능한 한 evidence path를 붙입니다.
- LLM은 blueprint 작성을 돕지만, 검증과 렌더링은 Bunya-Jido가 결정적으로 수행합니다.
- 최종 지도는 오프라인에서 열 수 있어야 합니다.
- 지도는 실제 지형이 아니라 검토 가능한 투영입니다.

## 한계

- Blueprint 모드의 품질은 코딩 에이전트의 분석 품질에 영향을 받습니다.
- 정적 모드는 빠르지만 큰 저장소에서는 노이즈가 많아질 수 있습니다.
- Bunya-Jido 자체는 LLM을 호출하지 않습니다.
- HTML 지도가 아키텍처의 정확성을 증명하지는 않습니다. 대신 가정과 근거를 더 쉽게 보고 검토할 수 있게 만듭니다.

## 릴리스와 로드맵

Bunya-Jido는 public alpha 단계입니다. 현재 라인은 시맨틱 지도 authoring,
코딩 에이전트 consumption, 그리고 지도 효과와 한계를 함께 보여주는
benchmark evidence를 중심으로 다듬고 있습니다. 커밋된 self-map은 현재
Studio 예시이며, 라이브 데모와 미리보기 이미지는 최신 constellation-viewer
디자인 작업을 반영합니다.

커밋된 self-map은 [docs/gallery.md](docs/gallery.md), 릴리스 gate와 게시
설정은 [docs/RELEASING.md](docs/RELEASING.md), 변경 내역은
[CHANGELOG.md](CHANGELOG.md), 기여 요건은 [CONTRIBUTING.md](CONTRIBUTING.md),
과거 구현 계획은 [docs/CONTRIBUTION_PLAN.md](docs/CONTRIBUTION_PLAN.md)에서
확인할 수 있습니다.

## 라이선스

MIT.
