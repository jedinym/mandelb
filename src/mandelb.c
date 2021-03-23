#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <complex.h>
#include "mandelb.h"


double scale(int num, int size)
{
    //printf("%d\n", num);
    return ((num - (size / 2)) / ((double) size / 4));
}


int c_get_iterations(long double scaled_x, long double scaled_y, int max_iters)
{
    int iters = 0;

    long double complex c = scaled_x + scaled_y * I;
    long double complex z = 0.0 + 0.0 * I;
    
    //try no square root after
    while ((creal(csqrt(z * z)) <= 2) && (iters < max_iters))
    { 
        z = (z * z) + c;
        ++iters;
    }

    return iters;
}