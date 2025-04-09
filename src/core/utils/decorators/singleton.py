import threading
from typing import TypeVar

T = TypeVar("T")


def Singleton[T](cls: type[T]) -> type:
    """A thread-safe singleton decorator.

    Respects the original class's __new__ and __init__ methods

    Returns:
        Singleton

    """
    instance = None
    lock = threading.Lock()

    def __new__(cls_new, *args, **kwargs) -> T:  # noqa: N807
        nonlocal instance, lock
        if instance is None:
            with lock:
                if instance is None:
                    instance = super(cls_new, cls_new).__new__(cls_new)
                    super(cls_new, instance).__init__(*args, **kwargs)
        return instance

    def __init__(self, *args, **kwargs):  # noqa: N807
        """Prevents re-initialization after first creation.

        __new__ always returns the same instance,
        but __init__ would normally be called repeatedly with different arguments
        By overriding __init__ we ensure that initialization happens only once inside __new__

        Example:
        @Singleton
        class Settings:
            def __init__(self, value):
                self.value = value

        s1 = Settings("first")
        s2 = Settings("second")
        print(s1 is s2)  # True
        print(s2.value)  # "first"

        """

    return type(
        cls.__name__,
        (cls,),
        {
            "__new__": __new__,
            "__init__": __init__,
        },
    )
