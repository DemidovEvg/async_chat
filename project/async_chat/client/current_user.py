from dataclasses import dataclass, field

from async_chat.settings import DEFAULT_ROOM


@dataclass
class User:
    account_name: str = ''
    password: str = ''
    is_entered: bool = False
    room: str = DEFAULT_ROOM
    contacts: list[str] = field(default_factory=list)


current_user = User()
