"""Десктопный интерфейс чата"""
import signal
import sys
import traceback
from pathlib import Path
import outcome
import trio
from queue import Queue, Empty
from dataclasses import dataclass
from PySide6 import QtWidgets, QtCore, QtUiTools
from PySide6.QtCore import QEvent, QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import QApplication
from async_chat.client.client_ui.client_ui_talk import ClientUiTalk
from async_chat.client.client import ClientChat
from async_chat.client.base_ui import BaseUI
from async_chat import jim
from async_chat.client.current_user import current_user
from async_chat.jim.common_schemas import UserBase
from async_chat.client.client_ui_response_handler import ClientUIResponseHandler
from async_chat.client.client_ui.chat_item import (
    ChatItem,
    ChatLine,
    OutgoingChatLine,
    IncommintChatLine
)


@dataclass
class ClientConfig:
    account_name: str
    password: str
    ip_address: int
    port: int


class MainWindowContol(BaseUI):
    ui_path = Path(__file__).resolve().parent / 'client.ui'
    grey = "background-color: rgb(224, 224, 224);"
    white = "background-color: rgb(255, 255, 255);"

    def __init__(
        self,
        parent: QtWidgets.QMainWindow,
        client_ui_talk: ClientUiTalk
    ):
        self.parent = parent
        self.client_ui_talk = client_ui_talk
        self.chat_item = ChatItem()

        self.current_user = current_user

        self._get_contacts = QTimer()
        self._get_contacts.timeout.connect(self.action_get_contacts)

        self.response_handler = ClientUIResponseHandler(ui=self)

        self.loginLine: QtWidgets.QLineEdit = parent.loginLine
        self.passwordLine: QtWidgets.QLineEdit = parent.passwordLine
        self.ipLine: QtWidgets.QLineEdit = parent.ipLine
        self.portLine: QtWidgets.QLineEdit = parent.portLine
        self.contactNameLine: QtWidgets.QLineEdit = parent.contactNameLine
        self.roomNameLine: QtWidgets.QLineEdit = parent.roomNameLine
        self.roomNameLabel: QtWidgets.QLabel = parent.roomName

        self.connectButton: QtWidgets.QPushButton = parent.connectButton
        self.loginButton: QtWidgets.QPushButton = parent.loginButton
        self.logoutButton: QtWidgets.QPushButton = parent.logoutButton
        self.enterRoomButton: QtWidgets.QPushButton = parent.enterRoomButton
        self.addContactButton: QtWidgets.QPushButton = parent.addContactButton
        self.deleteContactButton: QtWidgets.QPushButton = parent.deleteContactButton
        self.sendMessageButton: QtWidgets.QPushButton = parent.sendMessageButton
        self.leaveRoomButton: QtWidgets.QPushButton = parent.leaveRoomButton

        self.messageField: QtWidgets.QPlainTextEdit = parent.messageField
        self.roomChat: QtWidgets.QTextBrowser = parent.roomChat

        self.contactsList: QtWidgets.QListWidget = parent.contactsList

        self.onlineStatus: QtWidgets.QLabel = parent.onlineStatus
        self.loginStatus: QtWidgets.QLabel = parent.loginStatus

        self.command_queue = Queue()
        self.init_window()

    def init_window(self):
        self.loginLine.insert('Ivan1')
        self.passwordLine.insert('ivan123')
        self.ipLine.insert('127.0.0.1')
        self.portLine.insert('3000')
        self.contactNameLine.insert('Ivan2')
        self.roomNameLine.insert('gamers')
        self.set_status(self.onlineStatus, 'offline', 'red')
        self.set_status(self.loginStatus, 'no login', 'red')

        self.loginButton.setEnabled(False)
        self.set_enable_control_buttons(False)

        self.connectButton.clicked.connect(self.start_client)
        self.loginButton.clicked.connect(self.action_login)
        self.logoutButton.clicked.connect(self.action_logout)
        self.enterRoomButton.clicked.connect(self.action_join)
        self.addContactButton.clicked.connect(self.action_add_contact)
        self.deleteContactButton.clicked.connect(self.action_del_contact)
        self.sendMessageButton.clicked.connect(self.action_send_message)
        self.leaveRoomButton.clicked.connect(self.action_leave)
        self.roomNameLabel.setText(self.current_user.room)

    def set_enable_control_buttons(self, enabled: bool = True):
        self.enterRoomButton.setEnabled(enabled)
        self.addContactButton.setEnabled(enabled)
        self.deleteContactButton.setEnabled(enabled)
        self.sendMessageButton.setEnabled(enabled)
        self.leaveRoomButton.setEnabled(enabled)

    def result_login(self, success: bool, error: str = '') -> None:
        self.current_user.try_login = False
        self.login_status(success=success)
        if success:
            self._get_contacts.start(10000)
            self.action_get_contacts()
            self.set_enable_control_buttons(True)
        else:
            self._get_contacts.stop()
            self.loginButton.setEnabled(True)
            self.loginLine.setReadOnly(False)
            self.loginLine.setStyleSheet(self.__class__.white)
            self.passwordLine.setReadOnly(False)
            self.passwordLine.setStyleSheet(self.__class__.white)
            self.chat_item = ChatItem()
            self.contactsList.clear()
            self.rerender_chat()
            self.clean_contacts()
            self.rerender_contacts()
            self.set_enable_control_buttons(False)
            self.show_error(error)

    def get_selected_contact(self):
        item = self.contactsList.currentItem()
        if item:
            return item.text()
        return None

    def get_target_for_message(self):
        contact = self.get_selected_contact()
        if contact:
            return contact
        return '#'

    @Slot()
    def action_send_message(self) -> None:
        message = self.messageField.toPlainText()
        to_ = self.get_target_for_message()
        self.messageField.clear()
        command = f'message {to_} {message}'
        self.command_queue.put(command)
        self.print_message(message=command)

    @Slot()
    def action_get_contacts(self) -> None:
        command = 'contacts'
        self.command_queue.put(command)
        # self.print_message(message=command)

    @Slot()
    def action_add_contact(self) -> None:
        contact = self.contactNameLine.text()
        command = f'add-contact {contact}'
        self.command_queue.put(command)
        self.print_message(message=command)

    @Slot()
    def action_del_contact(self) -> None:
        contact = self.get_selected_contact()
        if not contact:
            self.show_error('Не выделен контакт для удаления')
            return
        command = f'del-contact {contact}'
        self.command_queue.put(command)
        self.print_message(message=command)

    @Slot()
    def action_join(self) -> None:
        target_room = self.roomNameLine.text()
        if not target_room:
            self.show_error('Не выбрана комнада для присоединения')
            return
        command = f'join {target_room}'
        self.command_queue.put(command)
        self.print_message(message=command)

    @Slot()
    def action_leave(self) -> None:
        command = 'leave'
        self.command_queue.put(command)
        self.print_message(message=command)

    @Slot()
    def action_login(self) -> None:
        self.current_user.try_login = True
        account_name = self.loginLine.text()
        password = self.passwordLine.text()
        command = f'login --account_name={account_name} --password={password}'
        self.command_queue.put(command)
        self.print_message(message=command)

        self.loginLine.setReadOnly(True)
        self.loginLine.setStyleSheet(self.__class__.grey)
        self.passwordLine.setReadOnly(True)
        self.passwordLine.setStyleSheet(self.__class__.grey)
        self.loginButton.setEnabled(False)

    @Slot()
    def action_logout(self) -> None:
        command = 'logout'
        self.command_queue.put(command)
        self.print_message(message=command)

    async def command_handler(self):
        while True:
            try:
                command = self.command_queue.get_nowait()
            except Empty:
                await trio.sleep(0.1)
            else:
                print(f'command={command}')
                if command:
                    await self.client_ui_talk.put_command_to_client(command)

    def print_message(
        self,
        message: str,
        direction: ChatItem.MessageDirection | None = None,
        source: str | None = None,
        target: str | None = None,
        message_id: str | None = None,
        message_chain_id: str | None = None,
    ) -> None:
        line_dict = dict(
            message=message,
            message_id=message_id,
            message_chain_id=message_chain_id
        )
        if direction == ChatItem.MessageDirection.outgoing:
            line_dict['source'] = source or 'Я'
            line_dict['target'] = target or self.current_user.room
            line_class = OutgoingChatLine

        elif direction == ChatItem.MessageDirection.incoming:
            line_dict['source'] = source or self.current_user.room
            line_dict['target'] = 'Я'
            line_class = IncommintChatLine
        else:
            line_dict['source'] = 'command'
            line_class = ChatLine

        new_line = line_class(**line_dict)

        self.chat_item.lines.append(new_line)
        self.rerender_chat()

    def rerender_chat(self):
        text = self.chat_item.get_plain_text()
        self.roomChat.setPlainText(text)
        verScrollBar = self.roomChat.verticalScrollBar()
        verScrollBar.setValue(verScrollBar.maximum())

    def set_status(self, target: QtWidgets.QLabel, status: str, color: str):
        target.setText(status)
        target.setStyleSheet(f"color: {color};")

    def client_ui_step(self):
        if self.client_ui_talk.get_connected():
            if not self.current_user.try_login and not current_user.is_entered:
                self.loginButton.setEnabled(True)
            self.set_status(self.onlineStatus, 'online', 'green')
        else:
            self.loginButton.setEnabled(False)
            self.connectButton.setEnabled(True)
            self.set_status(self.onlineStatus, 'offline', 'red')

        if self.current_user.is_entered:
            self.set_status(self.loginStatus, 'login success', 'green')
        else:
            self.set_status(self.loginStatus, 'no login', 'red')

        self.outgoing_messages_processing()
        self.incomming_messages_processing()

    def login_status(self, success=False) -> None:
        if success:
            self.set_status(self.loginStatus, 'login success', 'green')
        else:
            self.set_status(self.loginStatus, 'no login', 'red')

    def incomming_messages_processing(self):
        incomming_model = self.client_ui_talk.get_message_to_ui()
        if incomming_model:
            self.response_handler.dispatch_incomming_model(incomming_model)

    def outgoing_messages_processing(self):
        outgoing_model = self.client_ui_talk.get_outgoing_message()
        if outgoing_model:
            self.response_handler.dispatch_outgoing_model(outgoing_model)

    def save_contacts_and_render(self, incomming_model: jim.MessageContacts):
        self.current_user.contacts = incomming_model.alert
        self.rerender_contacts()

    def append_contact_and_render(self, contact: UserBase):
        self.current_user.contacts.append(contact)
        self.rerender_contacts()

    def clean_contacts(self):
        self.current_user.contacts: list[UserBase] = []

    def delete_contact_and_render(self, contact: UserBase):
        for i, account_name in enumerate(self.current_user.contacts):
            if account_name == contact.account_name:
                del self.current_user.contacts[i]
                break
        self.rerender_contacts()

    def rerender_contacts(self):
        self.contactsList.clear()
        contacts = self.current_user.contacts
        sorted_contacts = sorted(
            contacts, key=lambda u: u.account_name
        )
        for contact in sorted_contacts:
            account_name = contact.account_name
            self.contactsList.addItem(QtWidgets.QListWidgetItem(account_name))

    def success_join_room(self, new_room: str):
        self.roomNameLabel.setText(new_room)
        self.print_message(message=f'Вошли в комнату: {new_room}')

    def success_leave_room(self, old_room: str, new_room: str):
        self.roomNameLabel.setText(new_room)
        self.print_message(
            message=f'Вышли из комнаты: {old_room}'
                    f' Вошли в комнату: {new_room}'
        )

    def accept_messages(self, message_id: str):
        self.chat_item.accepted_lines(message_id)
        # Что бы видеть как меняется статус accepted
        self.rerender_chat()

    def init_config(self) -> None:
        login = self.loginLine.text()
        password = self.passwordLine.text()
        port = int(self.portLine.text())
        ip = self.ipLine.text()

        self.config_dto = ClientConfig(
            account_name=login,
            password=password,
            port=port,
            ip_address=ip
        )

    def get_config(self) -> ClientConfig:
        if self.config_dto:
            return self.config_dto
        raise Exception('no config')

    @Slot()
    def start_client(self):
        try:
            self.init_config()
            self.client_ui_talk.put_client_config(self.get_config())

            self.ipLine.setReadOnly(True)
            self.ipLine.setStyleSheet(self.__class__.grey)
            self.portLine.setReadOnly(True)
            self.portLine.setStyleSheet(self.__class__.grey)
            self.connectButton.setEnabled(False)

            self._timer = QTimer()
            self._timer.timeout.connect(self.client_ui_step)
            self._timer.start(200)

            self.__class__.external_async_loop_trigger.emit()
        except Exception as exc:
            self.show_error(exc.__repr__())

    def show_error(self, error: str):
        if error:
            self.widget = QtWidgets.QDialog()
            self.widget.setStyleSheet("background-color: pink;")
            layout = QtWidgets.QVBoxLayout()
            error_text = QtWidgets.QTextBrowser()
            error_text.setText(error)
            error_text.setStyleSheet("font-size: 12pt")
            layout.addWidget(error_text)
            self.widget.setLayout(layout)

            self.widget.show()

    def show(self):
        self.parent.show()

    @classmethod
    def start_widget(cls, external_async_loop_trigger, *args):
        cls.external_async_loop_trigger = external_async_loop_trigger
        path = Path(__file__).resolve().parent / cls.ui_path
        ui_file = QtCore.QFile(str(path))
        if not ui_file.open(QtCore.QIODevice.ReadOnly):
            reason = ui_file.errorString()
            print(f"Cannot open {path}: {reason}")
            sys.exit(-1)
        loader = QtUiTools.QUiLoader()
        widget = loader.load(ui_file, None)

        instance = cls(widget, *args)
        return instance


