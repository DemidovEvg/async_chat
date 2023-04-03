import unittest
from ..server import ServerChat


class TestInitServerChat(unittest.TestCase):
    def setUp(self) -> None:
        self.max_users = 5
        self.port = 3000

    def test_init(self):
        server_chat = ServerChat(
            port=self.port,
            max_users=self.max_users
        )
        self.assertEqual(server_chat.port, self.port)
        self.assertEqual(server_chat.max_users, self.max_users)
        self.assertEqual(server_chat.max_data_size, 1024)
