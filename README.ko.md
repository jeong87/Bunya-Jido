# Bunya-Jido

<p align="center">
  <a href="https://jeong87.github.io/Bunya-Jido/demo.html">
    <img src="docs/assets/bunyajido_preview.jpg" alt="Bunya-Jido preview" width="100%">
  </a>
</p>

<p align="center">
  <a href="./README.md">EN</a> | <strong>KR</strong>
</p>

<p align="center">
  <a href="https://jeong87.github.io/Bunya-Jido/demo.html"><strong>데모 체험하기</strong></a>
</p>

`Bunya-Jido`는 저장소를 오프라인 아키텍처 지도로 바꿔주는 도구입니다.

이 프로젝트는 천상열차분야지도에서 영감을 받았습니다. 하늘의 별을 구역과 관계로 읽어내듯, Bunya-Jido는 코드 저장소 안의 파일, 모듈, 문서, 설정, 런타임 산출물, 코딩 에이전트의 설계 해석을 하나의 지도로 엮습니다.

목표는 사람이 검토할 수 있고, 코딩 에이전트가 작업 시작점으로 삼을 수 있는 근거 있는 지도를 만드는 것입니다.

## 무엇을 만드나요?

Bunya-Jido는 두 가지 결과물을 만듭니다.

1. 브라우저에서 바로 열 수 있는 단일 HTML 아키텍처 지도
2. Codex, Claude Code, Cursor, Cline 같은 코딩 에이전트가 작업 문맥으로 사용할 수 있는 `.bunya-jido/` 컨텍스트 팩

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

## 빠른 시작

1. 설치: `python -m pip install git+https://github.com/jeong87/Bunya-Jido.git`
2. Codex에게 지시: 아래 Blueprint 모드 프롬프트를 붙여넣으면 문서 작성, 검증, HTML 지도 생성까지 맡길 수 있습니다.

설치는 한 줄이면 됩니다.

```bash
python -m pip install git+https://github.com/jeong87/Bunya-Jido.git
```

PyPI 배포는 추후 예정입니다.

설치가 끝나면 명령어를 확인합니다.

```bash
bunya-jido --version
```

### Blueprint 모드

Blueprint 모드는 Bunya-Jido의 핵심입니다.

1. Bunya-Jido가 저장소를 정적으로 스캔합니다.
2. 코딩 에이전트가 저장소와 스캔 결과를 읽습니다.
3. 에이전트가 구성요소 문서, 워크플로우 문서, blueprint, agent map을 작성합니다.
4. Bunya-Jido가 작성된 파일을 검증합니다.
5. 검증된 blueprint를 단일 HTML 지도로 렌더링합니다.

저장소 루트에서 코딩 에이전트에게 다음 지시를 줍니다.

```text
Run `bunya-jido prepare --root . --quiet` if needed, then read and execute `.bunya-jido/BUNYA_JIDO_BLUEPRINT_PROMPT.md`. Create or refresh `.bunya-jido/COMPONENTS.md`, `.bunya-jido/WORKFLOWS.md`, `.bunya-jido/bunya-jido.blueprint.json`, and `.bunya-jido/bunya-jido.agent-map.json`; run `bunya-jido validate-blueprint --root .` and `bunya-jido validate-agent-map --root .`; fix errors and reduce classification warnings when practical; then run `bunya-jido build --root . --out bunya-jido.html`; confirm the HTML path and say `ready`.
```

이 프롬프트는 마지막에 `bunya-jido.html`까지 생성합니다. Blueprint를 고친 뒤 직접 다시 만들고 싶으면 다음 명령을 실행하면 됩니다.

```bash
bunya-jido build --root . --out bunya-jido.html
```

그 다음 `bunya-jido.html`을 브라우저에서 열면 됩니다.

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

검증:

```bash
bunya-jido validate-agent-map --root .
```

### `bunya-jido-static-scan.json`

LLM 없이 결정적으로 생성되는 정적 스캔 결과입니다.

파일, 모듈, import, 문서, 설정, 런타임 산출물, 외부 API 힌트를 담습니다. 코딩 에이전트가 blueprint를 만들 때 raw evidence로 사용합니다.

## HTML 지도

생성된 HTML 지도에는 다음 기능이 들어갑니다.

- 책임 영역별 plane cluster
- 노드와 엣지 필터링
- 선택한 노드 주변만 보는 local graph focus
- 근거 파일과 설명을 보여주는 evidence panel
- 워크플로우와 작업 경로를 보여주는 path preset
- PNG와 JSON export
- blueprint가 제공하는 경우 overview/detail 계층 전환

지도의 근거는 저장소의 코드, 문서, 설정, 테스트, 런타임 산출물, 검증된 blueprint 파일에 있습니다. Bunya-Jido는 그 근거를 보기 좋은 형태로 투영합니다.

## 코딩 에이전트와 함께 쓰기

Blueprint와 agent map이 있으면 특정 작업에 맞는 handoff를 만들 수 있습니다.

```bash
bunya-jido context --root . --task "modify provider behavior" --out .bunya-jido/CONTEXT.md
```

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

이 파일들은 코딩 에이전트에게 작업을 맡기기 전에 붙여넣거나 첨부하기 좋습니다.

## 에이전트용 가이드 스니펫

Codex, Claude Code, Cursor, Cline 스타일 환경에서 사용할 수 있는 instruction snippet을 생성할 수 있습니다.

```bash
bunya-jido install-agent-guides --root . --agent all
```

생성 위치:

```text
.bunya-jido/agent-guides/
```

루트의 `AGENTS.md`, `CLAUDE.md`, Cursor rules, Cline rules를 자동으로 덮어쓰지는 않습니다. 해당 도구가 항상 Bunya-Jido 지침을 참고하게 만들고 싶을 때만 필요한 부분을 옮기면 됩니다.

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

## 라이선스

MIT.
