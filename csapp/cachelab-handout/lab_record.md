# lab record

part a 比较常规写完了, 在写 part b 的时候都有点想放弃了, 但是在博客上看到一句话, 下定决心搞它

> 谁不想用最简单的方法获得最强大的能力，但是这又怎么可能。捷径，如果指的是最短的路径，那么也就是梯度上升最快的路径，更是最难的路径。靠什么去走完这段旅程呢？靠自己。靠自己的思考。靠自己的百折不挠。

共勉

## part b

cache 参数如下

- s = 5, 共 32 个 set
- E = 1, 每个 set 仅有一行, 即直接映射 (direct-mapped cache)
- b = 5, 每个 block 可以缓存 32 个字节, 即 8 个 int

```
     标记         组索引         块偏移
+------------+--------------+------------+
|            |      5       |      5     |
+------------+--------------+------------+
```

### 32 x 32

考虑 `M = N = 32` 的情形, 一个缓存块可以存放 8 个 int, 所以容易想到按 8 x 8 分块.

```c
void trans(int M, int N, int A[N][M], int B[M][N]) {
    for (i = 0; i < 32; i += 8) {
        for (j  = 0; j < 32; j += 8) {
            for (m = i; m < i + 8; ++m) {
                for (n = j; n < j + 8; ++n) {
                    B[n][m] = A[m][n];
                }
            }
        }
    }
}
```

此时 miss 为 343, 未达到满分要求.

打印发现 `&A == 0x602100, &B == 0x642100`, 而 `&B-&A == 0x40000` 且组索引位为 5~9 位, 所以 A 和 B 都按如下的方式映射到 cache(数字为组索引)

```
...8.... ...9.... ...10... ...11...
...12... ...13... ...14... ...15...
...16... ...17... ...18... ...19...
...20... ...21... ...22... ...23...
...24... ...25... ...26... ...27...
...28... ...29... ...30... ...31...
...0.... ...1.... ...2.... ...3....
...4.... ...5.... ...6.... ...7....
```

打印具体访存情况查看一下

```
M=32, N=32
L 602100,4 miss eviction    A[0][0] setIndex: 8
S 642100,4 miss eviction    B[0][0] setIndex: 8
L 602104,4 miss eviction    A[0][1] setIndex: 8
S 642180,4 miss             B[1][0] setIndex: 12
L 602108,4 hit              A[0][2] setIndex: 8
S 642200,4 miss             B[2][0] setIndex: 16
L 60210c,4 hit              A[0][3] setIndex: 8
S 642280,4 miss             B[3][0] setIndex: 20
L 602110,4 hit              A[0][4] setIndex: 8
S 642300,4 miss             B[4][0] setIndex: 24
L 602114,4 hit              A[0][5] setIndex: 8
S 642380,4 miss             B[5][0] setIndex: 28
L 602118,4 hit              A[0][6] setIndex: 8
S 642400,4 miss             B[6][0] setIndex: 0
L 60211c,4 hit              A[0][7] setIndex: 8
S 642480,4 miss             B[7][0] setIndex: 4
L 602180,4 miss eviction    A[1][0] setIndex: 12
S 642104,4 miss eviction    B[0][1] setIndex: 8
L 602184,4 hit              A[1][1] setIndex: 12
S 642184,4 miss eviction    B[1][1] setIndex: 12
L 602188,4 miss eviction    A[1][2] setIndex: 12
S 642204,4 hit              B[2][1] setIndex: 16
L 60218c,4 hit              A[1][3] setIndex: 12
S 642284,4 hit              B[3][1] setIndex: 20
L 602190,4 hit              A[1][4] setIndex: 12
S 642304,4 hit              B[4][1] setIndex: 24
L 602194,4 hit              A[1][5] setIndex: 12
S 642384,4 hit              B[5][1] setIndex: 28
L 602198,4 hit              A[1][6] setIndex: 12
S 642404,4 hit              B[6][1] setIndex: 0
L 60219c,4 hit              A[1][7] setIndex: 12
S 642484,4 hit              B[7][1] setIndex: 4
L 602200,4 miss eviction    A[2][0] setIndex: 16
S 642108,4 hit              B[0][2] setIndex: 8
L 602204,4 hit              A[2][1] setIndex: 16
S 642188,4 miss eviction    B[1][2] setIndex: 12
L 602208,4 hit              A[2][2] setIndex: 16
S 642208,4 miss eviction    B[2][2] setIndex: 16
L 60220c,4 miss eviction    A[2][3] setIndex: 16
S 642288,4 hit              B[3][2] setIndex: 20
L 602210,4 hit              A[2][4] setIndex: 16
S 642308,4 hit              B[4][2] setIndex: 24
```

