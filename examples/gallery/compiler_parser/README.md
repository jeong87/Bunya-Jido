# Pebble Compiler

`compile_source` sends source text through `parse`, `lower`, and `emit` in
that order. Each stage produces the form accepted by the next stage.

This miniature is intentionally a transformation pipeline: ordered playback is
grounded in the implementation and its documented public entrypoint.
