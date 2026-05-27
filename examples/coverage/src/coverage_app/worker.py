import openai

from coverage_app.core import normalize


def build(value: str) -> str:
    return normalize(value)


def main() -> None:
    build("ready")
