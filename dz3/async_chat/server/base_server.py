import socket
import json
import signal
import sys
from abc import ABC, abstractmethod
from typing import Any, Type
import logging

from async_chat import jim
from async_chat.server.db import UserService, SessionLocal
from async_chat.server.users_sockets import UsersSockets
from async_chat.utils import Request, Response, MessageDto, get_message_dto_, T

logger = logging.getLogger('server-logger')


def handler(signum, frame):
    signame = signal.Signals(signum).name
    print(f'Signal handler called with signal {signame} ({signum})')
    sys.exit(0)


class BaseServerChat(ABC):
    def __init__(self, port: int, max_users: int, max_data_size: int = 1024):
        logger.debug(
            'Инициализируем сервер используя %s %s',
            port,
            max_users
        )
        self.port = port
        self.max_users = max_users
        self.max_data_size = max_data_size
        self.users_sockets = UsersSockets()
        signal.signal(signal.SIGTERM, handler)

    @staticmethod
    def get_message_dto(schema: Type[T], data: dict[str, Any]) -> MessageDto[T]:
        return get_message_dto_(
            schema=schema,
            data=data
        )

    def send_response(self, client: socket.socket, response: Response) -> None:
        logger.debug('send_response: %s', response)
        client.send(response.encode())

    def get_request(self, client: socket.socket) -> Request:
        incomming_bytes_data = client.recv(self.max_data_size)
        request = Request(incomming_bytes_data.decode())
        logger.debug('get_request: %s', request)
        return request

    @abstractmethod
    def login_user(self, data: dict[str, Any]) -> Response:
        pass

    @abstractmethod
    def logout_user(self, data: dict[str, Any]) -> Response:
        pass

    @abstractmethod
    def join_user_to_room(self) -> Response:
        pass

    @abstractmethod
    def leave_user_from_room(self) -> Response:
        pass

    @abstractmethod
    def processing_presence(self, data: dict[str, Any]) -> Response:
        pass

    def init_socket(self) -> None:
        self.chat_socket = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM
        )
        self.chat_socket.bind(('localhost', self.port))
        self.chat_socket.listen(self.max_users)

    def start_loop(self) -> None:
        while True:
            logger.debug('Ждем очередной запрос')
            client, addr = self.chat_socket.accept()
            self.current_client: socket.socket = client
            self.current_address: tuple[str, int] = addr
            self.current_user = None

            logger.debug(
                'Пришел новый запрос',
                extra=dict(
                    address=f'{self.current_address[0]}:{self.current_address[1]}'
                )
            )

            with SessionLocal() as session:
                user_service = UserService(session=session)
                self.current_user = user_service.get_online_user_by_address(
                    self.current_address
                )

            request = self.get_request(client=client)
            response = self.processing_request(request)
            self.send_response(client=client, response=response)
            client.close()

    def processing_request(self, request: Request) -> Response:
        try:
            data: dict[str, Any] = json.loads(request)
        except json.decoder.JSONDecodeError as exc:
            logger.error('error=%s with request=%s', str(exc), request)
            return Response(jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error=str(exc)).json())
        response = self.dispatch(data)
        return response

    @abstractmethod
    def dispatch(self, incomming_data: dict[str, Any]) -> Response:
        pass
