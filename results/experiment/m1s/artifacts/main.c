/* M1-S — suy luận CNN int8 đầy đủ 5 lớp trên SoC PicoRV32 (Tang Nano 20K).
 *
 * Kiến trúc (channels-last, không đệm biên):
 *   Conv 3x3 1->8  + bias + ReLU + requantize -> 26x26x8    48.672 MAC
 *   MaxPool 2x2                               -> 13x13x8
 *   Conv 3x3 8->16 + bias + ReLU + requantize -> 11x11x16   139.392 MAC
 *   MaxPool 2x2                               ->  5x5x16
 *   Dense 400->10 + bias (int32) -> argmax    -> 10            4.000 MAC
 *                                                tổng        192.064 MAC
 *
 * Hai biến thể, chọn bằng cờ biên dịch:
 *   (mặc định)  A-V0: mọi lớp bằng C thẳng
 *   USE_DOT4    A-V2: conv2 và dense dùng lệnh tùy biến DOT4 (4 MAC/lệnh)
 *
 * Vì sao conv1 KHÔNG dùng DOT4: DOT4 nạp 4 byte liền nhau bằng `lw` và cần địa chỉ
 * thẳng hàng 4 byte (lõi bật CATCH_MISALIGN). Với channels-last, conv2 có Cin=8 nên
 * 4 kênh vào liền nhau luôn thẳng hàng; conv1 có Cin=1 nên không có 4 giá trị liền
 * nhau để cộng dồn mà vẫn thẳng hàng. conv1 chiếm 48.672/192.064 = 25,3 % số MAC.
 *
 * In ra UART (CSV, kết thúc \r\n):
 *   M1S,hello,<git hash>,<biến thể>
 *   M1S,img,<idx>,<nhãn>,<dự đoán>,<dự đoán golden>,<ok bitmask>
 *   M1S,cyc,<idx>,<conv1>,<pool1>,<conv2>,<pool2>,<dense>,<tổng>,<instret>
 *   M1S,crc,<idx>,<a1>,<p1>,<a2>,<p2>,<logit>
 *   M1S,sum,<số ảnh>,<số dự đoán đúng nhãn>,<số khớp golden>,<số CRC khớp hết>
 *   M1S,done
 *
 * Mỗi lớp là một hàm __attribute__((noinline)). Lý do: nếu để GCC nội suy cả 5 lớp
 * vào main (nó làm vậy ở -O2 vì mỗi hàm chỉ gọi một lần), cấp phát thanh ghi của
 * conv1 thay đổi theo việc conv2 dùng DOT4 hay không — đo thấy conv1 lệch
 * 3.803.170 so với 4.950.316 chu kỳ giữa hai biến thể dù mã nguồn y hệt. `noinline`
 * làm conv1/pool1/pool2 sinh ra mã GIỐNG HỆT ở cả hai biến thể, nên so sánh
 * A-V0 với A-V2 theo từng lớp mới công bằng.
 *
 * Chính sách LED: nhiều nhất một LED sáng.
 */
#include "soc.h"
#include "weights.h"

#ifndef GIT_HASH
#define GIT_HASH "unknown"
#endif

#ifndef RUN_IMGS
#define RUN_IMGS M1S_NIMG
#endif

#ifdef USE_DOT4
#define VARIANT "A-V2"
#else
#define VARIANT "A-V0"
#endif

typedef signed char   i8;
typedef unsigned char u8;
typedef int           i32;
typedef unsigned int  u32;
typedef long long     i64;

/* ---------- lệnh tùy biến DOT4 ---------- */
#ifdef USE_DOT4
static inline i32 dot4(u32 a, u32 b)
{
    i32 r;
    __asm__ (".insn r 0x0B, 0, 0, %0, %1, %2" : "=r"(r) : "r"(a), "r"(b));
    return r;
}
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

/* ---------- CRC32 chuẩn (zlib) ---------- */
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

/* ---------- requantize kiểu gemmlowp (khớp từng bit với golden Python) ---------- */
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

static i8 requant(i32 acc, i32 m0, int shift)
{
    i32 q;
    if (acc < 0)
        acc = 0;                      /* ReLU trên int32 */
    q = rdiv_pot(sat_rdhmul(acc, m0), shift);
    if (q > 127)
        q = 127;
    else if (q < 0)
        q = 0;
    return (i8)q;
}

/* ---------- đệm activation (channels-last), thẳng hàng 4 byte ---------- */
static i8  a1[M1S_OUT1 * M1S_OUT1 * M1S_C1]   __attribute__((aligned(4)));  /* 26x26x8  */
static i8  p1[M1S_POOL1 * M1S_POOL1 * M1S_C1] __attribute__((aligned(4)));  /* 13x13x8  */
static i8  a2[M1S_OUT2 * M1S_OUT2 * M1S_C2]   __attribute__((aligned(4)));  /* 11x11x16 */
static i8  p2[M1S_POOL2 * M1S_POOL2 * M1S_C2] __attribute__((aligned(4)));  /* 5x5x16   */
static i32 logit[M1S_NCLS];

