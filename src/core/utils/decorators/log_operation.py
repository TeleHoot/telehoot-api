import functools
import inspect
import logging
from collections.abc import Callable, Sized
from typing import Any


def log_operation(func: Callable) -> Callable:  # noqa: C901
    """
    An async decorator that automatically logs the start, successful completion, and
    exceptions for the operation.

    Has to be used with service or repository methods.

    Returns:
         The result of the decorated async function.
    """

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):  # noqa: C901
        if not self or not hasattr(self, "logger"):
            default_logger = logging.getLogger(__name__)
            default_logger.warning("Decorator used without proper instance logger")
            return await func(*args, **kwargs)

        context: dict[str, Any] = {}
        layer = "service"

        try:
            if hasattr(self, "repo_operation_context"):
                context_method = self.repo_operation_context
                if callable(context_method):
                    repo_context = context_method()
                    if isinstance(repo_context, dict):
                        context.update(repo_context)
                        layer = "repository"
        except Exception as e:  # noqa: BLE001
            self.logger.warning("Failed to get repo context", extra=repr(e))

        context.update({
            "class_name": self.__class__.__name__,
            "layer": layer,
            "operation": func.__name__,
        })

        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()

        excluded_params = {"self", "session"}

        for arg_name, arg_value in bound_args.arguments.items():
            if arg_name.lower() in excluded_params:
                continue
            if isinstance(arg_value, Sized) and not isinstance(arg_value, str):
                context[f"{arg_name}_count"] = len(arg_value)
            else:
                context[arg_name] = arg_value

        if layer == "repository":
            start_msg = "Starting repository operation"
            success_msg = "Repository operation completed successfully"
        else:
            start_msg = "Starting service operation"
            success_msg = "Service operation completed successfully"

        self.logger.debug(start_msg, extra=context)
        try:
            result = await func(self, *args, **kwargs)
            self.logger.info(success_msg, extra=context)
            return result
        except Exception as e:
            context.update({"exception": e.__class__.__name__})
            self.logger.exception("Operation failed", extra=context, exc_info=e)
            raise

    return wrapper
