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
 * Bốn biến thể, chọn bằng hai cờ biên dịch độc lập (bảng 2x2):
 *   (không cờ)              A-V0      : C thẳng, không lệnh tùy biến
 *   OPT_KERNELS             A-V1      : C đã tối ưu (bung vòng, con trỏ chạy, trọng số
 *                                       giữ trong thanh ghi), không lệnh tùy biến
 *   USE_DOT4                A-V2      : C thẳng + DOT4 ở conv2/dense
 *   OPT_KERNELS + USE_DOT4  A-V1+DOT4 : C tối ưu + DOT4
 * Nhờ 2x2 này mới tách được "nhanh nhờ code tốt" khỏi "nhanh nhờ lệnh tùy biến".
 *
 * Thêm một biến thể thứ năm:
 *   OPT_KERNELS + USE_DOT4 + CONV1_DOT4   A-V1+DOT4+C1
 * Nó gỡ nút cổ chai conv1 bằng BỐ CỤC, không thêm phần cứng: tạo 4 bản sao ảnh dịch
 * 0/1/2/3 byte, mỗi hàng đệm lên 32 byte, nên với mọi x luôn có một bản mà địa chỉ
 * &img[y][x] thẳng hàng 4 byte -> conv1 dùng được DOT4 (3 lệnh cho 3 hàng, tap thứ 4
 * có trọng số 0). Chi phí: 3.584 byte .bss và 3.136 byte sao chép mỗi ảnh.
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
 * Chế độ STREAM_10K: thay vì 10 ảnh nhúng sẵn, nhận ảnh qua UART để chạy ĐỦ 10.000
 * ảnh test trên kit. Khung truyền: 1 byte đồng bộ 0xA5 + 784 byte ảnh int8. Pixel
 * lượng tử hoá nằm trong [0,127] nên KHÔNG BAO GIỜ bằng 0xA5 -> nếu mất byte thì
 * khung sau tự đồng bộ lại. Kit báo CRC32 của chính 784 byte nó nhận được, nhờ vậy
 * phân biệt được "lỗi đường truyền" với "lỗi tính toán". In ra:
 *   M1S10K,hello,<git hash>,<biến thể>
 *   M1S10K,<idx>,<dự đoán>,<crc ảnh>,<crc logit>,<conv1>,<pool1>,<conv2>,<pool2>,
 *          <dense>,<tổng>,<instret>
 *
 * Chính sách LED: nhiều nhất một LED sáng.
 */
#include "soc.h"
#include "weights.h"

#ifndef GIT_HASH
#define GIT_HASH "unknown"
#endif

/* Dấu vân tay nội dung mã nguồn (main.c + weights.h). In ra để mọi số đo truy được
 * về đúng bản nguồn đã sinh ra nó. */
#ifndef SRC_HASH
#define SRC_HASH "unknown"
#endif

#ifndef RUN_IMGS
#define RUN_IMGS M1S_NIMG
#endif

#if defined(OPT_KERNELS) && defined(USE_DOT4) && defined(CONV1_DOT4)
#define VARIANT "A-V1+DOT4+C1"
#elif defined(OPT_KERNELS) && defined(USE_DOT4)
#define VARIANT "A-V1+DOT4"
#elif defined(OPT_KERNELS)
#define VARIANT "A-V1"
#elif defined(USE_DOT4)
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

/* ---------- cộng dồn 8 kênh vào liền địa chỉ ----------
 * Dùng cho conv2 (Cin = 8, channels-last). Hai bản cho cùng một phép tính, nên
 * CRC32 của a2 phải giống nhau ở mọi biến thể.
 */
#ifdef USE_DOT4
#define MAC8(XP, WP)  (dot4(((const u32 *)(const void *)(XP))[0],                  \
                            ((const u32 *)(const void *)(WP))[0])                  \
                     + dot4(((const u32 *)(const void *)(XP))[1],                  \
                            ((const u32 *)(const void *)(WP))[1]))
#else
#define MAC8(XP, WP)  ( (i32)(XP)[0] * (i32)(WP)[0] + (i32)(XP)[1] * (i32)(WP)[1]  \
                      + (i32)(XP)[2] * (i32)(WP)[2] + (i32)(XP)[3] * (i32)(WP)[3]  \
                      + (i32)(XP)[4] * (i32)(WP)[4] + (i32)(XP)[5] * (i32)(WP)[5]  \
                      + (i32)(XP)[6] * (i32)(WP)[6] + (i32)(XP)[7] * (i32)(WP)[7] )
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

