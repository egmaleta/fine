from abc import ABC, abstractmethod


class AST(ABC):
    pass


class Expr(AST):
    @property
    @abstractmethod
    def lineno(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def index(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def end(self) -> int:
        raise NotImplementedError()
