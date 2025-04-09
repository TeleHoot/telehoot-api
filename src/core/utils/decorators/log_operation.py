import functools
import inspect
from typing import cast


def log_operation(func):
    """
    An async decorator that automatically logs the start, successful completion, and
    exceptions for the operation.

    Returns:
         The result of the decorated async function.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Assuming that args[0] is 'self'
        instance = args[0]
        context = dict()

        if hasattr(instance, "repo_operation_context") and callable(
            instance.repo_operation_context
        ):
            repo_context: dict = cast(dict, instance.repo_operation_context(func.__name__))
            context.update(repo_context)
            layer = "repository"
        else:
            context.update({"operation": func.__name__})
            layer = "service"

        context.update({"layer": layer, "class": instance.__class__.__name__})

        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        for key, value in bound_args.arguments.items():
            if key.lower() in {"self", "session"}:
                continue
            if isinstance(value, list):
                context[f"{key}_count"] = len(value)
            else:
                context[key] = value

        if layer == "repository":
            start_msg = "Starting repository operation"
            success_msg = "Repository operation completed successfully"
        else:
            start_msg = "Starting service operation"
            success_msg = "Service operation completed successfully"

        instance.logger.debug(start_msg, extra=context)
        try:
            result = await func(*args, **kwargs)
            instance.logger.info(success_msg, extra=context)
            return result
        except Exception as e:
            context.update({"exception": e.__class__.__name__, "error_message": repr(e)})
            instance.logger.exception("Operation failed", extra=context)
            raise

    return wrapper
