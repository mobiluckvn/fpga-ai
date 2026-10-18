/* Kernel C THẲNG, tổng quát theo số kênh — không dùng lệnh tùy biến nào.
 *
 * Đây là mốc cơ sở của bước S8 (mô hình giữ lại): cùng một tệp này chạy cho M1-S
 * (C1=8, C2=16) và cho M1-L (C1=16, C2=32), mọi kích thước lấy từ weights.h. Không
 * DOT4, không REQ, không PMAX4, không bố cục 4 pha — nên nó chạy được trên MỌI cấu
 * hình, kể cả PicoRV32 gốc.
 *
 * Phép toán khớp từng bit với model/golden_m1s.py: channels-last, pool lấy sàn,
 * requantize kiểu gemmlowp.
 */

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

#define REQUANT1(ACC) requant((ACC), M1S_M0_1, M1S_SH_1)
#define REQUANT2(ACC) requant((ACC), M1S_M0_2, M1S_SH_2)

/* ---------- đệm activation (channels-last) ---------- */
static i8  a1[M1S_OUT1 * M1S_OUT1 * M1S_C1]   __attribute__((aligned(4)));
static i8  p1[M1S_POOL1 * M1S_POOL1 * M1S_C1] __attribute__((aligned(4)));
static i8  a2[M1S_OUT2 * M1S_OUT2 * M1S_C2]   __attribute__((aligned(4)));
static i8  p2[M1S_POOL2 * M1S_POOL2 * M1S_C2] __attribute__((aligned(4)));
static i32 logit[M1S_NCLS];

/* ---------- lớp 1: Conv 3x3, 1 -> C1 kênh ---------- */
static __attribute__((noinline)) void conv1(const i8 *img)
{
    int oc, y, x, ky, kx;
    for (oc = 0; oc < M1S_C1; oc++) {
        const i8 *w = &m1s_w1[oc * 9];
        const i32 bias = m1s_b1[oc];
        for (y = 0; y < M1S_OUT1; y++) {
            for (x = 0; x < M1S_OUT1; x++) {
                i32 acc = bias;
                for (ky = 0; ky < 3; ky++)
                    for (kx = 0; kx < 3; kx++)
                        acc += (i32)img[(y + ky) * M1S_IMG + (x + kx)]
                             * (i32)w[ky * 3 + kx];
                a1[(y * M1S_OUT1 + x) * M1S_C1 + oc] = REQUANT1(acc);
            }
        }
    }
}

/* ---------- lớp 2: MaxPool 2x2 ---------- */
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

/* ---------- lớp 3: Conv 3x3, C1 -> C2 kênh ---------- */
static __attribute__((noinline)) void conv2(void)
{
    int y, x, oc, ky, kx, ic;
    for (y = 0; y < M1S_OUT2; y++) {
        for (x = 0; x < M1S_OUT2; x++) {
            const i8 *base = &p1[(y * M1S_POOL1 + x) * M1S_C1];
            i8 *o = &a2[(y * M1S_OUT2 + x) * M1S_C2];
            for (oc = 0; oc < M1S_C2; oc++) {
                const i8 *w = &m1s_w2[oc * 9 * M1S_C1];
                i32 acc = m1s_b2[oc];
                for (ky = 0; ky < 3; ky++) {
                    for (kx = 0; kx < 3; kx++) {
                        const i8 *xp = base + (ky * M1S_POOL1 + kx) * M1S_C1;
                        for (ic = 0; ic < M1S_C1; ic++)
                            acc += (i32)xp[ic] * (i32)w[ic];
                        w += M1S_C1;
                    }
                }
                o[oc] = REQUANT2(acc);
            }
        }
    }
}

/* ---------- lớp 4: MaxPool 2x2 (lấy sàn) ---------- */
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

/* ---------- lớp 5: Dense NFLAT -> NCLS, giữ int32 ---------- */
#define NFLAT (M1S_POOL2 * M1S_POOL2 * M1S_C2)

static __attribute__((noinline)) void dense(void)
{
    int c, i;
    for (c = 0; c < M1S_NCLS; c++) {
        const i8 *w = &m1s_w3[c * NFLAT];
        i32 acc = m1s_b3[c];
        for (i = 0; i < NFLAT; i++)
            acc += (i32)p2[i] * (i32)w[i];
        logit[c] = acc;
    }
}
