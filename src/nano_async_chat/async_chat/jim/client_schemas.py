from enum import Enum
from pydantic import Field
from .common_schemas import ActionTimeBase, UserBase


class ClientActions(str, Enum):
    presence = 'presense'
    quit = 'quit'
    msg = 'msg'
    authenticate = 'authenticate'
    join_ = 'join'
    leave = 'leave'
    get_contacts = 'get_contacts'
    add_contact = 'add_contact'
    del_contact = 'del_contact'


class Statuses(str, Enum):
    i_am_here = 'Yep, I am here!'


class UserForAuth(UserBase):
    password: str = Field(min_length=5, max_length=15)


class UserForPresence(UserBase):
    status: str = Field(Statuses.i_am_here.value, const=True)


class MessageUserPresence(ActionTimeBase):
    action: str = Field(ClientActions.presence.value, const=True)
    user: UserForPresence
    token: str


class MessageUserQuit(ActionTimeBase):
    action: str = Field(ClientActions.quit.value, const=True)
    user: UserBase
    token: str


class MessageUserAuth(ActionTimeBase):
    action: str = Field(ClientActions.authenticate.value, const=True)
    user: UserForAuth


class MessageBaseActionSend(ActionTimeBase):
    action: str = Field(ClientActions.msg.value, const=True)
    from_: str = Field(min_length=3, max_length=25)
    encoding: str | None
    message: str = Field(min_length=0, max_length=500)
    token: str


class MessageSendMessage(MessageBaseActionSend):
    to_: str = Field(min_length=3, max_length=25)
    user: UserBase
    token: str


class MessageUserJoinRoom(ActionTimeBase):
    action: str = Field(ClientActions.join_.value, const=True)
    room: str = Field(min_length=3, max_length=25)
    user: UserBase
    token: str


class MessageUserLeaveRoom(ActionTimeBase):
    action: str = Field(ClientActions.leave.value, const=True)
    user: UserBase
    token: str


class MessageGetContacts(ActionTimeBase):
    action: str = Field(ClientActions.get_contacts.value, const=True)
    user: UserBase
    token: str


class MessageAddContact(ActionTimeBase):
    action: str = Field(ClientActions.add_contact.value, const=True)
    target_user: UserBase
    user: UserBase
    token: str


class MessageDeleteContact(ActionTimeBase):
    action: str = Field(ClientActions.del_contact.value, const=True)
    target_user: UserBase
    user: UserBase
    token: str
