import click
from async_chat.client import ClientChat
import log_config.client_log_config  # noqa


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
    client_chat = ClientChat(
        account_name=account_name,
        password=password,
        ip_address=ip_address,
        port=port
    )
    client_chat.start_client()


if __name__ == '__main__':
    main()