一个缓存块可以缓存 8 个 int, 所以较好的情况应该是, 访问第一个 int 时 miss, 加载 8 个 int 到 cache, 后边访问剩下的 7 个 int 能够 hit.

但需要注意 conflict miss 的情况, 如上边对 `A[0][0], B[0][0], A[0][1]` 的依次访问:

1. 访问 `A[0][0]`, miss, 加载 `A[0][0]~A[0][7]` 到 cache, 组索引为 8.
2. 访问 `B[0][0]`, miss, 加载 `B[0][0]~B[0][7]` 到 cache, 组索引为 8, 即此时`A[0][0]~A[0][7]` 被驱逐.
3. 访问 `A[0][1]`, miss, 重新加载 `A[0][0]~A[0][7]` 到 cache, 组索引为 8.

出现上述 conflict miss 的原因是, 当访问对角线元素时, `A[m][m], B[m][m]` 被映射到同一个缓存块, 交替访问 A, B, 就会出现同一个缓存块被不断加载驱逐的情形.

解决方式: 先将 A 的 8 个 int 一次性读到栈上, 再将栈上的 8 个 int 一次性赋值给 B, 就达到了充分利用缓存的效果(读进一块, 充分利用完毕, 再丢弃它).

```c
void trans(int M, int N, int A[N][M], int B[M][N]) {
    int i, j, m;    // control loop
    int a0, a1, a2, a3, a4, a5, a6, a7; // read a complete block
    for (i = 0; i < M; i += 8) {
        for (j  = 0; j < N; j += 8) {
            for (m = i; m < i + 8; ++m) {

                a0 = A[m][j];
                a1 = A[m][j+1];
                a2 = A[m][j+2];
                a3 = A[m][j+3];
                a4 = A[m][j+4];
                a5 = A[m][j+5];
                a6 = A[m][j+6];
                a7 = A[m][j+7];
                
                B[j][m] = a0;
                B[j+1][m] = a1;
                B[j+2][m] = a2;
                B[j+3][m] = a3;
                B[j+4][m] = a4;
                B[j+5][m] = a5;
                B[j+6][m] = a6;
                B[j+7][m] = a7;
            }
        }
    }
}
```

现在 miss 为 287 达到要求

再打印一下具体访存情形

```
M=32, N=32
L 602100,4 miss eviction    A[0][0] setIndex: 8
L 602104,4 hit              A[0][1] setIndex: 8
L 602108,4 hit              A[0][2] setIndex: 8
L 60210c,4 hit              A[0][3] setIndex: 8
L 602110,4 hit              A[0][4] setIndex: 8
L 602114,4 hit              A[0][5] setIndex: 8
L 602118,4 hit              A[0][6] setIndex: 8
L 60211c,4 hit              A[0][7] setIndex: 8
S 642100,4 miss eviction    B[0][0] setIndex: 8
S 642180,4 miss             B[1][0] setIndex: 12
S 642200,4 miss             B[2][0] setIndex: 16
S 642280,4 miss             B[3][0] setIndex: 20
S 642300,4 miss             B[4][0] setIndex: 24
S 642380,4 miss             B[5][0] setIndex: 28
S 642400,4 miss             B[6][0] setIndex: 0
S 642480,4 miss             B[7][0] setIndex: 4
L 602180,4 miss eviction    A[1][0] setIndex: 12
L 602184,4 hit              A[1][1] setIndex: 12
L 602188,4 hit              A[1][2] setIndex: 12
L 60218c,4 hit              A[1][3] setIndex: 12
L 602190,4 hit              A[1][4] setIndex: 12
L 602194,4 hit              A[1][5] setIndex: 12
L 602198,4 hit              A[1][6] setIndex: 12
L 60219c,4 hit              A[1][7] setIndex: 12
S 642104,4 hit              B[0][1] setIndex: 8
S 642184,4 miss eviction    B[1][1] setIndex: 12
S 642204,4 hit              B[2][1] setIndex: 16
S 642284,4 hit              B[3][1] setIndex: 20
```

