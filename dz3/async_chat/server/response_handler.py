import json
from typing import Any, Type
import logging
from async_chat import jim
from async_chat.server.db import UserService, SessionLocal, User
from async_chat.server.clients import Client, Clients
from async_chat.utils import Request, Response, MessageDto, get_message_dto_, T

logger = logging.getLogger('server-logger')


class ResponseHandler:
    def __init__(
        self,
        current_client: Client,
        clients: Clients,
    ):
        self.current_client = current_client
        self.clients = clients

    def put_message_for_user(self, message: str, user: User):
        self.clients.users_messages.put_message_to_queue(
            target=user.id,
            message=message
        )

    def put_message_for_current_client(self, message: str, client: Client | None = None):
        if not client:
            client = self.current_client
            self.clients.users_messages.put_message_to_queue(
                target=client.user_id or client.socket,
                message=message
            )

    def put_message_for_all_users_exclude_current(self, message: str, users_ids: list[int]):
        for user_id in users_ids:
            if user_id != self.current_client.user_id:
                self.clients.users_messages.put_message_to_queue(
                    target=user_id,
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
                self.put_message_for_current_client(message_error)
                return
            if action == 'authenticate':
                return self.processing_login_user(data=incomming_data)
            elif action == 'presense':
                return self.processing_presence(data=incomming_data)
            elif action == 'quit' or action == 'logout':
                return self.processing_logout_user(data=incomming_data)
            elif action == 'msg':
                return self.processing_message(data=incomming_data)
            elif action == 'join':
                return self.processing_join_room(data=incomming_data)
            elif action == 'leave':
                return self.processing_leave_room(data=incomming_data)
            else:
                logger.error(
                    f'Unknown action for incomming_data={incomming_data} '
                )
                message_error = jim.MessageError(
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error='Unknown action'
                ).json()
                self.put_message_for_current_client(message_error)
                return
        except Exception as exc:
            logger.error(
                f'ERROR={exc.__repr__()} for incomming_data={incomming_data} '
            )
            message_error = jim.MessageError(
                response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                error=str(exc)
            ).json()
            self.put_message_for_current_client(message_error)
            return

    def processing_login_user(self, data: dict[str, Any]) -> Response:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserAuth,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            self.put_message_for_current_client(message_dto.error_message)
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
                self.put_message_for_current_client(error_message)
                return
            if user_service.is_online(current_user) and self.current_client.user_id == current_user.id:
                self.clients.remove_user(current_user.id)
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_409_CONFLICT,
                    error="You are already login"
                ).json()
                logger.error(
                    f'User already login for data={data} '
                )
                self.put_message_for_current_client(error_message)
                return
            if user_service.is_online(current_user) and not self.current_client.user_id:
                self.clients.remove_another_client_with_user(current_user.id)
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
        self.put_message_for_current_client(ok_message)

    def processing_logout_user(self, data: dict[str, Any]) -> Response:
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
            self.put_message_for_current_client(message_dto.error_message)
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
        self.put_message_for_current_client(ok_message)

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

    def processing_presence(self, data: dict[str, Any]) -> None:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserPresence,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            self.put_message_for_current_client(message_dto.error_message)
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
                self.put_message_for_current_client(error_message)
                return

            if not user_service.is_online(user=current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Auth required'
                ).json()
                logger.error(
                    f'Auth required for data={data} '
                )
                self.put_message_for_current_client(error_message)
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
        self.put_message_for_current_client(message)
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
            self.put_message_for_current_client(message_dto.error_message)
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
                self.put_message_for_current_client(error_message)
                return

            if not user_service.is_online(user=current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Auth required'
                ).json()
                logger.error(
                    f'Auth required for data={data} '
                )
                self.put_message_for_current_client(error_message)
                return

            user_service.presence(
                user=current_user,
                time=message_model.time
            )

            message_accepted = jim.MessageAlert(
                response=jim.StatusCodes.HTTP_202_ACCEPTED,
                alert='message accepted'
            ).json()

            if '#' in message_model.to_:
                target_room = message_model.to_.replace('#', '')
                if not target_room:
                    # Отошлем в текущю комнату юзера
                    target_room = self.clients.get_room_name(
                        self.current_client
                    )
                users_ids = self.clients.get_users_ids_in_room(target_room)
                self.put_message_for_all_users_exclude_current(
                    message_model.json(),
                    users_ids
                )
                self.put_message_for_current_client(message_accepted)
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
                self.put_message_for_current_client(error_message)
                return

            if not user_service.is_online(user=target_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error='Target user offline'
                ).json()
                logger.error(
                    f'Target user offline for data={data} '
                )
                self.put_message_for_current_client(error_message)
                return

            logger.debug(
                'processing_presence: %s current_user=%s',
                message_dto,
                current_user
            )
            self.put_message_for_user(message_model.json(), target_user)
            session.commit()
        self.put_message_for_current_client(message_accepted)

    def processing_join_room(self, data: dict[str, Any]) -> Response:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserJoinRoom,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            self.put_message_for_current_client(message_dto.error_message)
            return

        if not message_dto.message_model:
            logger.error(
                f'Could not get message_model for '
                f'schema=jim.MessageUserJoinRoom '
                f'for data={data}'
            )
            raise Exception('Could not get message_model for message')

        message_model: jim.MessageUserJoinRoom = message_dto.message_model

        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                message_model.user.account_name
            )

            if not user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_409_CONFLICT,
                    error="You are not login"
                ).json()
                logger.error(
                    f'User not login for data={data} '
                )
                self.put_message_for_current_client(error_message)
                return

            self.clients.join_to_room(self.current_client, message_model.room)

            logger.debug(
                'current_user=%s joined to room=%s', current_user, message_model.room
            )
            session.commit()
        ok_message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_current_client(ok_message)

    def processing_leave_room(self, data: dict[str, Any]) -> Response:
        message_dto = self.get_message_dto(
            schema=jim.MessageUserLeaveRoom,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            self.put_message_for_current_client(message_dto.error_message)
            return

        if not message_dto.message_model:
            logger.error(
                f'Could not get message_model for '
                f'schema=jim.MessageUserLeaveRoom '
                f'for data={data}'
            )
            raise Exception('Could not get message_model for message')

        message_model: jim.MessageUserLeaveRoom = message_dto.message_model

        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                message_model.user.account_name
            )

            if not user_service.is_online(current_user):
                error_message = jim.MessageError(
                    response=jim.StatusCodes.HTTP_409_CONFLICT,
                    error="You are not login"
                ).json()
                logger.error(
                    f'User not login for data={data} '
                )
                self.put_message_for_current_client(error_message)
                return

            self.clients._leave_current_room(self.current_client.user_id)
            room = self.clients.get_room_name(self.current_client)

            logger.debug(
                'current_user=%s left room=%s', current_user, room
            )
            session.commit()
        ok_message = jim.MessageAlert(
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_current_client(ok_message)
