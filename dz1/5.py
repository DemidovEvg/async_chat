# Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из
# байтовового в строковый тип на кириллице.


import subprocess

args = ['ping', 'yandex.ru']
sites = [
    'yandex.ru',
    'youtube.com',
]
processes = []
for site in sites:
    processes.append(
        subprocess.Popen(['ping', site], stdout=subprocess.PIPE)
    )
need_continue = True
while need_continue:
    codes = []
    not_finished_processes = processes.copy()
    for i, process in enumerate(processes):
        try:
            line = next(iter(process.stdout))
            not_finished_processes.append(process)
            print(f"{process}\n {line.decode('cp866')}")
        except StopIteration:
            process.kill()
        codes.append(process.returncode)

    need_continue = bool([code for code in codes if code is None])
