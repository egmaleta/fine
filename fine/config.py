from dataclasses import dataclass


@dataclass
class Config:
    max_op_precedence: int
    min_op_precedence: int
    default_op_precedence: int
    assoc_is_left: bool

    ignore_name: str

    def __post_init__(self):
        assert (
            self.min_op_precedence
            <= self.default_op_precedence
            < self.max_op_precedence
        )


DEFAULT_CONFIG = Config(
    max_op_precedence=10,
    min_op_precedence=0,
    default_op_precedence=9,
    assoc_is_left=True,
    ignore_name="_",
)
