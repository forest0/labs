# bomb lab record

边拆边记, 懒得整理了, 后边是拆弹现场.

## phase_1

```
 ► f 0           401342 strings_not_equal+10
   f 1           400eee phase_1+14
   f 2           400e3f main+159
   f 3     7ffff7a32f45 __libc_start_main+245
   f 4           400cb9 _start+41
```

反汇编发现 `strings_not_equal` 会调用两次 `string_length`, 一次针对用户输入, 另外一次就是内置的答案了.
调用结束后寄存器 `rax` 值为 0x34, 说明答案字符串长度为 0x34.
寄存器 `rdi` 中存放的即为答案字符串首地址, 打印即可得到答案.

```
call puts((char *)$rdi)
```

## phase_2

```
 ► 0x400f05 <phase_2+9>     call   read_six_numbers              <0x40145c>
        rdi: 0x6037d0 (input_strings+80) ◂— 0x6f6168696e /* 'nihao' */          字符串地址
        rsi: 0x7fffffffd4f0 ◂— 0x0
        rdx: 0x2
        rcx: 0x5                                                                字符串长度


读取 6 个 int 到栈上, 起始地址为 0x7fffffffd4f0
 ► 0x40148a <read_six_numbers+46>    call   __isoc99_sscanf@plt           <0x400bf0>
        s: 0x6037d0 (input_strings+80) ◂— 0x6f6168696e /* 'nihao' */
        format: 0x4025c3 ◂— 0x6425206425206425 ('%d %d %d')                     注意这里应该是 6 个 %d
        vararg: 0x7fffffffd4f0 ◂— 0x0
```

sscanf 返回值说明:

On success, the function returns the number of items in the argument list successfully filled. 
This count can match the expected number of items or be less (even zero) in the case of a matching failure.
In the case of an input failure before any data could be successfully interpreted, EOF is returned.

```
至少需要输入 6 个数字

  40148a:   e8 61 f7 ff ff          callq  400bf0 <__isoc99_sscanf@plt>
  40148f:   83 f8 05                cmp    $0x5,%eax
  401492:   7f 05                   jg     401499 <read_six_numbers+0x3d>
  401494:   e8 a1 ff ff ff          callq  40143a <explode_bomb>
```

read_six_numbers 伪码

```c
// ...
int cnt = sscanf(input_str, "%d %d %d %d %d %d", ...);
if (cnt <= 5) {
    explode_bomb();
}
```

```
第一个数字必须为 1
0000000000400efc <phase_2>:
  400efc:   55                      push   %rbp
  400efd:   53                      push   %rbx
  400efe:   48 83 ec 28             sub    $0x28,%rsp
  400f02:   48 89 e6                mov    %rsp,%rsi
  400f05:   e8 52 05 00 00          callq  40145c <read_six_numbers>
  400f0a:   83 3c 24 01             cmpl   $0x1,(%rsp)
  400f0e:   74 20                   je     400f30 <phase_2+0x34>
  400f10:   e8 25 05 00 00          callq  40143a <explode_bomb>    不是 1, explode
```

```
第二个数字必须为 2
  400f17:   8b 43 fc                mov    -0x4(%rbx),%eax          移动第一个数字到 eax
  400f1a:   01 c0                   add    %eax,%eax                两倍
  400f1c:   39 03                   cmp    %eax,(%rbx)              同第二个数字比较
  400f1e:   74 05                   je     400f25 <phase_2+0x29>
  400f20:   e8 15 05 00 00          callq  40143a <explode_bomb>    不是 2, explode
```

```
第三个数字为 4
  400f25:   48 83 c3 04             add    $0x4,%rbx
  400f29:   48 39 eb                cmp    %rbp,%rbx
```

phase_2 伪码
```c
int i = 0;
if (input_num[i] != 1) {
    explode_bomb();
}
for (; i < 6; ++i) {
    if (input_num[i] != 2*input_num[i-1]) {
        explode_bomb()
    }
}
```

## phase_3

