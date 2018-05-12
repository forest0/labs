#define _GNU_SOURCE // to use getline
#include "cachelab.h"
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>

#define KEY_TYPE int64_t

// struct definitions {{{
struct CmdOpts {
    bool help;
    bool verbose;
    int s;                  // Number of set index bits
    int E;                  // Number of lines per set
    int b;                  // Number of block offset bits
    const char *traceFile;
};

struct StatisticInfo {
    int hitCnt;
    int missCnt;
    int evictionCnt;
};

struct CacheLine {
    bool isValid;
    int timeStamp;
    KEY_TYPE tag;
    KEY_TYPE key;
    // type value;
};

struct CacheGroup {
    struct CacheLine *lines;
};

/* address is defined as KEY_TYPE, here int64_t is used
 *        tag               set index              block offset
 * +----------------+-----------------------+---------------------+
 * |       t        |          s            |          b          |
 * +----------------+-----------------------+---------------------+
 */
struct Cache {
    int t;                      // tag length
    int s;                      // set index length
    int b;                      // block offset length
    int E;                      // line amount in each set
    struct CacheGroup *groups;
};

// }}}

// function declarations {{{
void printUsage();
int parseCmdOpt(int argc, char **argv, struct CmdOpts *cmdOpts);
int getTimeStamp();
void verbosePuts(const char *s, bool verbose);

/* too much args here
 *      seems that setIndex and tag can be produced by cache and addr,
 *      but this will cause memoryAcessHandler calculate mask every time
 */
void memoryAcessHandler(struct Cache *cache, KEY_TYPE addr,
                        KEY_TYPE setIndex, KEY_TYPE tag,
                        struct StatisticInfo *statisticInfo,
                        bool verbose);


struct Cache * newCache(int s, int E, int t);

bool setCache(struct Cache *cache, KEY_TYPE key,
        KEY_TYPE setIndex, KEY_TYPE tag);
/* void setCache(struct Cache *cache, KEY_TYPE key, type value); */

bool getCache(struct Cache *cache,// KEY_TYPE key,
        KEY_TYPE setIndex, KEY_TYPE tag);
/* type getCache(struct Cache *cache, KEY_TYPE key); */

void deleteCache(struct Cache *cache);


void simulate(struct Cache *cache, FILE *in, bool verbose);

// }}}

int main(int argc, char **argv) { // {{{
    struct CmdOpts cmdOpts;
    FILE *fd;

    if ((parseCmdOpt(argc, argv, &cmdOpts) != 0) || cmdOpts.help) {
        printUsage();
        exit(0);
    }

    fd = fopen(cmdOpts.traceFile, "r");
    if (!fd) {
        fputs("failed to open trace file", stderr);
        exit(-1);
    }

    struct Cache *cache = newCache(cmdOpts.s, cmdOpts.E, cmdOpts.b);

    simulate(cache, fd, cmdOpts.verbose);

    deleteCache(cache);
    return 0;
} // }}}

/* print usage information */
void printUsage() { // {{{
    puts("Usage: ./csim [-hv] -s <num> -E <num> -b <num> -t <file>\n"
         "Options:\n"
         "  -h         Print this help message.\n"
         "  -v         Optional verbose flag.\n"
         "  -s <num>   Number of set index bits.\n"
         "  -E <num>   Number of lines per set.\n"
         "  -b <num>   Number of block offset bits.\n"
         "  -t <file>  Trace file.\n"
         "\n"
         "Examples:\n"
         "  linux>  ./csim -s 4 -E 1 -b 4 -t traces/yi.trace\n"
         "  linux>  ./csim -v -s 8 -E 2 -b 4 -t traces/yi.trace"
         );
} // }}}

