import signal
import sys
from typing import Any, TypeVar
from pydantic import BaseModel

from async_chat import jim
from async_chat.server.db import UserService, SessionLocal
from async_chat.utils import Request, Response
from async_chat.server.base_server import BaseServerChat

T = TypeVar('T', bound=BaseModel)


def handler(signum, frame):
    signame = signal.Signals(signum).name
    print(f'Signal handler called with signal {signame} ({signum})')
    sys.exit(0)


class ServerChat(BaseServerChat):
    def login_user(self, data: dict[str, Any]) -> Response:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserAuth,
            data=data
        )
        if message_dto.error_message:
            return Response(message_dto.error_message)

        if not message_dto.message_model:
            raise Exception('Could not get message_model for message')

        message_model: jim.MessageUserAuth = message_dto.message_model

        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                message_model.user.account_name
            )
            if not current_user or not user_service.check_password(
                user=current_user,
                password=message_model.user.password
            ):

                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_402_BAD_PASSWORD_OR_LOGIN,
                    error="Bad password or login"
                ).json()
                return Response(error_message)

            if user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_409_CONFLICT,
                    error="User already login"
                ).json()
                return Response(error_message)
            user_service.login(current_user, message_model.time)
            current_user.address = str(self.current_address)
            self.users_sockets.add_client(
                user_id=current_user.id,
                client=self.current_client
            )
            print(
                f'login_user: {message_model} current_user={current_user}'
            )
            session.commit()
        ok_message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        return Response(ok_message)

    def logout_user(self, data: dict[str, Any]) -> Response:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserQuit,
            data=data
        )
        if message_dto.error_message:
            return Response(message_dto.error_message)

        if not message_dto.message_model:
            raise Exception('Could not get message_model for message')

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
                return Response(error_message)
            if not user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error="User already offline"
                ).json()
                return Response(error_message)
            user_service.logout(current_user, message_model.time)
            current_user.address = str(self.current_address)
            self.users_sockets.drop_client(current_user.id)
            print(
                f'logout_user: {message_dto} current_user={current_user}'
            )
            session.commit()

        ok_message = Request(jim.MessageAlert(
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json())
        return Response(ok_message)

    def join_user_to_room(self):
        pass

    def leave_user_from_room(self):
        pass

    def processing_presence(self, data: dict[str, Any]) -> Response:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserPresence,
            data=data
        )
        if message_dto.error_message:
            return Response(message_dto.error_message)

        if not message_dto.message_model:
            raise Exception('Could not get message_model for message')

        message_model: jim.MessageUserPresence = message_dto.message_model
        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                account_name=message_model.user.account_name
            )
            if not current_user:
                return Response(jim.MessageError(
                    response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                    error='User not found'
                ).json())
            if not user_service.is_online(user=current_user):
                return Response(jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Auth required'
                ).json())
            user_service.presence(
                user=current_user,
                time=message_model.time
            )
            current_user.address = str(self.current_address)
            print(
                f'processing_presence: {message_dto} current_user={current_user}'
            )
            session.commit()
        return Response(jim.MessageAlert(
            response=jim.StatusCodes.HTTP_202_ACCEPTED,
            alert='Presense accepted'
        ).json())

    def dispatch(self, incomming_data: dict[str, Any]) -> Response:
        action = incomming_data.get('action')
        try:
            if not action:
                return Response(jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error='Field action is required'
                ).json())
            if action == 'authenticate':
                return self.login_user(data=incomming_data)
            elif action == 'presense':
                return self.processing_presence(data=incomming_data)
            elif action == 'quit':
                return self.logout_user(data=incomming_data)
            else:
                return Response(jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error='Unknown action'
                ).json())
        except Exception as exc:
            return Response(jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error=str(exc)
            ).json())