```
需要输入两个数
 ► 0x400f5b <phase_3+24>    call   __isoc99_sscanf@plt           <0x400bf0>
        s: 0x603820 (input_strings+160) ◂— 0x6f6168696e /* 'nihao' */
        format: 0x4025cf ◂— 0x7245006425206425 /* '%d %d' */                    这里确实是两个数
        vararg: 0x7fffffffd518 —▸ 0x4014ac (read_line+14) ◂— test   rax, rax

   0x400f60 <phase_3+29>     cmp    eax, 1
   0x400f63 <phase_3+32>     jg     phase_3+39                    <0x400f6a>
   0x400f65 <phase_3+34>     call   <explode_bomb>

第一个数必须小于 7
 ► 0x400f6a <phase_3+39>     cmp    dword ptr [rsp + 8], 7
   0x400f6f <phase_3+44>     ja     phase_3+106                   <0x400fad>    explode_bomb

   400f71:   8b 44 24 08             mov    0x8(%rsp),%eax
   400f75:   ff 24 c5 70 24 40 00    jmpq   *0x402470(,%rax,8)                  这里猜测是个跳转表

打印查看一下跳转表
0x402470:   0x0000000000400f7c  0x0000000000400fb9
0x402480:   0x0000000000400f83  0x0000000000400f8a
0x402490:   0x0000000000400f91  0x0000000000400f98
0x4024a0:   0x0000000000400f9f  0x0000000000400fa6

这里方式应该是不唯一的, 随便跳一个就好

但需要注意的是, 第二个输入应与第一个输入决定的跳转后对 rax 的赋值相同
  400fbe:   3b 44 24 0c             cmp    0xc(%rsp),%eax
  400fc2:   74 05                   je     400fc9 <phase_3+0x86>                phase_3 成功
  400fc4:   e8 71 04 00 00          callq  40143a <explode_bomb>
```

phase_3 伪码
```c
int cnt = sscanf(input_str, "%d %d", ...);
if (cnt <= 1 || input_num[0] > 7) {
    explode_bomb();
}
int target;
switch(input_num[0]) {
    case xxx:
        target = yyy;
        break;
    case 1:
        target = 311;
        break;
    // case ...:
}
if (input_num[1] != target) {
    explode_bomb();
}
```

## phase_4

```
000000000040100c <phase_4>:
  40100c:   48 83 ec 18             sub    $0x18,%rsp
  401010:   48 8d 4c 24 0c          lea    0xc(%rsp),%rcx
  401015:   48 8d 54 24 08          lea    0x8(%rsp),%rdx
  40101a:   be cf 25 40 00          mov    $0x4025cf,%esi
  40101f:   b8 00 00 00 00          mov    $0x0,%eax
  401024:   e8 c7 fb ff ff          callq  400bf0 <__isoc99_sscanf@plt>
  401029:   83 f8 02                cmp    $0x2,%eax                        输入两个数字
  40102c:   75 07                   jne    401035 <phase_4+0x29>
  40102e:   83 7c 24 08 0e          cmpl   $0xe,0x8(%rsp)
  401033:   76 05                   jbe    40103a <phase_4+0x2e>            第一个数字应小于等于 0xe
  401035:   e8 00 04 00 00          callq  40143a <explode_bomb>
  40103a:   ba 0e 00 00 00          mov    $0xe,%edx
  40103f:   be 00 00 00 00          mov    $0x0,%esi
  401044:   8b 7c 24 08             mov    0x8(%rsp),%edi
  401048:   e8 81 ff ff ff          callq  400fce <func4>
  40104d:   85 c0                   test   %eax,%eax                        func4 必须返回 0
  40104f:   75 07                   jne    401058 <phase_4+0x4c>
  401051:   83 7c 24 0c 00          cmpl   $0x0,0xc(%rsp)                   第二个数字必须是 0
  401056:   74 05                   je     40105d <phase_4+0x51>
  401058:   e8 dd 03 00 00          callq  40143a <explode_bomb>
  40105d:   48 83 c4 18             add    $0x18,%rsp
  401061:   c3                      retq   
```

func4 存在递归调用, 看晕了, 不过瞎猜 0 0 正确了.

## phase_5

