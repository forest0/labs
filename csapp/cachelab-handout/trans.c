/* 
 * trans.c - Matrix transpose B = A^T
 *
 * Each transpose function must have a prototype of the form:
 * void trans(int M, int N, int A[N][M], int B[M][N]);
 *
 * A transpose function is evaluated by counting the number of misses
 * on a 1KB direct mapped cache with a block size of 32 bytes.
 */ 
#include <stdio.h>
#include "cachelab.h"

int is_transpose(int M, int N, int A[N][M], int B[M][N]);
void trans_block(int M, int N, int A[N][M], int B[M][N], int bsize);

/* 
 * transpose_submit - This is the solution transpose function that you
 *     will be graded on for Part B of the assignment. Do not change
 *     the description string "Transpose submission", as the driver
 *     searches for that string to identify the transpose function to
 *     be graded. 
 */
char transpose_submit_desc[] = "Transpose submission";
void transpose_submit(int M, int N, int A[N][M], int B[M][N])
{
    int i, j, k, l;
    int a0, a1, a2, a3, a4, a5, a6, a7;

    if (M == 32 && N == 32) { // {{{
        for (i = 0; i < M; i += 8) {
            for (j  = 0; j < N; j += 8) {
                for (k = i; k < i + 8; ++k) {
                    /* for (n = j; n < j + 8; ++n) { */
                    /*     B[n][k] = A[m][n]; */
                    /* } */
                    a0 = A[k][j];
                    a1 = A[k][j+1];
                    a2 = A[k][j+2];
                    a3 = A[k][j+3];
                    a4 = A[k][j+4];
                    a5 = A[k][j+5];
                    a6 = A[k][j+6];
                    a7 = A[k][j+7];
                    
                    B[j][k] = a0;
                    B[j+1][k] = a1;
                    B[j+2][k] = a2;
                    B[j+3][k] = a3;
                    B[j+4][k] = a4;
                    B[j+5][k] = a5;
                    B[j+6][k] = a6;
                    B[j+7][k] = a7;
                }
            }
        }
// }}}
    } else if (M == 64 && N == 64) { // {{{
        // NOTE: details can be found at lab_record.md
        for (i = 0; i < M; i += 8) {
            for (j  = 0; j < N; j += 8) {
                for (k = i; k < i+4; ++k) {
                    // read 8 int pointed by k1
                    a0 = A[k][j];
                    a1 = A[k][j+1];
                    a2 = A[k][j+2];
                    a3 = A[k][j+3];
                    a4 = A[k][j+4];
                    a5 = A[k][j+5];
                    a6 = A[k][j+6];
                    a7 = A[k][j+7];

                    // store to k2
                    B[j][k]   = a0;
                    B[j+1][k] = a1;
                    B[j+2][k] = a2;
                    B[j+3][k] = a3;
                    
                    // store to k3
                    B[j][k+4]   = a4;
                    B[j+1][k+4] = a5;
                    B[j+2][k+4] = a6;
                    B[j+3][k+4] = a7;

                }

                for (l = j+4; l < j+8; ++l) {
                    // store value pointed by p1
                    a4 = A[i+4][l-4];
                    a5 = A[i+5][l-4];
                    a6 = A[i+6][l-4];
                    a7 = A[i+7][l-4];

                    // store value pointed by p2
                    a0 = B[l-4][i+4];
                    a1 = B[l-4][i+5];
                    a2 = B[l-4][i+6];
                    a3 = B[l-4][i+7];

                    // store to p2
                    B[l-4][i+4] = a4;
                    B[l-4][i+5] = a5;
                    B[l-4][i+6] = a6;
                    B[l-4][i+7] = a7;

                    // store to p3
                    B[l][i]   = a0;
                    B[l][i+1] = a1;
                    B[l][i+2] = a2;
                    B[l][i+3] = a3;

                    // p4 to p5
                    B[l][i+4] = A[i+4][l];
                    B[l][i+5] = A[i+5][l];
                    B[l][i+6] = A[i+6][l];
                    B[l][i+7] = A[i+7][l];
                }
            }
        }
// }}}
    } else if (M == 61 && N == 67){ // {{{
        /* trans_block(M, N, A, B, 23); */
        for (i = 0; i < N; i += 23) {
            for (j  = 0; j < M; j += 23) {
                for (k = i; k < i + 23 && k < N; ++k) {
                    for (l = j; l < j + 23 && l < M; ++l) {
                        B[l][k] = A[k][l];
                    }
                }
            }
        }
    } else {
        fprintf(stderr, "invalid M=%d, N=%d\n", M, N);
    } // }}}
}

/* 
 * You can define additional transpose functions below. We've defined
 * a simple one below to help you get started. 
 */ 

/* 
 * trans - A simple baseline transpose function, not optimized for the cache.
 */
char trans_desc[] = "Simple row-wise scan transpose";
void trans(int M, int N, int A[N][M], int B[M][N])
{
    int i, j;

    for (i = 0; i < N; i++) {
        for (j = 0; j < M; j++) {
            B[j][i] = A[i][j];
        }
    }    

}

/*
 * registerFunctions - This function registers your transpose
 *     functions with the driver.  At runtime, the driver will
 *     evaluate each of the registered functions and summarize their
 *     performance. This is a handy way to experiment with different
 *     transpose strategies.
 */
void registerFunctions()
{
    /* Register your solution function */
    registerTransFunction(transpose_submit, transpose_submit_desc); 

    /* Register any additional transpose functions */
    /* registerTransFunction(trans, trans_desc);  */

}

/* 
 * is_transpose - This helper function checks if B is the transpose of
 *     A. You can check the correctness of your transpose by calling
 *     it before returning from the transpose function.
 */
int is_transpose(int M, int N, int A[N][M], int B[M][N])
{
    int i, j;

    for (i = 0; i < N; i++) {
        for (j = 0; j < M; ++j) {
            if (A[i][j] != B[j][i]) {
                return 0;
            }
        }
    }
    return 1;
}

void trans_block(int M, int N, int A[N][M], int B[M][N], int bsize) {
    int i, j, k, l;
    for (i = 0; i < N; i += bsize) {
        for (j  = 0; j < M; j += bsize) {
            for (k = i; k < i + bsize && k < N; ++k) {
                for (l = j; l < j + bsize && l < M; ++l) {
                    B[l][k] = A[k][l];
                }
            }
        }
    }
}
