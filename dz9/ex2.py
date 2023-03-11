from ex1 import Ping, get_ip_address, get_process, check_pings


def get_range_pings(range_ips: list[str], encoding: str = 'utf-8') -> list[Ping]:
    start_ip = get_ip_address(range_ips[0])
    end_ip = get_ip_address(range_ips[1])
    result = [
        Ping(
            input_data=range_ips[0],
            resourse=start_ip,
            process=get_process(str(start_ip), encoding)
        )
    ]
    if start_ip == end_ip:
        return result
    start_ip, end_ip = (
        (start_ip, end_ip)
        if end_ip > start_ip
        else (end_ip, start_ip)
    )
    delta = (
        int(end_ip) - int(start_ip)
        if end_ip > start_ip
        else int(start_ip) - int(end_ip)
    )
    for i in range(delta):
        current_ip = start_ip + i + 1
        result.append(
            Ping(
                resourse=current_ip,
                process=get_process(str(current_ip), encoding)
            )
        )
    return result


def host_range_ping(range_ips: list[str], encoding: str = 'utf-8') -> list[Ping]:
    pings = get_range_pings(range_ips, encoding)
    check_pings(pings)
    return pings


if __name__ == '__main__':
    args = [
        '127.0.0.1',
        '127.0.0.15',
    ]
    result_list = host_range_ping(args, encoding='cp866')
    for result in result_list:
        print(
            f'Ресурс={result.input_data} результат пинга={result.result_message}'
        )
