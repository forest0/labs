/* 
 * CS:APP Data Lab 
 * 
 * <Please put your name and userid here>
 * 
 * bits.c - Source file with your solutions to the Lab.
 *          This is the file you will hand in to your instructor.
 *
 * WARNING: Do not include the <stdio.h> header; it confuses the dlc
 * compiler. You can still use printf for debugging without including
 * <stdio.h>, although you might get a compiler warning. In general,
 * it's not good practice to ignore compiler warnings, but in this
 * case it's OK.  
 */

#if 0
/*
 * Instructions to Students: {{{
 *
 * STEP 1: Read the following instructions carefully.
 */

You will provide your solution to the Data Lab by
editing the collection of functions in this source file.

INTEGER CODING RULES: {{{
 
  Replace the "return" statement in each function with one
  or more lines of C code that implements the function. Your code 
  must conform to the following style:
 
  int Funct(arg1, arg2, ...) {
      /* brief description of how your implementation works */
      int var1 = Expr1;
      ...
      int varM = ExprM;

      varJ = ExprJ;
      ...
      varN = ExprN;
      return ExprR;
  }

  Each "Expr" is an expression using ONLY the following:
  1. Integer constants 0 through 255 (0xFF), inclusive. You are
      not allowed to use big constants such as 0xffffffff.
  2. Function arguments and local variables (no global variables).
  3. Unary integer operations ! ~
  4. Binary integer operations & ^ | + << >>
    
  Some of the problems restrict the set of allowed operators even further.
  Each "Expr" may consist of multiple operators. You are not restricted to
  one operator per line.

  You are expressly forbidden to:
  1. Use any control constructs such as if, do, while, for, switch, etc.
  2. Define or use any macros.
  3. Define any additional functions in this file.
  4. Call any functions.
  5. Use any other operations, such as &&, ||, -, or ?:
  6. Use any form of casting.
  7. Use any data type other than int.  This implies that you
     cannot use arrays, structs, or unions.

 
  You may assume that your machine:
  1. Uses 2s complement, 32-bit representations of integers.
  2. Performs right shifts arithmetically.
  3. Has unpredictable behavior when shifting an integer by more
     than the word size.

EXAMPLES OF ACCEPTABLE CODING STYLE:
  /*
   * pow2plus1 - returns 2^x + 1, where 0 <= x <= 31
   */
  int pow2plus1(int x) {
     /* exploit ability of shifts to compute powers of 2 */
     return (1 << x) + 1;
  }

  /*
   * pow2plus4 - returns 2^x + 4, where 0 <= x <= 31
   */
  int pow2plus4(int x) {
     /* exploit ability of shifts to compute powers of 2 */
     int result = (1 << x);
     result += 4;
     return result;
  }

}}}

FLOATING POINT CODING RULES {{{

For the problems that require you to implent floating-point operations,
the coding rules are less strict.  You are allowed to use looping and
conditional control.  You are allowed to use both ints and unsigneds.
You can use arbitrary integer and unsigned constants.

You are expressly forbidden to:
  1. Define or use any macros.
  2. Define any additional functions in this file.
  3. Call any functions.
  4. Use any form of casting.
  5. Use any data type other than int or unsigned.  This means that you
     cannot use arrays, structs, or unions.
  6. Use any floating point data types, operations, or constants.


NOTES:
  1. Use the dlc (data lab checker) compiler (described in the handout) to 
     check the legality of your solutions.
  2. Each function has a maximum number of operators (! ~ & ^ | + << >>)
     that you are allowed to use for your implementation of the function. 
     The max operator count is checked by dlc. Note that '=' is not 
     counted; you may use as many of these as you want without penalty.
  3. Use the btest test harness to check your functions for correctness.
  4. Use the BDD checker to formally verify your functions
  5. The maximum number of ops for each function is given in the
     header comment for each function. If there are any inconsistencies 
     between the maximum ops in the writeup and in this file, consider
     this file the authoritative source.

}}}

