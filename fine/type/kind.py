from dataclasses import dataclass


class Kind:
    pass


@dataclass
class AtomKind(Kind):
    def __repr__(self):
        return "*"


ATOM_KIND = AtomKind()


@dataclass
class FunctionKind(Kind):
    args: list[Kind]

    def __post_init__(self):
        assert len(self.args) >= 2

    @property
    def left(self):
        return self.args[0]

    @property
    def right(self):
        match self.args[1:]:
            case [kind]:
                return kind
            case kinds:
                return FunctionKind(kinds)

    def __repr__(self):
        return " -> ".join(
            f"({kind})" if isinstance(kind, FunctionKind) else repr(kind)
            for kind in self.args
        )
