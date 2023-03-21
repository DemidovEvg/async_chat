import random
import datetime as dt
from sqlalchemy.orm import Session
from sqlalchemy import select


class TestData:
    def __init__(self, session: Session, count: int = 30):
        from async_chat.server import db
        from async_chat.server.user_service import UserService
        self.db = db
        self.count = count
        self.session = session
        self.user_service = UserService(self.session)

    def create_users(self):
        users: list[self.db.User] = []
        for i in range(self.count):
            users.append(
                self.db.User(account_name=f'Ivan{i}', password='ivan123')
            )
        self.session.add_all(users)
        self.session.flush()
        self.users = users

    def create_contacts(self):
        for user in self.users:
            friends = random.sample(self.users, k=random.randint(1, 10))
            for friend in friends:
                if friend != user:
                    contact = self.db.Contact(
                        friend_id=friend.id
                    )
                    user.contacts.append(contact)
        self.session.add_all(self.users)
        self.session.flush()

    def create_history(self):
        for user in self.users:
            start_time = dt.datetime(
                year=2023,
                month=1,
                day=random.randint(1, 31),
                hour=random.randint(1, 23),
                tzinfo=dt.timezone.utc
            )
            self.user_service.login(user, start_time, 'localhost')
            for _ in range(random.randint(1, 5)):
                start_time += dt.timedelta(minutes=5)
                self.user_service.user_get_message_from_server(
                    user,
                    start_time,
                    'localhost'
                )
                start_time += dt.timedelta(minutes=5)
                self.user_service.user_send_message_to_server(
                    user,
                    start_time,
                    'localhost'
                )
            start_time += dt.timedelta(minutes=5)
            self.user_service.logout(user, start_time, 'localhost')

    def create_data_if_not_exist(self, session: Session):
        if session.scalars(select(self.db.User)).first():
            return
        self.create_users()
        self.create_contacts()
        self.create_history()
        self.session.commit()
