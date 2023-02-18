import sys
import socket
import re
import ipaddress
from .. import jim

# Аноним сможет писать только в общую группу '#Флуд'
# Так же будет приватная группа '#Секреты'
# Юзеры Иванов, Петров, Сидоров


class WrongCommand(Exception):
    pass


class ClientChat:
    def __init__(
            self,
            account_name: str,
            password: str,
            ip_address: str,
            port: int,
            max_data_size: int = 1024
    ):
        self.account_name = account_name
        self.password = password
        self.port = port
        self.ip_address = ipaddress.ip_address(ip_address)
        self.max_data_size = max_data_size
        self.__chat_socket = None

    def connect_to_server(self) -> None:
        self.__chat_socket = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM
        )
        self.__chat_socket.connect((str(self.ip_address), self.port))

    @property
    def chat_socket(self) -> socket.socket:
        if not self.__chat_socket:
            self.connect_to_server()
        return self.__chat_socket

    def get_response(self) -> str:
        incomming_message = self.chat_socket.recv(self.max_data_size).decode()
        print(f'incomming_message={incomming_message}')
        return incomming_message

    def send_message(self, send_data: str) -> None:
        print(f'outcomming message={send_data}')
        try:
            self.chat_socket.send(send_data.encode())
        except OSError:
            self.close_socket()
            self.connect_to_server()
            self.chat_socket.send(send_data.encode())

    def close_socket(self):
        if self.chat_socket:
            self.chat_socket.close()

    def get_message(self) -> str:
        try:
            incomming_message = self.get_response()
        except OSError as exc:
            print(f'Пробуем переподключиться так как exc={str(exc)}')
            self.connect_to_server()
            incomming_message = self.get_response()
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
        result = RE_LOGIN_PARSER.match(command).groupdict()
        if not result:
            raise WrongCommand('command not valid')

        new_account_name = result.get('account_name')
        if self.account_name and self.account_name != new_account_name:
            print(
                f'self.account_name={self.account_name} new_account_name={new_account_name}'
            )
            self.logout()

        self.account_name = new_account_name
        self.password = result.get('password', self.password)

    def print_help(self) -> None:
        print('Допустимые команды:')
        print('- help')
        print('- login --account_name=account_name --password=password')
        print('- logout')
        print('- presence')
        print('- message Petrov "Привет Петруха"')
        print('- connect')

    def command_line_loop(self):
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
                    self.login()
                elif 'logout' in command:
                    self.logout()
                elif 'presence' in command:
                    self.send_presence()
                elif 'exit' in command:
                    self.logout()
                    sys.exit(0)
                else:
                    print('Не валидная команда, попробуйте еще раз!')
                    print('======================')
            except Exception as exc:
                print('ERROR: ' + str(exc))
                print('======================')
                self.print_help()

    def login(self):
        if not self.account_name or not self.password:
            raise Exception('Empty account_name or password')
        message_model = jim.MessageUserAuth(
            user=dict(
                account_name=self.account_name,
                password=self.password
            )
        )
        send_data = message_model.json()
        self.send_message(send_data=send_data)
        return self.get_message()

    def logout(self):
        message_model = jim.MessageUserQuit(
            user=dict(
                account_name=self.account_name,
            )
        )
        send_data = message_model.json()
        self.send_message(send_data=send_data)
        return self.get_message()

    def send_presence(self):
        if not self.account_name:
            raise Exception('Empty account_name')
        message_model = jim.MessageUserPresence(
            user=dict(account_name=self.account_name)
        )
        send_data = message_model.json()
        self.send_message(send_data=send_data)
        return self.get_message()
