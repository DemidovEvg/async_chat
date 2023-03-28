import socket
import signal
import sys
import logging
import select
import datetime as dt
import trio
import sqlalchemy as sa
from dataclasses import dataclass, field
from async_chat.utils import Request, Response
from async_chat.server.clients import Client, Clients
from async_chat.server.db import SessionLocal, User
from async_chat.server.user_service import UserService
from async_chat.server.response_handler import ResponseHandler
from async_chat import jim
from async_chat.server.server_verifier import ServerVerifier
from async_chat.utils import decrypt, load_keys

logger = logging.getLogger('server-logger')


@dataclass
class Sokets:
    for_reading: list[socket.socket] = field(default_factory=list)
    for_writing: list[socket.socket] = field(default_factory=list)
    for_error: list[socket.socket] = field(default_factory=list)


class PortDescriptor:
    def __set_name__(self, owner, name):
        self.public_name = 'port_' + name

    def __init__(
        self,
        default: int | None = None,
        minvalue: int | None = None,
        maxvalue: int | None = None
    ):
        self.default = default
        self.minvalue = minvalue
        self.maxvalue = maxvalue

    def __get__(self, owner, objtype=None):
        return getattr(owner, self.public_name)

    def __set__(self, owner, value=None):
        if not value and self.default is None:
            raise TypeError(
                f'{self.public_name} is None and set no default value'
            )
        if not value and self.default is not None:
            value = self.default

        if self.minvalue is not None and value < self.minvalue:
            raise ValueError(f'port num cannot be less than {self.minvalue}')
        if self.maxvalue is not None and value > self.maxvalue:
            raise ValueError(f'port num cannot be bigger than {self.maxvalue}')

        setattr(owner, self.public_name, value)


class ServerSocket(socket.socket):
    port = PortDescriptor(default=3000, minvalue=0)

    def bind(self, addr: tuple[str, int] | tuple[str]) -> None:
        self.ip = addr[0]
        self.port = addr[1] if len(addr) == 2 else None
        newaddr = (self.ip, self.port)
        print(newaddr)
        super().bind(newaddr)


class ServerChat(metaclass=ServerVerifier):

    def __init__(
        self, port: int,
        max_users: int,
        accept_timeout: float = 0.02,
        select_timeout: float = 0.03
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
        self.throttle = 0.01
        self.period_probe = dt.timedelta(seconds=20)
        self.socket_connected = False
        private_key, _ = load_keys()
        self.private_key = private_key
        signal.signal(signal.SIGTERM, self.close_server)
        signal.signal(signal.SIGINT, self.close_server)

    @property
    def database_connected(self):
        try:
            with SessionLocal() as session:
                session.scalars(sa.select(User)).all()
        except Exception:
            return False
        return True

    def close_server(self, signum, frame):
        signame = signal.Signals(signum).name
        logger.info(f'Signal handler called with signal {signame} ({signum})')
        self.chat_socket.close()
        sys.exit(0)

    def init_socket(self) -> None:
        self.chat_socket = ServerSocket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM
        )
        self.chat_socket.bind(('localhost', self.port))
        self.chat_socket.listen(self.max_users)
        self.chat_socket.settimeout(self.accept_timeout)
        self.socket_connected = True

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
        chunks = []
        bytes_recd = 0
        while bytes_recd < message_size:
            chunk = sock.recv(min(message_size - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        data_bytes = b''.join(chunks)
        request = Request(
            decrypt(data_bytes, self.private_key)
        )
        logger.debug('get_request: %s', request)
        with SessionLocal() as session:
            client = self.clients.get_client_by_socket(sock)
            user_service = UserService(session=session)
            user_service.user_send_message_to_server(
                user=client.user_id,
                adress=client.socket.getsockname()[0]
            )
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
        with SessionLocal() as session:
            UserService(session).user_get_message_from_server(
                user=client.user_id,
                adress=client.socket.getsockname()[0]
            )
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
                    client.user_id,
                    str(response)
                )

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
                    and client.time + self.period_probe < dt.datetime.now()):
                client.time = dt.datetime.now()
                message = jim.MessageProbe().json()

            # if client.user_id and message:
            #     logger.debug(
            #         'Отправляем сообщения для юзера user_id=%s', client.user_id
            #     )
            # else:
            #     logger.debug(
            #         'Отправляем сообщения для sock=%s', sock
            #     )

            self.send_message(client, message)

    async def run(self) -> None:
        self.init_socket()
        logger.debug('Старт цикла')
        while True:
            try:
                sock, addr = self.chat_socket.accept()
                # Сервер запущен
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
            await trio.sleep(self.throttle)
            print(len(self.clients))

            if not sockets:
                continue
            requests = self.get_requests(sockets)
            logger.debug('requests_len=%s', len(requests))
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
