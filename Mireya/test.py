from string import ascii_lowercase
from random import randint

def create_id():
    n = int(input('len of id: '))
    nid = int(input('num iof ids: '))
    for j in range(nid):
        res = ''
        for i in range(n):
            res += ('0123456789'+ascii_lowercase)[randint(0, 35)]
        print(res)
create_id()