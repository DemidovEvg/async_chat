import typing
if typing.TYPE_CHECKING:
    from async_chat.server.admin_ui.main import MainWindowContol, ServerConfig
    from async_chat.server import ServerChat


class ServerUiTalk:
    def __init__(self):
        self.server_config: ServerConfig | None = None
        self.main_window_control: MainWindowContol | None = None
        self.chat_server: ServerChat | None = None

    def put_window(self, main_window_control: 'MainWindowContol') -> None:
        self.main_window_control = main_window_control

    def put_server(self, server_chat: 'ServerChat') -> None:
        self.server_chat = server_chat

    def put_server_config(self, server_config_dto: 'ServerConfig') -> None:
        self.server_config = server_config_dto

    def get_server_config(self) -> 'ServerConfig':
        return self.server_config

    def get_server_status(self):
        if self.server_chat:
            return {
                'database_connected': self.server_chat.database_connected,
                'socket_connected': self.server_chat.socket_connected
            }
        return None


server_ui_talk = ServerUiTalk()