#ifdef STREAM_10K
static u8 getch(void)
{
    while (!(UART_STAT & UART_RX_VALID))
        ;
    return (u8)(UART_DATA & 0xFFu);
}
#endif

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
#ifdef CONV1_DOT4
/* Bố cục 4 pha dịch để conv1 dùng được DOT4.
 *
 * ph[p][y][j] = img[y][j - p]  (j < p thì 0) với bước hàng PHS = 32 byte.
 * Vậy img[y][x] nằm ở offset (x + p); chọn p = (-x) & 3 thì (x + p) chia hết 4,
 * tức &ph[p][y][x+p] luôn thẳng hàng 4 byte. Với x <= 25 thì offset lớn nhất đọc tới
 * là (x+p)+3 <= 31 < PHS nên không tràn hàng.
 * Trọng số nhân bản thành nhóm 4 với tap thứ 4 = 0, cũng thẳng hàng 4 byte.
 * Phép toán KHÔNG đổi (tap thứ 4 nhân 0), nên CRC phải khớp golden y như các biến thể khác.
 */
#define PHS 32
static i8 ph[4][M1S_IMG * PHS] __attribute__((aligned(4)));
static i8 w1x[M1S_C1 * 3 * 4]  __attribute__((aligned(4)));   /* [oc][ky][0..3], tap3 = 0 */

static __attribute__((noinline)) void conv1_prep(const i8 *img)
{
    int p, y, x, oc, ky;
    for (p = 0; p < 4; p++) {
        for (y = 0; y < M1S_IMG; y++) {
            i8 *d = &ph[p][y * PHS];
            const i8 *s = &img[y * M1S_IMG];
            for (x = 0; x < p; x++)
                d[x] = 0;
            for (x = 0; x < M1S_IMG; x++)
                d[p + x] = s[x];
            for (x = p + M1S_IMG; x < PHS; x++)
                d[x] = 0;
        }
    }
    for (oc = 0; oc < M1S_C1; oc++) {
        for (ky = 0; ky < 3; ky++) {
            i8 *d = &w1x[(oc * 3 + ky) * 4];
            const i8 *s = &m1s_w1[oc * 9 + ky * 3];
            d[0] = s[0];
            d[1] = s[1];
            d[2] = s[2];
            d[3] = 0;
        }
    }
}

static __attribute__((noinline)) void conv1(const i8 *img)
{
    int oc, p, y, x;
    conv1_prep(img);
    for (oc = 0; oc < M1S_C1; oc++) {
        const u32 *wr = (const u32 *)(const void *)&w1x[oc * 12];
        const u32 wr0 = wr[0], wr1 = wr[1], wr2 = wr[2];
        const i32 bias = m1s_b1[oc];
        for (p = 0; p < 4; p++) {
            const int x0 = (4 - p) & 3;          /* x nhỏ nhất của pha này */
            for (y = 0; y < M1S_OUT1; y++) {
                const u32 *r = (const u32 *)(const void *)&ph[p][y * PHS + x0 + p];
                i8 *o = &a1[(y * M1S_OUT1 + x0) * M1S_C1 + oc];
                for (x = x0; x < M1S_OUT1; x += 4) {
                    i32 acc = bias
                            + dot4(r[0],            wr0)
                            + dot4(r[PHS / 4],      wr1)
                            + dot4(r[2 * (PHS / 4)], wr2);
                    *o = requant(acc, M1S_M0_1, M1S_SH_1);
                    r += 1;                       /* +4 byte = x += 4 */
                    o += 4 * M1S_C1;
                }
            }
        }
    }
}
#elif defined(OPT_KERNELS)
/* Tối ưu: vòng kênh ra ở NGOÀI nên 9 trọng số + bias nằm trong thanh ghi suốt cả mặt
 * 26x26; 9 phép nhân dùng offset HẰNG SỐ từ một con trỏ hàng duy nhất (28, 56 là
 * bước hàng của ảnh 28x28); con trỏ ra chạy đều bước 8 byte. Toán học không đổi. */
