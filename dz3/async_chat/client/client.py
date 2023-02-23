import sys
import socket
import re
import ipaddress
from async_chat import jim
from async_chat.utils import (
    WrongCommand,
    IncommingMessage,
    OutgoingMessage,
)


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
        socket.setdefaulttimeout(5)

    def connect_to_server(self) -> None:
        self._chat_socket = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM
        )
        self._chat_socket = socket.create_connection(
            (str(self.ip_address), self.port))

    @property
    def chat_socket(self) -> socket.socket:
        if not hasattr(self, '_chat_socket') or not self._chat_socket:
            self.connect_to_server()
        return self._chat_socket

    def get_incomming_message(self) -> IncommingMessage:
        incomming_message = IncommingMessage(
            self.chat_socket.recv(self.max_data_size).decode()
        )
        print(f'get_incomming_message: {incomming_message=}')
        return incomming_message

    def send_outgoing_message(self, outgoing_message: OutgoingMessage) -> None:
        print(f'send_outgoing_message: {outgoing_message=}')
        try:
            self.chat_socket.send(outgoing_message.encode())
        except OSError as exc:
            print(f'OSError={str(exc)}')
            self.close_socket()
            self.connect_to_server()
            self.chat_socket.send(outgoing_message.encode())

    def close_socket(self) -> None:
        if self.chat_socket:
            self.chat_socket.close()

    def get_message(self) -> IncommingMessage:
        try:
            incomming_message = self.get_incomming_message()
        except OSError as exc:
            print(f'Пробуем переподключиться так как exc={str(exc)}')
            self.connect_to_server()
            incomming_message = self.get_incomming_message()
        self.close_socket()
        return incomming_message

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

    def print_help(self) -> None:
        print('Допустимые команды:')
        print('- help')
        print('- login --account_name=account_name --password=password')
        print('- logout')
        print('- exit')
        print('- presence')
        print('- message Petrov "Привет Петруха"')

    def command_line_loop(self) -> None:
        self.print_help()
        while True:
            password_mask = self.password and "*" * len(self.password)
            command = input(
                f'Команда(account_name={self.account_name}) self.password={password_mask}: '
            )
            try:
                if command == 'help':
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
                elif 'exit' in command:
                    try:
                        self.logout(
                            account_name=str(self.account_name)
                        )
                    except OSError as exc:
                        print('ERROR: ' + str(exc))
                        print('Выходим все равно')
                    sys.exit(0)
                else:
                    print('Не валидная команда, попробуйте еще раз!')
                    print('======================')
            except OSError as exc:
                print('ERROR: ' + str(exc))
                print('======================')
                self.print_help()

    def login(self, account_name: str, password: str) -> IncommingMessage:
        if not account_name or not password:
            raise Exception('Empty account_name or password')
        message_model = jim.MessageUserAuth(
            user=dict(
                account_name=account_name,
                password=password
            )
        )
        outgoing_message = OutgoingMessage(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        return self.get_message()

    def logout(self, account_name: str) -> IncommingMessage:
        message_model = jim.MessageUserQuit(
            user=dict(
                account_name=account_name,
            )
        )
        outgoing_message = OutgoingMessage(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        return self.get_message()

    def send_presence(self) -> IncommingMessage:
        if not self.account_name:
            raise Exception('Empty account_name')
        message_model = jim.MessageUserPresence(
            user=dict(account_name=self.account_name)
        )
        outgoing_message = OutgoingMessage(message_model.json())
        self.send_outgoing_message(outgoing_message=outgoing_message)
        return self.get_message()
