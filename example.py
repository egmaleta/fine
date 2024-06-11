from fine.ast import Int
from fine.check import NameChecker
from fine.config import DEFAULT_CONFIG
from fine.eval import Evaluator
from fine.parser import parse
from fine.transform import Transformer
from fine.utils import Env


checker = NameChecker(DEFAULT_CONFIG)
transformer = Transformer(DEFAULT_CONFIG)
evaluator = Evaluator(
    {
        "add": lambda x, y: Int(str(int(x.value) + int(y.value))),
        "sub": lambda x, y: Int(str(int(x.value) - int(y.value))),
        "times": lambda x, y: Int(str(int(x.value) * int(y.value))),
        "div": lambda x, y: Int(str(int(x.value) // int(y.value))),
        "mod": lambda x, y: Int(str(int(x.value) % int(y.value))),
        "pow": lambda x, y: Int(str(int(x.value) ** int(y.value))),
    }
)

SOURCE_CODE = """
# int
infixl 6 +
let a + b = #internal add

infixl 6 -
let a - b = #internal sub

infixl 7 *
let a * b = #internal times

infixl 7 /
let a / b = #internal div

infixl 7 %
let a % b = #internal mod

infixr 8 ^
let a ^ b = #internal pow

# list

data List(a) {
    Nil
    Cons: a -> List(a)
}

infixr 5 ::
let (::) = Cons

let map(f, list) = match list {
    Nil -> Nil
    Cons(head, tail) -> f(head) :: map(f, tail)
}

let main =
    let numbers = 1 :: 2 :: 3 :: 4 :: 5 :: Nil
    let squared(x) = x ^ 2
    in map(squared, numbers)
"""

if __name__ == "__main__":
    program = parse(SOURCE_CODE)
    assert program is not None

    checker.check(program, Env())

    program = transformer.transform(program, Env())

    entrypoints = ["main"]
    values = evaluator.eval(program, Env(), entrypoints)

    for entry, value in zip(entrypoints, values):
        print(entry, "is", value)
