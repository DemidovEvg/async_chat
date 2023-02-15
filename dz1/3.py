# Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в
# байтовом типе.

words = [
    'attribute',
    'класс',
    'функция',
    'type'
]

for word in words:
    if word.encode():
        print(word.encode())

b'attribute'
b'\xd0\xba\xd0\xbb\xd0\xb0\xd1\x81\xd1\x81'
b'\xd1\x84\xd1\x83\xd0\xbd\xd0\xba\xd1\x86\xd0\xb8\xd1\x8f'
b'type'

# Все слова можно записать в байтово виде
