/* F7 — kernel int8 thật, đúng từng bit, chạy trên SoC của F5 (RTL không đổi).
 *
 * Bài A: 100 tích vô hướng int8 dài 1.024  -> 102.400 MAC
 * Bài B: Conv 3x3, 1 -> 8 kênh, ảnh 28x28, bias int32, ReLU, requantize gemmlowp
 *        -> 48.672 MAC, đầu ra 26x26x8 int8
 *
 * In ra UART (CSV, kết thúc \r\n):
 *   F7,hello,<git hash>
 *   F7,mac,<MAC bài A>,<MAC bài B>
 *   F7,A,<cycles>,<hw_count>,<instret>,<crc hex>
 *   F7,B,<cycles>,<hw_count>,<instret>,<crc hex>
 *   F7,done
 *
 * Hai hàm requantize (sat_rdhmul, rdiv_pot) cài ĐÚNG như gemmlowp và y hệt bản Python
 * trong scripts/gen_f7_data.py, nên kết quả khớp từng bit.
 * CRC32 tính NGOÀI cửa sổ đo, không tính vào số chu kỳ của kernel.
 *
 * Chính sách LED: nhiều nhất một LED sáng.
 */
#include "soc.h"
#include "f7_data.h"

#ifndef GIT_HASH
#define GIT_HASH "unknown"
#endif

typedef signed char        i8;
typedef unsigned char      u8;
typedef int                i32;
typedef unsigned int       u32;
typedef long long          i64;

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

static void put_u32(u32 v)
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

static void put_hex32(u32 v)
{
    int i;
    for (i = 28; i >= 0; i -= 4) {
        u32 d = (v >> i) & 0xFu;
        putch((char)(d < 10u ? ('0' + d) : ('A' + d - 10u)));
    }
}

static void eol(void) { puts_("\r\n"); }

/* ---------- CRC32 chuẩn (zlib): 0xEDB88320, init 0xFFFFFFFF, đảo cuối ---------- */
static u32 crc32_buf(const u8 *p, u32 n)
{
    u32 crc = 0xFFFFFFFFu;
    u32 i;
    int b;
    for (i = 0; i < n; i++) {
        crc ^= p[i];
        for (b = 0; b < 8; b++)
            crc = (crc & 1u) ? ((crc >> 1) ^ 0xEDB88320u) : (crc >> 1);
    }
    return crc ^ 0xFFFFFFFFu;
}

/* ---------- requantize kiểu gemmlowp ---------- */
static i32 sat_rdhmul(i32 a, i32 b)
{
    i64 ab;
    i32 nudge;
    if (a == (i32)0x80000000 && b == (i32)0x80000000)
        return 0x7FFFFFFF;
    ab = (i64)a * (i64)b;
    nudge = (ab >= 0) ? (1 << 30) : (1 - (1 << 30));
    return (i32)((ab + (i64)nudge) >> 31);
}

static i32 rdiv_pot(i32 x, int exp)
{
    i32 mask, remainder, threshold;
    if (exp == 0)
        return x;
    mask = (i32)((1u << exp) - 1u);
    remainder = x & mask;
    threshold = (mask >> 1) + (x < 0 ? 1 : 0);
    return (x >> exp) + (remainder > threshold ? 1 : 0);
}

/* ---------- đệm kết quả (.bss) ---------- */
static i32 res_a[F7_NPAIR];
static i8  res_b[F7_OCH * F7_OUT * F7_OUT];

/* ---------- bài A: tích vô hướng int8 ---------- */
static void kernel_a(void)
{
    int p, i;
    for (p = 0; p < F7_NPAIR; p++) {
        const i8 *a = &f7_pool[f7_off[2 * p + 0]];
        const i8 *b = &f7_pool[f7_off[2 * p + 1]];
        i32 acc = 0;
        for (i = 0; i < F7_VLEN; i++)
            acc += (i32)a[i] * (i32)b[i];
        res_a[p] = acc;
    }
}

/* ---------- bài B: Conv 3x3 + bias + ReLU + requantize ---------- */
static void kernel_b(void)
{
    int oc, y, x, ky, kx;
    for (oc = 0; oc < F7_OCH; oc++) {
        const i8 *w = &f7_w[oc * F7_K * F7_K];
        i32 bias = f7_bias[oc];
        for (y = 0; y < F7_OUT; y++) {
            for (x = 0; x < F7_OUT; x++) {
                i32 acc = 0;
                i32 q;
                for (ky = 0; ky < F7_K; ky++) {
                    const i8 *row = &f7_img[(y + ky) * F7_IMG + x];
                    for (kx = 0; kx < F7_K; kx++)
                        acc += (i32)row[kx] * (i32)w[ky * F7_K + kx];
                }
                acc += bias;
                if (acc < 0)
                    acc = 0;                       /* ReLU trên int32 */
                q = rdiv_pot(sat_rdhmul(acc, F7_M0), F7_SHIFT);
                if (q > 127)
                    q = 127;
                else if (q < -128)
                    q = -128;
                res_b[(oc * F7_OUT + y) * F7_OUT + x] = (i8)q;
            }
        }
    }
}

int main(void)
{
    u32 ca, hwa, ia, cb, hwb, ib;
    u32 crc_a, crc_b;
    u32 t0, t1, i0, i1;

    LED_REG = 0x01u;

    /* ---- bài A ---- */
    HWC_CTRL = 1u;
    i0 = rdinstret();
    t0 = rdcycle();
    kernel_a();
    t1 = rdcycle();
    i1 = rdinstret();
    hwa = HWC_VALUE;
    HWC_CTRL = 0u;
    ca = t1 - t0;
    ia = i1 - i0;

    /* ---- bài B ---- */
    HWC_CTRL = 1u;
    i0 = rdinstret();
    t0 = rdcycle();
    kernel_b();
    t1 = rdcycle();
    i1 = rdinstret();
    hwb = HWC_VALUE;
    HWC_CTRL = 0u;
    cb = t1 - t0;
    ib = i1 - i0;

    /* ---- CRC32: NGOÀI cửa sổ đo ---- */
    crc_a = crc32_buf((const u8 *)res_a, (u32)sizeof(res_a));
    crc_b = crc32_buf((const u8 *)res_b, (u32)sizeof(res_b));

    LED_REG = 0x00u;

    for (;;) {
        puts_("F7,hello,"); puts_(GIT_HASH); eol();
        puts_("F7,mac,");   put_u32(F7_MAC_A); putch(','); put_u32(F7_MAC_B); eol();

        puts_("F7,A,");
        put_u32(ca);  putch(',');
        put_u32(hwa); putch(',');
        put_u32(ia);  putch(',');
        put_hex32(crc_a); eol();

        puts_("F7,B,");
        put_u32(cb);  putch(',');
        put_u32(hwb); putch(',');
        put_u32(ib);  putch(',');
        put_hex32(crc_b); eol();

        puts_("F7,done"); eol();

        LED_REG = 0x01u;
        busy_loop(2000000u);
        LED_REG = 0x00u;
    }
    return 0;
}
