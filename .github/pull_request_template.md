## Product Contract

Describe whether this changes documentation, grounding, agent-map parity,
viewer comprehension, scanner coverage, or release behavior.

## Evidence And Limits

- What repository evidence or fixture supports the change?
- Which claim remains intentionally limited?
- Does artifact mode or grounding status change?

## Verification

- [ ] `python -m unittest discover -s tests`
- [ ] `python -m bunya_jido diagnose --root . --require-grounded --json`
- [ ] `python -m bunya_jido check-stale --root . --git-diff origin/main...HEAD --require-reviewed` reviewed when tracked repository files change
- [ ] Generated HTML inspected when viewer, semantic graph, or gallery output changes
- [ ] Coverage matrix updated when scanner support claims change
