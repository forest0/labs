// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Ha, Human Resource Machine.

// Put your code here.
// idea: we can use addition multiple times to achieve multiplication.

// init variables
@R2
M=0 // production resutl

@cnt
M=0 // how many addition we have done


(LOOP)
@R0
D=M // how many addition we need

@cnt
D=D-M // how many addition left

@END
D;JEQ // no more addition need, we are done

@R1
D=M // load addend from memory

@R2
M=D+M // add and save to memory

@cnt
M=M+1 // add counter

@LOOP
0;JMP // goto LOOP

(END)
@END
0;JMP