可以看到对 A 来说达到另外完美的 cache 利用率, 但对 B 的对角线元素访问仍然存在一次 miss, 这是因为 `B[i][i]` 加载到缓存后, 在加载 `A[i][i]` 时会将 `B[i][i]` 驱逐, 导致后边访问 `B[i][i]` miss.

按此计算一下具体的 miss 数量

32 x 32 = 1024

对于 A, 仅在访问缓存块内第一个 int 时有一个 miss, 1024 * 1/8 = 128

对于 B, 除了在访问缓存块内第一个 int 时有一个 miss 外, 对角线上元素都会造成一次 miss, 1024 * 1/8 + 32 = 160

总和为 128 + 160 = 288 与输出 287 几乎一样.

### 64 x 64

cache 只能放下 A 中 4 行, 若仍旧使用 8 x 8 的块, 前 4 行可以放入 cache, 但后 4 行会和前 4 行冲突, 此时 miss 为 4611, 几乎同 Simple row-wise scan transpose 的 miss, 其值为 4723.

```
M=64, N=64
L 603100,4 miss eviction    A[0][0] setIndex: 8
L 603104,4 hit              A[0][1] setIndex: 8
L 603108,4 hit              A[0][2] setIndex: 8
L 60310c,4 hit              A[0][3] setIndex: 8
L 603110,4 hit              A[0][4] setIndex: 8
L 603114,4 hit              A[0][5] setIndex: 8
L 603118,4 hit              A[0][6] setIndex: 8
L 60311c,4 hit              A[0][7] setIndex: 8
S 643100,4 miss eviction    B[0][0] setIndex: 8
S 643200,4 miss             B[1][0] setIndex: 16
S 643300,4 miss             B[2][0] setIndex: 24
S 643400,4 miss             B[3][0] setIndex: 0
S 643500,4 miss eviction    B[4][0] setIndex: 8
S 643600,4 miss eviction    B[5][0] setIndex: 16
S 643700,4 miss eviction    B[6][0] setIndex: 24
S 643800,4 miss eviction    B[7][0] setIndex: 0
L 603200,4 miss eviction    A[1][0] setIndex: 16
L 603204,4 hit              A[1][1] setIndex: 16
L 603208,4 hit              A[1][2] setIndex: 16
L 60320c,4 hit              A[1][3] setIndex: 16
L 603210,4 hit              A[1][4] setIndex: 16
L 603214,4 hit              A[1][5] setIndex: 16
L 603218,4 hit              A[1][6] setIndex: 16
L 60321c,4 hit              A[1][7] setIndex: 16
S 643104,4 miss eviction    B[0][1] setIndex: 8
S 643204,4 miss eviction    B[1][1] setIndex: 16
S 643304,4 miss eviction    B[2][1] setIndex: 24
S 643404,4 miss eviction    B[3][1] setIndex: 0
S 643504,4 miss eviction    B[4][1] setIndex: 8
S 643604,4 miss eviction    B[5][1] setIndex: 16
S 643704,4 miss eviction    B[6][1] setIndex: 24
S 643804,4 miss eviction    B[7][1] setIndex: 0
L 603300,4 miss eviction    A[2][0] setIndex: 24
L 603304,4 hit              A[2][1] setIndex: 24
L 603308,4 hit              A[2][2] setIndex: 24
```

若改用 4 x 4, miss 为 1699, 已经好了很多, 但是还是达不到要求. cache 中能存放 8 个 int, 但只使用了 4 个.