/* ---------- lớp 1: Conv 3x3, 1 -> 8 kênh ---------- */
static __attribute__((noinline)) void conv1(const i8 *img)
{
    int y, x, oc, ky, kx;
    for (y = 0; y < M1S_OUT1; y++) {
        for (x = 0; x < M1S_OUT1; x++) {
            for (oc = 0; oc < M1S_C1; oc++) {
                i32 acc = m1s_b1[oc];
                const i8 *w = &m1s_w1[oc * 9];
                for (ky = 0; ky < 3; ky++) {
                    const i8 *row = &img[(y + ky) * M1S_IMG + x];
                    for (kx = 0; kx < 3; kx++)
                        acc += (i32)row[kx] * (i32)w[ky * 3 + kx];
                }
                a1[(y * M1S_OUT1 + x) * M1S_C1 + oc] =
                    requant(acc, M1S_M0_1, M1S_SH_1);
            }
        }
    }
}

/* ---------- lớp 2: MaxPool 2x2 trên 26x26x8 -> 13x13x8 ---------- */
static __attribute__((noinline)) void pool1(void)
{
    int y, x, c;
    for (y = 0; y < M1S_POOL1; y++) {
        for (x = 0; x < M1S_POOL1; x++) {
            for (c = 0; c < M1S_C1; c++) {
                i8 m = a1[((2 * y) * M1S_OUT1 + 2 * x) * M1S_C1 + c];
                i8 v = a1[((2 * y) * M1S_OUT1 + 2 * x + 1) * M1S_C1 + c];
                if (v > m) m = v;
                v = a1[((2 * y + 1) * M1S_OUT1 + 2 * x) * M1S_C1 + c];
                if (v > m) m = v;
                v = a1[((2 * y + 1) * M1S_OUT1 + 2 * x + 1) * M1S_C1 + c];
                if (v > m) m = v;
                p1[(y * M1S_POOL1 + x) * M1S_C1 + c] = m;
            }
        }
    }
}

/* ---------- lớp 3: Conv 3x3, 8 -> 16 kênh ---------- */
static __attribute__((noinline)) void conv2(void)
{
    int y, x, oc, ky, kx;
    for (y = 0; y < M1S_OUT2; y++) {
        for (x = 0; x < M1S_OUT2; x++) {
            for (oc = 0; oc < M1S_C2; oc++) {
                i32 acc = m1s_b2[oc];
                for (ky = 0; ky < 3; ky++) {
                    for (kx = 0; kx < 3; kx++) {
                        const i8 *xp = &p1[((y + ky) * M1S_POOL1 + (x + kx)) * M1S_C1];
                        const i8 *wp = &m1s_w2[((oc * 3 + ky) * 3 + kx) * M1S_C1];
#ifdef USE_DOT4
                        const u32 *xw = (const u32 *)(const void *)xp;
                        const u32 *ww = (const u32 *)(const void *)wp;
                        acc += dot4(xw[0], ww[0]);
                        acc += dot4(xw[1], ww[1]);
#else
                        int ic;
                        for (ic = 0; ic < M1S_C1; ic++)
                            acc += (i32)xp[ic] * (i32)wp[ic];
#endif
                    }
                }
                a2[(y * M1S_OUT2 + x) * M1S_C2 + oc] =
                    requant(acc, M1S_M0_2, M1S_SH_2);
            }
        }
    }
}

/* ---------- lớp 4: MaxPool 2x2 trên 11x11x16 -> 5x5x16 (lấy sàn) ---------- */
static __attribute__((noinline)) void pool2(void)
{
    int y, x, c;
    for (y = 0; y < M1S_POOL2; y++) {
        for (x = 0; x < M1S_POOL2; x++) {
            for (c = 0; c < M1S_C2; c++) {
                i8 m = a2[((2 * y) * M1S_OUT2 + 2 * x) * M1S_C2 + c];
                i8 v = a2[((2 * y) * M1S_OUT2 + 2 * x + 1) * M1S_C2 + c];
                if (v > m) m = v;
                v = a2[((2 * y + 1) * M1S_OUT2 + 2 * x) * M1S_C2 + c];
                if (v > m) m = v;
                v = a2[((2 * y + 1) * M1S_OUT2 + 2 * x + 1) * M1S_C2 + c];
                if (v > m) m = v;
                p2[(y * M1S_POOL2 + x) * M1S_C2 + c] = m;
            }
        }
    }
}

/* ---------- lớp 5: Dense 400 -> 10, giữ int32 ---------- */
#define NFLAT (M1S_POOL2 * M1S_POOL2 * M1S_C2)

