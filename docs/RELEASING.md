# Public Alpha Release Guide

Bunya-Jido is prepared for a public alpha release. Release readiness means its
published package and demo are gated by real grounding checks; it does not mean
the semantic map automatically proves an architecture correct.

## Compatibility And Limits

- Supported Python versions are `3.10`, `3.11`, and `3.12`.
- The CI compatibility matrix exercises Ubuntu with Python `3.10`-`3.12`,
  and Windows and macOS with Python `3.12`.
- The public interfaces under alpha review are the CLI commands, the generated
  offline HTML artifact, and the `.bunya-jido/` blueprint and agent-map flow.
- Python scanning is the strongest deterministic code surface. Exact scanner
  coverage and JS/TS limitations are recorded in
  [`SCANNER_COVERAGE.md`](SCANNER_COVERAGE.md).
- `grounded` indicates that required evidence and route validation checks pass.
  It is not an automated proof that an interpretation is complete.

## Version Policy

The package uses semantic versioning for public CLI and artifact contracts:

- Patch releases fix behavior without intentionally changing established
  command or schema expectations.
- Minor releases add compatible commands, viewer capabilities, or documented
  scanner evidence.
- Major releases are reserved for incompatible public contract changes.

Before `1.0.0`, a minor release may revise alpha contracts, but the change must
be called out in `CHANGELOG.md`, documentation, and tests. Keep the version in
`pyproject.toml` and `src/bunya_jido/__init__.py` identical.

## Release Gate

Run from a clean checkout:

```bash
python -m pip install -e . build twine
python -m unittest discover -s tests
python -m compileall -q src tests
python -m bunya_jido validate-blueprint --root .
python -m bunya_jido validate-agent-map --root .
python -m bunya_jido diagnose --root . --require-grounded --json
python -m bunya_jido evaluate-agent-utility --root . --require-pass --json
python -m bunya_jido check-stale --root . --git-diff origin/main...HEAD --require-reviewed
python -m build
python -m twine check dist/*
```

If the viewer or semantic self-map changed, regenerate and visually inspect
`docs/demo.html` and its screenshot using the commands in
[`gallery.md`](gallery.md) before releasing.

The stale-map gate does not rewrite semantic output. It requires a reviewed
blueprint, agent-map, or `.bunya-jido/MAP_REVIEW.md` note when files covered
by the committed `stale_map_policy` change; CI runs the same gate for pushes
and pull requests.

The agent-utility gate checks the committed bounded-context acceptance cases.
Its pass status supports a context-output contract claim only; behavioral
claims about live coding agents require the observation protocol in
[`AGENT_UTILITY_EVALUATION.md`](AGENT_UTILITY_EVALUATION.md).

## PyPI Trusted Publishing

The release workflow is `.github/workflows/publish.yml`. It builds
distributions in an unprivileged verification job, requires the GitHub Release
tag to match `v<package-version>`, runs tests plus the grounded diagnostic, and
publishes in a separate `pypi` environment using OpenID Connect trusted
publishing. It does not require a stored PyPI API token.

Maintainers must complete one-time repository and PyPI setup:

1. Create a GitHub environment named `pypi`, ideally with required reviewer
   approval.
2. Configure the `bunya-jido` project on PyPI with a GitHub Trusted Publisher
   for repository `jeong87/Bunya-Jido`, workflow file `publish.yml`, and
   environment `pypi`.
3. Update `CHANGELOG.md` and both package version declarations.
4. Merge the release commit, then publish a GitHub Release tagged
   `v<package-version>`. The workflow uploads the distributions only after its
   validation job succeeds.

## Demo And Gallery Publishing

The published demo is committed under `docs/`. The
`.github/workflows/pages.yml` workflow deploys that directory when dispatched
by a maintainer after reviewed changes merge. It runs the semantic self-map
tests and the strict grounded diagnostic before uploading the Pages artifact.

This design deliberately publishes the reviewed committed demo, rather than
generating an unreviewed semantic map during deployment.

Maintainers must select GitHub Actions as the repository's Pages build and
deployment source before the first workflow deployment.
