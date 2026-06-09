# Bunya-Jido 0.5.0 Alpha 2

This is a small public-alpha packaging fix after `0.5.0a1`.

## What Changed

- The README hero image now uses the public GitHub Pages URL:
  `https://jeong87.github.io/Bunya-Jido/assets/self-map-grounded.png`.
- This fixes the PyPI project page rendering, where the previous relative
  `docs/assets/self-map-grounded.png` path appeared as a broken image.

## Install

```bash
python -m pip install --pre bunya-jido
bunya-jido --version
```

Expected version:

```text
bunya-jido 0.5.0a2
```

## Notes

No runtime behavior, CLI contract, semantic-map format, benchmark result, or
agent-context behavior changed from `0.5.0a1`.
