from .type import *


def create_typeapp(f: TypeConstant | TypeVar, args: list[Type]) -> TypeApp:
    assert len(args) > 0

    app = f
    for arg in args:
        app = TypeApp(app, arg)

    return app
