# Logfmt for python

Logging Formatter to format log messages in [logfmt format](https://www.brandur.org/logfmt).

[![PyPI version](https://badge.fury.io/py/logfmt-julian-sobott.svg)](https://badge.fury.io/py/logfmt-julian-sobott)
![publish workflow](https://github.com/JulianSobott/python-logfmt/actions/workflows/python-publish.yml/badge.svg)
![test workflow](https://github.com/JulianSobott/python-logfmt/actions/workflows/python-test.yml/badge.svg)

> Logfmt is a simple text-based format for structured logging. It is designed to be easy to read by both humans and machines. 
> It is also designed to be easy to parse and generate.

## Example output
```
ts=2022-10-14T17:41:15+0200 lvl=INFO msg="Hello World"
```

## Log context

Additionally, this library supports to add additional information to the log message via LogContexts. 
This is also known as MDC (Mapped Diagnostic Context).
This adds values, to the log message across multiple log statements.

```python
with LogContext(foo="bar"):
    logger.info("Hello World")
    logger.info("This is a second test")
logger.info("Outside of context")
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="Hello World" foo=bar
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="This is a second test" foo=bar
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="Outside of context"
```

## Installation

```bash
pip install logfmt-julian-sobott
```

## Example usage

```python
import logging
from logfmt import LogFmtFormatter, LogContext, CallableLogContext

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = LogFmtFormatter()
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("Hello World")
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="Hello World"

logger.info("Hello World", extra={"foo": "bar"})
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="Hello World" foo=bar

with LogContext(foo="bar"):
    logger.info("Hello World")
    logger.info("This is a second test")
logger.info("Outside of context")
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="Hello World" foo=bar
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="This is a second test" foo=bar
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="Outside of context"

@CallableLogContext()
def foo(name: str):
    logger.info("Hello World")
foo("bar")
# ts=2022-10-14T17:41:15+0200 lvl=INFO msg="Hello World" name=bar


@CallableLogContext("name", "args")
def foo(name: str, surname: str, *args):
    logger.info("Hello World")
foo("bar with spaces", "baz", "qux")
# ts=2022-10-14T17:45:58+0200 lvl=INFO msg="Hello World" args=('qux',) name="bar with spaces"

try:
    raise Exception("Something went wrong")
except Exception as e:
    logger.exception("trying to fix it")
# ts=2022-10-14T22:49:31+0200 lvl=ERROR msg="trying to fix it" 
# exception="
# Traceback (most recent call last):
#   File \"/src/tests/x.py\", line 17, in <module>
#     raise Exception(\"Something went wrong\")
# Exception: Something went wrong"
```
