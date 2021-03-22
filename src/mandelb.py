#!/usr/bin/python3

from typing import Tuple, List
import cProfile
from math import sqrt
from PIL import Image
import argparse as ap
from multiprocessing import Pool
import ctypes as cp
from os import getcwd


Pixel = Tuple[int, int]


MAX_ITERATIONS = 1000
WIDTH = 0
HEIGHT = 0
THREADS = 4


def get_color(its: int) -> Tuple[int, int, int]:
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

    lib = cp.cdll.LoadLibrary(getcwd() + '/lib/mandelb.so')
    c_get_its = lib.c_get_iterations
    c_get_its.restype = cp.c_int

    for x in range(x0, x1):
        for y in range(y0, y1):
            pixel = (x, y)
            iters = c_get_its(x, y, WIDTH, HEIGHT, MAX_ITERATIONS)
            it_list.append((pixel, iters))

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
    parser = ap.ArgumentParser()
    parser.add_argument('-s,', '--size', required=True,
                        help='Size of the resulting image')
    parser.add_argument('-o', '--output', required=False,
                        help='Output filepath')
    parser.add_argument('-b', '--benchmark', action='store_const',
                        const='benchmark',
                        help='cProfile output to stdin')
    parser.add_argument('-m', '--max-iterations',
                        help='Maximum mandelb. set iterations')

    parser.add_argument('filepath', help='Output filepath')
    args = vars(parser.parse_args())

    if args['output'] is not None:
        output = args['output']
    else:
        output = args['filepath']

    if args['max_iterations'] is not None:
        MAX_ITERATIONS = int(args['max_iterations'])

    WIDTH = int(args['size'])
    HEIGHT = int(args['size'])

    if args['benchmark'] is not None:
        cProfile.run(fr'generateMSImage("{output}")')
    else:
        generateMSImage(output)
