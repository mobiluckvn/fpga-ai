/* F5 — firmware kiểm chứng SoC PicoRV32.
 *
 * In ra UART (CSV, kết thúc \r\n — theo quy ước trong CLAUDE.md):
 *   F5,hello,<git hash ngắn>
 *   F5,cycle,<rdcycle tại thời điểm đó>
 *   F5,loop,<số chu kỳ của busy_loop(N)>        <- tiêu chí ĐẠT: kit = Verilator
 *   F5,hwc,<số đếm của bộ đếm phần cứng cho cùng đoạn>
 *   F5,instret,<số lệnh đã thực thi cho cùng đoạn>
 *   F5,arith,<kết quả vài phép nhân/chia>       <- bắt lỗi DSP nếu có
 *   F5,ram,<tổng kiểm dữ liệu khởi tạo trong RAM>
 *   F5,done
 *
 * Sau đó in lại toàn bộ mỗi ~1 giây để host bắt được bất kể lúc nào mở cổng.
 */
#include "soc.h"

#ifndef GIT_HASH
#define GIT_HASH "unknown"
#endif

#ifndef LOOP_N
#define LOOP_N 1000u
#endif

/* ---------- xuất UART ---------- */
static void putch(char c)
{
    while (UART_STAT & UART_TX_BUSY)
        ;
    UART_DATA = (unsigned char)c;
}

static void puts_(const char *s)
{
    while (*s)
        putch(*s++);
}

static void put_u32(unsigned v)
{
    char buf[11];
    int i = 0;
    if (v == 0) {
        putch('0');
        return;
    }
    while (v) {
        buf[i++] = (char)('0' + (v % 10u));
        v /= 10u;
    }
    while (i)
        putch(buf[--i]);
}

static void put_hex32(unsigned v)
{
    int i;
    for (i = 28; i >= 0; i -= 4) {
        unsigned d = (v >> i) & 0xFu;
        putch((char)(d < 10u ? ('0' + d) : ('A' + d - 10u)));
    }
}

static void eol(void) { puts_("\r\n"); }

/* ---------- dữ liệu nằm trong .data, dùng để kiểm phần nạp $readmemh ---------- */
static const unsigned ram_pattern[8] = {
    0x01234567u, 0x89ABCDEFu, 0xDEADBEEFu, 0xCAFEBABEu,
    0x00000001u, 0x80000000u, 0xFFFFFFFFu, 0x5A5A5A5Au
};

static unsigned ram_sum(void)
{
    unsigned s = 0;
    int i;
    for (i = 0; i < 8; i++)
        s = s * 31u + ram_pattern[i];   /* dùng MUL -> cũng kiểm luôn bộ nhân */
    return s;
}

/* ---------- phép toán để bắt lỗi khối nhân/chia ---------- */
static unsigned arith_check(void)
{
    volatile unsigned a = 123456789u;
    volatile unsigned b = 3735928559u;   /* 0xDEADBEEF */
    volatile int      c = -12345;
    volatile int      d = 6789;
    unsigned r = 0;

    r += (unsigned)(a * b);              /* MUL */
    r += (unsigned)((int)(c * d));       /* MUL có dấu */
    r += a / 7919u;                      /* DIVU */
    r += a % 7919u;                      /* REMU */
    r += (unsigned)((int)c / d);         /* DIV */
    r += (unsigned)((int)c % d);         /* REM */
    return r;
}

int main(void)
{
    unsigned t0, t1, h0, h1, i0, i1;
    unsigned loop_cycles, hwc, instret;

    LED_REG = 0x01u;

    /* ---- đo đoạn busy_loop: rdcycle, bộ đếm phần cứng, rdinstret cùng lúc ---- */
    HWC_CTRL = 1u;                 /* xoá và chạy */
    i0 = rdinstret();
    t0 = rdcycle();
    busy_loop(LOOP_N);
    t1 = rdcycle();
    i1 = rdinstret();
    h1 = HWC_VALUE;
    HWC_CTRL = 0u;                 /* dừng */
    h0 = 0u;

    loop_cycles = t1 - t0;
    hwc         = h1 - h0;
    instret     = i1 - i0;

    LED_REG = 0x00u;

    for (;;) {
        puts_("F5,hello,"); puts_(GIT_HASH); eol();
        puts_("F5,cycle,");  put_u32(rdcycle()); eol();
        puts_("F5,loopn,");  put_u32(LOOP_N); eol();
        puts_("F5,loop,");   put_u32(loop_cycles); eol();
        puts_("F5,hwc,");    put_u32(hwc); eol();
        puts_("F5,instret,");put_u32(instret); eol();
        puts_("F5,arith,");  put_hex32(arith_check()); eol();
        puts_("F5,ram,");    put_hex32(ram_sum()); eol();
        puts_("F5,done");    eol();

        LED_REG = 0x01u;           /* chỉ 1 LED: bật cả 6 thì quá chói */
        busy_loop(2000000u);       /* ~ 2 lệnh/vòng, nghỉ giữa hai lần in */
        LED_REG = 0x00u;
    }
    return 0;
}
