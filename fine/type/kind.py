class Kind:
    def __eq__(self, other):
        return isinstance(other, type(self))


class AtomKind(Kind):
    def __repr__(self):
        return "Type"


class FunctionKind(Kind):
    def __init__(self, left: Kind, right: Kind):
        self.left = left
        self.right = right

    def __repr__(self):
        l = f"({self.left})" if isinstance(self.left, FunctionKind) else self.left
        return f"{l} -> {self.right}"

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and self.left == other.left
            and self.right == other.right
        )


ATOM = AtomKind()


def apply(f: FunctionKind, arg: Kind):
    assert f.left == arg
    return f.right
