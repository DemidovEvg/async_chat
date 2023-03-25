import click
import trio
from async_chat.server import ServerChat
import log_config.server_log_config  # noqa


def start_shell():
    from IPython import start_ipython
    from async_chat.server import db
    with db.SessionLocal() as session:
        user_ns = globals()
        user_ns.update(locals())
        start_ipython(argv=[], user_ns=globals())


@click.command()
@click.option('--port', default=3000, type=int)
@click.option('--max_users', default=1000, type=int)
@click.option('--shell', default=False, type=bool)
def main(port: int, max_users: int, shell: bool):
    if shell:
        start_shell()
        return

    server_chat = ServerChat(
        port=port,
        max_users=max_users
    )
    trio.run(server_chat.run)


if __name__ == '__main__':
    main()