static __attribute__((noinline)) void dense(void)
{
    int c;
    for (c = 0; c < M1S_NCLS; c++) {
        i32 acc = m1s_b3[c];
        const i8 *w = &m1s_w3[c * NFLAT];
#ifdef USE_DOT4
        const u32 *xw = (const u32 *)(const void *)p2;
        const u32 *ww = (const u32 *)(const void *)w;
        int i;
        for (i = 0; i < NFLAT / 4; i++)
            acc += dot4(xw[i], ww[i]);
#else
        int i;
        for (i = 0; i < NFLAT; i++)
            acc += (i32)p2[i] * (i32)w[i];
#endif
        logit[c] = acc;
    }
}

int main(void)
{
    u32 n_label_ok = 0, n_pred_ok = 0, n_crc_ok = 0;
    int k;

    LED_REG = 0x01u;

    for (;;) {
        n_label_ok = 0;
        n_pred_ok = 0;
        n_crc_ok = 0;

        puts_("M1S,hello,"); puts_(GIT_HASH); putch(','); puts_(VARIANT); eol();

        for (k = 0; k < RUN_IMGS; k++) {
            const i8 *img = &m1s_imgs[k * M1S_IMG * M1S_IMG];
            u32 t0, t1, i0, i1;
            u32 c_conv1, c_pool1, c_conv2, c_pool2, c_dense, c_tot, instr;
            u32 cr_a1, cr_p1, cr_a2, cr_p2, cr_lg;
            int c, best;
            i32 bestv;
            u32 okmask;

            i0 = rdinstret();
            t0 = rdcycle(); conv1(img); t1 = rdcycle(); c_conv1 = t1 - t0;
            t0 = rdcycle(); pool1();    t1 = rdcycle(); c_pool1 = t1 - t0;
            t0 = rdcycle(); conv2();    t1 = rdcycle(); c_conv2 = t1 - t0;
            t0 = rdcycle(); pool2();    t1 = rdcycle(); c_pool2 = t1 - t0;
            t0 = rdcycle(); dense();    t1 = rdcycle(); c_dense = t1 - t0;
            i1 = rdinstret();
            instr = i1 - i0;
            c_tot = c_conv1 + c_pool1 + c_conv2 + c_pool2 + c_dense;

            best = 0;
            bestv = logit[0];
            for (c = 1; c < M1S_NCLS; c++) {
                if (logit[c] > bestv) {
                    bestv = logit[c];
                    best = c;
                }
            }

            /* CRC32 ngoài cửa sổ đo */
            cr_a1 = crc32_buf((const u8 *)a1, (u32)sizeof(a1));
            cr_p1 = crc32_buf((const u8 *)p1, (u32)sizeof(p1));
            cr_a2 = crc32_buf((const u8 *)a2, (u32)sizeof(a2));
            cr_p2 = crc32_buf((const u8 *)p2, (u32)sizeof(p2));
            cr_lg = crc32_buf((const u8 *)logit, (u32)sizeof(logit));

            okmask = 0;
            if (cr_a1 == m1s_crc_a1[k])    okmask |= 1u;
            if (cr_p1 == m1s_crc_p1[k])    okmask |= 2u;
            if (cr_a2 == m1s_crc_a2[k])    okmask |= 4u;
            if (cr_p2 == m1s_crc_p2[k])    okmask |= 8u;
            if (cr_lg == m1s_crc_logit[k]) okmask |= 16u;
            if (okmask == 31u) n_crc_ok++;
            if (best == (int)m1s_pred_golden[k]) n_pred_ok++;
            if (best == (int)m1s_labels[k]) n_label_ok++;

            puts_("M1S,img,");
            put_u32((u32)k); putch(',');
            put_u32((u32)m1s_labels[k]); putch(',');
            put_u32((u32)best); putch(',');
            put_u32((u32)m1s_pred_golden[k]); putch(',');
            put_u32(okmask); eol();

            puts_("M1S,cyc,");
            put_u32((u32)k); putch(',');
            put_u32(c_conv1); putch(',');
            put_u32(c_pool1); putch(',');
            put_u32(c_conv2); putch(',');
            put_u32(c_pool2); putch(',');
            put_u32(c_dense); putch(',');
            put_u32(c_tot);   putch(',');
            put_u32(instr); eol();

            puts_("M1S,crc,");
            put_u32((u32)k); putch(',');
            put_hex32(cr_a1); putch(',');
            put_hex32(cr_p1); putch(',');
            put_hex32(cr_a2); putch(',');
            put_hex32(cr_p2); putch(',');
            put_hex32(cr_lg); eol();
        }

        puts_("M1S,sum,");
        put_u32((u32)RUN_IMGS); putch(',');
        put_u32(n_label_ok);    putch(',');
        put_u32(n_pred_ok);     putch(',');
        put_u32(n_crc_ok); eol();
        puts_("M1S,done"); eol();

        LED_REG = 0x01u;
        busy_loop(2000000u);
        LED_REG = 0x00u;
    }
    return 0;
}
