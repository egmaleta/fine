from dataclasses import dataclass


type Kind = AtomKind | FunctionKind


@dataclass
class AtomKind:
    def __repr__(self):
        return "*"


@dataclass
class FunctionKind:
    left: Kind
    right: Kind

    @classmethod
    def from_args(cls, args: list[Kind]):
        match args:
            case [kind]:
                return cls(kind, ATOM_KIND)
            case [kind, *rest]:
                return cls(kind, cls.from_args(rest))

    def __repr__(self):
        left_repr = (
            f"({self.left})" if isinstance(self.left, FunctionKind) else repr(self.left)
        )
        return f"{left_repr} -> {self.right}"


ATOM_KIND = AtomKind()
