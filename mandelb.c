#include "mandelb.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <complex.h>

int main(void)
{
    //printf("%d", get_iterations(1000, 1000, 2000, 2000, 1000));
    return 0;
}

double scale(int num, int size)
{
    //printf("%d\n", num);
    return ((num - (size / 2)) / ((double) size / 4));
}


int c_get_iterations(int x, int y, int width, int height, int max_iters)
{
    int iters = 0;

    double scaledX = scale(x, width);
    double scaledY = scale(y, height);

    double complex c = scaledX + scaledY * I;
    double complex z = 0.0 + 0.0 * I;

    
    //printf("%lf + %lf *i\n", creal(c), cimag(c));

    while ((creal(csqrt(z * z)) <= 2) && (iters < max_iters))
    { 
        z = (z * z) + c;
        //printf("%lf + %lf *i\n", creal(z), cimag(z));
        ++iters;
    }

    return iters;
}


// PixelIterations* build_mb_bounds(Pixel *ul_bound, Pixel *lr_bound)
// {
//     //printf("%d", (ul_bound -> x));

//     ssize_t size = ((lr_bound -> x) - (ul_bound -> x)) *
//     ((lr_bound -> y) - (ul_bound -> y));

//     PixelIterations **p_it_array = malloc(size * sizeof(**p_it_array));

//     int index = 0;

//     for (int x = (ul_bound -> x); x < (lr_bound -> x); ++x)
//     {
//         for (int y = (ul_bound -> y); y < (lr_bound -> y); ++y)
//         {
//             Pixel *pix = malloc(sizeof(*pix));
//             pix -> x = x;
//             pix -> y = y;

//             PixelIterations *p_it = malloc(sizeof(*p_it));
//             p_it -> pix = pix;
//             p_it -> iterations = get_iterations(pix);

//             p_it_array[index] = p_it;
//         }
//     }

//     return NULL;
// }