```
0000000000401062 <phase_5>:
  401062:   53                      push   %rbx
  401063:   48 83 ec 20             sub    $0x20,%rsp
  401067:   48 89 fb                mov    %rdi,%rbx
  40106a:   64 48 8b 04 25 28 00    mov    %fs:0x28,%rax
  401071:   00 00 
  401073:   48 89 44 24 18          mov    %rax,0x18(%rsp)
  401078:   31 c0                   xor    %eax,%eax
  40107a:   e8 9c 02 00 00          callq  40131b <string_length>
  40107f:   83 f8 06                cmp    $0x6,%eax
  401082:   74 4e                   je     4010d2 <phase_5+0x70>            输入字符串长度必须为 6
  401084:   e8 b1 03 00 00          callq  40143a <explode_bomb>
  401089:   eb 47                   jmp    4010d2 <phase_5+0x70>
  40108b:   0f b6 0c 03             movzbl (%rbx,%rax,1),%ecx               零扩展的字传送到双字(传送输入的第一个字节到 ecx)
  40108f:   88 0c 24                mov    %cl,(%rsp)                       cl 到栈顶
  401092:   48 8b 14 24             mov    (%rsp),%rdx                      栈顶到 rdx
  401096:   83 e2 0f                and    $0xf,%edx                        取 rdx 低 4 位
  401099:   0f b6 92 b0 24 40 00    movzbl 0x4024b0(%rdx),%edx
  4010a0:   88 54 04 10             mov    %dl,0x10(%rsp,%rax,1)
  4010a4:   48 83 c0 01             add    $0x1,%rax
  4010a8:   48 83 f8 06             cmp    $0x6,%rax                        长度为 6 的循环(根据输入, 不断地从 0x4024b0 附近拷贝字符到栈)
  4010ac:   75 dd                   jne    40108b <phase_5+0x29>
  4010ae:   c6 44 24 16 00          movb   $0x0,0x16(%rsp)                  末尾附加 \0
  4010b3:   be 5e 24 40 00          mov    $0x40245e,%esi                   目标字符串
  4010b8:   48 8d 7c 24 10          lea    0x10(%rsp),%rdi                  上述循环构造的字符串
  4010bd:   e8 76 02 00 00          callq  401338 <strings_not_equal>       比较两个字符串是否相等
  4010c2:   85 c0                   test   %eax,%eax
  4010c4:   74 13                   je     4010d9 <phase_5+0x77>
  4010c6:   e8 6f 03 00 00          callq  40143a <explode_bomb>
  4010cb:   0f 1f 44 00 00          nopl   0x0(%rax,%rax,1)
  4010d0:   eb 07                   jmp    4010d9 <phase_5+0x77>
  4010d2:   b8 00 00 00 00          mov    $0x0,%eax
  4010d7:   eb b2                   jmp    40108b <phase_5+0x29>
  4010d9:   48 8b 44 24 18          mov    0x18(%rsp),%rax
  4010de:   64 48 33 04 25 28 00    xor    %fs:0x28,%rax
  4010e5:   00 00 
  4010e7:   74 05                   je     4010ee <phase_5+0x8c>
  4010e9:   e8 42 fa ff ff          callq  400b30 <__stack_chk_fail@plt>
  4010ee:   48 83 c4 20             add    $0x20,%rsp
  4010f2:   5b                      pop    %rbx
  4010f3:   c3                      retq
```

phase_5 伪码

```c
char buffer[6];
int len = string_length(input_str);
int i;
if (len != 6) {
    explode_bomb();
}

for (i = 0; i < 6; ++i) {
    buffer[i] = char_arr[f(input_str[i])];
}

if (strings_not_equal(buffer, target_str)) {
    explode_bomb();
}
```

函数 f 仅对 input_str[i] 的低 4 位敏感, 所以答案也不唯一.

## phase_6

前边 5 个玩了一天, 这最后一个玩了一天...

