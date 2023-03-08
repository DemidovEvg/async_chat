import socket
import signal
import sys
import logging
import select
# import time
import datetime as dt
from dataclasses import dataclass, field
from async_chat.utils import Request, Response
from async_chat.server.clients import Client, Clients
from async_chat.server.response_handler import ResponseHandler
from async_chat import jim

logger = logging.getLogger('server-logger')


@dataclass
class Sokets:
    for_reading: list[socket.socket] = field(default_factory=list)
    for_writing: list[socket.socket] = field(default_factory=list)
    for_error: list[socket.socket] = field(default_factory=list)


class ServerChat:
    def __init__(
        self, port: int,
        max_users: int,
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
        self.accept_timeout = accept_timeout
        self.select_timeout = select_timeout
        self.clients = Clients()
        self.sockets = Sokets()
        self.message_head_size = 4
        signal.signal(signal.SIGTERM, self.close_server)
        signal.signal(signal.SIGINT, self.close_server)

    def close_server(self, signum, frame):
        signame = signal.Signals(signum).name
        logger.info(f'Signal handler called with signal {signame} ({signum})')
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

    def get_message_size(self, head: str) -> int:
        return int(head, 16)

    def get_request(self, sock: socket.socket) -> Request:
        message_head = (
            sock.recv(self.message_head_size).decode()
        )
        if len(message_head) == 0:
            return
        message_size = self.get_message_size(message_head)
        request = Request(
            sock.recv(message_size).decode()
        )
        logger.debug('get_request: %s', request)
        return request

    def get_requests(self, sockets: Sokets) -> dict[socket.socket, Request]:
        requests = {}
        for sock in sockets.for_reading:
            client = self.clients.get_client_by_socket(sock)
            try:
                requests[sock] = self.get_request(sock)
            except Exception:
                logger.debug(
                    'Клиент %s %s отключился',
                    sock.fileno(),
                    sock.getpeername()
                )
                client.socket.close()
                self.clients.remove(client)
        return requests

    def form_data(self, data: str) -> bytes:
        length = len(data.encode())
        hex_legth = hex(length)[2:]
        head_message = f'00{hex_legth}'[-4:]
        return f'{head_message}{data}'.encode()

    def send_response(self, client: Client, response: Response) -> None:
        try:
            logger.debug(
                'send_response %s %s response=%s',
                client.socket.fileno(),
                client.socket.getpeername(),
                response
            )
            client.socket.send(self.form_data(str(response)))
        except OSError:
            logger.debug(
                'Клиент %s %s отключился',
                client.socket.fileno(),
                client.socket.getpeername()
            )
            if client.user_id:
                self.clients.users_messages.put_back_message_to_queue(
                    str(response))

            client.socket.close()
            self.clients.remove(client)

    def send_message(self, client: Client, message: str) -> None:
        if message:
            self.send_response(client, Response(message))

    def processing_queues_messages(
        self,
        sockets: Sokets
    ) -> None:
        for sock in sockets.for_writing:
            client = self.clients.get_client_by_socket(sock)
            message = None
            if not client:
                continue
            if client.user_id:
                message = self.clients.users_messages.get_message_from_queue(
                    target=client.user_id
                )
            if not message:
                message = self.clients.users_messages.get_message_from_queue(
                    target=sock
                )
            if (client.user_id
                and not message
                    and client.time + dt.timedelta(seconds=20) < dt.datetime.now()):
                client.time = dt.datetime.now()
                message = jim.MessageProbe().json()

            if client.user_id and message:
                logger.debug(
                    'Отправляем сообщения для юзера user_id=%s', client.user_id
                )
            else:
                logger.debug(
                    'Отправляем сообщения для sock=%s', sock
                )

            self.send_message(client, message)

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

            print(self.clients)

            if not sockets:
                continue
            requests = self.get_requests(sockets)
            logger.debug('requests=%s', requests)
            if requests:
                self.dispatch_requests(requests)
            self.processing_queues_messages(sockets)

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
                clients=self.clients
            )
            response_handler.processing_request(request)
