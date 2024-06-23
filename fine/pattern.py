from dataclasses import dataclass, field

from .utils import String


type Pattern = CapturePattern | DataPattern | FloatPattern | IntPattern | StrPattern


@dataclass
class CapturePattern:
    name: String


@dataclass
class DataPattern:
    tag: String
    patterns: list[CapturePattern] = field(default_factory=lambda: [])


@dataclass
class FloatPattern:
    value: String


@dataclass
class IntPattern:
    value: String


@dataclass
class StrPattern:
    value: String
