# Contributing To Bunya-Jido

Thanks for contributing. Bunya-Jido treats repository maps as inspectable
claims: changes should make it easier to see evidence and uncertainty, not
quietly strengthen what the product promises.

## Development Setup

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m bunya_jido diagnose --root . --require-grounded --json
```

The committed self-map is a grounded semantic fixture. A clean contribution
must keep that release-gate diagnostic grounded unless the purpose of the
change is to update its evidence and generated gallery artifact.

## Choose The Contract You Are Changing

State one primary contract in an issue or pull request:

- deterministic scanner coverage
- semantic blueprint grounding or publication behavior
- validated agent-map routes and generated context
- viewer comprehension and evidence presentation
- public documentation or release behavior

## Required Evidence

| Change | Expected Verification |
|---|---|
| Scanner support claim | Add or update a small fixture, assertions for evidence/confidence/limits, and `docs/SCANNER_COVERAGE.md` |
| Grounding or agent-route behavior | Add blocked and grounded characterization tests; validate the self-map |
| Viewer or graph presentation | Update focused tests and inspect a generated HTML artifact; update gallery output when the committed example changes |
| Release or documentation | Keep compatibility/limitations accurate and run the release-gate diagnostic |

Do not include real credentials or private repository content in fixtures or
issues. Provider-name detection is heuristic evidence and needs a
false-positive case before its claims expand.

## Pull Request Checklist

```bash
python -m unittest discover -s tests
python -m compileall -q src tests
python -m bunya_jido validate-blueprint --root .
python -m bunya_jido validate-agent-map --root .
python -m bunya_jido diagnose --root . --require-grounded --json
```

When viewer or committed gallery behavior changes, regenerate and inspect the
offline demo following `docs/gallery.md`. Release publication is maintained
through `docs/RELEASING.md`.
