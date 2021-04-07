from typing import Tuple, List, Dict
from PIL import Image
from multiprocessing import Pool
import ctypes as cp
from os import getcwd, cpu_count
import os
# from os import environ
# environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
from itertools import chain


Pixel = Tuple[int, int]
PixelDiverList = List[Tuple[Pixel, int]]
Bound = Tuple[Pixel, Pixel]
View = Tuple[float, float]


class MandelbrotGenerator:
    def __init__(self, size: int, max_iterations: int,
                 lowest_res: int, chunk_count: int):
        self.size = size
        self.max_iterations = max_iterations
        self.lowest_resolution = lowest_res
        self.chunk_count = chunk_count
        self.bound_list = self.get_bound_list()
        self.color_dict = self.load_colors('colors.txt')

    def interactive_session(self) -> None:
        screen = pg.display.set_mode((self.size, self.size))
        render = True
        view: View = 0.0, 0.0
        zoom = 1 / 2
        resolution = self.lowest_resolution

        while True:
            re_lo, re_hi = view[0] - 1 / zoom, view[0] + 1 / zoom
            im_lo, im_hi = view[1] - 1 / zoom, view[1] + 1 / zoom
            m_x, m_y = pg.mouse.get_pos()
            sc_x = self.scale(re_lo, re_hi, m_x)
            sc_y = self.scale(im_lo, im_hi, m_y)
            zoom_coeff = 2

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    exit(0)
                elif event.type == pg.MOUSEBUTTONDOWN:
                    view = sc_x, sc_y
                    if event.button == 1:  # left click
                        zoom *= zoom_coeff
                    elif event.button == 3:  # right click
                        if zoom > 1:
                            zoom //= zoom_coeff
                    render = True
                    resolution = self.lowest_resolution

                elif event.type == pg.KEYUP:
                    if event.key == ord('q'):
                        exit(0)
                    elif event.key == ord('r'):
                        view = (0.0, 0.0)
                        zoom = 0.5
                        resolution = self.lowest_resolution
                        render = True

            os.system('clear||cls')  # cls for windows compat.

            print(sc_x, sc_y)

            if render:
                if resolution == 1:
                    render = False

                arg_list = self.get_arg_list(view, zoom, resolution)

                with Pool(cpu_count()) as pl:
                    it_maps = pl.starmap(self.build_mandelbrot_bounds, arg_list)

                it_map = list(chain.from_iterable(it_maps))  # might be too slow

                self.draw_image(it_map, screen, resolution)

                pg.display.flip()

                resolution //= 2

    def get_bound_list(self) -> List[Bound]:
        """Divide the screen/view into <self.chunk_count> chunks for faster processing.

        Return a list of bounds -> (<topleft_pixel>, <bottomright_pixel>)
        """
        x_step = self.size // self.chunk_count
        rest = self.size % self.chunk_count

        x_pos = 0

        bound_list: List[Bound] = []

        for x in range(self.chunk_count):
            x_step_end = x_pos + x_step

            if x == self.chunk_count - 1:
                x_step_end += rest

            bound_list.append(((x_pos, 0), (x_step_end, self.size)))
            x_pos += x_step

        return bound_list

    def get_arg_list(self, view: View, zoom: float, resolution: int) \
            -> List[Tuple[Bound, View, float, int]]:
        """Pack arguments into a list of tuples to pass to build_mandelbrot_bounds()
        """
        arg_list = []

        for bound in self.bound_list:
            arg_list.append((bound, view, zoom, resolution))

        return arg_list

    def get_color(self, its: int) -> Tuple[int, int, int]:
        cols = [(0, 0, 102), (0, 0, 153), (0, 0, 204), (0, 0, 255)]

        if its == self.max_iterations:
            return 0, 0, 0

        if its < 3:
            return cols[0]
        elif its < 7:
            return cols[1]
        elif its < 15:
            return cols[2]

        return cols[3]

    def scale(self, start: float, end: float, position: int) -> float:
        """Scale pixel coord to real/imaginary part of a complex number
        """
        coeff = abs(end - start) / self.size

        return start + position * coeff

    def get_iterations(self, c_lib: cp.cdll, scaled_x: float, scaled_y: float) -> int:
        c_get_its = c_lib.c_get_iterations
        c_get_its.restype = cp.c_int

        iters = c_get_its(cp.c_longdouble(scaled_x),
                          cp.c_longdouble(scaled_y),
                          cp.c_int(self.max_iterations))

        return iters

    def build_mandelbrot_bounds(self, bounds: Tuple[Pixel, Pixel],
                                view: Tuple[float, float],
                                zoom: int,
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

        c_lib = cp.cdll.LoadLibrary(getcwd() + '/lib/mandelb.so')  # TODO: rethink this

        for x in range(x0, x1, resolution):
            scaled_x = self.scale(re_lo, re_hi, x)
            for y in range(y0, y1, resolution):
                pixel = (x, y)

                scaled_y = self.scale(im_lo, im_hi, y)

                iters = self.get_iterations(c_lib, scaled_x, scaled_y)

                it_list.append((pixel, iters))

        return it_list

    def build_image(self, it_map: PixelDiverList) -> Image:
        """Build an Image object from list of pixels and their respective
        divergency points.
        """
        img = Image.new('RGB', (self.size, self.size), 'white')

        for pixel, iters in it_map:
            img.putpixel(pixel, self.get_color(iters))

        return img

    def generate_ms_image(self, filepath: str) -> None:
        view: View = 0.0, 0.0
        zoom = 1 / 2

        arg_list = self.get_arg_list(view, zoom, 1)

        with Pool(self.chunk_count) as pl:
            it_maps = pl.starmap(self.build_mandelbrot_bounds, arg_list)

        im = list(chain.from_iterable(it_maps))  # might be too slow

        img = self.build_image(im)

        img.save(filepath)

    def load_colors(self, filepath: str) -> Dict[int, Tuple[int, int, int]]:
        color_dict = dict()
        with open(filepath, 'r') as file:
            for line in file.readlines():
                line_split = line.split(',')
                color_dict[int(line_split[0])] = (int(line_split[1]),
                                                  int(line_split[2]),
                                                  int(line_split[3].rstrip()))

        color_dict[self.max_iterations] = (0, 0, 0)
        return color_dict

    def draw_image(self, it_map: PixelDiverList, screen, resolution) -> None:

        for pixel, iters in it_map:
            point = pg.Rect(pixel, (resolution, resolution))
            pg.draw.rect(screen, self.color_dict[iters], point)

