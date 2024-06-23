from dataclasses import dataclass

from .utils import String


type Pattern = CapturePattern | DataPattern | PolyDataPattern | FloatPattern | IntPattern | StrPattern


@dataclass
class CapturePattern:
    name: String


@dataclass
class DataPattern:
    tag: String


@dataclass
class PolyDataPattern:
    tag: String
    patterns: list[CapturePattern]


@dataclass
class FloatPattern:
    value: String


@dataclass
class IntPattern:
    value: String


@dataclass
class StrPattern:
    value: String
