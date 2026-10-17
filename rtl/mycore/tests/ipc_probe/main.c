/* ipc_probe — đo IPC và KIỂM CÁCH ĐẾM instret của một lõi, bằng các vòng lặp có
 * số lệnh BIẾT TRƯỚC từ assembly, không suy ra từ lõi nào cả.
 *
 * Mỗi vòng viết bằng asm cố định nên số lệnh mỗi lần lặp là hằng số, bất kể
 * tuỳ chọn tối ưu của trình biên dịch:
 *   alu   2 lệnh/vòng  (addi, bnez)                     -> không truy cập bộ nhớ
 *   mem   5 lệnh/vòng  (lw, addi, sw, addi, bnez)       -> 2 truy cập bộ nhớ
 *   mul   4 lệnh/vòng  (mul, addi, addi, bnez)          -> 1 phép nhân
 *   jmp   3 lệnh/vòng  (jal tới nhãn kế, addi, bnez)    -> nhảy vô điều kiện
 * In ra: tên, số vòng, số lệnh LÝ THUYẾT, chu kỳ đo, instret đo.
 * Nếu instret đo khác số lệnh lý thuyết thì lõi đó đếm sai.
 */
#include "soc.h"

typedef unsigned int u32;

static void putch(char c) { while (UART_STAT & UART_TX_BUSY); UART_DATA = (unsigned char)c; }
static void puts_(const char *s) { while (*s) putch(*s++); }
static void put_u32(u32 v)
{
    char b[10]; int n = 0;
    if (!v) { putch('0'); return; }
    while (v) { b[n++] = (char)('0' + v % 10u); v /= 10u; }
    while (n) putch(b[--n]);
}
static void eol(void) { puts_("\r\n"); }

static volatile u32 buf[4];

static __attribute__((noinline)) u32 loop_alu(u32 n)
{
    __asm__ volatile ("1: addi %0,%0,-1\n bnez %0,1b\n" : "+r"(n) :: );
    return n;
}
static __attribute__((noinline)) u32 loop_mem(u32 n, volatile u32 *p)
{
    u32 t;
    __asm__ volatile ("1: lw %1,0(%2)\n addi %1,%1,1\n sw %1,0(%2)\n"
                      "   addi %0,%0,-1\n bnez %0,1b\n"
                      : "+r"(n), "=&r"(t) : "r"(p) : "memory");
    return n;
}
static __attribute__((noinline)) u32 loop_mul(u32 n)
{
    u32 t = 3, acc = 0;
    __asm__ volatile ("1: mul %1,%1,%2\n addi %2,%2,1\n addi %0,%0,-1\n bnez %0,1b\n"
                      : "+r"(n), "+r"(acc) : "r"(t) : );
    return n + acc;
}
static __attribute__((noinline)) u32 loop_jmp(u32 n)
{
    __asm__ volatile ("1: jal zero,2f\n 2: addi %0,%0,-1\n bnez %0,1b\n" : "+r"(n) :: );
    return n;
}

#define RUN(NAME, IPL, CALL)                                   \
    do {                                                       \
        u32 c0, c1, i0, i1;                                    \
        i0 = rdinstret(); c0 = rdcycle();                      \
        CALL;                                                  \
        c1 = rdcycle(); i1 = rdinstret();                      \
        puts_("IPC," NAME ",");                                \
        put_u32(N); putch(',');                                \
        put_u32((u32)(IPL) * N); putch(',');                    \
        put_u32(c1 - c0); putch(',');                          \
        put_u32(i1 - i0); eol();                               \
    } while (0)

int main(void)
{
    const u32 N = 10000u;
    LED_REG = 0x00u;
    for (;;) {
        puts_("IPC,hello"); eol();
        RUN("alu", 2, loop_alu(N));
        RUN("mem", 5, loop_mem(N, buf));
        RUN("mul", 4, loop_mul(N));
        RUN("jmp", 3, loop_jmp(N));
        puts_("IPC,done"); eol();
        busy_loop(500000u);
    }
    return 0;
}
