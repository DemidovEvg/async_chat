import socket
import json
import signal
import sys
from typing import Any, Generic, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

from .. import jim
from .db import UserService, SessionLocal
from .users_sockets import UsersSockets


T = TypeVar('T', bound=BaseModel)


def handler(signum, frame):
    signame = signal.Signals(signum).name
    print(f'Signal handler called with signal {signame} ({signum})')
    sys.exit(0)


class MessageDto(GenericModel, Generic[T]):
    message_model: T | None
    error_message: str | None


class ServerChat:
    class_validator = jim.DataValidator

    def __init__(self, port: int, max_users: int, max_data_size: int = 1024):
        self.port = port
        self.max_users = max_users
        self.max_data_size = max_data_size
        self.users_sockets = UsersSockets()
        signal.signal(signal.SIGTERM, handler)

    def get_message_dto(self, schema: T, data: dict[str, Any]) -> MessageDto[T]:
        validator = self.__class__.class_validator[schema](
            schema=schema,
            data=data
        )
        message_dto = MessageDto[schema]()
        if not validator.is_valid():
            message_dto.error_message = jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error=str(validator.get_error())
            ).json()
            return message_dto
        message_dto.message_model = validator.get_model()
        return message_dto

    def get_message(self):
        pass

    def send_message(self, client: socket.socket, data: str):
        client.send(data.encode())

    def login_user(self, data: dict[str, Any]):
        message_dto = self.get_message_dto(
            schema=jim.MessageUserAuth,
            data=data
        )
        if message_dto.error_message:
            return message_dto.error_message
        message_model: jim.MessageUserAuth = message_dto.message_model

        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                message_model.user.account_name
            )
            found_user = True if current_user else False
            password_correct = found_user and user_service.check_password(
                user=current_user,
                password=message_model.user.password
            )
            if not found_user or not password_correct:
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_402_BAD_PASSWORD_OR_LOGIN,
                    error="Bad password or login"
                ).json()
                return error_message
            if user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_409_CONFLICT,
                    error="User already login"
                ).json()
                return error_message
            user_service.login(current_user, message_model.time)
            current_user.address = str(self.current_address)
            self.users_sockets.add_client(
                user_id=current_user.id,
                client=self.current_client
            )
            print(
                f'login_user: {message_dto} current_user={current_user}'
            )
            session.commit()
        ok_message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        return ok_message

    def logout_user(self, data: dict[str, Any]):
        message_dto = self.get_message_dto(
            schema=jim.MessageUserQuit,
            data=data
        )
        if message_dto.error_message:
            return message_dto.error_message
        message_model: jim.MessageUserQuit = message_dto.message_model

        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                message_model.user.account_name
            )
            if not current_user:
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                    error="Bad account_name"
                ).json()
                return error_message
            if not user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error="User already offline"
                ).json()
                return error_message
            user_service.logout(current_user, message_model.time)
            current_user.address = str(self.current_address)
            self.users_sockets.drop_client(current_user.id)
            print(
                f'logout_user: {message_dto} current_user={current_user}'
            )
            session.commit()

        ok_message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        return ok_message

    def probe_user(self):
        pass

    def join_user_to_room(self):
        pass

    def leave_user_from_room(self):
        pass

    def processing_presence(self, data: dict[str, Any]):
        message_dto = self.get_message_dto(
            schema=jim.MessageUserPresence,
            data=data
        )
        if message_dto.error_message:
            return message_dto.error_message
        message_model: jim.MessageUserPresence = message_dto.message_model
        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                account_name=message_model.user.account_name
            )
            if not current_user:
                return jim.MessageError(
                    response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                    error='User not found'
                ).json()
            if not user_service.is_online(user=current_user):
                return jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Auth required'
                ).json()
            user_service.presence(
                user=current_user,
                time=message_model.time
            )
            current_user.address = str(self.current_address)
            print(
                f'processing_presence: {message_dto} current_user={current_user}'
            )
            session.commit()
        return jim.MessageAlert(
            response=jim.StatusCodes.HTTP_202_ACCEPTED,
            alert='Presense accepted'
        ).json()

    def init_socket(self):
        self.chat_socket = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM
        )
        self.chat_socket.bind(('localhost', self.port))
        self.chat_socket.listen(self.max_users)

    def start_loop(self):
        while True:
            print('Ждем очередной запрос')
            client, addr = self.chat_socket.accept()
            self.current_client: socket.socket = client
            self.current_address: tuple[str, int] = addr
            self.current_user = None

            with SessionLocal() as session:
                user_service = UserService(session=session)
                self.current_user = user_service.get_online_user_by_address(
                    self.current_address
                )

            incomming_bytes_data = client.recv(self.max_data_size)
            response: str = self.processing_request(incomming_bytes_data)
            print(response)
            client.send(response.encode())
            client.close()

    def processing_request(self, incomming_bytes_data: bytes):
        try:
            data: dict[str, Any] = json.loads(incomming_bytes_data)
        except json.decoder.JSONDecodeError as exc:
            return jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error=str(exc)
            ).json()
        response: str = self.dispatch(data)
        return response

    def dispatch(self, incomming_data: dict[str, Any]):
        action = incomming_data.get('action')
        if not action:
            return jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error='Field action is required'
            ).json()
        if action == 'authenticate':
            return self.login_user(data=incomming_data)
        elif action == 'presense':
            return self.processing_presence(data=incomming_data)
        elif action == 'quit':
            return self.logout_user(data=incomming_data)
        else:
            return jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error='Unknown action'
            ).json()
