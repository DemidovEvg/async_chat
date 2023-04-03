"""Класс окна со списком статистики пользователей"""
from ..user_service import UserService
from ..db import SessionLocal, User
from ..admin_ui.item_list import ItemList


class UserListStat(ItemList):
    colums = [
        {
            'label': 'id',
            'field_name': 'id',
            'width': 50
        },
        {
            'label': 'Аккаунт',
            'field_name': 'account_name',
            'width': 150
        },
        {
            'label': 'Время последнего входа',
            'field_name': 'last_login_time',
            'width': 200
        },
        {
            'label': 'Время последнего сообщения',
            'field_name': 'last_message_time',
            'width': 200
        },
        {
            'label': 'Кол. отправленных сообщений',
            'field_name': 'send_messages_count',
            'width': 200
        },
        {
            'label': 'Вошел',
            'field_name': 'has_entered',
            'width': 50
        },
    ]
    title = 'Статистика'

    def get_columns_data(self, user: User) -> dict[str, str]:
        with SessionLocal() as session:
            session.add(user)

            result = user.__dict__
            result['last_login_time'] = user.last_login
            result['last_message_time'] = user.last_send_message
            user_service = UserService(session)
            result['send_messages_count'] = (
                user_service.get_user_send_messages_count(user)
            )
            return result

    def get_queryset(self) -> list[object]:
        with SessionLocal() as session:
            user_service = UserService(session)
            users = user_service.get_users()
        return users
