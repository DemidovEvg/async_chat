import socket
import signal
import sys
import logging
import select
import time
import datetime as dt
from dataclasses import dataclass, field
from async_chat.server.users_sockets import UsersSockets
from async_chat.utils import Request, Response
from async_chat.server.clients import Client, Clients, UsersMessages
from async_chat.server.response_handler import ResponseHandler
from async_chat import jim

logger = logging.getLogger('server-logger')


def handler(signum, frame):
    signame = signal.Signals(signum).name
    print(f'Signal handler called with signal {signame} ({signum})')
    sys.exit(0)


@dataclass
class Sokets:
    for_reading: list[socket.socket] = field(default_factory=list)
    for_writing: list[socket.socket] = field(default_factory=list)
    for_error: list[socket.socket] = field(default_factory=list)


class ServerChat:
    def __init__(
        self, port: int,
        max_users: int,
        max_data_size: int = 1024,
        accept_timeout: float = 0.2,
        select_timeout: float = 10.0
    ):
        logger.debug(
            'Инициализируем сервер используя %s %s',
            port,
            max_users
        )
        self.port = port
        self.max_users = max_users
        self.max_data_size = max_data_size
        self.users_sockets = UsersSockets()
        self.accept_timeout = accept_timeout
        self.select_timeout = select_timeout
        self.clients = Clients()
        self.sockets = Sokets()
        self.users_messages = UsersMessages()
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, self.close_server)

    def close_server(self, signum, frame):
        signame = signal.Signals(signum).name
        print(f'Signal handler called with signal {signame} ({signum})')
        self.chat_socket.close()
        sys.exit(0)

    def init_socket(self) -> None:
        self.chat_socket = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM
        )
        self.chat_socket.bind(('localhost', self.port))
        self.chat_socket.listen(self.max_users)
        self.chat_socket.settimeout(self.accept_timeout)

    @classmethod
    def get_sockets(cls, clients: Clients, timeout: float) -> None | Sokets:
        try:
            r, w, e = select.select(
                clients,
                clients,
                [],
                timeout
            )
        except OSError:
            return
        return Sokets(for_reading=r, for_writing=w, for_error=e)

    def get_request(self, client: socket.socket) -> Request:
        incomming_bytes_data = client.recv(self.max_data_size)
        request = Request(incomming_bytes_data.decode())
        logger.debug('get_request: %s', request)
        return request

    def get_requests(self, sockets: Sokets) -> dict[socket.socket, Request]:
        requests = {}
        for sock in sockets.for_reading:
            try:
                requests[sock] = self.get_request(sock)
            except Exception:
                logger.debug(
                    'Клиент %s %s отключился',
                    sock.fileno(),
                    sock.getpeername()
                )
                self.clients.remove(sock)
        return requests

    def send_response(self, sock: socket.socket, response: Response) -> None:
        try:
            logger.debug(
                'send_response %s %s response=%s',
                sock.fileno(),
                sock.getpeername(),
                response
            )
            sock.send(response.encode())
        except OSError:
            logger.debug(
                'Клиент %s %s отключился',
                sock.fileno(),
                sock.getpeername()
            )
            sock.close()
            self.clients.remove(sock)

    def send_messages(self, sock: socket.socket, messages: list[str]) -> None:
        for message in messages:
            self.send_response(sock, Response(message))

    def processing_queues_messages(
        self,
        sockets: Sokets
    ) -> None:
        for sock in sockets.for_writing:
            client = self.clients.get_client_by_socket(sock)
            messages = []
            if client and client.user_id:
                messages = self.users_messages.get_all_messages_from_queue_for_user(
                    user_id=client.user_id
                )
            if client and not client.user_id:
                messages = self.users_messages.get_all_messages_from_queue_for_socket(
                    sock
                )
            if (client
                and client.user_id
                and not messages
                    and client.time + dt.timedelta(seconds=60) < dt.datetime.now()):
                client.time = dt.datetime.now()
                messages.append(jim.MessageProbe().json())
            logger.debug(
                'Отправляем сообщения для юзера user_id=%s', client.user_id
            )
            self.send_messages(sock, messages)

    def run(self) -> None:
        logger.debug('Старт цикла')
        while True:
            try:
                sock, addr = self.chat_socket.accept()
                logger.debug('Получен сокет %s', sock)
            except OSError:
                ...
                # logger.debug('Timeout ожидания подключений вышел')
            else:
                logger.debug('Получен запрос на соединение от %s', addr)
                self.clients.append(Client(socket=sock))
            finally:
                sockets = self.__class__.get_sockets(
                    clients=self.clients,
                    timeout=self.select_timeout
                )

            if not sockets:
                continue
            requests = self.get_requests(sockets)
            logger.debug('requests=%s', requests)
            if requests:
                self.dispatch_requests(requests)
            self.processing_queues_messages(sockets)
            time.sleep(2)

    def dispatch_requests(self, requests: dict[socket.socket, Request]) -> None:
        for sock, request in requests.items():
            if not request:
                continue
            logger.debug(
                'Пришел новый запрос request=%s', request
            )
            client = self.clients.get_client_by_socket(sock)
            response_handler = ResponseHandler(
                current_client=client,
                users_messages=self.users_messages
            )
            response_handler.processing_request(request)
