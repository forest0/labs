// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(BEGIN)

// read keyboard
@KBD
D=M

// color: 0 for white,
//        1 for black.
@color
M=0 // default, no key pressed, set color to white, we brush 16 pixels(one word) a time

@DRAW
D;JEQ // if no input, no need to change color

// key pressed, set color to black, we brush 16 pixels(one word) a time
@color
M=!M

// DRAW begin
(DRAW)

// initialize current address to @SCREEN + 8192, and save it to @cur_addr
@8192
D=A
@SCREEN
D=D+A
@cur_addr
M=D

// we draw from higher address to lower address
// here we use a do-while structure
// DRAW_LOOP begin
(DRAW_LOOP)

// cur_addr -= 1
@cur_addr
M=M-1

// get current color
@color
D=M

// brush current address
@cur_addr
A=M // IMPORTANT: indirect addressing
M=D

// cur_addr - @SCREEN > 0?
D=A
@SCREEN
D=D-A

@DRAW_LOOP
D;JGT // bigger than 0, not complete yet, continue to draw

// DRAW_LOOP end

// DRAW end

// infinite loop
@BEGIN
0;JMP
