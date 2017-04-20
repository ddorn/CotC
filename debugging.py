# colors
def print_colored(style, fg, bg, *items, end='\n', **kwargs):
    format = ';'.join((str(style), str(fg), str(bg)))
    end = '\x1b[0m' + end
    print('\x1b[' + format + 'm', *items, end=end, **kwargs)


def red_bg(*args, **kwargs):
    print_colored(7, 31, 38, *args, **kwargs)


def red(*args, **kwargs):
    print_colored(6, 31, 38, *args, **kwargs)


def green_bg(*args, **kwargs):
    print_colored(7, 32, 38, *args, **kwargs)


def green(*args, **kwargs):
    print_colored(6, 32, 38, *args, **kwargs)


def blue_bg(*args, **kwargs):
    print_colored(7, 36, 40, *args, **kwargs)


def blue(*args, **kwargs):
    print_colored(5, 36, 38, *args, **kwargs)


def pink_bg(*args, **kwargs):
    print_colored(7, 35, 38, *args, **kwargs)


def pink(*args, **kwargs):
    print_colored(6, 35, 38, *args, **kwargs)


from pprint import pprint as pp
from time import sleep


def pprint(obj):
    pp(obj)
    sleep(0.001)  # so tracestack


def step(name: str, rank=0):
    s = ' ' + name + ' '
    s = s.center(80 - rank*10, '#') + ' '
    print('\n')
    print_colored(5, 36, 43, s)
    print()


__all__ = ['pprint', 'blue', 'blue_bg', 'red', 'red_bg', 'pink', 'pink_bg', 'green', 'green_bg', 'step']
