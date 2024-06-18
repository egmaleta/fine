from dataclasses import dataclass, field

from .utils import String


type Pattern = CapturePattern | DataPattern | LiteralPattern


@dataclass
class CapturePattern:
    name: String


@dataclass
class DataPattern:
    tag: String
    patterns: list[CapturePattern] = field(default_factory=lambda: [])


@dataclass
class LiteralPattern:
    value: String
