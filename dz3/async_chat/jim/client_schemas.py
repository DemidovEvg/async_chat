from pydantic import BaseModel
from enum import Enum
from pydantic import Field
from .common_schemas import ActionTimeBase


class ClientActions(str, Enum):
    presence = 'presense'
    quit = 'quit'
    msg = 'msg'
    authenticate = 'authenticate'
    join_ = 'join'
    leave = 'leave'


class Statuses(str, Enum):
    i_am_here = 'Yep, I am here!'


class UserBase(BaseModel):
    account_name: str = Field(min_length=3, max_length=25)


class UserForAuth(UserBase):
    password: str = Field(min_length=5, max_length=15)


class UserForPresence(UserBase):
    status: str = Field(Statuses.i_am_here.value, const=True)


class MessageUserPresence(ActionTimeBase):
    action: str = Field(ClientActions.presence.value, const=True)
    user: UserForPresence


class MessageUserQuit(ActionTimeBase):
    action: str = Field(ClientActions.quit.value, const=True)
    user: UserBase


class MessageUserAuth(ActionTimeBase):
    action: str = Field(ClientActions.authenticate.value, const=True)
    user: UserForAuth


class MessageBaseActionSend(ActionTimeBase):
    action: str = Field(ClientActions.msg.value, const=True)
    from_: str = Field(min_length=3, max_length=25)
    encoding: str | None
    message: str = Field(min_length=0, max_length=500)


class MessageSendMessage(MessageBaseActionSend):
    to_: str = Field(min_length=3, max_length=25)


class MessageUserJoinRoom(ActionTimeBase):
    action: str = Field(ClientActions.join_.value, const=True)
    room: str = Field(min_length=3, max_length=25)
    user: UserBase


class MessageUserLeaveRoom(ActionTimeBase):
    action: str = Field(ClientActions.leave.value, const=True)
    user: UserBase
