import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
import datetime as dt
from io import StringIO
from async_chat.client import ClientChat

result = []


class TestCommandLineClientChat(unittest.TestCase):

    def setUp(self) -> None:
        self.current_datetime = dt.datetime.now(
            dt.timezone.utc
        )
        self.account_name = 'Ivan'
        self.password = 'ivan123'
        self.ip_address = '127.0.0.101'
        self.port = 3001

    @patch('builtins.input', lambda x: 'exit')
    @patch('sys.stdout', new_callable=StringIO)
    def test_exit(self, stdout: StringIO):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port
        )
        client_chat.action_logout = MagicMock(
            return_value=None
        )
        with self.assertRaises(SystemExit):
            try:
                client_chat.command_line_loop()
            except SystemExit as exc:
                self.assertEqual(str(exc), '0')
                raise
        output = stdout.getvalue()
        self.assertIn('Допустимые команды:', output)
        client_chat.action_logout.assert_called_once()

    @patch('builtins.input', side_effect=[
        'login --account_name=test --password=test',
        'exit'
    ])
    @patch('sys.stdout', new_callable=StringIO)
    def test_login(self, stdout: StringIO, _):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port
        )
        client_chat.action_login = MagicMock(
            side_effect=None
        )
        client_chat.action_logout = MagicMock(
            return_value=None
        )
        with self.assertRaises(SystemExit):
            try:
                client_chat.command_line_loop()
            except SystemExit as exc:
                self.assertEqual(str(exc), '0')
                raise
        self.assertEqual(client_chat.account_name, 'test')
        self.assertEqual(client_chat.password, 'test')

        client_chat.action_login.assert_any_call(
            account_name='test',
            password='test'
        )
        client_chat.action_logout.assert_called()

    @patch('builtins.input', side_effect=[
        'presence',
        'exit'
    ])
    @patch('sys.stdout', new_callable=StringIO)
    def test_presence(self, stdout: StringIO, _):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port
        )
        client_chat.action_send_presence = MagicMock(
            side_effect=None
        )
        client_chat.action_logout = MagicMock(
            return_value=None
        )
        with self.assertRaises(SystemExit):
            try:
                client_chat.command_line_loop()
            except SystemExit as exc:
                self.assertEqual(str(exc), '0')
                raise

        client_chat.action_send_presence.assert_called_once()
        client_chat.action_logout.assert_called()

    @patch('builtins.input', side_effect=[
        'logout',
        'exit'
    ])
    @patch('sys.stdout', new_callable=StringIO)
    def test_logout(self, stdout: StringIO, _):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port
        )
        client_chat.action_logout = MagicMock(
            return_value=None
        )
        with self.assertRaises(SystemExit):
            try:
                client_chat.command_line_loop()
            except SystemExit as exc:
                self.assertEqual(str(exc), '0')
                raise
        client_chat.action_logout.assert_called()
