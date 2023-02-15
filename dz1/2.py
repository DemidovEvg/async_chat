# Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в
# последовательность кодов (не используя методы encode и decode) и определить тип,
# содержимое и длину соответствующих переменных.

words = [
    b'class',
    b'function',
    b'method'
]


for word in words:
    print(f' {word=} {type(word)=} {len(word)=}')

#  word=b'class' type(word)=<class 'bytes'> len(word)=5
#  word=b'function' type(word)=<class 'bytes'> len(word)=8
#  word=b'method' type(word)=<class 'bytes'> len(word)=6
