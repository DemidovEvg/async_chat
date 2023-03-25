import typing
from typing import TypeVar, Generic
from queue import Queue
from pydantic import BaseModel
import trio
if typing.TYPE_CHECKING:
    from project.async_chat.client.client_ui.client_ui import ClientConfig
    from async_chat.client import ClientChat

UI = TypeVar('UI')


class ClientUiTalk(Generic[UI]):
    def __init__(self):
        self.ui: UI | None = None
        self.client_config: ClientConfig | None = None
        self.client_chat: ClientChat | None = None

        send, receive = trio.open_memory_channel(100000)
        self.receive_channel_to_ui: trio.MemoryReceiveChannel = receive
        self.send_channel_to_ui: trio.MemorySendChannel = send

        send, receive = trio.open_memory_channel(100000)
        self.receive_channel_to_client: trio.MemoryReceiveChannel = receive
        self.send_channel_to_client: trio.MemorySendChannel = send

        send, receive = trio.open_memory_channel(100000)
        self.receive_channel_outgoing: trio.MemoryReceiveChannel = receive
        self.send_channel_outgoing: trio.MemorySendChannel = send

        self.error_from_server = Queue()

    def get_message_to_ui(self) -> BaseModel | None:
        try:
            return self.receive_channel_to_ui.receive_nowait()
        except trio.WouldBlock:
            pass

    def put_message_to_ui(self, message_model: BaseModel) -> None:
        try:
            self.send_channel_to_ui.send_nowait(message_model)
        except trio.WouldBlock:
            pass

    def get_outgoing_message(self) -> BaseModel | None:
        try:
            return self.receive_channel_outgoing.receive_nowait()
        except trio.WouldBlock:
            pass

    def put_outgoing_message(self, message_model: BaseModel) -> None:
        try:
            self.send_channel_outgoing.send_nowait(message_model)
        except trio.WouldBlock:
            pass

    def get_command_to_client(self) -> str | None:
        try:
            return self.receive_channel_to_client.receive_nowait()
        except trio.WouldBlock:
            pass

    async def put_command_to_client(self, command: str) -> None:
        await self.send_channel_to_client.send(command)

    def put_ui(self, ui: UI) -> None:
        self.ui = ui

    def get_ui(self) -> UI:
        if self.ui:
            return self.ui
        raise Exception('No ui')

    def put_client(self, client_chat: 'ClientChat') -> None:
        self.client_chat = client_chat

    def get_client(self) -> 'ClientChat':
        return self.client_chat

    def put_client_config(self, client_config_dto: 'ClientChat') -> None:
        self.client_config = client_config_dto

    def get_client_config(self) -> 'ClientChat':
        return self.client_config

    def set_connected(self, connected, message: str) -> None:
        self.connected = connected
        self.message = message

    def get_connected(self) -> bool:
        return getattr(self, 'connected', False)