/*
 * STEP 2: Modify the following functions according the coding rules.
 * 
 *   IMPORTANT. TO AVOID GRADING SURPRISES:
 *   1. Use the dlc compiler to check that your solutions conform
 *      to the coding rules.
 *   2. Use the BDD checker to formally verify that your solutions produce 
 *      the correct answers.
 */

/* }}} */


#endif
/* 
 * bitAnd - x&y using only ~ and | 
 *   Example: bitAnd(6, 5) = 4
 *   Legal ops: ~ |
 *   Max ops: 8
 *   Rating: 1
 */
int bitAnd(int x, int y) {
    /* DeMorgan's Law */
    return ~(~x | ~y);
}
/* 
 * getByte - Extract byte n from word x
 *   Bytes numbered from 0 (LSB) to 3 (MSB)
 *   Examples: getByte(0x12345678,1) = 0x56
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 6
 *   Rating: 2
 */
int getByte(int x, int n) {
    /* one byte is 8 bits */
    return 0xff & (x >> (n << 3));
}
/* 
 * logicalShift - shift x to the right by n, using a logical shift
 *   Can assume that 0 <= n <= 31
 *   Examples: logicalShift(0x87654321,4) = 0x08765432
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 20
 *   Rating: 3 
 */
int logicalShift(int x, int n) {
    /* logical right shift always fill 0 on the MSB */

    /* set most significant n bits to 0 */
    int mask = ~(((0x1 << 31) >> n) << 1);
    return (x >> n) & mask;

    /* return (x >> n) & ~(((0x1 << 31) >> n) << 1); */
}
/*
 * bitCount - returns count of number of 1's in word
 *   Examples: bitCount(5) = 2, bitCount(7) = 3
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 40
 *   Rating: 4
 */
int bitCount(int x) {
    /* divide and conquer
     * reference: 
     *      https://stackoverflow.com/questions/3815165/how-to-implement-bitcount-using-only-bitwise-operators
     *      https://stackoverflow.com/questions/109023/how-to-count-the-number-of-set-bits-in-a-32-bit-integer/15979139#15979139
     *      http://www.dalkescientific.com/writings/diary/archive/2008/07/03/hakmem_and_other_popcounts.html
     */

/*     a little more readable version, which will let dlc complain
 * 
 *     c = (v & 0x55555555) + ((v >> 1) & 0x55555555);
 *     c = (c & 0x33333333) + ((c >> 2) & 0x33333333);
 *     c = (c & 0x0F0F0F0F) + ((c >> 4) & 0x0F0F0F0F);
 *     c = (c & 0x00FF00FF) + ((c >> 8) & 0x00FF00FF);
 *     c = (c & 0x0000FFFF) + ((c >> 16)& 0x0000FFFF);
 */
    int count; 
    int tmpMask1 = (0x55) | (0x55<<8); 
    int mask1 = (tmpMask1) | (tmpMask1<<16); 
    int tmpMask2 = (0x33) | (0x33<<8); 
    int mask2 = (tmpMask2) | (tmpMask2<<16); 
    int tmpMask3 = (0x0f) | (0x0f<<8); 
    int mask3 = (tmpMask3) | (tmpMask3<<16); 
    int mask4 = (0xff) | (0xff<<16); 
    int mask5 = (0xff) | (0xff<<8); 
    count = (x & mask1) + ((x >> 1) & mask1); 
    count = (count&mask2) + ((count>>2)&mask2); 
    count = (count + (count >> 4)) & mask3; 
    count = (count + (count >> 8)) & mask4; 
    count = (count + (count >> 16)) & mask5; 
    return count; 
}
/* 
 * bang - Compute !x without using !
 *   Examples: bang(3) = 0, bang(0) = 1
 *   Legal ops: ~ & ^ | + << >>
 *   Max ops: 12
 *   Rating: 4 
 */
