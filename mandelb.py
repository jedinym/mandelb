import graphics as gph
from math import sqrt
from PIL import Image


MAX_ITERATIONS = 1000
WIDTH = 2000
HEIGHT = 2000


def get_mag(num: complex) -> float:
    return sqrt(num.real ** 2 + num.imag ** 2)


def scale(num, size):
    return (num - (size // 2)) / (size / 4)


def get_iterations(pixel: gph.Point) -> int:
    a = scale(pixel.getX(), WIDTH)
    b = scale(pixel.getY(), HEIGHT)

    c = complex(a, b)
    z = complex(0, 0)
    iters = 0

    traversed = set()

    while get_mag(z) <= 2 and iters < MAX_ITERATIONS:
        z = z**2 + c

        if z in traversed:
            return MAX_ITERATIONS

        traversed.add(z)

        iters += 1

    return iters


img = Image.new('RGB', (WIDTH, HEIGHT), 'white')

for x in range(WIDTH):
    for y in range(HEIGHT):
        p = gph.Point(x, y)

        its = get_iterations(p)

        if its == MAX_ITERATIONS:
            img.putpixel((x, y), (0, 0, 0))

img.save('mandelb.png')
