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

touch3 会调用函数 hexmatch, hexmatch 会调用 strncmp, 意味这栈会向低地址生长.

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