int bang(int x) {
    /* note that bang(x) returns 1 iff x == 0 */

    /* (x | (~x + 1))'s sign bit is 0 iff x == 0 */
    int signBit = x | (~x + 1);
    return (signBit >> 31) + 1;

    /* return ((x | (~x + 1)) >> 31) + 1; */
}
/* 
 * tmin - return minimum two's complement integer 
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 4
 *   Rating: 1
 */
int tmin(void) {
    return 0x1 << 31;
}
/* 
 * fitsBits - return 1 if x can be represented as an 
 *  n-bit, two's complement integer.
 *   1 <= n <= 32
 *   Examples: fitsBits(5,3) = 0, fitsBits(-4,3) = 1
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 15
 *   Rating: 2
 */
int fitsBits(int x, int n) {
    /* reference: https://stackoverflow.com/questions/14792521/bitwise-operations-and-shifts */

    /* idea: x can be represented as an n-bit, two's complement integer
     *       iff all bits to the left of position n-1(i.e., [n,31], inclusive, 0-index)
     *       have the same value as the bit in position n-1
     */

    /* equal to 32-n, which calculate the amount of remaining high order bits
     * after n low order bits used
     */
    int shift = 33 + ~n;

    /* ((x << shift) >> shift) fills the high order bits by bit n-1,
     * which is the sign bit of x under n-bit, two's complement integer representation
     * 
     * !(x ^ y) is same as x == y
     */
    return !(x ^ ((x << shift) >> shift));
}
/* 
 * divpwr2 - Compute x/(2^n), for 0 <= n <= 30
 *  Round toward zero
 *   Examples: divpwr2(15,1) = 7, divpwr2(-33,4) = -2
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 15
 *   Rating: 2
 */
int divpwr2(int x, int n) {
    /* reference: https://stackoverflow.com/questions/5061093/dividing-by-power-of-2-using-bit-shifting 
     *            http://caseyburkhardt.com/classes/csc2400/projects/DataLab/bits.c
     */

    /* return x >> n if x is non-negative
     * return (x >> n) + 1 otherwise
     * 
     * so when x is negative, we need add 1 to the result,
     * which will be implemented as add 2^n-1 to x before shift
     * note that ^ here means power
     */


    /* subtract 1 from 2^n
     * note that ~0 is same as -1
     */
    int mask = (1 << n) + ~0;

    /* use & operator on mask and sign bit of x  */
    int equalizer = (x >> 31) & mask;

    /* add 1 if x was originally negative
     * add 0 if x was originally positive
     */
    return (x + equalizer) >> n;

    /* return (x + ((x >> 31) & ((1 << n) + ~0))) >> n; */
}
/* 
 * negate - return -x 
 *   Example: negate(1) = -1.
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 5
 *   Rating: 2
 */
int negate(int x) {
    return ~x + 1;
}
/* 
 * isPositive - return 1 if x > 0, return 0 otherwise 
 *   Example: isPositive(-1) = 0.
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 8
 *   Rating: 3
 */
int isPositive(int x) {
    /* idea: a number is positive iff it's not negative and not zero */

    int negative = x & (0x1 << 31);
    int zero = !x;
    return !(negative | zero);

    /* return !((x & (0x1 << 31)) | !x); */
}
/* 
 * isLessOrEqual - if x <= y  then return 1, else return 0 
 *   Example: isLessOrEqual(4,5) = 1.
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 24
 *   Rating: 3
 */
int isLessOrEqual(int x, int y) {
    /* the following solution does not work because of overflow
     * int difference = y + ~x + 1;
     * return !(difference >> 31);
     */

    int signIsDifferent = !(x >> 31) ^ !(y >> 31);

    // different sign and x is negative
    int case1 = signIsDifferent  & (x >> 31);
    // same sign and x <= y, this takes care of overflow
    int case2 = !signIsDifferent & !((y + ~x +1) >> 31);

    return case1 | case2;
}
/*
 * ilog2 - return floor(log base 2 of x), where x > 0
 *   Example: ilog2(16) = 4
 *   Legal ops: ! ~ & ^ | + << >>
 *   Max ops: 90
 *   Rating: 4
 */
