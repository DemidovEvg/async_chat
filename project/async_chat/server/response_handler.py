"""Модуль реализующий класс обработки запросов пользователей

На вход основного метода processing_request принимает запрос от пользователя, 
ответ записывает в очередь сообщений пользователя
"""
import json
import logging
from typing import Any, Type
import datetime as dt
from async_chat.server.clients import Client, Clients
from async_chat.server.db import SessionLocal, User
from async_chat.server.user_service import UserService
from async_chat.server.utils_auth import append_current_user, login_required, create_access_token
from async_chat.utils import MessageDto, Request, Response, T, get_message_dto_

from async_chat import jim

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

    def get_message_model(self, schema: Type[T], data: dict[str, Any]) -> T:
        message_dto = self.__class__.get_message_dto(
            schema=schema,
            data=data
        )
        if message_dto.error_message:
            logger.error(
                f'error={message_dto.error_message} with data={message_dto.json()}'
            )
            self.put_message_for_current_client(message_dto.error_message)
            raise Exception(str(message_dto.error_message))

        if not message_dto.message_model:
            logger.error(
                f'Could not get message_model for '
                f'schema={schema} '
                f'for data={data}'
            )
            raise Exception('Could not get message_model for message')

        message_model: Type[T] = message_dto.message_model

        return message_model

    def processing_request(self, request: Request) -> str:
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
            if action == jim.ClientActions.authenticate.value:
                return self.processing_login_user(data=incomming_data)
            elif action == jim.ClientActions.presence.value:
                return self.processing_presence(data=incomming_data)
            elif action == jim.ClientActions.quit.value:
                return self.processing_logout_user(data=incomming_data)
            elif action == jim.ClientActions.msg.value:
                return self.processing_message(data=incomming_data)
            elif action == jim.ClientActions.get_contacts.value:
                return self.processing_get_contacts(data=incomming_data)
            elif action == jim.ClientActions.add_contact.value:
                return self.processing_add_contact(data=incomming_data)
            elif action == jim.ClientActions.del_contact.value:
                return self.processing_delete_contact(data=incomming_data)
            elif action == jim.ClientActions.join_.value:
                return self.processing_join_room(data=incomming_data)
            elif action == jim.ClientActions.leave.value:
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

    def return_error(
        self,
        chain_id: int | str,
        response: jim.StatusCodes,
        error_text: str
    ) -> None:
        error_message = jim.MessageError(
            chain_id=chain_id,
            response=response,
            error=error_text
        ).json()
        logger.error(error_text)
        self.put_message_for_current_client(error_message)
        return

    @append_current_user
    def processing_login_user(self, data: dict[str, Any], current_user: User | None) -> Response:
        message_model: jim.MessageUserAuth = self.get_message_model(
            schema=jim.MessageUserAuth,
            data=data
        )
        with SessionLocal() as session:
            if not current_user:
                return self.return_error(
                    chain_id=message_model.id,
                    response=jim.StatusCodes.HTTP_402_BAD_PASSWORD_OR_LOGIN,
                    error_text="Bad password or login"
                )
            session.add(current_user)
            plain_passord = message_model.user.password
            hashed_password = current_user.password
            if not current_user.__class__.verify_password(
                plain_passord,
                    hashed_password):
                return self.return_error(
                    chain_id=message_model.id,
                    response=jim.StatusCodes.HTTP_402_BAD_PASSWORD_OR_LOGIN,
                    error_text="Bad password or login"
                )
            if current_user.is_online() and self.current_client.user_id == current_user.id:
                return self.return_error(
                    chain_id=message_model.id,
                    response=jim.StatusCodes.HTTP_409_CONFLICT,
                    error_text="You are already login"
                )
            if current_user.is_online() and not self.current_client.user_id:
                self.clients.remove_another_client_with_user(current_user.id)
            user_service = UserService(session=session)
            user_service.login(current_user, message_model.time)
            self.current_client.user_id = current_user.id
            logger.debug(
                'login_user: %s current_user=%s', message_model, current_user
            )
            session.commit()
            user_model = jim.UserBase(account_name=current_user.account_name)
            token = create_access_token(
                data=user_model.dict(),
                expires_delta=dt.timedelta(days=1)
            )
            token_message = jim.MessageToken(
                chain_id=message_model.id,
                response=jim.StatusCodes.HTTP_201_CREATED,
                token=token
            ).json()
            self.put_message_for_current_client(token_message)

    @append_current_user
    @login_required
    def processing_logout_user(self, data: dict[str, Any], current_user: User | None) -> Response:
        message_model: jim.MessageUserQuit = self.get_message_model(
            schema=jim.MessageUserQuit,
            data=data
        )

        ok_message = jim.MessageAlert(
            chain_id=message_model.id,
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_current_client(ok_message)

        with SessionLocal() as session:
            user_service = UserService(session=session)
            current_user = user_service.get_user_by_account_name(
                message_model.user.account_name
            )

            if current_user and current_user.is_online():
                user_service.logout(current_user, message_model.time)
                logger.debug(
                    'logout_user: %s current_user=%s',
                    message_model,
                    current_user
                )
                session.commit()

    @append_current_user
    @login_required
    def processing_presence(self, data: dict[str, Any], current_user: User) -> None:
        message_model: jim.MessageUserPresence = self.get_message_model(
            schema=jim.MessageUserPresence,
            data=data
        )
        with SessionLocal() as session:
            user_service = UserService(session=session)
            user_service.presence(
                user=current_user,
                time=message_model.time
            )
            logger.debug(
                'processing_presence: %s current_user=%s',
                message_model,
                current_user
            )
            session.commit()
        message = jim.MessageAlert(
            chain_id=message_model.id,
            response=jim.StatusCodes.HTTP_202_ACCEPTED,
            alert='Presense accepted'
        ).json()
        self.put_message_for_current_client(message)
        return

    @append_current_user
    @login_required
    def processing_message(self, data: dict[str, Any], current_user: User) -> None:
        message_model: jim.MessageSendMessage = self.get_message_model(
            schema=jim.MessageSendMessage,
            data=data
        )

        with SessionLocal() as session:
            user_service = UserService(session=session)
            session.add(current_user)

            user_service.presence(
                user=current_user,
                time=message_model.time
            )

            message_accepted = jim.MessageAlert(
                chain_id=message_model.id,
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
                return self.return_error(
                    chain_id=message_model.id,
                    response=jim.StatusCodes.HTTP_404_NOT_FOUND,
                    error_text=f"Target user {message_model.to_} not found"
                )

            if not target_user.is_online():
                return self.return_error(
                    chain_id=message_model.id,
                    response=jim.StatusCodes.HTTP_401_UNAUTHORIZED,
                    error_text=f"Target user {message_model.to_} offline"
                )

            logger.debug(
                'processing_presence: %s current_user=%s',
                message_model,
                current_user
            )
            self.put_message_for_user(message_model.json(), target_user)
            session.commit()
        self.put_message_for_current_client(message_accepted)

    @append_current_user
    @login_required
    def processing_join_room(self, data: dict[str, Any], current_user: User) -> Response:
        message_model: jim.MessageUserJoinRoom = self.get_message_model(
            schema=jim.MessageUserJoinRoom,
            data=data
        )

        with SessionLocal() as session:
            session.add(current_user)

            self.clients.join_to_room(self.current_client, message_model.room)

            logger.debug(
                'current_user=%s joined to room=%s', current_user, message_model.room
            )
            session.commit()
        ok_message = jim.MessageAlert(
            chain_id=message_model.id,
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_current_client(ok_message)

    @append_current_user
    @login_required
    def processing_leave_room(self, data: dict[str, Any], current_user: User) -> Response:
        message_model: jim.MessageUserLeaveRoom = self.get_message_model(
            schema=jim.MessageUserLeaveRoom,
            data=data
        )

        with SessionLocal() as session:
            session.add(current_user)

            self.clients._leave_current_room(self.current_client.user_id)
            room = self.clients.get_room_name(self.current_client)

            logger.debug(
                'current_user=%s left room=%s', current_user, room
            )
            session.commit()
        ok_message = jim.MessageAlert(
            chain_id=message_model.id,
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_current_client(ok_message)

    @append_current_user
    @login_required
    def processing_get_contacts(self, data: dict[str, Any], current_user: User) -> Response:
        message_model: jim.MessageGetContacts = self.get_message_model(
            schema=jim.MessageGetContacts,
            data=data
        )

        with SessionLocal() as session:
            session.add(current_user)
            friends = [
                dict(account_name=u.account_name)
                for u in current_user.friends
            ]
            logger.debug(
                'current_user=%s get contancts', current_user
            )
        contacts_message = jim.MessageContacts(
            chain_id=message_model.id,
            response=jim.StatusCodes.HTTP_200_OK,
            alert=friends
        ).json()
        self.put_message_for_current_client(contacts_message)

    @append_current_user
    @login_required
    def processing_add_contact(self, data: dict[str, Any], current_user: User) -> Response:
        message_model: jim.MessageAddContact = self.get_message_model(
            schema=jim.MessageAddContact,
            data=data
        )

        with SessionLocal() as session:
            user_service = UserService(session=session)
            session.add(current_user)

            target_user = user_service.get_user_by_account_name(
                account_name=message_model.target_user.account_name
            )
            if not target_user:
                return self.return_error(
                    chain_id=message_model.id,
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error_text=f"Target user {message_model.target_user.account_name} not exist"
                )

            user_service.add_contact_for_user(
                current_user=current_user,
                contact=target_user
            )

            logger.debug(
                'current_user=%s add contancts', current_user
            )
        ok_message = jim.MessageAlert(
            chain_id=message_model.id,
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_current_client(ok_message)

    @append_current_user
    @login_required
    def processing_delete_contact(self, data: dict[str, Any], current_user: User) -> Response:
        message_model: jim.MessageDeleteContact = self.get_message_model(
            schema=jim.MessageDeleteContact,
            data=data
        )
        with SessionLocal() as session:
            user_service = UserService(session=session)
            session.add(current_user)
            target_user = user_service.get_user_by_account_name(
                account_name=message_model.target_user.account_name
            )
            if not target_user:
                return self.return_error(
                    chain_id=message_model.id,
                    response=jim.StatusCodes.HTTP_400_BAD_REQUEST,
                    error_text=f"Target user {message_model.target_user.account_name} not exist"
                )

            user_service.delete_contact_for_user(
                current_user=current_user,
                contact=target_user
            )

            logger.debug(
                'current_user=%s delete contancts', current_user
            )
        ok_message = jim.MessageAlert(
            chain_id=message_model.id,
            response=jim.StatusCodes.HTTP_200_OK,
            alert='OK'
        ).json()
        self.put_message_for_current_client(ok_message)
