from dataclasses import dataclass


class Kind:
    pass


@dataclass
class AtomKind(Kind):
    def __repr__(self):
        return "*"


@dataclass
class FunctionKind(Kind):
    left: Kind
    right: Kind

    def __repr__(self):
        l = f"({self.left})" if isinstance(self.left, FunctionKind) else self.left
        return f"{l} -> {self.right}"


ATOM = AtomKind()
