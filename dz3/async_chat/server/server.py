import signal
import sys
from typing import Any, TypeVar
from pydantic import BaseModel
import logging
from async_chat import jim
from async_chat.server.db import UserService, SessionLocal
from async_chat.utils import Request, Response
from async_chat.server.base_server import BaseServerChat

logger = logging.getLogger('server-logger')

T = TypeVar('T', bound=BaseModel)


def handler(signum, frame):
    signame = signal.Signals(signum).name
    logger.debug(f'Signal handler called with signal {signame} ({signum})')
    sys.exit(0)


class ServerChat(BaseServerChat):
    def login_user(self, data: dict[str, Any]) -> Response:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserAuth,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            return Response(message_dto.error_message)

        if not message_dto.message_model:
            logger.error(
                f'Could not get message_model for '
                f'schema=jim.MessageUserAuth '
                f'for data={data}'
            )
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
                logger.error(
                    f'Bad password or login for data={data} '
                )
                return Response(error_message)

            if user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_409_CONFLICT,
                    error="User already login"
                ).json()
                logger.error(
                    f'User already login for data={data} '
                )
                return Response(error_message)
            user_service.login(current_user, message_model.time)
            current_user.address = str(self.current_address)
            self.users_sockets.add_client(
                user_id=current_user.id,
                client=self.current_client
            )
            logger.debug(
                'login_user: %s current_user=%s', message_model, current_user
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
            logger.error(
                'error=%s with data=%s',
                message_dto.error_message,
                message_dto.json()
            )
            return Response(message_dto.error_message)

        if not message_dto.message_model:
            logger.error(
                'Could not get message_model for '
                'schema=jim.MessageUserQuit '
                'for data=%s',
                data
            )
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
                logger.error(
                    f'Bad account_name for data={data} '
                )
                return Response(error_message)
            if not user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error="User already offline"
                ).json()
                logger.error(
                    f'User already offline data={data} '
                )
                return Response(error_message)
            user_service.logout(current_user, message_model.time)
            current_user.address = str(self.current_address)
            self.users_sockets.drop_client(current_user.id)
            logger.debug(
                'logout_user: %s current_user=%s',
                message_dto,
                current_user
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
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            return Response(message_dto.error_message)

        if not message_dto.message_model:
            logger.error(
                f'Could not get message_model for '
                f'schema=jim.MessageUserPresence '
                f'for data={data}'
            )
            raise Exception('Could not get message_model for message')

        message_model: jim.MessageUserPresence = message_dto.message_model
        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                account_name=message_model.user.account_name
            )
            if not current_user:
                error_response = Response(jim.MessageError(
                    response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                    error='User not found'
                ).json())
                logger.error(
                    f'User not found for data={data} '
                )
                return error_response

            if not user_service.is_online(user=current_user):
                error_response = Response(jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Auth required'
                ).json())
                logger.error(
                    f'Auth required for data={data} '
                )
                return error_response
            user_service.presence(
                user=current_user,
                time=message_model.time
            )
            current_user.address = str(self.current_address)
            logger.debug(
                'processing_presence: %s current_user=%s',
                message_dto,
                current_user
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
                logger.error(
                    f'Field action is required for incomming_data={incomming_data} '
                )
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
                logger.error(
                    f'Unknown action for incomming_data={incomming_data} '
                )
                return Response(jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error='Unknown action'
                ).json())
        except Exception as exc:
            logger.error(
                f'ERROR={exc} for incomming_data={incomming_data} '
            )
            return Response(jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error=str(exc)
            ).json())
