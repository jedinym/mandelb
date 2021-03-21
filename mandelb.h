const int MAX_ITERATIONS = 1000;

typedef struct Pixel
{
    int x;
    int y;
}Pixel;

typedef struct PixelIterations 
{
    Pixel *pix;
    int iterations;
}PixelIterations;

typedef struct Complex
{
    double real;
    double imag;
}Complex;

int get_iterations(int x, int y, int width, int height, int max_iters);

PixelIterations* build_mb_bounds(Pixel *ul_bound, Pixel *lr_bound);
double scale(int num, int size);
