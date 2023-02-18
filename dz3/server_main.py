import click
from async_chat.server import ServerChat


@click.command()
@click.option('--port', default=3000, type=int)
@click.option('--max_users', default=5, type=int)
def main(port: int, max_users: int):
    print(f'Инициализируем сервер используя {port=} {max_users=}')
    server_chat = ServerChat(
        port=port,
        max_users=max_users
    )
    server_chat.init_socket()
    server_chat.start_loop()


if __name__ == '__main__':
    main()
