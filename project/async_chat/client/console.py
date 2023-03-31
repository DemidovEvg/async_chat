"""Консольное управление клиентом"""
import logging
import sys
import trio
from async_chat.settings import DEFAULT_ROOM
from async_chat.client.client_ui.client_ui_talk import ClientUiTalk
from async_chat.client.base_ui import BaseUI
from async_chat.client.current_user import current_user

logger = logging.getLogger('client-logger')


class ConsoleServer(BaseUI):
    def __init__(self, client_ui_talk: ClientUiTalk):
        self.client_ui_talk = client_ui_talk
        self.current_user = current_user
        super().__init__()

    async def command_handler(self):
        while True:
            message = self.get_message()
            print(message)
            clean_command = ''
            while not clean_command:
                raw_command = await self.ainput(message)
                clean_command = self.command_processing(raw_command)
            await self.client_ui_talk.put_command_to_client(clean_command)

    def set_is_entered(self, is_entered: bool) -> None:
        self.is_entered = is_entered

    def get_message(self):
        account_name = self.current_user.account_name
        password = self.current_user.password
        room = self.current_user.room
        is_entered = self.current_user.is_entered
        password_mask = password and "*" * len(password)
        message = (f'room={room or DEFAULT_ROOM} ---'
                   f' Команда(account_name={account_name})'
                   f' entered={is_entered} password={password_mask}: ')
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
            'leave',
            'contacts',
            'add-contact',
            'del-contact'
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
        return await trio.to_thread.run_sync(sys.stdin.readline)

    def print_help(self) -> None:
        print('Допустимые команды:')
        print('- help')
        print('- login --account_name=Ivan1 --password=ivan123')
        print('- logout')
        print('- exit')
        print('- presence')
        print('- message # "Сообщение в текущую комнату"')
        print('- message #common "Сообщение всем пользователям"')
        print('- message #room_name "Сообщение в другую комнату"')
        print('- message Ivan2 "Привет Иван"')
        print('- contacts')
        print('- add-contact Ivan2')
        print('- del-contact Ivan2')
        print('- join gamers')
        print('- leave')
