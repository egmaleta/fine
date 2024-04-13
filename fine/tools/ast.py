from abc import ABC, abstractmethod


class AST(ABC):
    pass


class Expr(AST):
    @abstractmethod
    def start_pos(self) -> tuple[int, int]:
        raise NotImplementedError()

    @abstractmethod
    def end_pos(self) -> tuple[int, int]:
        raise NotImplementedError()
