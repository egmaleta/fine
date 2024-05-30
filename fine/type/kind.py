from dataclasses import dataclass


class Kind:
    pass


@dataclass
class AtomKind(Kind):
    def __repr__(self):
        return "*"


ATOM = AtomKind()


@dataclass
class FunctionKind(Kind):
    kind_args: list[Kind]

    def __post_init__(self):
        assert len(self.kind_args) >= 2

    @property
    def left(self):
        return self.kind_args[0]

    @property
    def right(self):
        match self.kind_args[1:]:
            case [kind]:
                return kind
            case kinds:
                return FunctionKind(kinds)

    def __repr__(self):
        return " -> ".join(
            f"({kind})" if isinstance(kind, FunctionKind) else repr(kind)
            for kind in self.kind_args
        )
