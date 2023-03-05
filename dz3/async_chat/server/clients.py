import socket
from dataclasses import dataclass, field
from queue import Queue, Empty
from collections import defaultdict
import datetime as dt


@dataclass
class UsersMessages:
    _users_messages_queue: dict[int, Queue[str]] = field(
        default_factory=lambda: defaultdict(Queue)
    )
    _socket_messages_queue: dict[socket.socket, Queue[str]] = field(
        default_factory=lambda: defaultdict(Queue)
    )

    def get_all_messages_from_queue_for_socket(self, sock: socket.socket):
        messages = []
        try:
            while True:
                messages.append(
                    self.get_message_from_queue_from_socket(sock)
                )
        except Empty:
            return messages

    def get_all_messages_from_queue_for_user(self, user_id: int):
        messages = []
        try:
            while True:
                messages.append(
                    self.get_message_from_queue_from_user(user_id)
                )
        except Empty:
            return messages

    def put_message_to_queue_for_socket(self, sock: socket.socket, message: str) -> None:
        messages_queue = self._socket_messages_queue[sock]
        messages_queue.put(message)

    def get_message_from_queue_from_socket(self, sock: socket.socket) -> str:
        messages_queue = self._socket_messages_queue[sock]
        return messages_queue.get(block=False)

    def put_message_to_queue_for_user(self, user_id: int, message: str) -> None:
        self._users_messages_queue[user_id].put(message)

    def get_message_from_queue_from_user(self, user_id: int) -> str:
        messages_queue = self._users_messages_queue[user_id]
        return messages_queue.get(block=False)

    def _remove_closed_sockets(self):
        for sock in self._socket_messages_queue:
            if sock._closed:
                del self._socket_messages_queue[sock]


@dataclass
class Client:
    socket: socket.socket
    user_id: int | None = None
    time: dt.datetime = field(default_factory=dt.datetime.now)


class Clients:
    def __init__(self):
        self._clients: list[Client] = []

    def _find_client_by_socket(self, sock: socket.socket) -> int | None:
        for i in range(len(self._clients)):
            if self._clients[i].socket == sock:
                return i

    def get_client_by_socket(self, sock: socket.socket) -> Client:
        index = self._find_client_by_socket(sock)
        if index is None:
            return
        return self._clients[index]

    def append(self, client: Client):
        self._clients.append(client)

    def remove(self, obj: Client | socket.socket):
        if isinstance(obj, socket.socket):
            index = self._find_client_by_socket(obj)
            if index is None:
                return
            self._clients.pop(index)
        else:
            self._clients.remove(obj)

    def __iter__(self):
        for client in self._clients:
            yield client.socket

    def __bool__(self):
        return bool(self._clients)

    def __str__(self):
        return f'{self._clients}'