static __attribute__((noinline)) void conv1(const i8 *img)
{
    int oc, y, x;
    for (oc = 0; oc < M1S_C1; oc++) {
        const i8 *w = &m1s_w1[oc * 9];
        const i32 w0 = w[0], w1 = w[1], w2 = w[2];
        const i32 w3 = w[3], w4 = w[4], w5 = w[5];
        const i32 w6 = w[6], w7 = w[7], w8 = w[8];
        const i32 bias = m1s_b1[oc];
        i8 *o = &a1[oc];
        for (y = 0; y < M1S_OUT1; y++) {
            const i8 *r = &img[y * M1S_IMG];
            for (x = 0; x < M1S_OUT1; x++, r++, o += M1S_C1) {
                i32 acc = bias
                        + (i32)r[0]  * w0 + (i32)r[1]  * w1 + (i32)r[2]  * w2
                        + (i32)r[28] * w3 + (i32)r[29] * w4 + (i32)r[30] * w5
                        + (i32)r[56] * w6 + (i32)r[57] * w7 + (i32)r[58] * w8;
                *o = requant(acc, M1S_M0_1, M1S_SH_1);
            }
        }
    }
}
#else
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
#endif

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
#ifdef OPT_KERNELS
/* Tối ưu: bung hết 9 vị trí kernel bằng offset HẰNG SỐ từ một con trỏ gốc
 * (bước hàng của p1 là 13*8 = 104 byte), mỗi vị trí gọi MAC8 cộng dồn 8 kênh vào.
 * Toán học không đổi; chỉ bỏ phần tính chỉ số trong vòng lặp. */
static __attribute__((noinline)) void conv2(void)
{
    int y, x, oc;
    for (y = 0; y < M1S_OUT2; y++) {
        for (x = 0; x < M1S_OUT2; x++) {
            const i8 *base = &p1[(y * M1S_POOL1 + x) * M1S_C1];
            i8 *o = &a2[(y * M1S_OUT2 + x) * M1S_C2];
            for (oc = 0; oc < M1S_C2; oc++) {
                const i8 *w = &m1s_w2[oc * 9 * M1S_C1];
                i32 acc = m1s_b2[oc]
                        + MAC8(base +   0, w +  0)
                        + MAC8(base +   8, w +  8)
                        + MAC8(base +  16, w + 16)
                        + MAC8(base + 104, w + 24)
                        + MAC8(base + 112, w + 32)
                        + MAC8(base + 120, w + 40)
                        + MAC8(base + 208, w + 48)
                        + MAC8(base + 216, w + 56)
                        + MAC8(base + 224, w + 64);
                o[oc] = requant(acc, M1S_M0_2, M1S_SH_2);
            }
        }
    }
}
#else
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
                        acc += MAC8(xp, wp);
                    }
                }
                a2[(y * M1S_OUT2 + x) * M1S_C2 + oc] =
                    requant(acc, M1S_M0_2, M1S_SH_2);
            }
        }
    }
}
#endif

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

#ifdef OPT_KERNELS
/* Tối ưu: bung vòng trong theo bước 8 (400 = 50*8), con trỏ chạy. */
static __attribute__((noinline)) void dense(void)
{
    int c, i;
    for (c = 0; c < M1S_NCLS; c++) {
        const i8 *w = &m1s_w3[c * NFLAT];
        const i8 *xp = p2;
        i32 acc = m1s_b3[c];
        for (i = 0; i < NFLAT / 8; i++, xp += 8, w += 8)
            acc += MAC8(xp, w);
        logit[c] = acc;
    }
}
#else
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
#endif

#ifdef REQ_BENCH
/* Đo riêng chi phí của requantize: hai vòng giống hệt, khác đúng một thứ.
 * Toán hạng phụ thuộc biến đếm để GCC không nhấc ra ngoài vòng (bài học ở F8).
 */
static volatile i32 req_sink;

static __attribute__((noinline)) u32 bench_requant(u32 n)
{
    u32 t0, t1, i;
    i32 s = 0;
    t0 = rdcycle();
    for (i = 0; i < n; i++)
        s += requant((i32)(i * 7u + 1u), M1S_M0_1, M1S_SH_1);
    t1 = rdcycle();
    req_sink = s;
    return t1 - t0;
}

