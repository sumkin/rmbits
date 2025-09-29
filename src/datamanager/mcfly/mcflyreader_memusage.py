import tracemalloc

from mcflyreader import *
from yieldlookuploader import *


tracemalloc.start()

srcdate = '20200127'
depdate = '20201231'
bkgdate = '20201230'

srcyl = YieldLookupLoader(srcdate).get()
mcfly = McFlyReader(srcdate,depdate,bkgdate,srcyl)
mcfly.read_dfs()
num = 0
for r in mcfly.rows():
    num += 1
    if num % 10000 == 0:
        print('num = ', num)
current, peak = tracemalloc.get_traced_memory()
print(f'Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB')
tracemalloc.stop()



