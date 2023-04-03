"""Вспомогательный метакласс верификации кода класса сервера"""

import inspect


class ServerVerifier(type):
    def __init__(
            cls,
            classname: str,
            bases: tuple[str],
            dict_: dict[str, any]
    ) -> None:

        code_lines = inspect.getsourcelines(cls)
        file_name = inspect.getfile(cls)
        for line_num, line in enumerate(code_lines[0], code_lines[1]):
            if '.connect(' in line:
                raise Exception(
                    f'Methods connect is forbidden for creationg'
                    f' socket on {file_name=} {classname=} {line_num=}'
                )

        if 'SOCK_STREAM' not in inspect.getsource(cls):
            raise Exception(f'{classname=} TCP is required')

        type.__init__(cls, classname, bases, dict_)
