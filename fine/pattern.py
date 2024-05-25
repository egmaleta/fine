from dataclasses import dataclass, field
from lark.lexer import Token


class Pattern:
    pass


@dataclass
class CapturePattern(Pattern):
    name: Token


@dataclass
class DataPattern(Pattern):
    tag: Token
    patterns: list[CapturePattern] = field(default_factory=lambda: [])


@dataclass
class LiteralPattern(Pattern):
    value: Token
