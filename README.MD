##async_chat
Запуск сервера:
python .\dz3\server_main.py  

Опциональные аргументы: 
@click.option('--port', default=3000, type=int)
@click.option('--max_users', default=5, type=int)

Запуск клиента:
python .\dz3\client_main.py
python .\dz3\client_main.py --account_name=Ivan --password=ivan123

Опциональные аргументы: 
@click.option('--account_name', type=str)
@click.option('--password', type=str)
@click.option('--ip_address', default='127.0.0.1', type=str)
@click.option('--port', default=3000, type=int)

###Запуск тестов:
python -m unittest discover

###Добавлено логирование

### +dz6
Пример логов в консоли
2023-03-04 15:44:42,335---Вызвали функцию foo(a: int, b: int) -> int: из I:\python\async_chat\dz6\dz6.py---main---line=52
2023-03-04 15:44:42,336---Вызвали функцию foo(a: int, b: int) -> int: из I:\python\async_chat\dz6\dz6.py---main---line=53
2023-03-04 15:44:42,336---Вызвали функцию A.__init__(self): из I:\python\async_chat\dz6\dz6.py---<module>---line=57