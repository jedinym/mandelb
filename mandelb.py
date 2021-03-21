from typing import Tuple, List
import cProfile
from math import sqrt
from PIL import Image
import argparse as ap
from multiprocessing import Pool


Pixel = Tuple[int, int]


MAX_ITERATIONS = 1000
WIDTH = 3000
HEIGHT = 3000
THREADS = 4

# parser = ap.ArgumentParser()

# parser.add_argument('-w', '--width', type=int)


def get_mag(num: complex) -> float:
    return sqrt(num.real ** 2 + num.imag ** 2)


def scale(num, size):
    return (num - (size // 2)) / (size / 4)


def get_iterations(pixel: Pixel) -> int:
    a = scale(pixel[0], WIDTH)
    b = scale(pixel[1], HEIGHT)

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

    if its == 1000:
        return (0, 0, 0)

    if its < 3:
        return cols[0]
    elif its < 7:
        return cols[1]
    elif its < 15:
        return cols[2]

    return cols[3]


def build_mandelbrot_bounds(bounds: Tuple[Pixel, Pixel]) \
        -> List[Tuple[Pixel, int]]:

    ul_bound, lr_bound = bounds

    x0, y0 = ul_bound
    x1, y1 = lr_bound

    it_list = []

    for x in range(x0, x1):
        for y in range(y0, y1):
            pixel = (x, y)
            it_list.append((pixel, get_iterations(pixel)))

    return it_list


def build_image(it_map: List[Tuple[Pixel, int]]) -> Image:
    img = Image.new('RGB', (WIDTH, HEIGHT), 'white')

    for pixel, iters in it_map:
        img.putpixel(pixel, get_color(iters))

    return img


def generateMSImage(filepath: str) -> None:
    pl = Pool(THREADS)
    bound_list = [((0, 0), (WIDTH//2, HEIGHT//2)),
                  ((WIDTH//2, 0), (WIDTH, HEIGHT//2)),
                  ((0, HEIGHT//2), (WIDTH//2, HEIGHT)),
                  ((WIDTH // 2, HEIGHT//2), (WIDTH, HEIGHT))]

    itmaps = pl.map(build_mandelbrot_bounds, bound_list)

    im = itmaps[0] + itmaps[1] + itmaps[2] + itmaps[3]

    img = build_image(im)

    img.save(filepath)


if __name__ == "__main__":
    cProfile.run(r'generateMSImage("x.png")')
