import datetime as dt
from sqlalchemy import select, delete, func
from sqlalchemy.orm import (
    Session,
)
from async_chat.server.db import User, History, Contact


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def get_users(self) -> list[User]:
        return self.session.scalars(select(User)).all()

    def get_online_users(self) -> list[User]:
        users = self.get_users()
        online_users = [u for u in users if u.is_online()]
        return online_users

    def get_user_send_messages_count(self, user: User) -> int:
        session = Session.object_session(user)
        if not session:
            session = self.session
            session.add(user)
        event = History.Event.user_send_message_to_server
        stm = (
            select(func.count('*'))
            .select_from(History)
            .filter_by(user_id=user.id, event=event)
        )
        result = session.scalars(stm).first()
        return result

    def get_all_users_ids(self) -> list[int]:
        ids = self.session.scalars(select(User.id).select_from(User)).all()
        return ids

    def get_user_by_account_name(self, account_name: str) -> User | None:
        return self.session.scalars(
            select(User).filter(User.account_name == account_name)
        ).first()

    def get_user_by_id(self, id: int | None) -> User | None:
        if not id:
            return None
        return self.session.scalars(
            select(User).filter(User.id == id)
        ).first()

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

    def get_users_with_no_friends(self) -> list[User]:
        stmt = select(User).where(~User.contacts.any())
        return self.session.scalars(stmt).all()

    def add_contact_for_user(self, current_user: User, contact: User) -> None:
        query = select(Contact).filter_by(
            user_id=current_user.id,
            friend_id=contact.id
        )
        contacts = self.session.scalars(query).all()
        if not contacts:
            contact = Contact(
                friend_id=contact.id
            )
            current_user.contacts.append(contact)
            self.session.commit()

    def delete_contact_for_user(self, current_user: User, contact: User) -> None:
        query = delete(Contact).filter_by(
            user_id=current_user.id,
            friend_id=contact.id
        )
        self.session.execute(query)
        self.session.commit()
