import click
from async_chat.server import ServerChat
import log_config.server_log_config  # noqa


@click.command()
@click.option('--port', default=3000, type=int)
@click.option('--max_users', default=1000, type=int)
def main(port: int, max_users: int):
    server_chat = ServerChat(
        port=port,
        max_users=max_users
    )
    server_chat.init_socket()
    server_chat.run()


if __name__ == '__main__':
    main()