/* parse command line options, store it to cmdOpts */
int parseCmdOpt(int argc, char **argv, struct CmdOpts *cmdOpts) { // {{{
    int c;
    int cnt = 0;

    if ((argc < 2) || !argv || !cmdOpts) {
        return -1;
    }

    memset(cmdOpts, 0, sizeof(struct CmdOpts));

    while ((c = getopt(argc, argv, "hvs:E:b:t:")) != -1) {
        switch (c) {
            case 'h':
                cmdOpts->help = 1;
                break;
            case 'v':
                cmdOpts->verbose = 1;
                break;
            case 's':
                cmdOpts->s = atoi(optarg);
                cnt += 1;
                break;
            case 'E':
                cmdOpts->E = atoi(optarg);
                cnt += 1;
                break;
            case 'b':
                cmdOpts->b = atoi(optarg);
                cnt += 1;
                break;
            case 't':
                cmdOpts->traceFile = optarg;
                cnt += 1;
                break;
            default:
                return -1;
        }
    }

    if (cnt < 4) {
        fprintf(stderr, "%s: Missing required command line argument\n", argv[0]);
        return -1;
    }

    return 0;
} // }}}

/* get a timestamp */
int getTimeStamp() { // {{{
    static int timeStamp = 0;
    return ++timeStamp;
} // }}}

void verbosePuts(const char *s, bool verbose) { // {{{
    if (verbose) {
        printf("%s", s);
    }
} // }}}


void memoryAcessHandler(struct Cache *cache, KEY_TYPE addr,
        KEY_TYPE setIndex, KEY_TYPE tag,
        struct StatisticInfo *statisticInfo,
        bool verbose) { // {{{

    bool isCached;
    bool evictionSelected;

    /* isCached = getCache(cache, addr, setIndex, tag); */
    isCached = getCache(cache, setIndex, tag);
    if (!isCached) {
        verbosePuts(" miss", verbose);
        ++(statisticInfo->missCnt);
        evictionSelected = setCache(cache, addr, setIndex, tag);
        if (evictionSelected) {
            ++(statisticInfo->evictionCnt);
            verbosePuts(" eviction", verbose);
        }
    } else {
        ++(statisticInfo->hitCnt);
        verbosePuts(" hit", verbose);
    }
} // }}}

/* create a new cache object */
struct Cache * newCache(int s, int E, int b) { // {{{
    struct Cache *cache = NULL;
    int setAmount;
    int i;
    if (s <= 0 || E <= 0 || b <= 0) {
        return cache;
    }

    cache = (struct Cache *)malloc(sizeof(struct Cache));
    if (!cache) {
        fputs("failed to new Cache\n", stderr);
        exit(-1);
    }

    cache->s = s;
    cache->b = b;
    cache->E = E;

    /* NOTE: here may cause a bug */
    cache->t = sizeof(KEY_TYPE)*8 - s - b;

    setAmount = 1 << s;
    cache->groups = (struct CacheGroup *)
                        malloc(setAmount * sizeof(struct CacheGroup));
    if (!cache->groups) {
        fputs("failed to new CacheGroup\n", stderr);
        // free cache;
        exit(-1);
    }
    memset(cache->groups, 0, sizeof(setAmount * sizeof(struct CacheGroup)));

    for (i = 0; i < setAmount; ++i) {
        cache->groups[i].lines = (struct CacheLine *)
                        malloc(E * sizeof(struct CacheLine));
        if (!(cache->groups[i].lines)) {
            // free all previous things, fuck
            fputs("failed to new CacheLine\n", stderr);
            exit(-1);
        }

        /* for (j = 0; j < E; ++j) { */
        /*     memset(&(cache->groups[i].lines[j]), 0, sizeof(struct CacheLine)); */
        /* } */
        memset(cache->groups[i].lines, 0, sizeof(E*sizeof(struct CacheLine)));
    }

    return cache;
} // }}}

/* add a new item to cache, select a eviction if cache already full
 *      return true if a eviction is selected
 *      return false otherwise
 */
