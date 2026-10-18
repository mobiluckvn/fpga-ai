/* ---------------------------------------------------------------------------
 * cand_a — PHU THUOC DU LIEU DAU VAO. conv1: bo qua ca cap MAC khi byte anh
 * bang 0 (anh int8 co zero_point = 0 vi requant() clamp ve [0,127]; nen vung
 * nen cua anh la 0). PROFILE: conv1 = 361.394 chu ky (37,9% cua 954.673), mac
 * 47,1% = 170.217 chu ky tren 24.336 lan lay tap (moi lan 2 kenh ra) ~ 7,0
 * chu ky/lan = 2 mul (2 chu ky) + 2 add (1 chu ky). Mot bnez ton 1 chu ky
 * (branch_taken = branch_nt = 1) de bo 6 chu ky -> hoa von o 1/6 = 17% so 0.
 * Khong them bien song dai nao, nen 3 thanh ghi con trong cua vong conv1 van du.
 * Cong xv*w voi xv = 0 khong doi mot bit nao; conv2 giu nguyen.
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

#define REQUANT1(ACC) requant((ACC), M1S_M0_1, M1S_SH_1)
#define REQUANT2(ACC) requant((ACC), M1S_M0_2, M1S_SH_2)

/* ---------- đệm activation (channels-last), thẳng hàng 4 byte ---------- */
static i8  a1[M1S_OUT1 * M1S_OUT1 * M1S_C1]   __attribute__((aligned(4)));  /* 26x26x8  */
static i8  p1[M1S_POOL1 * M1S_POOL1 * M1S_C1] __attribute__((aligned(4)));  /* 13x13x8  */
static i8  a2[M1S_OUT2 * M1S_OUT2 * M1S_C2]   __attribute__((aligned(4)));  /* 11x11x16 */
static i8  p2[M1S_POOL2 * M1S_POOL2 * M1S_C2] __attribute__((aligned(4)));  /* 5x5x16   */
static i32 logit[M1S_NCLS];

/* ---------- lớp 1: Conv 3x3, 1 -> 8 kênh — 2 kênh ra dùng chung cửa sổ ------
 * Giống bản hiện tại hoàn toàn, chỉ thêm một lệnh nhảy: nếu byte ảnh bằng 0
 * thì hai phép nhân và hai phép cộng của nó là vô nghĩa (cộng 0) nên nhảy qua.
 * Thứ tự cộng dồn của từng accumulator không đổi -> đúng từng bit.
 */
#define CONV1_PAIR_TAP(I, R, K)                     \
    do {                                            \
        i32 xv = (R)[(K)];                          \
        if (xv != 0) {                              \
            e0 += xv * wa##I;                       \
            e1 += xv * wb##I;                       \
        }                                           \
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

/* ---------- lớp 3: Conv 3x3, 8 -> 16 kênh — giữ nguyên bản hiện tại ---------- */
#define W2OC (9 * M1S_C1)

#define CONV2_STEP(C)                                       \
    do {                                                    \
        i32 xv = xp[(C)];                                   \
        if (xv != 0) {                                      \
            acc0 += xv * (i32)wp[(C) + 0 * W2OC];           \
            acc1 += xv * (i32)wp[(C) + 1 * W2OC];           \
            acc2 += xv * (i32)wp[(C) + 2 * W2OC];           \
            acc3 += xv * (i32)wp[(C) + 3 * W2OC];           \
            acc4 += xv * (i32)wp[(C) + 4 * W2OC];           \
            acc5 += xv * (i32)wp[(C) + 5 * W2OC];           \
            acc6 += xv * (i32)wp[(C) + 6 * W2OC];           \
            acc7 += xv * (i32)wp[(C) + 7 * W2OC];           \
        }                                                   \
    } while (0)

static __attribute__((noinline)) void conv2(void)
{
    int y, x, oc0, ky, kx;
    for (y = 0; y < M1S_OUT2; y++) {
        for (x = 0; x < M1S_OUT2; x++) {
            i8 *op = &a2[(y * M1S_OUT2 + x) * M1S_C2];
            for (oc0 = 0; oc0 < M1S_C2; oc0 += 8) {
                const i8 *wb = &m1s_w2[oc0 * W2OC];
                i32 acc0 = m1s_b2[oc0 + 0];
                i32 acc1 = m1s_b2[oc0 + 1];
                i32 acc2 = m1s_b2[oc0 + 2];
                i32 acc3 = m1s_b2[oc0 + 3];
                i32 acc4 = m1s_b2[oc0 + 4];
                i32 acc5 = m1s_b2[oc0 + 5];
                i32 acc6 = m1s_b2[oc0 + 6];
                i32 acc7 = m1s_b2[oc0 + 7];
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
                op[oc0 + 4] = REQUANT2(acc4);
                op[oc0 + 5] = REQUANT2(acc5);
                op[oc0 + 6] = REQUANT2(acc6);
                op[oc0 + 7] = REQUANT2(acc7);
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
