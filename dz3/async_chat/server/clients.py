import socket
from dataclasses import dataclass, field
from collections import defaultdict, deque
import datetime as dt
from async_chat.server import db


@dataclass
class UsersMessages:
    _users_messages_queue: dict[int, deque[str]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    _socket_messages_queue: dict[socket.socket, deque[str]] = field(
        default_factory=lambda: defaultdict(deque)
    )

    def get_all_messages_from_queue(self, target: int | socket.socket):
        messages = []
        try:
            while True:
                messages.append(self.get_message_from_queue(target))
        except IndexError:
            return messages

    def get_message_from_queue(self, target: int | socket.socket) -> str:
        messages_queue = self.get_queue_for_target(target)
        try:
            return messages_queue.popleft()
        except IndexError:
            return None

    def put_message_to_queue(self, target: int | socket.socket, message: str) -> None:
        messages_queue = self.get_queue_for_target(target)
        messages_queue.append(message)

    def put_back_message_to_queue(self, target: int | socket.socket, message: str) -> None:
        messages_queue = self.get_queue_for_target(target)
        messages_queue.appendleft(message)

    def get_queue_for_target(self, target: int | socket.socket) -> deque:
        if isinstance(target, int):
            sock: socket.socket = target
            messages_queue = self._socket_messages_queue[sock]
        else:
            user_id: int = target
            messages_queue = self._socket_messages_queue[user_id]
        return messages_queue

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
        self.all_clients: list[Client] = []
        self.users_messages = UsersMessages()
        self._rooms: dict[str, dict[int, Client]] = defaultdict(dict)
        self._room_by_user_id: dict[int, str] = {}
        self.default_room = 'common'

    def get_room_name(self, client: Client):
        if not client.user_id:
            raise Exception('No client.user_id')
        if client.user_id not in self._room_by_user_id:
            return self.default_room
        return self._room_by_user_id[client.user_id]

    def _leave_current_room(self, user_id: int) -> None:
        room = self._room_by_user_id.get(user_id)
        if not room:
            return
        if room in self._rooms and user_id in self._rooms[room]:
            del self._rooms[room][user_id]

    def get_users_ids_in_room(self, room: str | None) -> list[int]:
        if not room or room == self.default_room:
            return [client.user_id for client in self.all_clients]
        if room in self._rooms:
            return list(self._rooms[room].keys())
        return []

    def join_to_room(self, client: Client, room: str) -> None:
        if not client.user_id:
            raise Exception('No client.user_id')
        self._leave_current_room(client.user_id)
        self._rooms[room][client.user_id] = client
        self._room_by_user_id[client.user_id] = room

    def _find_client_by_socket(self, sock: socket.socket) -> int | None:
        for i in range(len(self.all_clients)):
            if self.all_clients[i].socket == sock:
                return i

    def _find_client_by_user_id(self, user_id: int) -> int | None:
        for i in range(len(self.all_clients)):
            if self.all_clients[i].user_id == user_id:
                return i

    def get_client_by_socket(self, sock: socket.socket) -> Client:
        index = self._find_client_by_socket(sock)
        if index is None:
            return
        return self.all_clients[index]

    def append(self, client: Client):
        self.all_clients.append(client)

    def logout_client(self, client: Client):
        with db.SessionLocal() as session:
            user_service = db.UserService(session=session)
            user_service.logout(client.user_id)

    def remove_another_client_with_user(self, user_id: int) -> None:
        index = self._find_client_by_user_id(user_id)
        if index is None:
            return
        del self.all_clients[index]

    def remove(self, obj: Client | socket.socket):
        if isinstance(obj, socket.socket):
            index = self._find_client_by_socket(obj)
            if index is None:
                return
            self.all_clients.pop(index)
        else:
            client = obj
            self.all_clients.remove(client)
            if not client.user_id:
                return
            self.logout_client(client)
            room = self._room_by_user_id.get(client.user_id)
            if not room:
                return
            self._leave_current_room(client.user_id)

    def __iter__(self):
        for client in self.all_clients:
            yield client.socket

    def __bool__(self):
        return bool(self.all_clients)

    def __str__(self):
        return f'{self.all_clients}'