bool setCache(struct Cache *cache, KEY_TYPE key,
        KEY_TYPE setIndex, KEY_TYPE tag) { // {{{
    int i;
    int oldestTimeStamp = 2147483647;   // some big value here
    int oldestLineIdx;
    /* int setIndex = key & setIndexMask; */
    /* int tag = key & tagMask; */

    if (!cache) {
        return false;
    }

    for (i = 0; i < cache->E; ++i) {
        if (!(cache->groups[setIndex].lines[i].isValid)) { // empty line
            cache->groups[setIndex].lines[i].isValid = true;
            cache->groups[setIndex].lines[i].key = key;
            cache->groups[setIndex].lines[i].tag = tag;
            cache->groups[setIndex].lines[i].timeStamp = getTimeStamp();

            return false;
        } else {
            
            if (cache->groups[setIndex].lines[i].timeStamp < oldestTimeStamp) {
                oldestTimeStamp = cache->groups[setIndex].lines[i].timeStamp;
                oldestLineIdx = i;
            }
        }
    }
    cache->groups[setIndex].lines[oldestLineIdx].key = key;
    cache->groups[setIndex].lines[oldestLineIdx].tag = tag;
    cache->groups[setIndex].lines[oldestLineIdx].timeStamp = getTimeStamp();
    return true;
} // }}}

/* read value from cache
 *     return true if cache has this key
 *     return false otherwise
 */
bool getCache(struct Cache *cache,// KEY_TYPE key,
            KEY_TYPE setIndex, KEY_TYPE tag) { // {{{
    int i;
    /* int setIndex = key & setIndexMask; */
    /* int tag = key & tagMask; */

    if (!cache) {
        return false;
    }

    for (i = 0; i < cache->E; ++i) {
        if ((cache->groups[setIndex].lines[i].isValid) &&
                (cache->groups[setIndex].lines[i].tag == tag)) {
            cache->groups[setIndex].lines[i].timeStamp = getTimeStamp();
            return true;
        }
    }

    return false;
} // }}}

/* free a cache object */
void deleteCache(struct Cache *cache) { // {{{
    int i;

    if (!cache) {
        return;
    }

    int setAmount = 1 << cache->s;

    for (i = 0; i < setAmount; ++i) {
        free(cache->groups[i].lines);
    }

    free(cache->groups);
    free(cache);

    cache = NULL;
} // }}}

/* simulate a cache running */
void simulate(struct Cache *cache, FILE *in, bool verbose) { // {{{
    char *line = NULL;
    size_t len;
    ssize_t readCharAmount;
    char c;
    KEY_TYPE addr;

    struct StatisticInfo statisticInfo = {0, 0, 0};

    KEY_TYPE setIndex;
    KEY_TYPE setIndexMask = ((((KEY_TYPE)1 << (8*sizeof(KEY_TYPE)-1)) >> (cache->s))
        & (~((KEY_TYPE)1 << (8*sizeof(KEY_TYPE)-1)))) >> (cache->t-1);
    KEY_TYPE tag;
    KEY_TYPE tagMask = ((KEY_TYPE)1 << (8*sizeof(KEY_TYPE)-1)) >> (cache->t-1);

    if (!cache || !in) {
        return;
    }

    while ((readCharAmount = getline(&line, &len, in)) != -1) {


        addr = strtol(line+3, NULL, 16);
        c = line[1];

        if (c == 'I') { // ignore I
            continue;
        }

        setIndex = (setIndexMask & addr) >> cache->b;
        tag = (tagMask & addr) >> (cache->s+cache->b);

        if (verbose) {
            if (line[readCharAmount-1] == '\n') {
                line[readCharAmount-1] = '\0';
            }
        }
        verbosePuts(line+1, verbose); // +1 to skip the leading space

        switch (c) {
            case 'M':
            case 'L':
                memoryAcessHandler(cache, addr, setIndex, tag,
                        &statisticInfo, verbose);

                if (c == 'L') { // M = L + S
                    break;
                }
            case 'S':
                memoryAcessHandler(cache, addr, setIndex, tag,
                        &statisticInfo, verbose);
                break;
            default:
                break;
        }

        verbosePuts("\n", verbose);
    }

    if (line) {
        free(line);
    }

    printSummary(statisticInfo.hitCnt,
                 statisticInfo.missCnt,
                 statisticInfo.evictionCnt);
} // }}}
