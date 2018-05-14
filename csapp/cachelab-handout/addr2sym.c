#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>

/* 
 * util for cache lab, it translate address to symbol
 *     e.g. give address 0x602100(it is &A[0][0]), it output A[0][0]
 * 
 *     input:
 *              it takes `./csim-ref -s5 -E1 -b5 -t trace.fx -v` as input
 *     output:
 *              append address info for each line in csim-ref's output
 * 
 *     usage:
 *              ./csim-ref -s5 -E1 -b5 -t trace.fx -v > a_output_file
 *              ./addr2sym -M xx -N xx -F a_output_file
 *
 */

int main(int argc, char *argv[]) {
    int M, N, c;
    FILE *fd;
    const char *filename;

    char *line = NULL;
    size_t len;
    ssize_t readAmount;

    long addr;
    long baseAddrA = 0;
    long baseAddrB = 0;
    long baseAddr  = 0;
    long maxValidAddr = 0;
    char sym;

    long setIndexMask = 0x3e0;
    long setIndex;

    int row, column;

    int i;

    while ((c = getopt(argc, argv, "M:N:F:")) != -1) {
        switch (c) {
            case 'M':
                M = atoi(optarg);
                break;
            case 'N':
                N = atoi(optarg);
                break;
            case 'F':
                filename = optarg;
                break;
            default:
                fputs("invalid command line option\n", stderr);
                exit(0);
        }
    }

    if (M == 32) {
        baseAddrA = 0x602100;
        baseAddrB = 0x642100;
        maxValidAddr = 0x682100;
    } else if (M == 64) {
        baseAddrA = 0x603100;
        baseAddrB = 0x643100;
        maxValidAddr = 0x683100;
        /* TODO: <2018-05-14, forest9643, why addr is not stable?> */
        /* baseAddrA = 0x602100; */
        /* baseAddrB = 0x642100; */
        /* maxValidAddr = 0x682100; */
    }

    fd = fopen(filename, "r");
    if (!fd) {
        fputs("invalid command line option\n", stderr);
        exit(-1);
    }

    printf("M=%d, N=%d\n", M, N);

    while ((readAmount = getline(&line, &len, fd)) != -1) {
        addr = strtol(line+2, NULL, 16);

        if (addr >= maxValidAddr || addr < 0) { // ignore non-interesting things
            continue;
        }

        
        setIndex = (addr & setIndexMask) >> 5;

        if (line[readAmount-1] == '\n') {
            line[readAmount-1] = '\0';
        }

        printf("%s", line);
        for (i = 0; i < (int)(29-readAmount); ++i) { // align output
            putc(' ', stdout);
        }

        if (addr >= baseAddrB) { // array B
            baseAddr = baseAddrB;
            sym = 'B';
        } else {
            baseAddr = baseAddrA;
            sym = 'A';
        }

        row = (addr - baseAddr) / (M*sizeof(int));
        column = (addr - baseAddr - row*M*sizeof(int)) / sizeof(int);

        printf("%c[%d][%d] setIndex: %ld\n",
                sym, row, column, setIndex);
    }


    if (line) {
        free(line);
    }
    return 0;
}
