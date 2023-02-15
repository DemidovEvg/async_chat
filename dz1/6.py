# Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое
# программирование», «сокет», «декоратор». Проверить кодировку файла по умолчанию.
# Принудительно открыть файл в формате Unicode и вывести его содержимое.
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

file = open(BASE_DIR / 'test_file.txt')

print(file.encoding)
# cp1251

file_unicode = open(BASE_DIR / 'test_file.txt', encoding='utf-8')

print(file_unicode.readlines())
# ['сетевое программирование\n', 'сокет\n', 'декоратор']
