#!/usr/bin/python3

from typing import Tuple, List, Dict
import cProfile
from PIL import Image
import argparse as ap
from multiprocessing import Pool
import ctypes as cp
from os import getcwd, remove, cpu_count
import os
import sys
# from os import environ
# environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
from itertools import chain


Pixel = Tuple[int, int]
PixelDiverList = List[Tuple[Pixel, int]]
Bound = Tuple[Pixel, Pixel]
View = Tuple[float, float]


MAX_ITERATIONS = 1000
LOWEST_RESOLUTION = 16
CHUNK_COUNT = 32  # how many chunks to create
WIDTH = 0
HEIGHT = 0
SIZE = 0
C_LIB = None


def get_bound_list(n: int) -> List[Bound]:
    """Divide the screen/view into <n> chunks for faster processing.

    Return a list of bounds -> (<topleft_pixel>, <bottomright_pixel>)
    """
    # TODO: this might be wrong
    # FIXME: it actually is
    x_step = SIZE // n
    diff = SIZE % n

    x_pos = 0

    bound_list: List[Bound] = []

    for x in range(n - 1):
        bound_list.append(((x_pos, 0), (x_pos + x_step, SIZE)))
        x_pos += x_step

    last_step = diff if diff != 0 else x_step

    bound_list.append(((x_pos, 0), (x_pos + last_step, SIZE)))

    return bound_list


def get_arg_list(view: View, zoom: float, resolution: int) \
        -> List[Tuple[Bound, View, float, int]]:
    """Pack arguments into a list of tuples to pass to build_mandelbrot_bounds()
    """
    bound_list = get_bound_list(CHUNK_COUNT)

    arg_list = []

    for bound in bound_list:
        arg_list.append((bound, view, zoom, MAX_ITERATIONS, resolution))

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


def scale(start: float, end: float, position: int) -> float:
    """Scale pixel coord to real/imaginary part of a complex number
    """
    coeff = abs(end - start) / SIZE

    return start + position * coeff


def get_iterations(scaled_x: float, scaled_y: float,
                   max_iterations: int) -> int:

    c_get_its = C_LIB.c_get_iterations
    c_get_its.restype = cp.c_int

    iters = c_get_its(cp.c_longdouble(scaled_x),
                      cp.c_longdouble(scaled_y),
                      cp.c_int(max_iterations))

    return iters


def build_mandelbrot_bounds(bounds: Tuple[Pixel, Pixel],
                            view: Tuple[float, float],
                            zoom: int,
                            max_iterations: int,
                            resolution: int) \
        -> PixelDiverList:
    """Associate each pixel with their respective number of iterations at
    which they diverge.
    https://en.wikipedia.org/wiki/Mandelbrot_set
    """

    ul_bound, lr_bound = bounds

    x0, y0 = ul_bound
    x1, y1 = lr_bound

    re_lo, re_hi = view[0] - 1 / zoom, view[0] + 1 / zoom
    im_lo, im_hi = view[1] - 1 / zoom, view[1] + 1 / zoom

    it_list = []

    for x in range(x0, x1, resolution):
        scaled_x = scale(re_lo, re_hi, x)
        for y in range(y0, y1, resolution):
            pixel = (x, y)

            scaled_y = scale(im_lo, im_hi, y)

            iters = get_iterations(scaled_x, scaled_y, MAX_ITERATIONS)

            it_list.append((pixel, iters))

    return it_list


def build_image(it_map: PixelDiverList) -> Image:
    """Build an Image object from list of pixels and their respective
    divergency points.
    """
    img = Image.new('RGB', (WIDTH, HEIGHT), 'white')

    for pixel, iters in it_map:
        img.putpixel(pixel, get_color(iters))

    return img


def generateMSImage(filepath: str) -> None:
    view: View = 0.0, 0.0
    zoom = 1/2

    arg_list = get_arg_list(view, zoom)

    with Pool(CHUNK_COUNT) as pl:
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


def draw_image(it_map: PixelDiverList, screen, resolution) -> None:

    for pixel, iters in it_map:
        point = pg.Rect(pixel, (resolution, resolution))
        pg.draw.rect(screen, color_dict[iters], point)


def interactive_session(color_dict: Dict[int, Tuple[int, int, int]]) -> None:
    # TODO: implenent gradial resolution rise

    screen = pg.display.set_mode((SIZE, SIZE))
    render = True
    view: View = 0.0, 0.0
    zoom = 1/2
    resolution = LOWEST_RESOLUTION

    while True:
        re_lo, re_hi = view[0] - 1 / zoom, view[0] + 1 / zoom
        im_lo, im_hi = view[1] - 1 / zoom, view[1] + 1 / zoom
        m_x, m_y = pg.mouse.get_pos()
        sc_x = scale(re_lo, re_hi, m_x)
        sc_y = scale(im_lo, im_hi, m_y)
        zoom_coeff = 2

        for event in pg.event.get():
            if event.type == pg.QUIT:
                exit(0)
            elif event.type == pg.MOUSEBUTTONDOWN:
                view = sc_x, sc_y
                if event.button == 1:  # left click
                    zoom *= zoom_coeff
                elif event.button == 3:  # right click
                    # FIXME: fix zero division
                    if zoom > 1:
                        zoom //= zoom_coeff
                render = True
                resolution = LOWEST_RESOLUTION

            elif event.type == pg.KEYUP:
                if event.key == ord('q'):
                    exit(0)
                elif event.key == ord('r'):
                    view = (0.0, 0.0)
                    zoom = 0.5
                    resolution = LOWEST_RESOLUTION
                    render = True

        os.system('clear||cls')  # cls for windows compat.

        print(sc_x, sc_y)

        if render:
            if resolution == 1:
                render = False

            arg_list = get_arg_list(view, zoom, resolution)

            with Pool(cpu_count()) as pl:
                it_maps = pl.starmap(build_mandelbrot_bounds, arg_list)

            it_map = list(chain.from_iterable(it_maps))  # might be too slow

            draw_image(it_map, screen, resolution)

            pg.display.flip()

            resolution //= 2


def get_args() -> Dict[str, str]:
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
    parser.add_argument('-r', '--lowest-resolution',
                        default=16)

    cpu_c = cpu_count()
    assert cpu_c is not None
    cpu_c *= 4

    parser.add_argument('-c', '--chunk-count',
                        help='How many ch. to work on concurrently. Def. 32',
                        default=cpu_c)

    parser.add_argument('filepath', nargs='?',
                        default='out.png',
                        help='Output filepath')

    args = vars(parser.parse_args())

    return args


if __name__ == "__main__":
    args = get_args()

    if args['interactive'] is None:
        if args['output'] is not None:
            output: str = args['output']
        else:
            output = args['filepath']

    if args['max_iterations'] is not None:
        MAX_ITERATIONS = int(args['max_iterations'])

    WIDTH = int(args['size'])
    HEIGHT = int(args['size'])
    SIZE = HEIGHT

    try:
        C_LIB = cp.cdll.LoadLibrary(getcwd() + '/lib/mandelb.so')
    except OSError:
        print("ERROR: Library file not found in lib/ directory.",
              file=sys.stderr)
        exit(1)

    CHUNK_COUNT = int(args['chunk_count'])

    LOWEST_RESOLUTION = int(args['lowest_resolution'])

    if args['benchmark'] is not None:
        cProfile.run(fr'generateMSImage("{output}")')
        remove(output)
        exit(0)

    if args['interactive'] is not None:
        color_dict = load_colors('colors.txt')
        interactive_session(color_dict)
    else:
        generateMSImage(output)
