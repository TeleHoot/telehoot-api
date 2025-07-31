import functools
import inspect
import logging
from collections.abc import Callable, Sized
from typing import Any


def log_operation(func: Callable) -> Callable:
    """
    An async decorator that automatically logs the start, successful completion, and
    exceptions for the operation.

    Has to be used with service or repository methods.

    Returns:
         The result of the decorated async function.
    """

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self or not hasattr(self, "logger"):
            default_logger = logging.getLogger(__name__)
            default_logger.warning("Decorator used without proper instance logger")
            return await func(*args, **kwargs)

        context: dict[str, Any] = {}

        try:
            context.update(self.context)
        except AttributeError as e:
            self.logger.warning(
                "Failed to get context",
                extra={"exception": e.__class__.__name__},
                exc_info=True,
            )

        context.update({"operation": func.__name__})

        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()

        excluded_params = {"self", "session", "uow"}

        additional_context = {}
        for arg_name, arg_value in bound_args.arguments.items():
            if arg_name.lower() in excluded_params:
                continue
            if isinstance(arg_value, Sized) and not isinstance(arg_value, str):
                additional_context[f"{arg_name}_count"] = len(arg_value)
            else:
                additional_context[arg_name] = arg_value

        start_msg = "Starting operation"
        success_msg = "Operation completed successfully"
        error_msg = "Operation failed"

        self.logger.debug(start_msg, extra={**context, **additional_context})
        try:
            result = await func(self, *args, **kwargs)
            self.logger.info(success_msg, extra=context)
            return result
        except Exception as e:
            context.update({"exception": e.__class__.__name__})
            self.logger.exception(error_msg, extra=context)
            raise

    return wrapper
