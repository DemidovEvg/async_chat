import logging
import asyncio
import sys
from async_chat.settings import DEFAULT_ROOM


logger = logging.getLogger('client-logger')


class ConsoleServer:
    def __init__(
            self,
            account_name: str | None,
            password: str | None,
    ):
        super().__init__()
        self.account_name = account_name
        self.password = password
        self.is_entered = False
        self.room = ''
        self.start = True

    async def get_command(self):
        if self.start:
            # self.print_help()
            self.start = False
        message = self.get_message()
        print(message)
        stdin_task = asyncio.create_task(self.ainput(message))
        raw_command = await stdin_task
        clean_command = self.command_processing(raw_command)
        if not clean_command:
            return ''
        else:
            return clean_command

    def set_is_entered(self, is_entered: bool) -> None:
        self.is_entered = is_entered

    def set_account_name(self, account_name: str):
        self.account_name = account_name

    def set_password(self, password: str):
        self.password = password

    def set_room(self, room: str):
        self.room = room

    def get_message(self):
        password_mask = self.password and "*" * len(self.password)
        message = (f'room={self.room or DEFAULT_ROOM} ---'
                   f' Команда(account_name={self.account_name})'
                   f' entered={self.is_entered} password={password_mask}: ')
        return message

    def command_processing(self, raw_command: str):
        command_input = raw_command
        if 'help' in command_input:
            self.print_help()
        elif 'exit' in command_input:
            return command_input
        available_commands = [
            'login',
            'logout',
            'presence',
            'message',
            'join',
            'leave'
        ]
        right_command = False
        for command in available_commands:
            if command in command_input:
                right_command = True
                break
        if not right_command:
            print('Не валидная команда')
            return None
        else:
            return command_input

    async def ainput(self, message) -> str:
        # await asyncio.get_event_loop().run_in_executor(
        #     None,
        #     lambda message=message: sys.stdout.write(message)
        # )
        return await asyncio.get_event_loop().run_in_executor(
            None,
            sys.stdin.readline
        )

    def print_help(self) -> None:
        print('Допустимые команды:')
        print('- help')
        print('- login --account_name=Ivan51 --password=ivan123')
        print('- logout')
        print('- exit')
        print('- presence')
        print('- message # "Сообщение в текущую комнату"')
        print('- message #common "Сообщение всем пользователям"')
        print('- message #room_name "Сообщение в другую комнату"')
        print('- message Ivan2 "Привет Иван"')
        print('- join gamers')
        print('- leave')
