import socket


class UsersSockets:
    def __init__(self):
        self.users_sockets = {}

    def add_client(self, user_id: int, client: socket.socket) -> None:
        self.users_sockets[user_id] = client

    def get_client(self, user_id: int) -> socket.socket:
        return self.users_sockets.get(user_id)

    def drop_client(self, user_id: int) -> bool:
        del self.users_sockets[user_id]
        return True
