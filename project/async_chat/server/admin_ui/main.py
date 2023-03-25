import signal
import sys
import traceback
from pathlib import Path
import outcome
import trio
from typing import Any
from dataclasses import dataclass
from PySide6 import QtWidgets, QtCore, QtUiTools
from PySide6.QtCore import QEvent, QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import QApplication
from async_chat.server.admin_ui.user_list import UserList
from async_chat.server.admin_ui.user_list_stat import UserListStat
from async_chat.server.admin_ui.server_ui_talk import client_ui_talk
from async_chat.server.server import ServerChat


@dataclass
class ServerConfig:
    login_db: str
    password_db: str
    server_port: int
    server_max_users: int


class MainWindowContol:
    ui_path = Path(__file__).resolve().parent / 'main.ui'

    def __init__(
        self,
        parent: QtWidgets.QMainWindow,
    ):
        self.parent = parent

        self.loginDb: QtWidgets.QLineEdit = parent.loginDb
        self.passwordDb: QtWidgets.QLineEdit = parent.passwordDb
        self.connectDbStatus: QtWidgets.QLabel = parent.connectDbStatus

        self.startServerButton: QtWidgets.QPushButton = parent.startServer
        self.serverPort: QtWidgets.QLineEdit = parent.serverPort
        self.maxUsers: QtWidgets.QLineEdit = parent.maxUsers
        self.serverStatus: QtWidgets.QLabel = parent.serverStatus

        self.showUserListButton: QtWidgets.QPushButton = parent.showUserList
        self.showUserListStatButton: QtWidgets.QPushButton = parent.showUserListStat

        self.showUserListButton.clicked.connect(self.show_user_list)
        self.showUserListStatButton.clicked.connect(self.show_user_list_stat)
        self.startServerButton.clicked.connect(self.start_server)

        self.init_window()

    def init_window(self):
        self.loginDb.clear()
        self.loginDb.insert('Ivan1')
        self.passwordDb.clear()
        self.passwordDb.insert('ivan123')
        self.serverPort.clear()
        self.serverPort.insert('3000')
        self.maxUsers.clear()
        self.maxUsers.insert('5')
        self.set_db_status('Не подключены к бд', 'red')
        self.set_socket_status('Сокет не подключен', 'red')

    def set_db_status(self, status: str, color: str):
        self.connectDbStatus.setText(status)
        self.connectDbStatus.setStyleSheet(f"color: {color};")

    def set_socket_status(self, status: str, color: str):
        self.serverStatus.setText(status)
        self.serverStatus.setStyleSheet(f"color: {color};")

    def render_server_status(self, server_status: dict[str, Any]):
        if server_status.get('socket_connected'):
            self.set_socket_status('Сокет подключен', 'green')
        else:
            self.set_socket_status('Сокет не подключен', 'red')

        if server_status.get('database_connected'):
            self.set_db_status('Подключены к бд', 'green')
        else:
            self.set_db_status('Не подключены к бд', 'red')

    def get_config(self) -> ServerConfig:
        login_db = self.loginDb.text()
        password_db = self.passwordDb.text()
        server_port = int(self.serverPort.text())
        server_max_users = int(self.maxUsers.text())
        config_dto = ServerConfig(
            login_db=login_db,
            password_db=password_db,
            server_port=server_port,
            server_max_users=server_max_users
        )
        return config_dto

    def block_input_widgets(self):
        self.loginDb.setReadOnly(True)
        self.loginDb.setStyleSheet("background-color: rgb(224, 224, 224);")
        self.passwordDb.setReadOnly(True)
        self.passwordDb.setStyleSheet("background-color: rgb(224, 224, 224);")
        self.maxUsers.setReadOnly(True)
        self.maxUsers.setStyleSheet("background-color: rgb(224, 224, 224);")
        self.serverPort.setReadOnly(True)
        self.serverPort.setStyleSheet("background-color: rgb(224, 224, 224);")
        self.startServerButton.blockSignals(True)

    def check_server_status(self):
        server_status = client_ui_talk.get_server_status()
        self.render_server_status(server_status)

    def start_external_async_loop(self):

        try:
            config_dto = self.get_config()
            client_ui_talk.put_client_config(config_dto)
            self.block_input_widgets()
            self._timer = QTimer()
            self._timer.timeout.connect(self.check_server_status)
            self._timer.start(1000)
            self.__class__.external_async_loop_trigger.emit()
        except Exception as exc:
            self.show_error(exc.__repr__())

    def show_error(self, error: str):
        self.widget = QtWidgets.QDialog()
        layout = QtWidgets.QVBoxLayout()
        error_label = QtWidgets.QLabel()
        error_label.setText(error)
        layout.addWidget(error_label)
        self.widget.setLayout(layout)

        self.widget.show()

    @Slot()
    def start_server(self):
        self.start_external_async_loop()

    def show(self):
        self.parent.show()

    def show_user_list_stat(self):
        self.user_list_stat = UserListStat.start_widget()
        self.user_list_stat.show()

    def show_user_list(self):
        self.user_list = UserList.start_widget()
        self.user_list.show()

    @classmethod
    def start_widget(cls, external_async_loop_trigger):
        cls.external_async_loop_trigger = external_async_loop_trigger
        path = Path(__file__).resolve().parent / cls.ui_path
        ui_file = QtCore.QFile(str(path))
        if not ui_file.open(QtCore.QIODevice.ReadOnly):
            reason = ui_file.errorString()
            print(f"Cannot open {path}: {reason}")
            sys.exit(-1)
        loader = QtUiTools.QUiLoader()
        widget = loader.load(ui_file, None)

        instance = cls(parent=widget)
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
        print(args)
        if not self.entry:
            raise Exception("No entry point for the Trio guest run was set.")
        trio.lowlevel.start_guest_run(
            self.entry,
            run_sync_soon_threadsafe=self.next_guest_run_schedule,
            done_callback=self.trio_done_callback,
        )

    def next_guest_run_schedule(self, fn):
        QApplication.postEvent(self.reenter_qt, self.ReenterQtEvent(fn))

    def trio_done_callback(self, outcome_):
        if isinstance(outcome_, outcome.Error):
            error = outcome_.error
            traceback.print_exception(type(error), error, error.__traceback__)


async def start_server():
    server_config_dto: ServerConfig = client_ui_talk.get_server_config()
    if server_config_dto:
        server_chat = ServerChat(
            port=server_config_dto.server_port,
            max_users=server_config_dto.server_max_users
        )
        client_ui_talk.put_client(server_chat)
        await server_chat.run()


async def async_task_creator():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(start_server)


def main():
    app = QApplication(sys.argv)
    async_helper = AsyncHelper()
    main_window = MainWindowContol.start_widget(async_helper.trigger_signal)
    client_ui_talk.put_window(main_window)

    async_helper.set_entry(async_task_creator)

    async_helper.trigger_signal.connect(async_helper.launch_guest_run)

    main_window.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.exec()


if __name__ == "__main__":
    main()
