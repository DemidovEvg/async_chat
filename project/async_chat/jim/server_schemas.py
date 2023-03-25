from enum import Enum
from .common_schemas import ActionTimeBase, TimeBase, UserBase
from pydantic import Field


class ServerActions(str, Enum):
    probe = 'probe'


class ServerMessageType(str, Enum):
    contact = 'contact'


class StatusCodes(int, Enum):
    HTTP_100_INFO = 100
    HTTP_101_IMPORTANT_INFO = 101
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_202_ACCEPTED = 202
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_402_BAD_PASSWORD_OR_LOGIN = 402
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_409_CONFLICT = 409
    HTTP_410_GONE = 409


class RequestResponseBase(TimeBase):
    response: StatusCodes


class MessageAlert(RequestResponseBase):
    alert: str = Field(min_length=0, max_length=500)


class MessageError(RequestResponseBase):
    error: str = Field(min_length=0, max_length=500)


class MessageProbe(ActionTimeBase):
    action: str = Field(ServerActions.probe.value, const=True)


class MessageContacts(MessageAlert):
    alert: list[UserBase]
