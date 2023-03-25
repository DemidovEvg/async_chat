import re
from async_chat.client.base_response_handler import BaseResponseHandler
import logging
from pydantic import BaseModel, ValidationError
from async_chat import jim
from async_chat.utils import WrongCommand, get_message_dto_
from async_chat.settings import DEFAULT_ROOM
logger = logging.getLogger('client-logger')


class ClientResponseHandler(BaseResponseHandler):
    def result_login(
        self,
        request_model: jim.MessageUserAuth,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        self.current_user.is_entered = success
        if success:
            logger.debug('Вход удачный')
        else:
            logger.debug('Вход не удачный')

    def result_logout(
        self,
        request_model: jim.MessageUserQuit,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        self.current_user.is_entered = not success
        if success:
            logger.debug('Выход удачный')
        else:
            logger.debug('Выход не удачный')

    def result_get_contacts(
        self,
        request_model: jim.MessageGetContacts,
        response_model: jim.MessageContacts,
    ):
        success = self.is_success(response_model)
        if success:
            logger.debug(
                'Успешно получили контакты %s',
                response_model.alert
            )
        else:
            logger.debug(
                'Не удалось получить контакты'
            )

    def result_add_contact(
        self,
        request_model: jim.MessageAddContact,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        if success:
            logger.debug(
                'Успешно добавили контакт %s',
                request_model.target_user.account_name
            )
        else:
            logger.debug(
                'Не получилось добавить контакт %s',
                request_model.target_user.account_name
            )

    def result_delete_contact(
        self,
        request_model: jim.MessageDeleteContact,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        if success:
            logger.debug(
                'Успешно удалили контакт %s',
                request_model.target_user.account_name
            )
        else:
            logger.debug(
                'Не получилось удалить контакт %s',
                request_model.target_user.account_name
            )

    def result_join_room(
        self,
        request_model: jim.MessageUserJoinRoom,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        if success:
            self.current_user.room = request_model.room
            logger.debug(
                'Успешно вошли в комнату %s',
                request_model.room
            )
        else:
            logger.debug(
                'Не получилось удалить контакт %s',
                request_model.room
            )

    def result_leave_room(
        self,
        request_model: jim.MessageUserLeaveRoom,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        if success:
            logger.debug(
                'Успешно покинули комнату %s',
                self.current_user.room
            )
            self.current_user.room = DEFAULT_ROOM
        else:
            logger.debug(
                'Не получилось покинуть комнату %s',
                self.current_user.room
            )

    def strange_result(
        self,
        request_model: jim.MessageUserLeaveRoom,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        logger.warning(
            'Пришел странный ответ от сервера %s',
            request_model
        )

    def result_probe(
        self,
        request_model: jim.MessageProbe,
    ) -> jim.MessageUserPresence:
        message_model = jim.MessageUserPresence(
            user=dict(account_name=self.current_user.account_name)
        )
        return message_model

    def result_message(
        self,
        request_model: None,
        response_model: jim.MessageSendMessage
    ) -> jim.MessageUserPresence:
        logger.debug(f'get message: {response_model}')

    def result_out_message(
        self,
        request_model: jim.MessageSendMessage,
        response_model: jim.MessageAlert
    ):
        logger.debug('Удачно отправили сообщение')

    def processing_outgoing_message(
        self,
        request_model: jim.MessageSendMessage,
    ):
        pass

    async def sync_account_name_and_password_from_command(self, command: str) -> None:
        if '--account_name' not in command:
            return

        if '--password' not in command:
            raise WrongCommand('--password is required')

        RE_LOGIN_PARSER = re.compile(
            r'login --account_name=(?P<account_name>\w+) --password=(?P<password>\w+)'
        )
        re_match = RE_LOGIN_PARSER.match(command)
        if not re_match:
            raise WrongCommand('command not valid')

        result = re_match.groupdict()
        if not result:
            raise WrongCommand('command not valid')

        new_account_name = str(result.get('account_name'))
        new_password = str(result.get('password', self.current_user.password))
        if self.current_user.account_name and self.current_user.account_name != new_account_name:
            print(
                f'account_name={self.current_user.account_name} new_account_name={new_account_name}'
            )
            await self.action_logout(account_name=self.current_user.account_name)

        self.current_user.account_name = new_account_name
        self.current_user.password = new_password

    async def processing_command(self, command: str) -> None | BaseModel:
        logger.debug('Input command=%s for=%s', command,
                     self.current_user.account_name)
        request_model = None
        try:
            if 'login' in command:
                await self.sync_account_name_and_password_from_command(
                    command
                )
                request_model = await self.action_login(
                    account_name=str(self.current_user.account_name),
                    password=str(self.current_user.password)
                )
            elif 'logout' in command:
                request_model = await self.action_logout(
                    account_name=str(self.current_user.account_name)
                )
            elif 'message' in command:
                _, target, *message_words = command.split()
                message = ' '.join(message_words)
                request_model = await self.action_send_message(target, message)
            elif 'contacts' in command:
                request_model = await self.action_get_contacts()
            elif 'add-contact' in command:
                _, account_name = command.split()
                request_model = await self.action_add_contact(account_name=account_name)
            elif 'del-contact' in command:
                _, account_name = command.split()
                request_model = await self.action_del_contact(account_name=account_name)
            elif 'join' in command:
                _, room, *_ = command.split()
                request_model = await self.action_join(room)
            elif 'leave' in command:
                request_model = await self.action_leave()
            elif 'exit' in command:
                request_model = await self.action_logout(
                    account_name=str(self.current_user.account_name)
                )
            else:
                raise WrongCommand(
                    f'Не валидная команда {command}, попробуйте еще раз!'
                )
            return request_model
        except (OSError, WrongCommand) as exc:
            logger.error('ERROR: %s', str(exc))
            raise WrongCommand(str(exc))

    async def action_login(self, account_name: str, password: str) -> jim.MessageUserAuth:
        if not account_name or not password:
            raise Exception('Empty account_name or password')

        message_dto = get_message_dto_(
            schema=jim.MessageUserAuth,
            data=dict(
                user=dict(
                    account_name=account_name,
                    password=password
                ))
        )
        if message_dto.error_message:
            raise WrongCommand(message_dto.error_message)

        if not message_dto.message_model:
            raise WrongCommand('Could not get message_model for message')

        message_model: jim.MessageUserAuth = message_dto.message_model
        return message_model

    async def action_logout(self, account_name: str) -> jim.MessageUserQuit:
        message_model = jim.MessageUserQuit(
            user=dict(
                account_name=account_name,
            )
        )
        message_dto = get_message_dto_(
            schema=jim.MessageUserQuit,
            data=dict(
                user=dict(
                    account_name=account_name,
                ))
        )
        if message_dto.error_message:
            raise WrongCommand(message_dto.error_message)

        if not message_dto.message_model:
            raise WrongCommand('Could not get message_model for message')
        return message_model

    async def action_send_message(self, target: str, message: str) -> jim.MessageSendMessage:
        if not self.current_user.account_name:
            raise WrongCommand('Empty account_name')
        if target == '#':
            target = f'#{self.current_user.room}'
        try:
            message_model = jim.MessageSendMessage(
                from_=self.current_user.account_name,
                to_=target,
                message=message
            )
        except ValidationError as exc:
            raise WrongCommand(str(exc))
        return message_model

    async def action_join(self, room: str) -> jim.MessageUserJoinRoom:
        if not room:
            raise WrongCommand('Empty room')
        try:
            message_model = jim.MessageUserJoinRoom(
                room=room,
                user=dict(
                    account_name=self.current_user.account_name,
                )
            )
        except ValidationError as exc:
            raise WrongCommand(str(exc))
        return message_model

    async def action_leave(self) -> jim.MessageUserLeaveRoom:
        message_model = jim.MessageUserLeaveRoom(
            user=dict(
                account_name=self.current_user.account_name,
            )
        )
        return message_model

    async def action_get_contacts(self) -> jim.MessageGetContacts:
        message_model = jim.MessageGetContacts()
        return message_model

    async def action_add_contact(self, account_name: str) -> jim.MessageAddContact:
        message_model = jim.MessageAddContact(
            target_user=dict(account_name=account_name)
        )
        return message_model

    async def action_del_contact(self, account_name: str) -> jim.MessageDeleteContact:
        message_model = jim.MessageDeleteContact(
            target_user=dict(account_name=account_name)
        )
        return message_model
