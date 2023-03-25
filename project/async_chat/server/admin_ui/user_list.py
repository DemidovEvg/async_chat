from async_chat.server.user_service import UserService
from async_chat.server.db import SessionLocal, User
from async_chat.server.admin_ui.item_list import ItemList


class UserList(ItemList):
    colums = [
        {
            'label': 'id',
            'field_name': 'id',
            'width': 50
        },
        {
            'label': 'Аккаунт',
            'field_name': 'account_name',
            'width': 200
        },
        {
            'label': 'Вошел',
            'field_name': 'has_entered',
            'width': 50
        },
    ]
    title = 'Пользователи'

    def get_columns_data(self, item: User) -> dict[str, str]:
        return item.__dict__

    def get_queryset(self) -> list[object]:
        with SessionLocal() as session:
            user_service = UserService(session)
            users = user_service.get_users()
        return users
