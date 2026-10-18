/* ---------------------------------------------------------------------------
 * cand_a — conv2: khối thanh ghi 4 kênh ra x 3 cột ra (12 accumulator sống).
 * PROFILE: conv2 = 792.680 chu kỳ (63,5% của 1.249.201) cho 139.392 MAC;
 * load_data 40,5% = 321.035 chu kỳ ~ 160.000 lệnh nạp (load = 2 chu kỳ).
 * Bản hiện tại: mỗi 8 MAC nạp 8 trọng số + 1 byte p1 = 18 chu kỳ nạp (2,25/MAC).
 * Tile 4x3: mỗi 12 MAC nạp 4 trọng số + 3 byte p1 = 14 chu kỳ nạp (1,17/MAC);
 * phần mac (mul 2 + add 1 = 3 chu kỳ/MAC) không đổi. Vòng nóng conv2 còn 11
 * thanh ghi trống nên 12 acc + 3 x + 1 w (thay 8 acc + 1 x) vẫn chưa tràn.
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

/* ---------- lớp 1: Conv 3x3, 1 -> 8 kênh — 2 kênh ra dùng chung cửa sổ (KHÔNG đổi) --- */
#define CONV1_PAIR_TAP(I, R, K)                     \
    do {                                            \
        i32 xv = (R)[(K)];                          \
        e0 += xv * wa##I;                           \
        e1 += xv * wb##I;                           \
    } while (0)

