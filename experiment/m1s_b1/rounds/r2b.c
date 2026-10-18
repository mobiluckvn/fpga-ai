/* ---------------------------------------------------------------------------
 * cand_b — conv2: tính HAI hàng ra (y, y+1) cùng lúc với khối 4 kênh ra, nên
 * mỗi byte trọng số nạp một lần dùng cho 8 MAC. PROFILE: conv2 = 792.680 chu
 * kỳ (49% của 1.612.135), 139.392 MAC ⇒ 5,69 chu kỳ/MAC, trong đó mac 53,4%
 * (= 3,04 chu kỳ/MAC: mul 2 + add 1, đã sát sàn) và load_data 40,5% ⇒ 1,13
 * lần nạp/MAC: khối 8 kênh ra hiện nạp 1 activation + 8 trọng số cho 8 MAC.
 * Ghép 2 hàng × 4 kênh còn 2 activation + 4 trọng số cho 8 MAC = 0,75 nạp/MAC
 * (load = 2 chu kỳ ⇒ bớt ~104k chu kỳ) mà VẪN chỉ 8 accumulator, đúng mức
 * thanh ghi hiện tại — vòng nóng conv2 chỉ còn 11 thanh ghi trống.
 * --------------------------------------------------------------------------- */

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

/* ---------- lệnh tùy biến REQ (nhánh B cổng B5, nhánh A cổng A-V3) ----------
 * Thay CẢ hàm requant() bằng một lệnh. funct7 mang số bit dịch, nên nó phải là
 * HẰNG SỐ lúc biên dịch — dùng hai tầng macro để bung M1S_SH_x thành chữ số.
 * Ngữ nghĩa: rd = clamp(rdiv_pot(sat_rdhmul(ReLU(rs1), rs2), funct7), 0, 127),
 * khớp từng bit với requant() ở trên.
 */
#define REQUANT1(ACC) requant((ACC), M1S_M0_1, M1S_SH_1)
#define REQUANT2(ACC) requant((ACC), M1S_M0_2, M1S_SH_2)

/* ---------- đệm activation (channels-last), thẳng hàng 4 byte ---------- */
static i8  a1[M1S_OUT1 * M1S_OUT1 * M1S_C1]   __attribute__((aligned(4)));  /* 26x26x8  */
static i8  p1[M1S_POOL1 * M1S_POOL1 * M1S_C1] __attribute__((aligned(4)));  /* 13x13x8  */
static i8  a2[M1S_OUT2 * M1S_OUT2 * M1S_C2]   __attribute__((aligned(4)));  /* 11x11x16 */
static i8  p2[M1S_POOL2 * M1S_POOL2 * M1S_C2] __attribute__((aligned(4)));  /* 5x5x16   */
static i32 logit[M1S_NCLS];

/* ---------- lớp 1: Conv 3x3, 1 -> 8 kênh (KHÔNG đổi, để cô lập ý tưởng) ---------- */
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
                    REQUANT1(acc);
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

/* ---------- lớp 3: Conv 3x3, 8 -> 16 kênh — 2 hàng ra × 4 kênh ra ----------
 * Mỗi accumulator vẫn cộng theo đúng thứ tự (ky, kx, c) như bản cũ, chỉ đan
 * xen 4 kênh ra của hai hàng ra kề nhau, nên mọi giá trị int32 giống từng bit.
 * Hai hàng ra y và y+1 dùng hàng vào (y+ky) và (y+1+ky), cách nhau P1ROW byte
 * trong p1, nên một con trỏ + một offset hằng là đủ (không thêm phép nhân).
 * W2OC = bước byte giữa hai kênh ra trong m1s_w2 (9 tap × M1S_C1).
 */
#define W2OC  (9 * M1S_C1)
#define P1ROW (M1S_POOL1 * M1S_C1)

#define CONV2_PAIR_STEP(C)                                              \
    do {                                                                \
        i32 xa = xp[(C)];                                               \
        i32 xb = xp[(C) + P1ROW];                                       \
        i32 wv;                                                         \
        wv = (i32)wp[(C) + 0 * W2OC]; s0 += xa * wv; t0 += xb * wv;     \
        wv = (i32)wp[(C) + 1 * W2OC]; s1 += xa * wv; t1 += xb * wv;     \
        wv = (i32)wp[(C) + 2 * W2OC]; s2 += xa * wv; t2 += xb * wv;     \
        wv = (i32)wp[(C) + 3 * W2OC]; s3 += xa * wv; t3 += xb * wv;     \
    } while (0)

