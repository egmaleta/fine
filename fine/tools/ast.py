from abc import ABC, abstractmethod


class AST(ABC):
    @abstractmethod
    def start_pos(self) -> tuple[int, int]:
        raise NotImplementedError()

    @abstractmethod
    def end_pos(self) -> tuple[int, int]:
        raise NotImplementedError()


class Expr(AST):
    pass
