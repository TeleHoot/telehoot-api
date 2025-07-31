from src.core import utils


def test_singleton():
    @utils.decorators.Singleton
    class DecoratedClass:
        def __init__(self, value):
            self.value = value

    first = DecoratedClass("first")
    second = DecoratedClass("second")

    assert first is second
    assert second.value == "first"

    second.value = "newvalue"

    assert first is second
    assert first.value == "newvalue"
