"""Основной класс клиента ассинхронного чата"""
import sys
import socket
import signal
import trio
import ipaddress
import logging
import datetime as dt
from typing import Any
from typing import TypeVar
import json
from pydantic import BaseModel
from async_chat.utils import (
    WrongCommand,
)
from async_chat.client.current_user import current_user
from async_chat.client.client_verifier import ClientVerifier
# from async_chat.client.messages_ui import MessageToUI
from async_chat.client.client_ui.client_ui_talk import ClientUiTalk
from async_chat.client.client_response_handler import ClientResponseHandler
from async_chat.client.message_chain import messages_chain
from async_chat.utils import encrypt, load_keys


logger = logging.getLogger('client-logger')

T = TypeVar('T', bound=BaseModel)


class Timer:
    def restart(self, seconds: int):
        self.start = dt.datetime.now()
        self.delta = dt.timedelta(seconds=seconds)

    def time_is_over(self):
        if self.start + self.delta < dt.datetime.now():
            return True
        return False


class ClientChat(metaclass=ClientVerifier):
    def __init__(
            self,
            account_name: str | None,
            password: str | None,
            ip_address: str,
            port: int,
            client_ui_talk: ClientUiTalk,
    ):
        self.current_user = current_user
        self.current_user.account_name = account_name
        self.current_user.password = password

        self.response_handler = ClientResponseHandler()

        self.port = port
        self.ip_address = ipaddress.ip_address(ip_address)
        self.client_ui_talk = client_ui_talk
        self.message_head_size = 4
        self.message_chain = messages_chain
        signal.signal(signal.SIGTERM, self.close_client)
        signal.signal(signal.SIGINT, self.close_client)
        self.counter = 0
        _, publick_key = load_keys()
        self.publick_key = publick_key

    def close_client(self, signum, frame):
        signame = signal.Signals(signum).name
        logger.info(f'Signal handler called with signal {signame} ({signum})')
        self.close_socket()
        sys.exit(0)

    def connect_to_server(self) -> None:
        self._chat_socket = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM
        )
        self._chat_socket = socket.create_connection(
            address=(str(self.ip_address), self.port),
            timeout=0.01
        )
        self._chat_socket.settimeout(0.01)

    async def connect_to_server_loop(self) -> None:
        while True:
            try:
                self.connect_to_server()
                self.client_ui_talk.set_connected(
                    connected=True,
                    message='Подключились'
                )
                break
            except Exception as exc:
                self.client_ui_talk.set_connected(
                    connected=False,
                    message=f'Ошибка подключения {exc.__repr__()}'
                )
                logger.error(
                    f'Неудачное подключение к серверу {exc.__repr__()}'
                )
            await trio.sleep(0.1)

    def get_message_size(self, head: str) -> int:
        return int(head, 16)

    async def get_incomming_message(self) -> str | None:
        self.counter = self.counter + 1
        # print(f'{self.counter}---{self.account_name}---get_incomming_message')
        try:
            message_head = (
                self._chat_socket.recv(self.message_head_size)
            )
            print(f'{message_head=}')
            if len(message_head) == 0:
                raise ConnectionResetError()
            message_size = self.get_message_size(message_head)
            incomming_message = (
                self._chat_socket.recv(message_size).decode()
            )
        except BlockingIOError:
            # logger.debug('BlockingIOError')
            return
        except TimeoutError:
            # logger.debug('TimeoutError')
            return
        except ConnectionResetError:
            logger.debug('Сокет закрыт, пробуем переподлючиться')
            await self.connect_to_server_loop()
            return
        logger.debug('get_incomming_message: %s', incomming_message)
        return incomming_message

    def parse_incomming_message(self, incomming_message: str) -> dict[str, Any] | None:
        try:
            incomming_data: dict[str, Any] = json.loads(incomming_message)
        except json.decoder.JSONDecodeError as exc:
            logger.error(
                'error=%s with incomming_message=%s',
                str(exc),
                incomming_message
            )
            return
        return incomming_data

    def dispatch_incomming_data(self, incomming_data: dict[str, Any]) -> None:
        logger.debug('dispatch_incomming_data %s', incomming_data)
        handler = ClientResponseHandler()
        message_model = handler.dispatch_incomming_data(incomming_data)
        self.client_ui_talk.put_message_to_ui(message_model)

    def print_message(self, incomming_data: dict[str, Any]) -> None:
        print(f'Пришло сообщение: {incomming_data["message"]}')

    def put_message_to_ui(self, message_model: BaseModel) -> None:
        try:
            self.client_ui_talk.put_message_to_ui(message_model)
        except Exception as exc:
            self.client_ui_talk.error_from_server.put(
                dict(error=exc.__repr__())
            )

    def form_data(self, data: bytes) -> bytes:
        length = len(data)
        hex_legth = hex(length)[2:]
        head_message = f'00{hex_legth}'[-4:]
        return head_message.encode() + data

    async def send_outgoing_message(self, outgoing_message: str) -> None:
        try:
            logger.debug('send_outgoing_message: %s', outgoing_message)
            encrypted_data = encrypt(outgoing_message, self.publick_key)
            data = self.form_data(encrypted_data)
            self._chat_socket.send(data)
        except OSError as exc:
            logger.error('OSError= %s', str(exc))
            await self.connect_to_server_loop()

    def close_socket(self) -> None:
        if hasattr(self, '_chat_socket'):
            self._chat_socket.close()

    async def run(self):
        await self.main_loop()

    async def main_loop(self):
        await self.connect_to_server_loop()
        async with trio.open_nursery() as nursery:
            ui = self.client_ui_talk.get_ui()
            nursery.start_soon(ui.command_handler)
            while True:
                await trio.sleep(0.1)
                command = self.client_ui_talk.get_command_to_client()
                if command:
                    print(f'Получили новую команду {command}')
                    try:
                        await self.processing_command(command)
                    except WrongCommand as exc:
                        print(exc.__repr__())
                    except SystemExit:
                        logger.debug('Выходим')
                        self.close_socket()
                        return

                # logger.debug('incomming_messages_loop: тик-так')
                incomming_message = await self.get_incomming_message()
                if incomming_message:
                    incomming_data = self.parse_incomming_message(
                        incomming_message
                    )
                    if incomming_data:
                        self.dispatch_incomming_data(incomming_data)

    async def processing_command(self, command: str) -> None:
        request_model = await self.response_handler.processing_command(command)

        if request_model:
            await self.processing_outgoing_model(request_model)

    async def processing_outgoing_model(self, message_model: BaseModel):
        outgoing_message = str(message_model.json())
        await self.send_outgoing_message(outgoing_message=outgoing_message)
        self.client_ui_talk.put_outgoing_message(
            message_model
        )
        self.message_chain[message_model.id] = message_model
