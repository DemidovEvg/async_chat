"""Класс обработки запросов-ответов для интерфейска"""
from async_chat.client.base_response_handler import BaseResponseHandler
import logging
import typing
from async_chat import jim
if typing.TYPE_CHECKING:
    from async_chat.client.client_ui.client_ui import MainWindowContol
from async_chat.client.client_ui.chat_item import ChatItem
from async_chat.settings import DEFAULT_ROOM


logger = logging.getLogger('client-logger')


class ClientUIResponseHandler(BaseResponseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui: MainWindowContol = kwargs.get('ui')

    def result_login(
        self,
        request_model: jim.MessageUserAuth,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        error = ''
        if isinstance(response_model, jim.MessageError):
            error = response_model.error
        self.ui.result_login(success=success, error=error)

    def result_logout(
        self,
        request_model: jim.MessageUserQuit,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        self.ui.result_login(success=not success)

    def result_get_contacts(
        self,
        request_model: jim.MessageGetContacts,
        response_model: jim.MessageContacts,
    ):
        success = self.is_success(response_model)
        if success:
            self.ui.save_contacts_and_render(response_model)
        else:
            self.ui.show_error('Произошла ошибка при получении контактов')

    def result_add_contact(
        self,
        request_model: jim.MessageAddContact,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        if success:
            target_user = request_model.target_user
            self.ui.append_contact_and_render(target_user)
        else:
            self.ui.show_error(response_model.error)

    def result_delete_contact(
        self,
        request_model: jim.MessageDeleteContact,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        if success:
            target_user = request_model.target_user
            self.ui.delete_contact_and_render(target_user)
        else:
            self.ui.show_error(response_model.error)

    def result_join_room(
        self,
        request_model: jim.MessageUserJoinRoom,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        if success:
            new_room = request_model.room
            self.ui.success_join_room(new_room)
        else:
            self.ui.show_error(response_model.error)

    def result_leave_room(
        self,
        request_model: jim.MessageUserLeaveRoom,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        success = self.is_success(response_model)
        if success:
            old_room = self.current_user.room
            new_room = DEFAULT_ROOM
            self.ui.success_leave_room(old_room, new_room)
        else:
            self.ui.show_error(response_model.error)

    def strange_result(
        self,
        request_model: jim.MessageUserLeaveRoom,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        self.ui.show_error(str(response_model))

    def result_probe(self, *args, **kwargs):
        pass

    def result_message(
        self,
        request_model: None,
        response_model: jim.MessageSendMessage
    ) -> jim.MessageUserPresence:
        message = response_model.message
        source = response_model.from_
        message_id = response_model.id
        message_chain_id = response_model.chain_id
        self.ui.print_message(
            source=source,
            message=message,
            message_id=message_id,
            message_chain_id=message_chain_id,
            direction=ChatItem.MessageDirection.incoming
        )

    def result_out_message(
        self,
        request_model: jim.MessageSendMessage,
        response_model: jim.MessageAlert
    ):
        message_id = request_model.id
        self.ui.accept_messages(message_id=message_id)

    def processing_outgoing_message(
        self,
        request_model: jim.MessageSendMessage,
    ):
        message = request_model.message
        target = request_model.to_
        message_id = request_model.id
        self.ui.print_message(
            target=target,
            message=message,
            message_id=message_id,
            message_chain_id=message_id,
            direction=ChatItem.MessageDirection.outgoing
        )
