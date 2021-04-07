#!/usr/bin/python3

from typing import Any, Dict
import cProfile
import argparse as ap
from os import remove, cpu_count
import mandelb_gen as mbg


def get_args() -> Dict[str, Any]:
    parser = ap.ArgumentParser()
    parser.add_argument('-s,', '--size', required=True,
                        type=int,
                        help='Size of the resulting image')
    parser.add_argument('-o', '--output', required=False,
                        type=str,
                        help='Output filepath')
    parser.add_argument('-b', '--benchmark', action='store_const',
                        const='benchmark',
                        help='cProfile output to stdin')
    parser.add_argument('-m', '--max-iterations',
                        type=int,
                        default=1000,
                        help='Maximum mandelb. set iterations')
    parser.add_argument('-i', '--interactive', action='store_const',
                        const='interactive')
    parser.add_argument('-r', '--lowest-resolution',
                        type=int,
                        default=16)

    cpu_c = cpu_count()
    assert cpu_c is not None
    cpu_c *= 4

    parser.add_argument('-c', '--chunk-count',
                        help='How many ch. to work on concurrently. Def. 32',
                        type=int,
                        default=cpu_c)

    parser.add_argument('filepath', nargs='?',
                        default='out.png',
                        type=str,
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

    max_iterations: int = args['max_iterations']
    size: int = args['size']
    chunk_count: int = args['chunk_count']
    lowest_resolution: int = args['lowest_resolution']

    mb_gen = mbg.MandelbrotGenerator(size, max_iterations, lowest_resolution,
                                     chunk_count)

    if args['benchmark'] is not None:
        cProfile.run(fr'mb_gen.generateMSImage("{output}")')
        remove(output)
        exit(0)

    if args['interactive'] is not None:
        mb_gen.interactive_session()
    else:
        mb_gen.generate_ms_image(output)
