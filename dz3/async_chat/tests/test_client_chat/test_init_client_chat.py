import unittest
import datetime as dt
import socket
from async_chat.client import ClientChat


class TestInitClientChat(unittest.TestCase):
    def setUp(self) -> None:
        self.current_datetime = dt.datetime.now(
            dt.timezone.utc
        )
        self.account_name = 'Ivan'
        self.password = 'ivan123'
        self.ip_address = '127.0.0.101'
        self.port = 3001

    def test_empty_init(self):
        with self.assertRaises(TypeError) as exc:
            ClientChat()
            self.assertIn(
                'missing 4 required positional arguments' in str(exc)
            )

    def test_init_with_none_account(self):
        client_chat = ClientChat(
            account_name=None,
            password=None,
            ip_address='127.0.0.1',
            port='3000'

        )
        self.assertTrue(
            client_chat.account_name is None
        )
        self.assertTrue(
            client_chat.password is None
        )
        self.assertTrue(
            str(client_chat.ip_address) == '127.0.0.1'
        )
        self.assertTrue(
            client_chat.port == '3000'
        )

    def test_init_with_account(self):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port

        )
        self.assertTrue(
            client_chat.account_name == self.account_name
        )
        self.assertTrue(
            client_chat.password == self.password
        )
        self.assertTrue(
            str(client_chat.ip_address) == self.ip_address
        )
        self.assertTrue(
            client_chat.port == self.port
        )

    def test_check_default_timeout(self):
        ClientChat(
            account_name=None,
            password=None,
            ip_address='127.0.0.1',
            port='3000'
        )
        self.assertEqual(socket.getdefaulttimeout(), 5)