```
00000000004010f4 <phase_6>:
  4010f4:   41 56                   push   %r14
  4010f6:   41 55                   push   %r13
  4010f8:   41 54                   push   %r12
  4010fa:   55                      push   %rbp
  4010fb:   53                      push   %rbx                             保存 5 个寄存器
  4010fc:   48 83 ec 50             sub    $0x50,%rsp                       栈上分配 0x50 字节空间
  401100:   49 89 e5                mov    %rsp,%r13
  401103:   48 89 e6                mov    %rsp,%rsi
  401106:   e8 51 03 00 00          callq  40145c <read_six_numbers>        读取六个整数
  40110b:   49 89 e6                mov    %rsp,%r14
  40110e:   41 bc 00 00 00 00       mov    $0x0,%r12d                       外循环初始化 i = 0
  401114:   4c 89 ed                mov    %r13,%rbp  <--------------+
  401117:   41 8b 45 00             mov    0x0(%r13),%eax            |
  40111b:   83 e8 01                sub    $0x1,%eax                 |
  40111e:   83 f8 05                cmp    $0x5,%eax                 |
  401121:   76 05              +--  jbe    401128 <phase_6+0x34>     |      每个数字应小于等于 6
  401123:   e8 12 03 00 00     |    callq  40143a <explode_bomb>     |
  401128:   41 83 c4 01        +--> add    $0x1,%r12d                |      ++i
  40112c:   41 83 fc 06             cmp    $0x6,%r12d                |      外循环 6 次 i < 6
  401130:   74 21            +----  je     401153 <phase_6+0x5f>     |
  401132:   44 89 e3         |      mov    %r12d,%ebx                |      内循环初始化 j = i
  401135:   48 63 c3         |      movslq %ebx,%rax  <------------+ |
  401138:   8b 04 84         |      mov    (%rsp,%rax,4),%eax      | |      遍历后边的数字 j < 6
  40113b:   39 45 00         |      cmp    %eax,0x0(%rbp)          | |
  40113e:   75 05            | +--  jne    401145 <phase_6+0x51>   | |
  401140:   e8 f5 02 00 00   | |    callq  40143a <explode_bomb>   | |      后边的数字不能和当前数字相等
  401145:   83 c3 01         | +--> add    $0x1,%ebx               | |      ++j
  401148:   83 fb 05         |      cmp    $0x5,%ebx               | |      内循环 j < 6
  40114b:   7e e8            |      jle    401135 <phase_6+0x41> --+ |
  40114d:   49 83 c5 04      |      add    $0x4,%r13                 |
  401151:   eb c1            |      jmp    401114 <phase_6+0x20> ----+
  401153:   48 8d 74 24 18   +----> lea    0x18(%rsp),%rsi                  最后一个数字
  401158:   4c 89 f0                mov    %r14,%rax                        栈顶
  40115b:   b9 07 00 00 00          mov    $0x7,%ecx
  401160:   89 ca               +-> mov    %ecx,%edx
  401162:   2b 10               |   sub    (%rax),%edx
  401164:   89 10               |   mov    %edx,(%rax)
  401166:   48 83 c0 04         |   add    $0x4,%rax
  40116a:   48 39 f0            |   cmp    %rsi,%rax
  40116d:   75 f1               +-- jne    401160 <phase_6+0x6c>            循环遍历输入的 6 个数字, 用 7 减该数字的差赋值给该数字
  40116f:   be 00 00 00 00          mov    $0x0,%esi                        循环初始化
  401174:   eb 21               +-- jmp    401197 <phase_6+0xa3>
  401176:   48 8b 52 08         | +>mov    0x8(%rdx),%rdx <------------+    指向链表下一个节点
  40117a:   83 c0 01            | | add    $0x1,%eax                   |
  40117d:   39 c8               | | cmp    %ecx,%eax                   |
  40117f:   75 f5               | +-jne    401176 <phase_6+0x82>       |    获得链表的第 k 个节点
  401181:   eb 05               | +-jmp    401188 <phase_6+0x94>       |
  401183:   ba d0 32 60 00      | | mov    $0x6032d0,%edx              | <--+
  401188:   48 89 54 74 20      | +>mov    %rdx,0x20(%rsp,%rsi,2)      |    |   根据用 7 减后的数字 k, 将链表第 k 个节点依次复制到栈上
  40118d:   48 83 c6 04         |   add    $0x4,%rsi                   |    |
  401191:   48 83 fe 18         |   cmp    $0x18,%rsi                  |    |
  401195:   74 14               |   je     4011ab <phase_6+0xb7> --+   |    |
  401197:   8b 0c 34            +-> mov    (%rsp,%rsi,1),%ecx      |   |    |
  40119a:   83 f9 01                cmp    $0x1,%ecx               |   |    |
  40119d:   7e e4                   jle    401183 <phase_6+0x8f>   |   |  --+
  40119f:   b8 01 00 00 00          mov    $0x1,%eax               |   |
  4011a4:   ba d0 32 60 00          mov    $0x6032d0,%edx          |   |        链表头
  4011a9:   eb cb                   jmp    401176 <phase_6+0x82>   | --+
  4011ab:   48 8b 5c 24 20          mov    0x20(%rsp),%rbx  <------+            最先复制到栈上的节点的地址
  4011b0:   48 8d 44 24 28          lea    0x28(%rsp),%rax
  4011b5:   48 8d 74 24 50          lea    0x50(%rsp),%rsi                      最后复制到栈的节点在栈上地址
  4011ba:   48 89 d9                mov    %rbx,%rcx
  4011bd:   48 8b 10                mov    (%rax),%rdx <-----------+
  4011c0:   48 89 51 08             mov    %rdx,0x8(%rcx)          |            按栈上顺序重新组织链表链接顺序
  4011c4:   48 83 c0 08             add    $0x8,%rax               |            迭代栈上节点
  4011c8:   48 39 f0                cmp    %rsi,%rax               |
  4011cb:   74 05                 +-je     4011d2 <phase_6+0xde>   |
  4011cd:   48 89 d1              | mov    %rdx,%rcx               |
  4011d0:   eb eb                 | jmp    4011bd <phase_6+0xc9> --+
  4011d2:   48 c7 42 08 00 00 00  +>movq   $0x0,0x8(%rdx)                       附加末尾空指针
  4011d9:   00 
  4011da:   bd 05 00 00 00          mov    $0x5,%ebp
  4011df:   48 8b 43 08         +-> mov    0x8(%rbx),%rax
  4011e3:   8b 00               |   mov    (%rax),%eax
  4011e5:   39 03               |   cmp    %eax,(%rbx)
  4011e7:   7d 05               | +-jge    4011ee <phase_6+0xfa>                链表节点值必须降序排列
  4011e9:   e8 4c 02 00 00      | | callq  40143a <explode_bomb>
  4011ee:   48 8b 5b 08         | +>mov    0x8(%rbx),%rbx                       迭代链表节点
  4011f2:   83 ed 01            |   sub    $0x1,%ebp
  4011f5:   75 e8               +---jne    4011df <phase_6+0xeb>
  4011f7:   48 83 c4 50             add    $0x50,%rsp
  4011fb:   5b                      pop    %rbx
  4011fc:   5d                      pop    %rbp
  4011fd:   41 5c                   pop    %r12
  4011ff:   41 5d                   pop    %r13
  401201:   41 5e                   pop    %r14
  401203:   c3                      retq
```

伪码如下

```c
for (int i = 0; i < 6; ++i) {
    if (input_num[i] -1 > 5) {
        explode_bomb();
    }
    for (int j = i; j < 6; ++j) {
        if (input_num[j] == input_num[i]) {
            explode_bomb();
        }
    }
}

for (int i = 0; i < 6; ++i) {
    input_num[i] = 7 - input_num[i];
}

for (int i = 0; i < 6; ++i) {
    if (input_num[i] <= i) {
        cur = head;
    } else {
        cur = head;
        for (int j = 1; j < input_num[i]; ++j) {
            cur = cur->next;
        }
    }
    addr_on_stack[i] = cur;
}

for (int i = 0; i < 5; ++i) {
    addr_on_stack[i]->next = addr_on_stack[i+1];
}
addr_on_stack[5]->next = NULL;

cur = addr_on_stack[0];
for (int i = 1; i < 6; ++i) {
    if (cur->value < cur->next->value) {
            explode_bomb();
    }
    cur = cur->next;
}
```
