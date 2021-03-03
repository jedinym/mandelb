from typing import Tuple
from collections import defaultdict
import graphics as gph
from math import sqrt
from PIL import Image
import argparse as ap


MAX_ITERATIONS = 1000
WIDTH = 3000
HEIGHT = 3000

#parser = ap.ArgumentParser()

#parser.add_argument('-w', '--width', type=int)


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


def get_color(its) -> Tuple[int, int, int]:
    cols = [(0, 0, 102), (0, 0, 153), (0, 0, 204), (0, 0, 255)]

    if its < 5:
        return cols[0]
    elif its < 10:
        return cols[1]
    elif its < 15:
        return cols[2]

    return cols[3]


if __name__ == "__main__":
    img = Image.new('RGB', (WIDTH, HEIGHT), 'white')

    itsh = defaultdict(lambda: 0)

    for x in range(WIDTH):
        for y in range(HEIGHT):
            p = gph.Point(x, y)

            its = get_iterations(p)

            itsh[its] += 1

            if its == MAX_ITERATIONS:
                img.putpixel((x, y), (0, 0, 0))
            else:
                img.putpixel((x, y), get_color(its))

    img.save('mandelb.png')

    with open("histo.txt", 'w') as file:
        for it, n_it in itsh.items():
            file.write(f"{it} : {n_it}\n")
