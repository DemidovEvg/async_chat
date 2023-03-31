import unittest
from unittest.mock import MagicMock, patch
import datetime as dt
from async_chat.server.user_service import UserService
from async_chat.server import ServerChat
from async_chat.server import db as test_db  # Noqa
from async_chat import jim
import json


class TestActionsServerChat(unittest.TestCase):
    def setUp(self) -> None:
        self.account_name_exist = 'Ivan'
        self.password_right = 'ivan123'
        self.account_name_not_exist = 'Ivan2'
        self.password_wrong = '00000'

        self.max_users = 5
        self.port = 3000

    def test_login_user_exist(self):
        server_chat = ServerChat(
            port=self.port,
            max_users=self.max_users
        )

        data = dict(
            action=jim.ClientActions.authenticate.value,
            time=dt.datetime.now(dt.timezone.utc).timestamp(),
            user=dict(
                account_name=self.account_name_exist,
                password=self.password_right
            )
        )
        server_chat.current_address = ('127.0.0.333', 44444)
        server_chat.current_client = MagicMock()
        response = server_chat.login_user(data=data)
        result = json.loads(response)
        self.assertEqual(result.get('alert'), 'OK')

    def test_login_user_not_exist(self):
        server_chat = ServerChat(
            port=self.port,
            max_users=self.max_users
        )

        data = dict(
            action=jim.ClientActions.authenticate.value,
            time=dt.datetime.now(dt.timezone.utc).timestamp(),
            user=dict(
                account_name=self.account_name_not_exist,
                password=self.password_wrong
            )
        )
        server_chat.current_address = ('127.0.0.333', 44444)
        server_chat.current_client = MagicMock()
        response = server_chat.login_user(data=data)
        result = json.loads(response)
        self.assertEqual(result.get('error'), 'Bad password or login')

    def test_logout_user_exist(self):
        server_chat = ServerChat(
            port=self.port,
            max_users=self.max_users
        )

        data = dict(
            action=jim.ClientActions.quit.value,
            time=dt.datetime.now(dt.timezone.utc).timestamp(),
            user=dict(
                account_name=self.account_name_exist,
            )
        )
        server_chat.current_address = ('127.0.0.333', 44444)
        server_chat.current_client = MagicMock()
        response = server_chat.logout_user(data=data)
        result = json.loads(response)
        self.assertEqual(result.get('alert'), 'OK')

    def test_processing_presence_online(self):
        with patch.object(UserService, 'is_online') as mock_is_online:
            server_chat = ServerChat(
                port=self.port,
                max_users=self.max_users
            )

            data = dict(
                action=jim.ClientActions.presence.value,
                time=dt.datetime.now(dt.timezone.utc).timestamp(),
                user=dict(
                    account_name=self.account_name_exist,
                    status=jim.Statuses.i_am_here
                )
            )
            server_chat.current_address = ('127.0.0.333', 44444)
            server_chat.current_client = MagicMock()
            mock_is_online.return_value = True
            response = server_chat.processing_presence(data=data)
            result = json.loads(response)
            self.assertEqual(result.get('alert'), 'Presense accepted')

    def test_processing_presence_offline(self):
        with patch.object(UserService, 'is_online') as mock_is_online:
            server_chat = ServerChat(
                port=self.port,
                max_users=self.max_users
            )

            data = dict(
                action=jim.ClientActions.presence.value,
                time=dt.datetime.now(dt.timezone.utc).timestamp(),
                user=dict(
                    account_name=self.account_name_exist,
                    status=jim.Statuses.i_am_here
                )
            )
            server_chat.current_address = ('127.0.0.333', 44444)
            server_chat.current_client = MagicMock()
            mock_is_online.return_value = False
            response = server_chat.processing_presence(data=data)
            result = json.loads(response)
            self.assertEqual(result.get('error'), 'Auth required')