static __attribute__((noinline)) u32 bench_clamp(u32 n)
{
    u32 t0, t1, i;
    i32 s = 0;
    t0 = rdcycle();
    for (i = 0; i < n; i++) {
        i32 v = (i32)(i * 7u + 1u);
        s += (v > 127) ? 127 : v;          /* cùng cấu trúc vòng, bỏ requantize */
    }
    t1 = rdcycle();
    req_sink = s;
    return t1 - t0;
}
#endif

#ifdef STREAM_10K
/* ---------- chế độ nhận ảnh qua UART: chạy đủ 10.000 ảnh test ---------- */
#define SYNC_BYTE 0xA5u
static i8 img_buf[M1S_IMG * M1S_IMG] __attribute__((aligned(4)));
/* Con trỏ volatile: chặn GCC lan truyền hằng số địa chỉ img_buf vào conv1 (nó sẽ
 * sinh bản nhân bản conv1.constprop.0 với mã KHÁC v1dc, làm mất tính so sánh được).
 * Nhờ biến này, mã của cả 5 lớp giữ nguyên như bản v1dc đã kiểm kit = Verilator. */
static i8 *volatile img_p = img_buf;

int main(void)
{
    u32 idx = 0;

    LED_REG = 0x00u;
    puts_("M1S10K,hello,"); puts_(GIT_HASH); putch(','); puts_(VARIANT);
    putch(','); puts_(SRC_HASH); eol();

    for (;;) {
        u32 i, t0, t1, i0, i1;
        u32 c_conv1, c_pool1, c_conv2, c_pool2, c_dense, c_tot, instr;
        u32 cr_img, cr_lg;
        int c, best;
        i32 bestv;

        /* chờ byte đồng bộ (0xA5 không thể là pixel) */
        while (getch() != (u8)SYNC_BYTE)
            ;
        for (i = 0; i < (u32)sizeof(img_buf); i++)
            img_buf[i] = (i8)getch();

        LED_REG = 0x01u;
        i0 = rdinstret();
        t0 = rdcycle(); conv1(img_p);  t1 = rdcycle(); c_conv1 = t1 - t0;
        t0 = rdcycle(); pool1();        t1 = rdcycle(); c_pool1 = t1 - t0;
        t0 = rdcycle(); conv2();        t1 = rdcycle(); c_conv2 = t1 - t0;
        t0 = rdcycle(); pool2();        t1 = rdcycle(); c_pool2 = t1 - t0;
        t0 = rdcycle(); dense();        t1 = rdcycle(); c_dense = t1 - t0;
        i1 = rdinstret();
        LED_REG = 0x00u;
        instr = i1 - i0;
        c_tot = c_conv1 + c_pool1 + c_conv2 + c_pool2 + c_dense;

        best = 0;
        bestv = logit[0];
        for (c = 1; c < M1S_NCLS; c++) {
            if (logit[c] > bestv) { bestv = logit[c]; best = c; }
        }

        cr_img = crc32_buf((const u8 *)img_buf, (u32)sizeof(img_buf));
        cr_lg  = crc32_buf((const u8 *)logit,   (u32)sizeof(logit));

        puts_("M1S10K,");
        put_u32(idx);     putch(',');
        put_u32((u32)best); putch(',');
        put_hex32(cr_img); putch(',');
        put_hex32(cr_lg);  putch(',');
        put_u32(c_conv1); putch(',');
        put_u32(c_pool1); putch(',');
        put_u32(c_conv2); putch(',');
        put_u32(c_pool2); putch(',');
        put_u32(c_dense); putch(',');
        put_u32(c_tot);   putch(',');
        put_u32(instr);   eol();
        idx++;
    }
    return 0;
}
#else

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
        puts_("M1S,src,"); puts_(SRC_HASH); eol();

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

#ifdef REQ_BENCH
        {
            u32 nb = 20000u;
            u32 cr = bench_requant(nb);
            u32 cc = bench_clamp(nb);
            puts_("M1S,req,");
            put_u32(nb); putch(',');
            put_u32(cr); putch(',');
            put_u32(cc); eol();
        }
#endif
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
#endif /* STREAM_10K */
