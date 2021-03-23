#!/usr/bin/python3

from typing import Any, Tuple, List, Dict
import cProfile
from PIL import Image
import argparse as ap
from multiprocessing import Pool
import ctypes as cp
from os import getcwd, remove, cpu_count
# from os import environ
# environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
from itertools import chain


Pixel = Tuple[int, int]


MAX_ITERATIONS = 1000
CHUNK_COUNT = 32  # how many chunks to create
WIDTH = 0
HEIGHT = 0
SIZE = 0


def get_bound_list(n):
    x_step = SIZE // n
    diff = SIZE % n

    x_pos = 0

    bound_list = []

    for x in range(n - 1):
        bound_list.append(((x_pos, 0), (x_pos + x_step, SIZE)))
        x_pos += x_step

    last_step = diff if diff != 0 else x_step

    bound_list.append(((x_pos, 0), (x_pos + last_step, SIZE)))

    return bound_list


def get_arg_list(view, zoom) -> List[Any]:
    bound_list = get_bound_list(CHUNK_COUNT)

    arg_list = []

    for bound in bound_list:
        arg_list.append((bound, view, zoom, MAX_ITERATIONS))

    return arg_list


def get_color(its: int) -> Tuple[int, int, int]:
    cols = [(0, 0, 102), (0, 0, 153), (0, 0, 204), (0, 0, 255)]

    if its == MAX_ITERATIONS:
        return (0, 0, 0)

    if its < 3:
        return cols[0]
    elif its < 7:
        return cols[1]
    elif its < 15:
        return cols[2]

    return cols[3]


def scale(start: float, end: float, position: int, size: int) -> float:
    coeff = abs(end - start) / size

    return start + position * coeff


def build_mandelbrot_bounds(bounds: Tuple[Pixel, Pixel],
                            view: Tuple[float, float],
                            zoom: int,
                            max_iterations: int) \
        -> List[Tuple[Pixel, int]]:

    ul_bound, lr_bound = bounds

    x0, y0 = ul_bound
    x1, y1 = lr_bound

    re_lo, re_hi = view[0] - 1 / zoom, view[0] + 1 / zoom
    im_lo, im_hi = view[1] - 1 / zoom, view[1] + 1 / zoom

    it_list = []

    lib = cp.cdll.LoadLibrary(getcwd() + '/lib/mandelb.so')
    c_get_its = lib.c_get_iterations
    c_get_its.restype = cp.c_int

    for x in range(x0, x1):
        scaled_x = scale(re_lo, re_hi, x, WIDTH)
        for y in range(y0, y1):
            pixel = (x, y)

            scaled_y = scale(im_lo, im_hi, y, HEIGHT)

            # print(f"x: {scaled_x}  y: {scaled_y}")

            iters = c_get_its(cp.c_longdouble(scaled_x),
                              cp.c_longdouble(scaled_y),
                              cp.c_int(max_iterations))

            it_list.append((pixel, iters))

    return it_list


def build_image(it_map: List[Tuple[Pixel, int]]) -> Image:
    img = Image.new('RGB', (WIDTH, HEIGHT), 'white')

    for pixel, iters in it_map:
        img.putpixel(pixel, get_color(iters))

    return img


def generateMSImage(filepath: str) -> None:
    pl = Pool(cpu_count())

    view = 0.0, 0.0
    zoom = 1/2

    arg_list = get_arg_list(view, zoom)

    with Pool(cpu_count()) as pl:
        it_maps = pl.starmap(build_mandelbrot_bounds, arg_list)

    im = list(chain.from_iterable(it_maps))  # might be too slow

    img = build_image(im)

    img.save(filepath)


def load_colors(filepath: str) -> Dict[int, Tuple[int, int, int]]:
    color_dict = dict()
    with open(filepath, 'r') as file:
        for line in file.readlines():
            line_split = line.split(',')
            color_dict[int(line_split[0])] = (int(line_split[1]),
                                              int(line_split[2]),
                                              int(line_split[3].rstrip()))

    color_dict[MAX_ITERATIONS] = (0, 0, 0)
    return color_dict


def interactive_session(color_dict: Dict[int, Tuple[int, int, int]]) -> None:
    # TODO: implenent gradial resolution rise

    screen = pg.display.set_mode((SIZE, SIZE))

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                exit(0)
            if event.type == pg.MOUSEBUTTONDOWN:
                # TODO: implement mouse zooming
                pass

        view = -1.767936363, -0.005048188
        zoom = 100

        arg_list = get_arg_list(view, zoom)

        with Pool(cpu_count()) as pl:
            it_maps = pl.starmap(build_mandelbrot_bounds, arg_list)

        it_map = list(chain.from_iterable(it_maps))  # might be too slow

        for pixel, iters in it_map:
            point = pg.Rect(pixel, (1, 1))
            pg.draw.rect(screen, color_dict[iters], point)

        pg.display.flip()


def get_args() -> Dict[str, Any]:
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
    parser.add_argument('-i', '--interactive', action='store_const',
                        const='interactive')
    parser.add_argument('-c', '--chunk-count',
                        help='How many chunks to work on concurrently. Default 32',
                        default=cpu_count() * 4)

    parser.add_argument('filepath', nargs='?',
                        default=None,
                        help='Output filepath')

    args = vars(parser.parse_args())

    return args


if __name__ == "__main__":
    args = get_args()

    if args['interactive'] is None:
        if args['output'] is not None:
            output = args['output']
        else:
            output = args['filepath']

    if args['max_iterations'] is not None:
        MAX_ITERATIONS = int(args['max_iterations'])

    WIDTH = int(args['size'])
    HEIGHT = int(args['size'])
    SIZE = HEIGHT

    CHUNK_COUNT = int(args['chunk_count'])

    if args['benchmark'] is not None:
        cProfile.run(fr'generateMSImage("{output}")')
        remove(output)
        exit(0)

    if args['interactive'] is not None:
        color_dict = load_colors('colors.txt')
        interactive_session(color_dict)
    else:
        generateMSImage(output)
