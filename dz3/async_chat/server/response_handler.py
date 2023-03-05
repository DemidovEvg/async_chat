import json
from typing import Any, Type
import logging
from async_chat import jim
from async_chat.server.db import UserService, SessionLocal
from async_chat.server.clients import Client, UsersMessages
from async_chat.utils import Request, Response, MessageDto, get_message_dto_, T

logger = logging.getLogger('server-logger')


class ResponseHandler:
    def __init__(self, current_client: Client, users_messages: UsersMessages):
        self.current_client = current_client
        self.users_messages = users_messages

    def put_message_for_client(self, message: str, client: Client | None = None):
        if not client:
            client = self.current_client
        if self.current_client.user_id:
            self.users_messages.put_message_to_queue_for_user(
                user_id=self.current_client.user_id,
                message=message
            )
        else:
            self.users_messages.put_message_to_queue_for_socket(
                sock=self.current_client.socket,
                message=message
            )

    def put_message_for_all_users_exclude_current(self, message: str):
        for user_id in self.users_messages._users_messages_queue.keys():
            if user_id != self.current_client.user_id:
                self.users_messages.put_message_to_queue_for_user(
                    user_id=user_id,
                    message=message
                )

    @staticmethod
    def get_message_dto(schema: Type[T], data: dict[str, Any]) -> MessageDto[T]:
        return get_message_dto_(
            schema=schema,
            data=data
        )

    def processing_request(self, request: Request) -> None:
        try:
            data: dict[str, Any] = json.loads(request)
        except json.decoder.JSONDecodeError as exc:
            logger.error('error=%s with request=%s', str(exc), request)
            return Response(jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error=str(exc)).json())
        response = self.dispatch_request(data)
        return response

    def dispatch_request(self, incomming_data: dict[str, Any]) -> Response:
        action = incomming_data.get('action')
        try:
            if not action:
                logger.error(
                    f'Field action is required for incomming_data={incomming_data} '
                )
                message_error = jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error='Field action is required'
                ).json()
                self.put_message_for_client(message_error)
                return
            if action == 'authenticate':
                return self.login_user(data=incomming_data)
            elif action == 'presense':
                return self.processing_presence(data=incomming_data)
            elif action == 'quit' or action == 'logout':
                return self.logout_user(data=incomming_data)
            elif action == 'msg':
                return self.processing_message(data=incomming_data)
            else:
                logger.error(
                    f'Unknown action for incomming_data={incomming_data} '
                )
                message_error = jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error='Unknown action'
                ).json()
                self.put_message_for_client(message_error)
                return
        except Exception as exc:
            logger.error(
                f'ERROR={exc} for incomming_data={incomming_data} '
            )
            message_error = jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error=str(exc)
            ).json()
            self.put_message_for_client(message_error)
            return

    def login_user(self, data: dict[str, Any]) -> Response:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserAuth,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            self.put_message_for_client(message_dto.error_message)
            return

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
                self.put_message_for_client(error_message)
                return

            if user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_409_CONFLICT,
                    error="User already login"
                ).json()
                logger.error(
                    f'User already login for data={data} '
                )
                self.put_message_for_client(error_message)
                return
            user_service.login(current_user, message_model.time)
            self.current_client.user_id = current_user.id
            logger.debug(
                'login_user: %s current_user=%s', message_model, current_user
            )
            session.commit()
        ok_message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_client(ok_message)

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
            self.put_message_for_client(message_dto.error_message)
            return

        if not message_dto.message_model:
            logger.error(
                'Could not get message_model for '
                'schema=jim.MessageUserQuit '
                'for data=%s',
                data
            )
            raise Exception('Could not get message_model for message')

        message_model: jim.MessageUserQuit = message_dto.message_model
        ok_message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_client(ok_message)

        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                message_model.user.account_name
            )

            if current_user and user_service.is_online(current_user):
                user_service.logout(current_user, message_model.time)
                logger.debug(
                    'logout_user: %s current_user=%s',
                    message_dto,
                    current_user
                )
                session.commit()

    def join_user_to_room(self):
        pass

    def leave_user_from_room(self):
        pass

    def processing_presence(self, data: dict[str, Any]) -> None:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserPresence,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            self.put_message_for_client(message_dto.error_message)
            return

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
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                    error='User not found'
                ).json()
                logger.error(
                    f'User not found for data={data} '
                )
                self.put_message_for_client(error_message)
                return

            if not user_service.is_online(user=current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Auth required'
                ).json()
                logger.error(
                    f'Auth required for data={data} '
                )
                self.put_message_for_client(error_message)
                return

            user_service.presence(
                user=current_user,
                time=message_model.time
            )
            logger.debug(
                'processing_presence: %s current_user=%s',
                message_dto,
                current_user
            )
            session.commit()
        message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_202_ACCEPTED,
            alert='Presense accepted'
        ).json()
        self.put_message_for_client(message)
        return

    def processing_message(self, data: dict[str, Any]) -> None:
        message_dto = self.get_message_dto(
            schema=jim.MessageSendMessage,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            self.put_message_for_client(message_dto.error_message)
            return

        if not message_dto.message_model:
            logger.error(
                f'Could not get message_model for '
                f'schema=jim.MessageSendMessage '
                f'for data={data}'
            )
            raise Exception('Could not get message_model for message')

        message_model: jim.MessageSendMessage = message_dto.message_model
        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                account_name=message_model.from_
            )
            if not current_user:
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                    error='From user not found'
                ).json()
                logger.error(
                    f'From user not found for data={data} '
                )
                self.put_message_for_client(error_message)
                return

            if not user_service.is_online(user=current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Auth required'
                ).json()
                logger.error(
                    f'Auth required for data={data} '
                )
                self.put_message_for_client(error_message)
                return

            user_service.presence(
                user=current_user,
                time=message_model.time
            )

            message_accepted = jim.MessageAlert(
                response=jim.StatusCodes.HTTP_202_ACCEPTED,
                alert='message accepted'
            ).json()

            if message_model.to_ == 'all':
                self.put_message_for_all_users_exclude_current(
                    message_model.json()
                )
                self.put_message_for_client(message_accepted)
                return

            target_user = user_service.get_user_by_account_name(
                account_name=message_model.to_
            )
            if not target_user:
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                    error='Target user not found'
                ).json()
                logger.error(
                    f'Target user not found for data={data} '
                )
                self.put_message_for_client(error_message)
                return

            if not user_service.is_online(user=target_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Target user offline'
                ).json()
                logger.error(
                    f'Target user offline for data={data} '
                )
                self.put_message_for_client(error_message)
                return

            logger.debug(
                'processing_presence: %s current_user=%s',
                message_dto,
                current_user
            )
            self.put_message_for_client(message_model.json(), target_user)
            session.commit()
        self.put_message_for_client(message_accepted)
