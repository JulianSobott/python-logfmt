import logging
import pytest

from logfmt import LogFmtFormatter, LogContext, CallableLogContext


from dataclasses import dataclass


class InMemoryHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.last_line = None

    def emit(self, record):
        msg = self.format(record)
        self.lines.append(msg)
        self.last_line = msg

    def clear(self):
        self.lines = []
        self.last_line = None


@pytest.fixture
def logger_handler():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = LogFmtFormatter(fmt="level=%(levelname)s msg=%(message)s %(mdc)s")
    handler = InMemoryHandler()
    handler.setFormatter(formatter)
    logger.handlers = [handler]
    logger.propagate = False
    return logger, handler


def test_formatting(logger_handler):
    logger, handler = logger_handler
    logger.info("Hello World", extra={"foo": "bar"})
    assert handler.last_line == 'level=INFO msg="Hello World" foo=bar'


def test_extra(logger_handler):
    logger, handler = logger_handler
    logger.info("Hello World", extra={"foo": "bar"})
    assert handler.last_line == 'level=INFO msg="Hello World" foo=bar'


def test_log_context_dict(logger_handler):
    logger, handler = logger_handler
    with LogContext({"foo": "bar"}):
        logger.info("Hello World")
    assert handler.last_line == 'level=INFO msg="Hello World" foo=bar'


def test_ignore_dunder(logger_handler):
    logger, handler = logger_handler
    logger.info("Hello World", extra={"__foo": "bar"})
    assert handler.last_line == 'level=INFO msg="Hello World" '


def test_log_context_kwargs(logger_handler):
    logger, handler = logger_handler
    with LogContext(foo="bar"):
        logger.info("Hello World")
    assert handler.last_line == 'level=INFO msg="Hello World" foo=bar'


def test_log_context_nested(logger_handler):
    logger, handler = logger_handler
    with LogContext(foo="bar"):
        with LogContext(x="baz"):
            logger.info("Hello World")
            assert handler.last_line == 'level=INFO msg="Hello World" foo=bar x=baz'
        logger.info("Hello World")
        assert handler.last_line == 'level=INFO msg="Hello World" foo=bar'
    logger.info("Hello World")
    # getting rid of the last whitespace is a bit tricky, so I just leave it
    assert handler.last_line == 'level=INFO msg="Hello World" '


def test_static_function_decorator(logger_handler):
    logger, handler = logger_handler

    @LogContext(foo="bar")
    def foo():
        logger.info("Hello World")

    foo()
    assert handler.last_line == 'level=INFO msg="Hello World" foo=bar'


def test_function_decorator_sub_attribute(logger_handler):
    logger, handler = logger_handler

    @dataclass
    class Foo:
        name: str

    @CallableLogContext("c.name")
    def foo(c: Foo):
        logger.info("Hello World")

    foo(Foo("Tom"))
    assert handler.last_line == 'level=INFO msg="Hello World" c.name=Tom'


def test_function_decorator_alias_deep_sub_attribute(logger_handler):
    logger, handler = logger_handler

    @dataclass
    class Foo:
        name: str

    @dataclass
    class Bar:
        foo: Foo

    @CallableLogContext(name="c.foo.name")
    def foo(c: Bar):
        logger.info("Hello World")

    foo(Bar(Foo("Jerry")))
    assert handler.last_line == 'level=INFO msg="Hello World" name=Jerry'


def test_function_decorator_sub_non_attribute(logger_handler):
    logger, handler = logger_handler

    @dataclass
    class Foo:
        name: str

    @CallableLogContext("c.non_existing")
    def foo(c: Foo):
        logger.info("Hello World")

    foo(Foo("Tom"))
    assert handler.last_line == 'level=INFO msg="Hello World" c.non_existing=None'


def test_function_decorator_args(logger_handler):
    logger, handler = logger_handler

    @CallableLogContext("name")
    def foo(name: str):
        logger.info("Hello World")

    foo("Tom")
    assert handler.last_line == 'level=INFO msg="Hello World" name=Tom'


def test_function_decorator_args_log_all(logger_handler):
    logger, handler = logger_handler

    @CallableLogContext()
    def foo(name: str):
        logger.info("Hello World")

    foo("Tom")
    assert handler.last_line == 'level=INFO msg="Hello World" name=Tom'


def test_function_decorator_args_log_all_complex(logger_handler):
    logger, handler = logger_handler

    @CallableLogContext()
    def foo(name: str, *args, **kwargs):
        logger.info("Hello World")

    foo("Tom", 1, 2, a=1, b=2)
    assert (
        handler.last_line
        == 'level=INFO msg="Hello World" name=Tom args="(1, 2)" kwargs="{\'a\': 1, \'b\': 2}"'
    )


def test_multiple_threads(logger_handler):
    logger, handler = logger_handler
    import threading

    def foo(x):
        with LogContext(foo=x):
            logger.info("Hello World")

    threads = []
    for i in range(5):
        t = threading.Thread(target=foo, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    for i in range(5):
        assert f'level=INFO msg="Hello World" foo={i}' in handler.lines


def test_exception(logger_handler):
    logger, handler = logger_handler
    try:
        raise Exception("Test")
    except Exception:
        logger.exception("Hello World")
    assert 'level=ERROR msg="Hello World" \nexception="\n' in handler.last_line
    assert 'Exception: Test"' in handler.last_line


def test_stack_info(logger_handler):
    logger, handler = logger_handler
    logger.info("Hello World", stack_info=True)
    assert 'level=INFO msg="Hello World" \nstack="\n' in handler.last_line
    assert 'logger.info(\\"Hello World\\", stack_info=True)"' in handler.last_line
