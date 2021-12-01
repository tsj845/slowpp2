import sys

x = None

def f ():
    raise Exception(0)

try:
    f()
except Exception:
    x = sys.exc_info()
    print(x)