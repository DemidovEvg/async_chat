import unittest
from unittest.mock import MagicMock
import socket
from async_chat.server import ServerChat


class TestBaseServerChat(unittest.TestCase):
    def setUp(self) -> None:
        self.max_users = 5
        self.port = 3000

    def test_get_request(self):
        server_chat = ServerChat(
            port=self.port,
            max_users=self.max_users
        )
        client = MagicMock(spec=socket.socket)
        client.recv = MagicMock(return_value=b'result')
        request = server_chat.get_request(
            client=client
        )
        self.assertTrue(request == 'result')

    def test_processing_request(self):
        server_chat = ServerChat(
            port=self.port,
            max_users=self.max_users
        )
        server_chat.dispatch = MagicMock(return_value='response')
        request = "{}"
        result = server_chat.processing_request(request)
        self.assertEqual(result, 'response')
