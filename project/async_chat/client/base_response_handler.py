from typing import Any
import logging
from abc import ABC, abstractmethod
from pydantic import BaseModel
from async_chat import jim
from async_chat.client.current_user import current_user
from async_chat.client.message_chain import messages_chain

logger = logging.getLogger('client-logger')


class BaseResponseHandler(ABC):

    def __init__(self, *args, **kwargs):
        self.current_user = current_user
        self.messages_chain = messages_chain

    def is_success(
            self,
            response_model: jim.MessageAlert | jim.MessageError
    ):
        success = (
            True
            if isinstance(response_model, jim.MessageAlert)
            else False
        )
        return success

    @abstractmethod
    def result_login(
        self,
        request_model: jim.MessageUserAuth,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        pass

    @abstractmethod
    def result_logout(
        self,
        request_model: jim.MessageUserQuit,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        pass

    @abstractmethod
    def result_get_contacts(
        self,
        request_model: jim.MessageGetContacts,
        response_model: jim.MessageContacts,
    ):
        pass

    @abstractmethod
    def result_add_contact(
        self,
        request_model: jim.MessageAddContact,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        pass

    @abstractmethod
    def result_delete_contact(
        self,
        request_model: jim.MessageDeleteContact,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        pass

    @abstractmethod
    def result_join_room(
        self,
        request_model: jim.MessageUserJoinRoom,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        pass

    @abstractmethod
    def result_leave_room(
        self,
        request_model: jim.MessageUserLeaveRoom,
        response_model: jim.MessageAlert | jim.MessageError,
    ):
        pass

    @abstractmethod
    def strange_result(
        self,
        request_model: BaseModel,
        response_model: jim.MessageAlert | jim.MessageError,
        *args,
        **kwargs
    ):
        pass

    @abstractmethod
    def result_probe(self, request_model=jim.MessageProbe):
        pass

    @abstractmethod
    def result_message(
        self,
        request_model: None,
        response_model: jim.MessageSendMessage
    ):
        pass

    @abstractmethod
    def result_out_message(
        self,
        request_model: jim.MessageSendMessage,
        response_model: jim.MessageAlert
    ):
        pass

    def dispatch_result_dict(self, result_dict: dict[str, Any]):
        request_model = result_dict['request_model']
        if request_model and isinstance(request_model, jim.MessageUserAuth):
            self.result_login(**result_dict)
        elif request_model and isinstance(request_model, jim.MessageUserQuit):
            self.result_logout(**result_dict)
        elif request_model and isinstance(request_model, jim.MessageGetContacts):
            self.result_get_contacts(**result_dict)
        elif request_model and isinstance(request_model, jim.MessageAddContact):
            self.result_add_contact(**result_dict)
        elif request_model and isinstance(request_model, jim.MessageDeleteContact):
            self.result_delete_contact(**result_dict)
        elif request_model and isinstance(request_model, jim.MessageUserJoinRoom):
            self.result_join_room(**result_dict)
        elif request_model and isinstance(request_model, jim.MessageUserLeaveRoom):
            self.result_leave_room(**result_dict)
        elif request_model and isinstance(request_model, jim.MessageSendMessage):
            self.result_out_message(**result_dict)
        else:
            self.strange_result(**result_dict)

    def processing_incomming_alert_or_error(
        self,
        request_model: jim.MessageUserAuth,
        response_model: jim.MessageAlert | jim.MessageError | jim.MessageContacts
    ):
        logger.debug('dispatch_incomming_data: %s', response_model)
        result_dict = dict(
            request_model=request_model,
            response_model=response_model
        )
        return self.dispatch_result_dict(result_dict)

    @abstractmethod
    def processing_outgoing_message(
        self,
        request_model: jim.MessageSendMessage,
    ):
        pass

    def dispatch_incomming_model(self, response_model: BaseModel):
        request_model = self.messages_chain.get(response_model.chain_id)
        if (
            isinstance(response_model, jim.MessageAlert)
            or isinstance(response_model, jim.MessageError)
            or isinstance(response_model, jim.MessageContacts)
        ):
            return self.processing_incomming_alert_or_error(
                request_model=request_model,
                response_model=response_model
            )
        elif isinstance(response_model, jim.MessageProbe):
            return self.result_probe(request_model=response_model)
        elif isinstance(response_model, jim.MessageSendMessage):
            return self.result_message(
                request_model=request_model,
                response_model=response_model
            )
        else:
            logger.error(
                f'Unknown message for response_model={response_model}'
            )
            return self.strange_result(
                request_model=request_model,
                response_model=response_model
            )

    def dispatch_incomming_data(self, incomming_data: dict[str, Any]) -> BaseModel:
        logger.debug('dispatch_incomming_data %s', incomming_data)

        schema = getattr(jim, incomming_data.get('schema_class'))
        response_model = schema(**incomming_data)
        self.dispatch_incomming_model(response_model)
        return response_model

    def dispatch_outgoing_model(self, request_model: BaseModel):
        if isinstance(request_model, jim.MessageSendMessage):
            return self.processing_outgoing_message(
                request_model=request_model,
            )