int ilog2(int x) {
    /* find the leftmost bit 1
     * use a method that is similar to binary search
     */
    int result = 0;
    result = (!!(x >> 16)) << 4; // if > 16? 
    // based on previous result, if > (result + 8)
    result = result + ((!!(x >> (result + 8))) << 3);
    result = result + ((!!(x >> (result + 4))) << 2);
    result = result + ((!!(x >> (result + 2))) << 1);
    result = result + (!!(x >> (result + 1)));
    return result;
}
/* 
 * float_neg - Return bit-level equivalent of expression -f for
 *   floating point argument f.
 *   Both the argument and result are passed as unsigned int's, but
 *   they are to be interpreted as the bit-level representations of
 *   single-precision floating point values.
 *   When argument is NaN, return argument.
 *   Legal ops: Any integer/unsigned operations incl. ||, &&. also if, while
 *   Max ops: 10
 *   Rating: 2
 */
unsigned float_neg(unsigned uf) {
    unsigned exp = (uf >> 23) & 0xff;
    unsigned frac = uf << 9;
    if (exp == 0xff && frac != 0) { // uf is NaN
        return uf;
    }
    return uf ^ 0x80000000;
}
/* 
 * float_i2f - Return bit-level equivalent of expression (float) x
 *   Result is returned as unsigned int, but
 *   it is to be interpreted as the bit-level representation of a
 *   single-precision floating point values.
 *   Legal ops: Any integer/unsigned operations incl. ||, &&. also if, while
 *   Max ops: 30
 *   Rating: 4
 */
unsigned float_i2f(int x) {
    int sign= (x >> 31) & 0x1;
    int i;
    int exponent;
    int fraction;
    int delta;
    int fraction_mask;

    if (x == 0)  {
        return x;
    } else if (x == 0x80000000) { // implicit casting here
        fraction = 0;
        exponent = 31;
    } else {
        if (sign) { // turn negtive to positive
            x = -x;
        }

        i = 30;
        while (!(x >> i)) { // see how many bits do x have(rightshift until 0) 
            i--;
        }
        exponent = i;

        x = x << (31 - i); // clean all those zeroes of high bits
        fraction_mask = 0x7fffff; // (1 << 23) - 1;
        // right shift 8 bits to get the fraction
        fraction = fraction_mask & (x >> 8);

        x = x & 0xff;
        //if lowest 8 bits of x is larger than a half,or is 1.5,round up 1
        delta = x > 128 || ((x == 128) && (fraction & 1));
        fraction += delta;
        if (fraction >> 23) {//if after rounding fraction is larger than 23bits
            fraction &= fraction_mask;
            exponent += 1;
        }
    }
    return (sign<<31) | ((exponent + 127) <<23) | fraction;
}
/* 
 * float_twice - Return bit-level equivalent of expression 2*f for
 *   floating point argument f.
 *   Both the argument and result are passed as unsigned int's, but
 *   they are to be interpreted as the bit-level representation of
 *   single-precision floating point values.
 *   When argument is NaN, return argument
 *   Legal ops: Any integer/unsigned operations incl. ||, &&. also if, while
 *   Max ops: 30
 *   Rating: 4
 */
unsigned float_twice(unsigned uf) {

    int exp = uf & 0x7f800000;
    
    if ((uf == 0) || (uf == (1 << 31))) { // +-0 case.
        return uf;
    }
    
    if (exp == 0x7f800000) { // NaN case.
        return uf;
    }

    if (exp == 0x00) { // Tiny value, but non-zero case.
        return (uf & (1 << 31)) | (uf << 1);
    }

    //Otherwise, Add 1 to exp value.
    return uf + (1 << 23);
}
