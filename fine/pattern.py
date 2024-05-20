from dataclasses import dataclass

from .utils import String


class Pattern:
    pass


class CapturePattern(Pattern):
    name: String


@dataclass
class DataPattern(Pattern):
    tag: String
    patterns: list[CapturePattern] = []


@dataclass
class LiteralPattern(Pattern):
    value: String
