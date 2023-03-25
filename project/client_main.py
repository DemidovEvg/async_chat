import click
import trio
from async_chat.client import ClientChat
from log_config import client_log_config  # noqa
from async_chat.client.console import ConsoleServer
from async_chat.client.client_ui.client_ui_talk import ClientUiTalk


@click.command()
@click.option('--account_name', type=str)
@click.option('--password', type=str)
@click.option('--ip_address', default='127.0.0.1', type=str)
@click.option('--port', default=3000, type=int)
def main(
    account_name: str | None,
    password: str | None,
    ip_address: str,
    port: int
):
    print(
        f'Инициализируем клента {account_name=}, используя {ip_address=} {port=}'
    )
    client_ui_talk = ClientUiTalk[ConsoleServer]()
    ui = ConsoleServer(client_ui_talk)

    client_ui_talk.put_ui(ui)
    client_chat = ClientChat(
        account_name=account_name,
        password=password,
        ip_address=ip_address,
        port=port,
        client_ui_talk=client_ui_talk
    )
    client_ui_talk.put_client(client_chat)

    trio.run(client_chat.run)


if __name__ == '__main__':
    main()
