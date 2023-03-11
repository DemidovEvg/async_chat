import ipaddress

from ipaddress import IPv4Address, IPv6Address
import socket
import subprocess
from dataclasses import dataclass, field
import enum


@dataclass
class Ping:
    class Result(enum.Enum):
        AVAILABLE = 1
        NOT_AVAILABLE = 2

    resourse: IPv4Address | IPv6Address
    process: subprocess.Popen
    input_data: str = ''
    result: Result = field(default=Result.NOT_AVAILABLE)

    @property
    def result_message(self) -> str:
        if self.result == self.__class__.Result.AVAILABLE:
            return 'Узел доступен'
        else:
            return 'Узел не доступен'


def get_ip_address(host_or_ip: str) -> IPv4Address | IPv6Address:
    try:
        return ipaddress.ip_address(host_or_ip)
    except ValueError:
        return ipaddress.ip_address(socket.gethostbyname(host_or_ip))


def get_ip_addresses(hosts_or_ips: list[str]) -> tuple[str, IPv4Address | IPv6Address]:
    resourses = []
    for arg in hosts_or_ips:
        resourses.append((arg, get_ip_address(arg)))

    return resourses


def get_process(resourse: str, encoding: str = 'utf-8') -> subprocess.Popen:
    return subprocess.Popen(
        ['ping', str(resourse), '-n', '1'],
        stdout=subprocess.PIPE,
        encoding=encoding,
        text=True
    )


def create_pings(
    resourses: tuple[str, IPv4Address | IPv6Address],
    encoding: str = 'utf-8'
):
    pings: list[Ping] = []
    for input_data, resourse in resourses:
        process = get_process(str(resourse), encoding)
        pings.append(
            Ping(
                input_data=input_data,
                resourse=resourse,
                process=process
            )
        )
    return pings


def check_pings(pings: list[Ping]) -> list[Ping]:
    pings_tmp = pings[:]
    while pings_tmp:
        finished_pings = [
            ping for ping in pings_tmp if ping.process.poll() is not None]
        for current_ping in finished_pings:
            pings_tmp.remove(current_ping)
            if int(current_ping.process.returncode) == 0:
                current_ping.result = Ping.Result.AVAILABLE
            else:
                current_ping.result = Ping.Result.NOT_AVAILABLE


def host_ping(hosts_or_ips: list[str], encoding: str = 'utf-8') -> list[Ping]:
    resourses = get_ip_addresses(hosts_or_ips)
    pings = create_pings(resourses, encoding=encoding)
    check_pings(pings)
    return pings


if __name__ == '__main__':
    args = [
        '133.3.3.1',
        'ya.ru'
    ]
    result_list = host_ping(args, encoding='cp866')
    for result in result_list:
        print(
            f'Ресурс={result.input_data} результат пинга={result.result_message}'
        )
