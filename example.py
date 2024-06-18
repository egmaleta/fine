from fine.ast import Int
from fine.check import SemanticChecker
from fine.config import DEFAULT_CONFIG
from fine.eval import Evaluator, try_pythonize
from fine.parser import parse
from fine.transform import Transformer


SOURCE_CODE = """
infixl 6 + -
infixl 7 * / %
infixr 8 ^ **

let a + b = %internal add
let a - b = %internal sub
let a * b = %internal times
let a / b = %internal div
let a % b = %internal mod
let a ^ b = %internal pow
let (**) = (^)

type List a {
    | Nil: List a
    | Cons: a -> List a -> List a
}

infixr 5 ::
let (::) = Cons

let map: forall a b. (a -> b) -> List a -> List b
let map f list = match list {
    | Nil -> Nil
    | Cons head tail -> f head :: map f tail
}

let main =
    let numbers = 1 :: 2 :: 3 :: 4 :: 5 :: Nil
    let squared x = x ** 2
    in map squared numbers
"""


def pipeline(source, config):
    program = parse(source)
    assert program is not None

    checker = SemanticChecker(config)
    checker.check(program)

    transformer = Transformer(config)
    program = transformer.transform(program)

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
    env = evaluator.eval(program)

    return lambda ep: try_pythonize(env.get(ep)[0])


if __name__ == "__main__":
    eval = pipeline(SOURCE_CODE, DEFAULT_CONFIG)

    entrypoints = ["main"]
    for ep in entrypoints:
        value = eval(ep)
        print(ep, "=", value)
