from dataclasses import dataclass


@dataclass
class Config:
    max_op_precedence: int
    min_op_precedence: int

    ignore_name: str

    def __post_init__(self):
        assert self.max_op_precedence > self.min_op_precedence


DEFAULT_CONFIG = Config(
    max_op_precedence=10,
    min_op_precedence=0,
    ignore_name="_",
)
