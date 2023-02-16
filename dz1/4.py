# Преобразовать слова «разработка», «администрирование», «protocol», «standard» из
# строкового представления в байтовое и выполнить обратное преобразование (используя
# методы encode и decode).

words = [
    'разработка',
    'администрирование',
    'protocol',
    'standard'
]
bwords: list[bytes] = []
for word in words:
    bwords.append(word.encode())

print(bwords)
# [b'\xd1\x80\xd0\xb0\xd0\xb7\xd1\x80\xd0\xb0\xd0\xb1\xd0\xbe\xd1\x82\xd0\xba\xd0\xb0', b'\xd0\xb0\xd0\xb4\xd0\xbc\xd0\xb8\xd0\xbd\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb8\xd1\x80\xd0\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xb5', b'protocol', b'standard']

words = []
for bword in bwords:
    words.append(bword.decode())

print(words)
# ['разработка', 'администрирование', 'protocol', 'standard']
