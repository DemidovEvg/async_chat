import subprocess
from pathlib import Path
import time
import signal
from dataclasses import dataclass
import click

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHONPATH = str(BASE_DIR/'env/scripts/python')


@dataclass
class Client:
    username: str
    process: subprocess.Popen


def exit_handler(clients: list[Client]):
    gracefull_close(clients)
    raise SystemExit(0)


def gracefull_close(clients: list[Client]):
    print('Мягко завершаем процессы')
    for client in clients:
        client.process.terminate()
    all_done = False
    while not all_done:
        all_done = True
        for client in clients:
            if client.process.poll() is None:
                all_done = False
                break


@click.command()
@click.option('--num_clients', default=2, type=int)
def main(num_clients: int):
    clients: list[Client] = []
    signal.signal(
        signal.SIGINT, lambda signum, frame: exit_handler(clients)
    )
    signal.signal(
        signal.SIGTERM, lambda signum, frame: exit_handler(clients)
    )
    for i in range(num_clients):
        username = f'Ivan{i+1}'
        process = subprocess.Popen(
            [
                PYTHONPATH,
                f'{str(BASE_DIR)}/dz3/client_main.py',
                f'--account_name={username}',
                '--password=ivan123'
            ],
            bufsize=0,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        clients.append(
            Client(
                username=username,
                process=process
            )
        )
    time.sleep(1)
    for client in clients:
        time.sleep(0.5)
        print('Вбиваем команду')
        client.process.stdin.write(b'login\n\r')
    client1 = clients[0]
    client2 = clients[-1]
    command = ''.encode()
    client1.process.stdin.write(command)
    command = f'message {client2.username} Hello my friend\n\r'.encode()
    client1.process.stdin.write(command)
    command = f'message {client2.username} How are you?\n\r'.encode()
    client1.process.stdin.write(command)
    command = f'message {client2.username} I am fine!\n\r'.encode()
    client1.process.stdin.write(command)
    count = 0
    while True:
        time.sleep(0.05)
        count = count + 1
        print(count)
        result_bytes_list: list[bytes] = [client2.process.stdout.readline()]
        for result_bytes in result_bytes_list:
            result = result_bytes.decode('cp1251')
            if 'Пришло сообщение:' in result:
                print(result.strip())


if __name__ == '__main__':
    main()
