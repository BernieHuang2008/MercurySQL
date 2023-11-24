from typing import Any


class Test:
    def __init__(self, x):
        self.x = x

    def __getattribute__(self, __name: str) -> Any:
        if __name == 'x':
            return object.__getattribute__(self, __name)


if __name__ == '__main__':
    t = Test(1)
    print(t.x)
    print(t.y)
