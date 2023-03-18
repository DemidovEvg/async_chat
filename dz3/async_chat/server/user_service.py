import datetime as dt
from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
)
from async_chat.server.db import User, History


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def get_all_users_ids(self) -> list[int]:
        ids = self.session.scalars(select(User.id).select_from(User)).all()
        return ids

    def get_user_by_account_name(self, account_name: str) -> User | None:
        return self.session.scalars(
            select(User).filter(User.account_name == account_name)
        ).first()

    def get_user_by_id(self, id: int) -> User | None:
        return self.session.scalars(
            select(User).filter(User.id == id)
        ).first()

    def check_password(self, user: User, password: str) -> bool:
        return user.check_password(password)

    def login(
        self,
        user: User | int,
        time: dt.datetime | None = None,
        adress: str = ''
    ) -> None:
        if not time:
            time = dt.datetime.now(dt.timezone.utc)
        if isinstance(user, int):
            current_user = self.session.scalars(
                select(User).filter_by(id=user)
            ).one()
        else:
            current_user = user
        history = History(
            user=current_user,
            event=History.Event.login,
            time=time,
            adress=adress
        )
        self.session.add(history)
        current_user.has_entered = True
        self.session.commit()

    def logout(
        self,
        user: User | int,
        time: dt.datetime = None,
        adress: str = ''
    ) -> None:
        if not time:
            time = dt.datetime.now(dt.timezone.utc)
        if isinstance(user, int):
            current_user = self.session.scalars(
                select(User).filter_by(id=user)
            ).one()
        else:
            current_user = user
        history = History(
            user=current_user,
            event=History.Event.logout,
            time=time,
            adress=adress
        )
        self.session.add(history)
        current_user.has_entered = False
        self.session.commit()

    def presence(
        self,
        user: User,
        time: dt.datetime,
        adress: str = ''
    ) -> None:
        history = History(
            user=user,
            event=History.Event.user_send_message_to_server,
            time=time,
            adress=adress
        )
        self.session.add(history)
        self.session.commit()

    def user_get_message_from_server(
        self,
        user: User | int | None,
        time: dt.datetime | None = None,
        adress: str = ''
    ) -> None:
        time = dt.datetime.now(dt.timezone.utc)
        if user is None:
            current_user = None
        elif isinstance(user, int):
            current_user = self.session.scalars(
                select(User).filter_by(id=user)
            ).one()
        else:
            current_user = user
        history = History(
            user=current_user,
            event=History.Event.user_get_message_from_server,
            time=time,
            adress=adress
        )
        self.session.add(history)
        self.session.commit()

    def user_send_message_to_server(
        self,
        user: User | int | None,
        time: dt.datetime | None = None,
        adress: str = ''
    ) -> None:
        time = dt.datetime.now(dt.timezone.utc)
        if user is None:
            current_user = None
        elif isinstance(user, int):
            current_user = self.session.scalars(
                select(User).filter_by(id=user)
            ).one()
        else:
            current_user = user
        history = History(
            user=current_user,
            event=History.Event.user_send_message_to_server,
            time=time,
            adress=adress
        )
        self.session.add(history)
        self.session.commit()

    def is_online(self, user: User) -> bool:
        return user.is_online()
