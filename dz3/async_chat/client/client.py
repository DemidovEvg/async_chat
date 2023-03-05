import sys
import socket
import re
import signal
import ipaddress
import logging
import asyncio
from typing import Any
import json
from async_chat import jim
from async_chat.utils import (
    WrongCommand,
    IncommingMessage,
    OutgoingMessage,
)
from async_chat.utils import get_message_dto_

logger = logging.getLogger('client-logger')


def handler(signum, frame, callback):
    signame = signal.Signals(signum).name
    print(f'Signal handler called with signal {signame} ({signum})')
    callback()
    sys.exit(0)


class ClientChat:
    def __init__(
            self,
            account_name: str | None,
            password: str | None,
            ip_address: str,
            port: int,
            max_data_size: int = 1024
    ):
        self.account_name = account_name
        self.password = password
        self.port = port
        self.ip_address = ipaddress.ip_address(ip_address)
        self.max_data_size = max_data_size
        self.is_entered = False
        socket.setdefaulttimeout(1)
        signal.signal(signal.SIGTERM, self.close_client)
        signal.signal(signal.SIGINT, self.close_client)

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

    def reconnect_to_server(self) -> None:
        self._chat_socket = socket.create_connection(
            (str(self.ip_address), self.port)
        )

    def get_incomming_message(self) -> str | None:
        incomming_message = None
        try:
            incomming_message = self._chat_socket.recv(
                self.max_data_size).decode()
        except ConnectionError as exc:
            logger.error(
                f'Пробуем переподключиться так как exc={str(exc)}'
            )
            self.close_socket()
            self.reconnect_to_server()
            incomming_message = self._chat_socket.recv(
                self.max_data_size).decode()
        except TimeoutError:
            pass
        if incomming_message:
            logger.debug('get_incomming_message: %s', incomming_message)
        return incomming_message

    def processing_incomming_message(self, incomming_message: str) -> None:
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
        logger.debug('dispatch_incomming_data')
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
                self.send_presence()
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
        logger.debug('Пришло сообщение: %s', incomming_data['message'])

    def send_outgoing_message(self, outgoing_message: OutgoingMessage) -> None:
        logger.debug('send_outgoing_message: %s', outgoing_message)

        try:
            if self._chat_socket._closed:
                logger.debug('Сокет был закрыт, переподключаемся')
                self.reconnect_to_server()
            self._chat_socket.send(outgoing_message.encode())
        except OSError as exc:
            logger.error('OSError= %s', str(exc))
            self.close_socket()
            self.reconnect_to_server()
            self._chat_socket.send(outgoing_message.encode())

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
            self.logout(account_name=self.account_name)

        self.account_name = new_account_name
        self.password = new_password

    async def ainput(self) -> str:
        password_mask = self.password and "*" * len(self.password)
        message = f'Команда(account_name={self.account_name}) entered={self.is_entered} password={password_mask}: '
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda message=message: sys.stdout.write(message)
        )
        return await asyncio.get_event_loop().run_in_executor(
            None,
            sys.stdin.readline
        )

    def run(self):
        asyncio.run(self.main_loop())

    async def incomming_messages_loop(self):
        self.connect_to_server()
        while True:
            logger.debug('incomming_messages_loop: тик-так')
            incomming_message = self.get_incomming_message()
            print(incomming_message)
            if incomming_message:
                incomming_data = self.processing_incomming_message(
                    incomming_message
                )
                self.dispatch_incomming_data(incomming_data)
            await asyncio.sleep(3)

    def print_help(self) -> None:
        print('Допустимые команды:')
        print('- help')
        print('- login --account_name=Ivan1 --password=ivan123')
        print('- logout')
        print('- exit')
        print('- presence')
        print('- message all "Привет всем"')

    async def main_loop(self) -> None:
        asyncio.create_task(self.incomming_messages_loop())
        self.print_help()
        while True:
            console_task = asyncio.create_task(self.ainput())
            command = await console_task
            try:
                self.processing_command(command)
            except SystemExit:
                logger.debug('Выходим')
                self.close_socket()
                return

    def processing_command(self, command: str) -> None:
        logger.debug('Input command=%s for=%s', command, self.account_name)
        try:
            if 'help' in command:
                self.print_help()
            elif 'login' in command:
                self.sync_account_name_and_password_from_command(
                    command
                )
                self.login(
                    account_name=str(self.account_name),
                    password=str(self.password)
                )
            elif 'logout' in command:
                self.logout(
                    account_name=str(self.account_name)
                )
            elif 'presence' in command:
                self.send_presence()
            elif 'message' in command:
                _, target, message_words = command.split()
                message = ''.join(message_words)
                self.send_message(target, message)
            elif 'exit' in command:
                try:
                    self.logout(
                        account_name=str(self.account_name)
                    )
                except OSError as exc:
                    print('ERROR: ' + str(exc))
            else:
                print(f'Не валидная команда {command}, попробуйте еще раз!')
                print('======================')
        except (OSError, WrongCommand) as exc:
            print('ERROR: ' + str(exc))
            print('======================')
            logger.error('ERROR: %s', str(exc))
            self.print_help()

    def login(self, account_name: str, password: str) -> IncommingMessage:
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
        outgoing_message = OutgoingMessage(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        incomming_message = ''
        while not incomming_message:
            incomming_message = self.get_incomming_message()
        if incomming_message:
            incomming_data = self.processing_incomming_message(
                incomming_message
            )
            if incomming_data.get('alert') and incomming_data.get('alert').upper() == 'OK':
                self.is_entered = True
                logger.debug('Вход удачный')

    def logout(self, account_name: str) -> IncommingMessage:
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
        outgoing_message = OutgoingMessage(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        incomming_message = self.get_incomming_message()
        try:
            is_ok = self.check_ok(incomming_message)
            if is_ok:
                raise SystemExit()
        except Exception as exc:
            import pdb
            pdb.set_trace()
            logger.debug('Выход не удачный %s', str(exc))

    def check_ok(self, incomming_message: str) -> bool:
        if incomming_message:
            incomming_data = self.processing_incomming_message(
                incomming_message
            )
            alert_model = jim.MessageAlert(**incomming_data)
            if alert_model.alert == 'OK':
                return True

    def send_presence(self):
        if not self.account_name:
            raise WrongCommand('Empty account_name')
        message_model = jim.MessageUserPresence(
            user=dict(account_name=self.account_name)
        )
        outgoing_message = OutgoingMessage(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)

    def send_message(self, target: str, message: str) -> IncommingMessage:
        if not self.account_name:
            raise WrongCommand('Empty account_name')

        message_model = jim.MessageSendMessage(
            from_=self.account_name,
            to_=target,
            message=message
        )
        outgoing_message = OutgoingMessage(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
