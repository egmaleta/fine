from dataclasses import dataclass, field

from .utils import String


class Pattern:
    pass


@dataclass
class CapturePattern(Pattern):
    name: String


@dataclass
class DataPattern(Pattern):
    tag: String
    patterns: list[CapturePattern] = field(default_factory=lambda: [])


@dataclass
class LiteralPattern(Pattern):
    value: String