```
M=64, N=64
L 602100,4 miss eviction    A[0][0] setIndex: 8
L 602104,4 hit              A[0][1] setIndex: 8
L 602108,4 hit              A[0][2] setIndex: 8
L 60210c,4 hit              A[0][3] setIndex: 8
S 642100,4 miss eviction    B[0][0] setIndex: 8
S 642200,4 miss             B[1][0] setIndex: 16
S 642300,4 miss             B[2][0] setIndex: 24
S 642400,4 miss             B[3][0] setIndex: 0
L 602200,4 miss eviction    A[1][0] setIndex: 16
L 602204,4 hit              A[1][1] setIndex: 16
L 602208,4 hit              A[1][2] setIndex: 16
L 60220c,4 hit              A[1][3] setIndex: 16
S 642104,4 hit              B[0][1] setIndex: 8
S 642204,4 miss eviction    B[1][1] setIndex: 16
S 642304,4 hit              B[2][1] setIndex: 24
S 642404,4 hit              B[3][1] setIndex: 0
L 602300,4 miss eviction    A[2][0] setIndex: 24
L 602304,4 hit              A[2][1] setIndex: 24
L 602308,4 hit              A[2][2] setIndex: 24
L 60230c,4 hit              A[2][3] setIndex: 24
S 642108,4 hit              B[0][2] setIndex: 8
S 642208,4 hit              B[1][2] setIndex: 16
S 642308,4 miss eviction    B[2][2] setIndex: 24
S 642408,4 hit              B[3][2] setIndex: 0
L 602400,4 miss eviction    A[3][0] setIndex: 0
L 602404,4 hit              A[3][1] setIndex: 0
L 602408,4 hit              A[3][2] setIndex: 0
L 60240c,4 hit              A[3][3] setIndex: 0
S 64210c,4 hit              B[0][3] setIndex: 8
S 64220c,4 hit              B[1][3] setIndex: 16
S 64230c,4 hit              B[2][3] setIndex: 24
S 64240c,4 miss eviction    B[3][3] setIndex: 0
L 602110,4 miss eviction    A[0][4] setIndex: 8
L 602114,4 hit              A[0][5] setIndex: 8
L 602118,4 hit              A[0][6] setIndex: 8
L 60211c,4 hit              A[0][7] setIndex: 8
S 642500,4 miss eviction    B[4][0] setIndex: 8
S 642600,4 miss eviction    B[5][0] setIndex: 16
S 642700,4 miss eviction    B[6][0] setIndex: 24
S 642800,4 miss eviction    B[7][0] setIndex: 0
L 602210,4 miss eviction    A[1][4] setIndex: 16
L 602214,4 hit              A[1][5] setIndex: 16
```

参考了网上的写法, 链接在最后

块仍按 8 x 8 划分, 但是每一个 8 x 8 的块在内部划分为 4 个 4 x 4 的块进行处理.

```
为方便描述, 把这四个小块分别按顺时针命名为 1, 2, 3, 4
    +--------+--------+
    |        |        |
    |        |        |
    |   1    |   2    |
    |        |        |
    +--------+--------+
    |        |        |
    |        |        |
    |   4    |   3    |
    |        |        |
    +--------+--------+

1. 先把 A 的 1, 2 区域复制到 B 的 1, 2 区域, 后边再把 B 的 2 移到 4

                                  k2       k3
                                  |        |
                                  v        v
    +--------+--------+          +--------+--------+
k1->|.......>|*******>|          |. . . . |* * * * |
    |.......>|*******>|          |. . . . |* * * * |
    |.......>|*******>|          |. . . . |* * * * |
    |.......>|*******>|          |v v v v |v v v v |
    +--------+--------+          +--------+--------+
    |        |        |          |        |        |
    |        |        |          |        |        |
    |        |        |          |        |        |
    |        |        |          |        |        |
    +--------+--------+          +--------+--------+
             A                            B         

不考虑对角线元素, k1 读 8 个 int, 一次 miss, k2 在第一列全 miss 后边都会 hit.

2. 
    - 用 a4~a7 存储 A 中 p1 指向的列
    - 用 a0~a3 存储 B 中 p2 指向的行
    - a4~a7 赋值给 p2 指向的位置
    - a0~a3 赋值给 p3 指向的位置
    - p4 指向的列赋值给 p5 指向的行
    - 更新 5 个指针, 循环 4 次


                                              a0a1a2a3
    +--------+--------+             +--------+--------+
    |        |        |             |        |o o o o |    <--- p2
    |        |        |             |        |, , , , |
    |        |        |             |        |, , , , |
    |        |        |             |        |v v v v |
    +--------+--------+             +--------+--------+
 a4 |o``````>|        |     p3 ---> |o o o o |        |    <--- p5
 a5 |o``````>|        |             |        |        |
 a6 |o``````>|        |             |        |        |
 a7 |o``````>|        |             |        |        |
    +--------+--------+             +--------+--------+
             A                               B
     ^        ^
     |        |
     |        |
     p1       p4

保证了 A 的 3, 4 区域在 cache 中, 而 B 仅需要 2 个缓存块
```

```c
for (i = 0; i < 64; i += 8) {
    for (j  = 0; j < 64; j += 8) {
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
```

此时 miss 为 1171, 达到要求.

## 61 x 67

不规则矩阵, 尝试分块, 从 4 开始我试到了 27, 发现 23 处有个低值 1928

# 参考

> https://zhengjingwei.github.io/2018/01/31/CSAPP-lab3-cachelab/
