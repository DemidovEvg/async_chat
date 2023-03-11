from tabulate import tabulate
from ex2 import host_range_ping


def host_range_ping_tab(*args, **kwargs):
    pings_list = host_range_ping(*args, **kwargs)
    tabular_data = dict(reachable=[], unreachable=[])
    for ping in pings_list:
        if ping.result == ping.Result.AVAILABLE:
            tabular_data['reachable'].append(ping.resourse)
        else:
            tabular_data['unreachable'].append(ping.resourse)
    return tabulate(tabular_data=tabular_data, headers='keys', tablefmt='rounded_outline')


if __name__ == '__main__':
    args = [
        '127.255.255.250',
        '128.0.0.5',
    ]
    table1 = host_range_ping_tab(args, encoding='cp866')
    print(table1)