static __attribute__((noinline)) void conv1(const i8 *img)
{
    int oc, y, x;
    for (oc = 0; oc < M1S_C1; oc += 2) {
        const i8 *wa = &m1s_w1[oc * 9];
        const i8 *wb = wa + 9;
        const i32 bias0 = m1s_b1[oc + 0];
        const i32 bias1 = m1s_b1[oc + 1];
        const i32 wa0 = wa[0], wa1 = wa[1], wa2 = wa[2];
        const i32 wa3 = wa[3], wa4 = wa[4], wa5 = wa[5];
        const i32 wa6 = wa[6], wa7 = wa[7], wa8 = wa[8];
        const i32 wb0 = wb[0], wb1 = wb[1], wb2 = wb[2];
        const i32 wb3 = wb[3], wb4 = wb[4], wb5 = wb[5];
        const i32 wb6 = wb[6], wb7 = wb[7], wb8 = wb[8];
        i8 *op = &a1[oc];
        for (y = 0; y < M1S_OUT1; y++) {
            const i8 *r0 = &img[y * M1S_IMG];
            const i8 *r1 = r0 + M1S_IMG;
            const i8 *r2 = r1 + M1S_IMG;
            for (x = 0; x < M1S_OUT1; x++) {
                i32 e0 = bias0;
                i32 e1 = bias1;
                CONV1_PAIR_TAP(0, r0, 0);
                CONV1_PAIR_TAP(1, r0, 1);
                CONV1_PAIR_TAP(2, r0, 2);
                CONV1_PAIR_TAP(3, r1, 0);
                CONV1_PAIR_TAP(4, r1, 1);
                CONV1_PAIR_TAP(5, r1, 2);
                CONV1_PAIR_TAP(6, r2, 0);
                CONV1_PAIR_TAP(7, r2, 1);
                CONV1_PAIR_TAP(8, r2, 2);
                op[0] = REQUANT1(e0);
                op[1] = REQUANT1(e1);
                op += M1S_C1;
                r0++;
                r1++;
                r2++;
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

/* ---------- lớp 3: Conv 3x3, 8 -> 16 kênh — khối 4 kênh ra x 3 cột ra -------
 * Mỗi accumulator vẫn cộng bias rồi (ky,kx) = 0..8, trong mỗi tap là ic = 0..7,
 * đúng thứ tự cũ: chỉ đan xen 12 accumulator độc lập nên từng int32 giống hệt
 * từng bit. Một lần nạp trọng số dùng cho 3 cột ra, một lần nạp byte p1 dùng
 * cho 4 kênh ra; mọi lệnh nạp đều là offset hằng số từ 2 con trỏ gốc (xp, wp)
 * nên không sinh thêm lệnh addr.
 */
#define W2OC (9 * M1S_C1)

/* 4 kênh ra x 3 cột ra */
#define CONV2_T3(C)                                                            \
    do {                                                                       \
        i32 u0 = xp[(C)];                                                      \
        i32 u1 = xp[(C) + 1 * M1S_C1];                                         \
        i32 u2 = xp[(C) + 2 * M1S_C1];                                         \
        i32 wv;                                                                \
        wv = wp[(C) + 0 * W2OC]; s00 += u0 * wv; s10 += u1 * wv; s20 += u2 * wv; \
        wv = wp[(C) + 1 * W2OC]; s01 += u0 * wv; s11 += u1 * wv; s21 += u2 * wv; \
        wv = wp[(C) + 2 * W2OC]; s02 += u0 * wv; s12 += u1 * wv; s22 += u2 * wv; \
        wv = wp[(C) + 3 * W2OC]; s03 += u0 * wv; s13 += u1 * wv; s23 += u2 * wv; \
    } while (0)

/* 4 kênh ra x 2 cột ra (phần dư khi M1S_OUT2 không chia hết cho 3) */
#define CONV2_T2(C)                                                            \
    do {                                                                       \
        i32 u0 = xp[(C)];                                                      \
        i32 u1 = xp[(C) + 1 * M1S_C1];                                         \
        i32 wv;                                                                \
        wv = wp[(C) + 0 * W2OC]; s00 += u0 * wv; s10 += u1 * wv;               \
        wv = wp[(C) + 1 * W2OC]; s01 += u0 * wv; s11 += u1 * wv;               \
        wv = wp[(C) + 2 * W2OC]; s02 += u0 * wv; s12 += u1 * wv;               \
        wv = wp[(C) + 3 * W2OC]; s03 += u0 * wv; s13 += u1 * wv;               \
    } while (0)

/* 4 kênh ra x 1 cột ra (phần dư) */
#define CONV2_T1(C)                                                            \
    do {                                                                       \
        i32 u0 = xp[(C)];                                                      \
        s00 += u0 * (i32)wp[(C) + 0 * W2OC];                                   \
        s01 += u0 * (i32)wp[(C) + 1 * W2OC];                                   \
        s02 += u0 * (i32)wp[(C) + 2 * W2OC];                                   \
        s03 += u0 * (i32)wp[(C) + 3 * W2OC];                                   \
    } while (0)

#define CONV2_TAPS(MAC)                                                        \
    do {                                                                       \
        int ky, kx;                                                            \
        for (ky = 0; ky < 3; ky++) {                                           \
            const i8 *xr = xb + ky * (M1S_POOL1 * M1S_C1);                     \
            const i8 *wr = wb + ky * (3 * M1S_C1);                             \
            for (kx = 0; kx < 3; kx++) {                                       \
                const i8 *xp = xr + kx * M1S_C1;                               \
                const i8 *wp = wr + kx * M1S_C1;                               \
                MAC(0); MAC(1); MAC(2); MAC(3);                                \
                MAC(4); MAC(5); MAC(6); MAC(7);                                \
            }                                                                  \
        }                                                                      \
    } while (0)

static void conv2_tile3(const i8 *xb, const i8 *wb, const i32 *bp, i8 *op)
{
    i32 s00 = bp[0], s01 = bp[1], s02 = bp[2], s03 = bp[3];
    i32 s10 = bp[0], s11 = bp[1], s12 = bp[2], s13 = bp[3];
    i32 s20 = bp[0], s21 = bp[1], s22 = bp[2], s23 = bp[3];
    CONV2_TAPS(CONV2_T3);
    op[0] = REQUANT2(s00);
    op[1] = REQUANT2(s01);
    op[2] = REQUANT2(s02);
    op[3] = REQUANT2(s03);
    op[1 * M1S_C2 + 0] = REQUANT2(s10);
    op[1 * M1S_C2 + 1] = REQUANT2(s11);
    op[1 * M1S_C2 + 2] = REQUANT2(s12);
    op[1 * M1S_C2 + 3] = REQUANT2(s13);
    op[2 * M1S_C2 + 0] = REQUANT2(s20);
    op[2 * M1S_C2 + 1] = REQUANT2(s21);
    op[2 * M1S_C2 + 2] = REQUANT2(s22);
    op[2 * M1S_C2 + 3] = REQUANT2(s23);
}

static void conv2_tile2(const i8 *xb, const i8 *wb, const i32 *bp, i8 *op)
{
    i32 s00 = bp[0], s01 = bp[1], s02 = bp[2], s03 = bp[3];
    i32 s10 = bp[0], s11 = bp[1], s12 = bp[2], s13 = bp[3];
    CONV2_TAPS(CONV2_T2);
    op[0] = REQUANT2(s00);
    op[1] = REQUANT2(s01);
    op[2] = REQUANT2(s02);
    op[3] = REQUANT2(s03);
    op[1 * M1S_C2 + 0] = REQUANT2(s10);
    op[1 * M1S_C2 + 1] = REQUANT2(s11);
    op[1 * M1S_C2 + 2] = REQUANT2(s12);
    op[1 * M1S_C2 + 3] = REQUANT2(s13);
}

static void conv2_tile1(const i8 *xb, const i8 *wb, const i32 *bp, i8 *op)
{
    i32 s00 = bp[0], s01 = bp[1], s02 = bp[2], s03 = bp[3];
    CONV2_TAPS(CONV2_T1);
    op[0] = REQUANT2(s00);
    op[1] = REQUANT2(s01);
    op[2] = REQUANT2(s02);
    op[3] = REQUANT2(s03);
}

static __attribute__((noinline)) void conv2(void)
{
    int y, x, oc0;
    for (y = 0; y < M1S_OUT2; y++) {
        const i8 *xrow = &p1[(y * M1S_POOL1) * M1S_C1];
        i8 *orow = &a2[(y * M1S_OUT2) * M1S_C2];
        for (oc0 = 0; oc0 < M1S_C2; oc0 += 4) {
            const i8 *wb = &m1s_w2[oc0 * W2OC];
            const i32 *bp = &m1s_b2[oc0];
            i8 *ob = orow + oc0;
            for (x = 0; x + 2 < M1S_OUT2; x += 3)
                conv2_tile3(xrow + x * M1S_C1, wb, bp, ob + x * M1S_C2);
            if (x + 1 < M1S_OUT2) {
                conv2_tile2(xrow + x * M1S_C1, wb, bp, ob + x * M1S_C2);
                x += 2;
            }
            if (x < M1S_OUT2)
                conv2_tile1(xrow + x * M1S_C1, wb, bp, ob + x * M1S_C2);
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
