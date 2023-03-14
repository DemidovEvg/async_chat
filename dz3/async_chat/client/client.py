import sys
import socket
import re
import signal
import ipaddress
import logging
import datetime as dt
from typing import Any
import json
import asyncio
from pydantic import ValidationError
from async_chat import jim
from async_chat.utils import (
    WrongCommand,
)
from async_chat.utils import get_message_dto_
from async_chat.client.console import ConsoleServer
from async_chat.settings import DEFAULT_ROOM
from async_chat.client.client_verifier import ClientVerifier


logger = logging.getLogger('client-logger')


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
    ):
        self.account_name = account_name
        self.password = password
        self.port = port
        self.ip_address = ipaddress.ip_address(ip_address)
        self.message_head_size = 4
        signal.signal(signal.SIGTERM, self.close_client)
        signal.signal(signal.SIGINT, self.close_client)
        self.console = ConsoleServer(
            account_name=self.account_name,
            password=self.password
        )
        self.room = DEFAULT_ROOM
        self.counter = 0

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
            (str(self.ip_address), self.port))
        self._chat_socket.settimeout(1.0)
        # self._chat_socket.setblocking(0)

    def reconnect_to_server(self) -> None:
        self._chat_socket = socket.create_connection(
            (str(self.ip_address), self.port)
        )

    def get_message_size(self, head: str) -> int:
        return int(head, 16)

    def get_incomming_message(self) -> str | None:
        self.counter = self.counter + 1
        # print(f'{self.counter}---{self.account_name}---get_incomming_message')
        try:
            message_head = (
                self._chat_socket.recv(self.message_head_size)
            )
            print(message_head)
            if len(message_head) == 0:
                return
            message_size = self.get_message_size(message_head)
            incomming_message = (
                self._chat_socket.recv(message_size).decode()
            )
        except BlockingIOError:
            # logger.debug('BlockingIOError')
            return
        except TimeoutError:
            return
        except ConnectionResetError:
            logger.debug('Сокет закрыт')
            self.reconnect_to_server()
        logger.debug('get_incomming_message: %s', incomming_message)
        return incomming_message

    def processing_incomming_message(self, incomming_message: str) -> dict[str, Any] | None:
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
        alert = incomming_data.get('alert')
        if alert:
            logger.info('dispatch_incomming_data: %s', incomming_data)
            return
        error = incomming_data.get('error')
        if error:
            logger.error('dispatch_incomming_data: %s', incomming_data)
            return

        action = incomming_data.get('action')
        try:
            if not action:
                logger.debug(
                    f'Action not exist={incomming_data} '
                )
            elif action == 'probe':
                self.action_send_presence()
            elif action == 'msg':
                self.print_message(incomming_data)
            else:
                logger.error(
                    f'Unknown action for incomming_data={incomming_data} '
                )
        except Exception as exc:
            logger.error(
                f'ERROR={exc} for incomming_data={incomming_data} '
            )

    def print_message(self, incomming_data: str) -> None:
        print(f'Пришло сообщение: {incomming_data["message"]}')

    def form_data(self, data: str) -> bytes:
        length = len(data.encode())
        hex_legth = hex(length)[2:]
        head_message = f'00{hex_legth}'[-4:]
        return f'{head_message}{data}'.encode()

    def send_outgoing_message(self, outgoing_message: str) -> None:

        try:
            if self._chat_socket._closed:
                logger.debug('Сокет был закрыт, переподключаемся')
                self.reconnect_to_server()
            data = self.form_data(outgoing_message)
            logger.debug('send_outgoing_message: %s', data.decode())
            self._chat_socket.send(data)
        except OSError as exc:
            logger.error('OSError= %s', str(exc))
            self.close_socket()
            self.reconnect_to_server()

    def close_socket(self) -> None:
        if hasattr(self, '_chat_socket'):
            self._chat_socket.close()

    def sync_account_name_and_password_from_command(self, command: str) -> None:
        if '--account_name' not in command:
            return

        if '--password' not in command:
            raise WrongCommand('--password is required')

        RE_LOGIN_PARSER = re.compile(
            r'login --account_name=(?P<account_name>\w+) --password=(?P<password>\w+)'
        )
        re_match = RE_LOGIN_PARSER.match(command)
        if not re_match:
            raise WrongCommand('command not valid')

        result = re_match.groupdict()
        if not result:
            raise WrongCommand('command not valid')

        new_account_name = str(result.get('account_name'))
        new_password = str(result.get('password', self.password))
        if self.account_name and self.account_name != new_account_name:
            print(
                f'account_name={self.account_name} new_account_name={new_account_name}'
            )
            self.action_logout(account_name=self.account_name)

        self.account_name = new_account_name
        self.password = new_password
        self.console.set_account_name(new_account_name)
        self.console.set_password(new_password)

    def start_client(self):
        asyncio.run(self.main_loop())

    async def main_loop(self):
        while True:
            try:
                self.connect_to_server()
                break
            except ConnectionRefusedError:
                logger.info('Неудачное подключение к серверу')

        task_command = asyncio.create_task(self.console.get_command())
        while True:
            await asyncio.sleep(0.1)
            if task_command.done():
                command = await task_command
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
                task_command = asyncio.create_task(
                    self.console.get_command()
                )

            # logger.debug('incomming_messages_loop: тик-так')
            incomming_message = self.get_incomming_message()
            if incomming_message:
                incomming_data = self.processing_incomming_message(
                    incomming_message
                )
                if incomming_data:
                    self.dispatch_incomming_data(incomming_data)

    async def processing_command(self, command: str) -> None:
        logger.debug('Input command=%s for=%s', command, self.account_name)
        try:
            if 'login' in command:
                self.sync_account_name_and_password_from_command(
                    command
                )
                await self.action_login(
                    account_name=str(self.account_name),
                    password=str(self.password)
                )
            elif 'logout' in command:
                self.action_logout(
                    account_name=str(self.account_name)
                )
            elif 'presence' in command:
                self.action_send_presence()
            elif 'message' in command:
                _, target, *message_words = command.split()
                message = ' '.join(message_words)
                self.action_send_message(target, message)
            elif 'join' in command:
                _, room, *_ = command.split()
                self.action_join(room)
            elif 'leave' in command:
                self.action_leave()
            elif 'exit' in command:
                try:
                    self.action_logout(
                        account_name=str(self.account_name)
                    )
                except OSError as exc:
                    logger.error('ERROR: ' + str(exc))
            else:
                raise WrongCommand(
                    f'Не валидная команда {command}, попробуйте еще раз!'
                )
        except (OSError, WrongCommand) as exc:
            logger.error('ERROR: %s', str(exc))
            raise WrongCommand(str(exc))

    async def action_login(self, account_name: str, password: str) -> None:
        if not account_name or not password:
            raise Exception('Empty account_name or password')

        message_dto = get_message_dto_(
            schema=jim.MessageUserAuth,
            data=dict(
                user=dict(
                    account_name=account_name,
                    password=password
                ))
        )
        if message_dto.error_message:
            raise WrongCommand(message_dto.error_message)

        if not message_dto.message_model:
            raise WrongCommand('Could not get message_model for message')

        message_model: jim.MessageUserAuth = message_dto.message_model
        outgoing_message = str(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        incomming_message = ''
        timer = Timer()
        timer.restart(seconds=5)
        while not incomming_message and not timer.time_is_over():
            await asyncio.sleep(0.01)
            incomming_message = self.get_incomming_message()

        if not incomming_message:
            logger.debug('Вход НЕ удачный %s', incomming_message)
            return
        incomming_data = self.processing_incomming_message(
            incomming_message
        )
        if not incomming_data:
            logger.debug('Вход НЕ удачный %s', incomming_message)
            return
        if incomming_data.get('alert') and incomming_data.get('alert').upper() == 'OK':
            logger.debug('Вход удачный')
            self.console.set_is_entered(True)

    def action_logout(self, account_name: str) -> None:
        message_model = jim.MessageUserQuit(
            user=dict(
                account_name=account_name,
            )
        )
        message_dto = get_message_dto_(
            schema=jim.MessageUserQuit,
            data=dict(
                user=dict(
                    account_name=account_name,
                ))
        )
        if message_dto.error_message:
            raise WrongCommand(message_dto.error_message)

        if not message_dto.message_model:
            raise WrongCommand('Could not get message_model for message')
        outgoing_message = str(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        incomming_message = self.get_incomming_message()
        try:
            is_ok = self.check_ok(incomming_message)
            self.console.set_is_entered(False)
            if is_ok:
                raise SystemExit()
        except Exception as exc:
            logger.debug('Выход не удачный %s', str(exc))

    def check_ok(self, incomming_message: str) -> bool:
        if incomming_message:
            incomming_data = self.processing_incomming_message(
                incomming_message
            )
            alert_model = jim.MessageAlert(**incomming_data)
            if alert_model.alert == 'OK':
                return True

    def action_send_presence(self) -> None:
        if not self.account_name:
            raise WrongCommand('Empty account_name')
        message_model = jim.MessageUserPresence(
            user=dict(account_name=self.account_name)
        )
        outgoing_message = str(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)

    def action_send_message(self, target: str, message: str) -> None:
        if not self.account_name:
            raise WrongCommand('Empty account_name')
        if target == '#':
            target = f'#{self.room}'
        try:
            message_model = jim.MessageSendMessage(
                from_=self.account_name,
                to_=target,
                message=message
            )
        except ValidationError as exc:
            raise WrongCommand(str(exc))
        outgoing_message = str(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)

    def action_join(self, room: str) -> None:
        if not room:
            raise WrongCommand('Empty room')
        try:
            message_model = jim.MessageUserJoinRoom(
                room=room,
                user=dict(
                    account_name=self.account_name,
                )
            )
        except ValidationError as exc:
            raise WrongCommand(str(exc))
        outgoing_message = str(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        incomming_message = ''
        timer = Timer()
        timer.restart(seconds=5)
        print('Перед проверкой ответа от сервера')
        while not incomming_message and not timer.time_is_over():
            incomming_message = self.get_incomming_message()

        print('После проверки ответа от сервера')
        if not incomming_message:
            logger.debug('Вход в комнату НЕ удачный')
            return
        incomming_data = self.processing_incomming_message(
            incomming_message
        )
        if not incomming_data:
            logger.debug('Вход в комнату НЕ удачный')
            return
        if incomming_data.get('alert') and incomming_data.get('alert').upper() == 'OK':
            logger.debug('Вход в комнату удачный')
            self.room = room
            self.console.set_room(room)

    def action_leave(self) -> None:
        message_model = jim.MessageUserLeaveRoom(
            user=dict(
                account_name=self.account_name,
            )
        )
        outgoing_message = str(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        incomming_message = ''
        timer = Timer()
        timer.restart(seconds=5)
        while not incomming_message and not timer.time_is_over():
            incomming_message = self.get_incomming_message()

        if not incomming_message:
            logger.debug('Не смогли выйти из комнаты')
            return
        incomming_data = self.processing_incomming_message(
            incomming_message
        )
        if not incomming_data:
            logger.debug('Не смогли выйти из комнаты')
            return
        if incomming_data.get('alert') and incomming_data.get('alert').upper() == 'OK':
            logger.debug('Удачно вышли из комнаты')
            self.room = DEFAULT_ROOM
            self.console.set_room(self.room)
