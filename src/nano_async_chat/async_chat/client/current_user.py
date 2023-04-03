from dataclasses import dataclass, field

from ..settings import DEFAULT_ROOM


@dataclass
class User:
    account_name: str = ''
    password: str = ''
    is_entered: bool = False
    room: str = DEFAULT_ROOM
    contacts: list[str] = field(default_factory=list)
    try_login: bool = False
    token: str = ''


current_user = User()