#define CONV2_STEP(C)                                       \
    do {                                                    \
        i32 xv = xp[(C)];                                   \
        acc0 += xv * (i32)wp[(C) + 0 * W2OC];               \
        acc1 += xv * (i32)wp[(C) + 1 * W2OC];               \
        acc2 += xv * (i32)wp[(C) + 2 * W2OC];               \
        acc3 += xv * (i32)wp[(C) + 3 * W2OC];               \
    } while (0)

static __attribute__((noinline)) void conv2(void)
{
    int y, x, oc0, ky, kx;

    for (y = 0; y + 1 < M1S_OUT2; y += 2) {
        for (x = 0; x < M1S_OUT2; x++) {
            i8 *op0 = &a2[(y * M1S_OUT2 + x) * M1S_C2];
            i8 *op1 = op0 + M1S_OUT2 * M1S_C2;
            for (oc0 = 0; oc0 < M1S_C2; oc0 += 4) {
                const i8 *wb = &m1s_w2[oc0 * W2OC];
                i32 s0 = m1s_b2[oc0 + 0];
                i32 s1 = m1s_b2[oc0 + 1];
                i32 s2 = m1s_b2[oc0 + 2];
                i32 s3 = m1s_b2[oc0 + 3];
                i32 t0 = s0, t1 = s1, t2 = s2, t3 = s3;
                for (ky = 0; ky < 3; ky++) {
                    const i8 *xr = &p1[((y + ky) * M1S_POOL1 + x) * M1S_C1];
                    const i8 *wr = wb + (ky * 3) * M1S_C1;
                    for (kx = 0; kx < 3; kx++) {
                        const i8 *xp = xr + kx * M1S_C1;
                        const i8 *wp = wr + kx * M1S_C1;
                        CONV2_PAIR_STEP(0);
                        CONV2_PAIR_STEP(1);
                        CONV2_PAIR_STEP(2);
                        CONV2_PAIR_STEP(3);
                        CONV2_PAIR_STEP(4);
                        CONV2_PAIR_STEP(5);
                        CONV2_PAIR_STEP(6);
                        CONV2_PAIR_STEP(7);
                    }
                }
                op0[oc0 + 0] = REQUANT2(s0);
                op0[oc0 + 1] = REQUANT2(s1);
                op0[oc0 + 2] = REQUANT2(s2);
                op0[oc0 + 3] = REQUANT2(s3);
                op1[oc0 + 0] = REQUANT2(t0);
                op1[oc0 + 1] = REQUANT2(t1);
                op1[oc0 + 2] = REQUANT2(t2);
                op1[oc0 + 3] = REQUANT2(t3);
            }
        }
    }

    /* hàng ra lẻ còn lại (M1S_OUT2 = 11): một hàng, khối 4 kênh ra */
    for (y = (M1S_OUT2 & ~1); y < M1S_OUT2; y++) {
        for (x = 0; x < M1S_OUT2; x++) {
            i8 *op = &a2[(y * M1S_OUT2 + x) * M1S_C2];
            for (oc0 = 0; oc0 < M1S_C2; oc0 += 4) {
                const i8 *wb = &m1s_w2[oc0 * W2OC];
                i32 acc0 = m1s_b2[oc0 + 0];
                i32 acc1 = m1s_b2[oc0 + 1];
                i32 acc2 = m1s_b2[oc0 + 2];
                i32 acc3 = m1s_b2[oc0 + 3];
                for (ky = 0; ky < 3; ky++) {
                    const i8 *xr = &p1[((y + ky) * M1S_POOL1 + x) * M1S_C1];
                    const i8 *wr = wb + (ky * 3) * M1S_C1;
                    for (kx = 0; kx < 3; kx++) {
                        const i8 *xp = xr + kx * M1S_C1;
                        const i8 *wp = wr + kx * M1S_C1;
                        CONV2_STEP(0);
                        CONV2_STEP(1);
                        CONV2_STEP(2);
                        CONV2_STEP(3);
                        CONV2_STEP(4);
                        CONV2_STEP(5);
                        CONV2_STEP(6);
                        CONV2_STEP(7);
                    }
                }
                op[oc0 + 0] = REQUANT2(acc0);
                op[oc0 + 1] = REQUANT2(acc1);
                op[oc0 + 2] = REQUANT2(acc2);
                op[oc0 + 3] = REQUANT2(acc3);
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
        int i;
        for (i = 0; i < NFLAT; i++)
            acc += (i32)p2[i] * (i32)w[i];
        logit[c] = acc;
    }
}
