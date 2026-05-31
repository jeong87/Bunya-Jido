from dataclasses import dataclass


@dataclass(frozen=True)
class FormatOptions:
    separator: str = "-"
    width: int = 24


def slugify(text: str, options: FormatOptions = FormatOptions()) -> str:
    words = text.lower().split()
    return options.separator.join(words)


def wrap_label(text: str, options: FormatOptions = FormatOptions()) -> str:
    return text if len(text) <= options.width else text[: options.width - 3] + "..."


USAGE_EXAMPLES = {
    "slug": slugify("Clear Text"),
    "label": wrap_label("A compact public helper surface"),
}
