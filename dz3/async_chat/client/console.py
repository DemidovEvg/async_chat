from queue import Queue
from threading import Thread, Lock, Condition
import logging
from async_chat.settings import DEFAULT_ROOM


logger = logging.getLogger('client-logger')


class InputCommander(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.input_queue = Queue()
        self.message = ''
        self.lock = Lock()
        self.message_condition = Condition()

    def set_message(self, message: str) -> None:
        with self.lock:
            self.message = message

    def go(self) -> None:
        with self.message_condition:
            self.message_condition.notify_all()

    def run(self):
        while True:
            with self.message_condition:
                self.message_condition.wait()
                command_input = input(self.message)
                self.input_queue.put_nowait(command_input)


class ConsoleServer(Thread):
    def __init__(
            self,
            account_name: str | None,
            password: str | None,
    ):
        super().__init__()
        self.account_name = account_name
        self.password = password
        self.daemon = True
        self.lock = Lock()
        self.is_entered = False
        self.room = ''
        self.commands_queue = Queue()
        self.errors_queue = Queue()
        self.message_condition = Condition()
        self.input_commander = InputCommander()

    def put_error(self, str) -> None:
        self.errors_queue.put_nowait(str)

    def is_commands_queue_empty(self) -> bool:
        return self.commands_queue.empty()

    def get_command(self) -> str:
        command = self.commands_queue.get_nowait()
        self.commands_queue.task_done()
        return command

    def set_is_entered(self, is_entered: bool) -> None:
        with self.lock:
            self.is_entered = is_entered

    def set_account_name(self, account_name: str):
        with self.lock:
            self.account_name = account_name

    def set_password(self, password: str):
        with self.lock:
            self.password = password

    def set_room(self, room: str):
        with self.lock:
            self.room = room

    def get_message(self):
        password_mask = self.password and "*" * len(self.password)
        message = (f'room={self.room or DEFAULT_ROOM} ---'
                   f' Команда(account_name={self.account_name})'
                   f' entered={self.is_entered} password={password_mask}: ')
        return message

    def go(self):
        self.input_commander.set_message(self.get_message())
        self.input_commander.go()

    def run(self):
        self.print_help()
        self.input_commander.start()
        self.go()
        while True:
            if not self.errors_queue.empty():
                print(self.errors_queue.get())
            if not self.input_commander.input_queue.empty():
                command_input = self.input_commander.input_queue.get()
            else:
                continue

            if 'help' in command_input:
                self.print_help()
                self.go()
            elif 'exit' in command_input:
                self.commands_queue.put_nowait(command_input)
                self.commands_queue.join()
                break
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
                    self.commands_queue.put_nowait(command_input)
                    right_command = True
                    break
            if not right_command:
                self.errors_queue.put_nowait('Не валидная команда')
                self.go()

        logger.info('Вышли из консоли')

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
        print('- join gamers')
        print('- leave')
