import logging
import threading
import time
from contextlib import contextmanager
import collections.abc
import inspect

__all__ = ["new_log_context", "callable_context", "LogFmtFormatter", "LogContext", "CallableLogContext"]


logging._mdc = threading.local()


def get_mdc_fields():
    result = {}
    contexts = vars(logging._mdc)
    for context_id in contexts:
        result.update(**vars(contexts[context_id]))
    return result


DEFAULT_LOGFMT_FORMAT = "ts=%(asctime)s lvl=%(levelname)s msg=%(message)s %(mdc)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class LogFmtFormatter(logging.Formatter):

    ALL_DEFAULT_KEYS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }
    EXTRA_MDC_KEY = "mdc"
    BASE_TYPES = (str, int, float, bool, type(None))

    def __init__(
        self,
        fmt=DEFAULT_LOGFMT_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
        style="%",
        *args,
        **kwargs,
    ):
        super().__init__(fmt, datefmt, style, *args, **kwargs)
        if self.EXTRA_MDC_KEY in fmt:
            self.add_mdcs = True
            included_keys = set()
            for key in self.ALL_DEFAULT_KEYS:
                if f"%({key})" in self._fmt:
                    included_keys.add(key)
            self.excluded_keys = self.ALL_DEFAULT_KEYS - set(included_keys)
            self.include_keys = included_keys
        else:
            self.add_mdcs = False

    def format(self, record):
        record.msg = self._format_value(record.msg)
        if self.add_mdcs:
            key_values = {}
            for attr, value in record.__dict__.items():
                if attr not in self.ALL_DEFAULT_KEYS:
                    key_values[attr] = self._format_value(value)
            for key, value in get_mdc_fields().items():
                key_values[key] = self._format_value(value)
            if key_values:
                extra_args = " ".join([f"{k}={v}" for k, v in key_values.items()])
            else:
                extra_args = ""
            setattr(record, self.EXTRA_MDC_KEY, extra_args)
        return super().format(record)

    def _format_value(self, value):
        if isinstance(value, self.BASE_TYPES):
            formatted = value
        else:
            formatted = repr(value)
        try:
            if (
                " " in formatted
                or '"' in formatted
                or "\n" in formatted
                or "\t" in formatted
            ):
                formatted.replace('"', r"\"")
                formatted = f'"{formatted}"'

        except Exception:
            pass
        return formatted


@contextmanager
def new_log_context(*args, **kwargs):
    if (
        args
        and len(args) == 1
        and isinstance(args[0], collections.abc.Mapping)
        and args[0]
    ):
        kwargs = args[0]

    context_id = "mdc-{thread}-{context}".format(
        thread=threading.current_thread().ident, context=time.time()
    )

    setattr(logging._mdc, context_id, threading.local())

    context = getattr(logging._mdc, context_id)

    for key, value in kwargs.items():
        setattr(context, key, value)

    try:
        yield context
    finally:
        delattr(logging._mdc, context_id)


def callable_context(*args: str):
    args_to_watch = set(args)
    log_all = not args_to_watch

    def decorator(func):
        signature = inspect.signature(func)

        def wrapper(*args, **kwargs):
            bound_arguments = signature.bind(*args, **kwargs)
            if not log_all:
                ctx = {arg: bound_arguments.arguments[arg] for arg in args_to_watch}
            else:
                ctx = bound_arguments.arguments
            with new_log_context(ctx):
                return func(*args, **kwargs)

        return wrapper

    return decorator


LogContext = new_log_context
CallableLogContext = callable_context
