"""Вспомогательный метакласс верификации класса клиента"""
import inspect
import socket


class ClientVerifier(type):
    def __init__(
            cls,
            classname: str,
            bases: tuple[str],
            dict_: dict[str, any]
    ) -> None:
        code_lines = inspect.getsourcelines(cls)
        file_name = inspect.getfile(cls)
        for line_num, line in enumerate(code_lines[0], code_lines[1]):
            if '.accept(' in line or '.listen(' in line:
                raise Exception(
                    f'Methods accept and listen are forbidden for creationg'
                    f' socket on {file_name=} {classname=} {line_num=}'
                )

        if 'SOCK_STREAM' not in inspect.getsource(cls):
            raise Exception(f'{classname=} TCP is required')

        for attr_name, attr_body in dict_.items():
            if isinstance(attr_body, socket.socket):
                raise Exception(
                    f'Socket instance forrbidden like class'
                    f' {classname=} attribute attr={attr_name}'
                )

        type.__init__(cls, classname, bases, dict_)
