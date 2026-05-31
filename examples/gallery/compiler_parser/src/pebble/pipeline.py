from dataclasses import dataclass


@dataclass(frozen=True)
class SyntaxTree:
    name: str


@dataclass(frozen=True)
class IntermediateForm:
    instruction: str


def parse(source: str) -> SyntaxTree:
    return SyntaxTree(name=source.strip())


def lower(tree: SyntaxTree) -> IntermediateForm:
    return IntermediateForm(instruction=f"LOAD {tree.name}")


def emit(ir: IntermediateForm) -> str:
    return ir.instruction + "\nHALT"


def compile_source(source: str) -> str:
    return emit(lower(parse(source)))
