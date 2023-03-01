from functools import wraps
from inspect import signature
from dataclasses import dataclass
from inspect import currentframe, getframeinfo
import logging

FORMAT = '%(asctime)s---%(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def log(func):
    def get_caller():
        frame = getframeinfo(currentframe().f_back.f_back)
        return f'{frame.filename}---{frame.function}---line={frame.lineno}'

    @dataclass
    class FuncData:
        name: str
        signature: str
        caller_info: str

    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = signature(func)
        func_data = FuncData(
            name=func.__qualname__,
            signature=str(sig),
            caller_info=get_caller()
        )
        logger.debug(
            f'Вызвали функцию {func_data.name}{func_data.signature}:'
            f' из {func_data.caller_info}'
        )
        result = func(*args, **kwargs)
        return result
    return wrapper


@log
def foo(a: int, b: int) -> int:
    return a + b


def main():
    foo(a=3, b=4)


main()
