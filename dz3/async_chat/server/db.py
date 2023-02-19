import datetime as dt
from typing import Optional
from sqlalchemy import create_engine, select
from sqlalchemy.orm import (
    Session,
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker
)


engine = create_engine("sqlite+pysqlite:///:memory:")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    account_name: Mapped[str]
    password: Mapped[str]
    message_time: Mapped[Optional[dt.datetime]]
    logout_time: Mapped[Optional[dt.datetime]]
    has_entered: Mapped[Optional[bool]] = mapped_column(default=False)
    address: Mapped[Optional[str]]

    def __repr__(self):
        return (
            f'User(id={self.id}, account_name={self.account_name}),'
            f' message_time={self.message_time}, logout_time={self.logout_time},'
            f' has_entered={self.has_entered}, address={self.address}'
        )

    def is_online(self):
        if not self.has_entered or not self.message_time:
            return False
        aware_message_time = self.message_time.replace(tzinfo=dt.timezone.utc)
        diff = dt.datetime.now(dt.timezone.utc) - aware_message_time
        if diff < dt.timedelta(seconds=600):
            return True
        return False

    def check_password(self, password: str):
        return self.password == password


Base.metadata.create_all(bind=engine)


with Session(engine) as session:
    users = [
        User(account_name='Ivan', password='ivan123'),
        User(account_name='Oleg', password='oleg123'),
        User(account_name='Petr', password='oleg123'),
    ]
    session.add_all(users)
    session.commit()


class UserService:
    def __init__(self, session: Session):
        self.session = session

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

    def login(self, user: User, time: dt.datetime) -> None:
        user.has_entered = True
        user.message_time = time

    def logout(self, user: User, time: dt.datetime) -> None:
        user.has_entered = False
        user.message_time = time
        user.logout_time = time

    def presence(self, user: User, time: dt.datetime) -> None:
        user.message_time = time

    def is_online(self, user: User) -> bool:
        return user.is_online()

    def get_online_user_by_address(self, address: tuple[str, int]) -> User | None:
        user = self.session.scalars(
            select(User).filter(
                User.address == str(address)
            )
        ).first()
        if not user:
            return None

        if not user.is_online():
            user.address = ''
            return None
        return user
