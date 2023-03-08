import unittest
from unittest.mock import MagicMock, patch
import datetime as dt
from async_chat.client import ClientChat
from async_chat.utils import (
    IncommingMessage,
)


class TestActionsClientChat(unittest.TestCase):
    def setUp(self) -> None:
        self.current_datetime = dt.datetime.now(
            dt.timezone.utc
        )
        self.account_name = 'Ivan'
        self.password = 'ivan123'
        self.ip_address = '127.0.0.101'
        self.port = 3001

    @patch('async_chat.jim.MessageUserAuth')
    def test_login(self, MockMessageUserAuth: MagicMock):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port
        )
        client_chat.send_outgoing_message = MagicMock(
            return_value=None
        )
        client_chat.get_message = MagicMock(
            return_value=IncommingMessage('some_message')
        )

        client_chat.action_login(
            account_name=self.account_name,
            password=self.password
        )
        MockMessageUserAuth.assert_called()
        client_chat.send_outgoing_message.assert_called_once()
        client_chat.get_message.assert_called_once()

    @patch('async_chat.jim.MessageUserAuth')
    def test_login_if_none_account(self, MockMessageUserAuth: MagicMock):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port
        )
        client_chat.send_outgoing_message = MagicMock(
            return_value=None
        )
        client_chat.get_message = MagicMock(
            return_value=IncommingMessage('some_message')
        )
        with self.assertRaises(Exception):
            client_chat.action_login(
                account_name=None,
                password=None
            )
        MockMessageUserAuth.assert_not_called()

    @patch('async_chat.jim.MessageUserQuit')
    def test_logout(self, MockMessageUserQuit: MagicMock):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port
        )
        client_chat.send_outgoing_message = MagicMock(
            return_value=None
        )
        client_chat.get_message = MagicMock(
            return_value=IncommingMessage('some_message')
        )

        client_chat.action_logout(self.account_name)
        MockMessageUserQuit.assert_called()
        client_chat.send_outgoing_message.assert_called_once()
        client_chat.get_message.assert_called_once()

    @patch('async_chat.jim.MessageUserPresence')
    def test_precense(self, MockMessageUserPresence: MagicMock):
        client_chat = ClientChat(
            account_name=self.account_name,
            password=self.password,
            ip_address=self.ip_address,
            port=self.port
        )
        client_chat.send_outgoing_message = MagicMock(
            return_value=None
        )
        client_chat.get_message = MagicMock(
            return_value=IncommingMessage('some_message')
        )

        client_chat.action_send_presence()
        MockMessageUserPresence.assert_called()
        client_chat.send_outgoing_message.assert_called_once()
        client_chat.get_message.assert_called_once()
