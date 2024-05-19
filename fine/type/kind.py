class Kind:
    def __eq__(self, other):
        return isinstance(other, type(self))


class AtomKind(Kind):
    def __repr__(self):
        return "Type"

    def __len__(self):
        return 1


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

    def __len__(self):
        return 1 + len(self.right)


ATOM = AtomKind()


def apply(f: Kind, args: list[Kind]):
    assert isinstance(f, FunctionKind)
    assert 0 < len(args) < len(f)

    k = f
    for arg in args:
        assert f.left == arg
        k = f.right

    return k