class AsyncHelper(QObject):

    trigger_signal = Signal()

    class ReenterQtObject(QObject):
        def event(self, event):
            if event.type() == QEvent.User + 1:
                event.fn()
                return True
            return False

    class ReenterQtEvent(QEvent):
        def __init__(self, fn):
            super().__init__(QEvent.Type(QEvent.User + 1))
            self.fn = fn

    def __init__(self, entry=None):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject()
        self.entry = entry

    def set_entry(self, entry):
        self.entry = entry

    @Slot()
    def launch_guest_run(self, *args):
        if not self.entry:
            raise Exception("No entry point for the Trio guest run was set.")
        trio.lowlevel.start_guest_run(
            self.entry,
            *args,
            run_sync_soon_threadsafe=self.next_guest_run_schedule,
            done_callback=self.trio_done_callback,
        )

    def next_guest_run_schedule(self, fn):
        QApplication.postEvent(self.reenter_qt, self.ReenterQtEvent(fn))

    def trio_done_callback(self, outcome_):
        if isinstance(outcome_, outcome.Error):
            error = outcome_.error
            traceback.print_exception(type(error), error, error.__traceback__)


async def start_client(client_ui_talk: ClientUiTalk[MainWindowContol]):
    # while True:
    #     print('Псевдо цикл клиента')
    #     await trio.sleep(1)
    client_config_dto: ClientConfig = client_ui_talk.get_client_config()
    if client_config_dto:
        client_chat = ClientChat(
            account_name=client_config_dto.account_name,
            password=client_config_dto.password,
            ip_address=client_config_dto.ip_address,
            port=client_config_dto.port,
            client_ui_talk=client_ui_talk
        )
        client_ui_talk.put_client(client_chat)
        await client_chat.run()


async def async_task_creator(*args):
    async with trio.open_nursery() as nursery:
        nursery.start_soon(start_client, *args)


def main():
    app = QApplication(sys.argv)
    async_helper = AsyncHelper()

    client_ui_talk = ClientUiTalk[MainWindowContol]()
    main_window = MainWindowContol.start_widget(
        async_helper.trigger_signal,
        client_ui_talk
    )

    client_ui_talk.put_ui(main_window)

    async_helper.set_entry(async_task_creator)

    async_helper.trigger_signal.connect(
        lambda: async_helper.launch_guest_run(client_ui_talk))

    main_window.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec()


if __name__ == "__main__":
    main()
