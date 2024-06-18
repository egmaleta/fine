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
    left: Kind
    right: Kind

    @classmethod
    def from_args(cls, args: list[Kind]):
        match args:
            case [kind]:
                return cls(kind, ATOM)
            case [kind, *rest]:
                return cls(kind, cls.from_args(rest))

    def __repr__(self):
        left_repr = (
            f"({self.left})" if isinstance(self.left, FunctionKind) else repr(self.left)
        )
        return f"{left_repr} -> {self.right}"
