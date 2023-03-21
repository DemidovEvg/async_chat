import datetime as dt
from typing import Optional
import enum
from functools import cached_property
import sqlalchemy as sa
from sqlalchemy import create_engine, select, ForeignKey
from sqlalchemy.orm import (
    Session,
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
    relationship
)
from async_chat import settings


engine = create_engine(settings.database_path)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    account_name: Mapped[str]
    password: Mapped[str]
    has_entered: Mapped[Optional[bool]] = mapped_column(default=False)
    histories: Mapped[list['History']] = relationship(
        back_populates='user',
        cascade='all, delete'
    )
    contacts: Mapped[list['Contact']] = relationship(
        back_populates='user',
        foreign_keys='Contact.user_id'
    )
    friends_with_us: Mapped[list['Contact']] = relationship(
        back_populates='user',
        foreign_keys='Contact.friend_id'
    )

    @property
    def friends(self) -> list['User']:
        session = Session.object_session(self)
        subq = select(Contact).where(Contact.user_id == self.id).subquery()
        stmt = select(User).join(subq, User.id == subq.c.friend_id)
        select(User).join_from(User, User.contacts).where(Contact.user_id == 1)
        return session.scalars(stmt).all()

    @cached_property
    def user_service(self):
        from async_chat.server.user_service import UserService
        session = Session.object_session(self)
        return UserService(session)

    def _get_last_event_time(self, event: 'History.Event'):
        session = Session.object_session(self)
        stm = (
            select(History.time)
            .filter_by(user_id=self.id, event=event)
            .order_by(History.time.desc())
        )
        result = session.scalars(stm).first()
        return result

    @property
    def last_login(self):
        return self._get_last_event_time(event=History.Event.login)

    @property
    def last_logout(self):
        return self._get_last_event_time(event=History.Event.logout)

    @property
    def last_send_message(self):
        return self._get_last_event_time(event=History.Event.user_send_message_to_server)

    @property
    def last_get_message(self):
        return self._get_last_event_time(event=History.Event.user_get_message_from_server)

    def __repr__(self):
        return (
            f'User(id={self.id}, account_name={self.account_name}),'
        )

    def is_online(self):
        if not self.has_entered:
            return False
        return True

    def check_password(self, password: str):
        return self.password == password


class History(Base):
    __tablename__ = 'history'

    class Event(str, enum.Enum):
        login = 'login'
        logout = 'logout'
        user_send_message_to_server = 'user_send_message_to_server'
        user_get_message_from_server = 'user_get_message_from_server'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('user.id'))
    user: Mapped[User | None] = relationship(back_populates='histories')
    event: Mapped[Event] = mapped_column(sa.Enum(Event))
    time: Mapped[dt.datetime]
    adress: Mapped[str | None]


class Contact(Base):
    __tablename__ = 'contact'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id')
    )
    user: Mapped[User] = relationship(
        back_populates='contacts',
        foreign_keys=[user_id]
    )

    friend_id: Mapped[int] = mapped_column(
        ForeignKey('user.id')
    )
    friend: Mapped[User] = relationship(
        back_populates='friends_with_us',
        foreign_keys=[friend_id]
    )


Base.metadata.create_all(bind=engine)


def create_test_data():
    from async_chat.server import test_data
    with SessionLocal() as session:
        creator = test_data.TestData(session)
        creator.create_data_if_not_exist(session)


create_test_data()
