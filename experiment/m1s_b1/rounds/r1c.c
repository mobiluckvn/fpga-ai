/* ---------------------------------------------------------------------------
 * cand_c — conv2: chia khối 2 CHIỀU, 4 kênh ra × 2 cột ra cùng lúc (8 acc).
 * PROFILE: conv2 = 1.159.242 chu kỳ, load_data 49,5% + mac 36,4%; mỗi MAC
 * hiện tốn 2 load (2+2 chu kỳ) + mul (2) + add (1) = 8,32 chu kỳ/MAC.
 * Chặn theo kênh ra tái dùng activation, chặn theo cột ra tái dùng trọng số:
 * mỗi 8 MAC chỉ còn 2 load activation + 4 load trọng số = 12 chu kỳ load
 * thay vì 32, tức ~4,5 chu kỳ/MAC — thấp hơn cả chặn 1 chiều.
 * Vòng nóng conv2 còn 22 thanh ghi trống: 8 acc + 2 activation + 1 trọng số
 * + 2 con trỏ vẫn dưới mức tràn, và mọi độ dời (≤ 3*72+7) nằm trong lb.
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

/* ---------- lớp 3: Conv 3x3, 8 -> 16 kênh — chặn 4 kênh ra × 2 cột ra ----------
 * q a0..a3 là 4 kênh ra của cột x, qb0..qb3 là CÙNG 4 kênh ra của cột x+1.
 * Mỗi trọng số nạp một lần dùng cho 2 cột; mỗi byte activation nạp một lần
 * dùng cho 4 kênh ra. Thứ tự cộng dồn của từng accumulator vẫn là (ky,kx,c)
 * với cùng toán hạng như MAC8 cũ ⇒ int32 trước requant giống từng bit.
 * Cột cuối (M1S_OUT2 lẻ) đi theo nhánh đuôi, chỉ chặn theo kênh ra.
 */
#define W2OC (9 * M1S_C1)

#define C2_PAIR(C)                                              \
    do {                                                        \
        i32 xa = xp[(C)];                                       \
        i32 xb = xp[(C) + M1S_C1];                              \
        i32 wv;                                                 \
        wv = wp[(C) + 0 * W2OC]; qa0 += xa * wv; qb0 += xb * wv; \
        wv = wp[(C) + 1 * W2OC]; qa1 += xa * wv; qb1 += xb * wv; \
        wv = wp[(C) + 2 * W2OC]; qa2 += xa * wv; qb2 += xb * wv; \
        wv = wp[(C) + 3 * W2OC]; qa3 += xa * wv; qb3 += xb * wv; \
    } while (0)

#define C2_ONE(C)                                               \
    do {                                                        \
        i32 xa = xp[(C)];                                       \
        qa0 += xa * (i32)wp[(C) + 0 * W2OC];                    \
        qa1 += xa * (i32)wp[(C) + 1 * W2OC];                    \
        qa2 += xa * (i32)wp[(C) + 2 * W2OC];                    \
        qa3 += xa * (i32)wp[(C) + 3 * W2OC];                    \
    } while (0)

#define C2_UNROLL8(MAC)                                         \
    do { MAC(0); MAC(1); MAC(2); MAC(3);                        \
         MAC(4); MAC(5); MAC(6); MAC(7); } while (0)

static __attribute__((noinline)) void conv2(void)
{
    int y, x, oc0, ky, kx;
    for (y = 0; y < M1S_OUT2; y++) {
        for (x = 0; x + 1 < M1S_OUT2; x += 2) {
            i8 *op = &a2[(y * M1S_OUT2 + x) * M1S_C2];
            for (oc0 = 0; oc0 < M1S_C2; oc0 += 4) {
                const i8 *wb = &m1s_w2[oc0 * W2OC];
                i32 qa0 = m1s_b2[oc0 + 0], qb0 = qa0;
                i32 qa1 = m1s_b2[oc0 + 1], qb1 = qa1;
                i32 qa2 = m1s_b2[oc0 + 2], qb2 = qa2;
                i32 qa3 = m1s_b2[oc0 + 3], qb3 = qa3;
                for (ky = 0; ky < 3; ky++) {
                    const i8 *xr = &p1[((y + ky) * M1S_POOL1 + x) * M1S_C1];
                    const i8 *wr = wb + (ky * 3) * M1S_C1;
                    for (kx = 0; kx < 3; kx++) {
                        const i8 *xp = xr + kx * M1S_C1;
                        const i8 *wp = wr + kx * M1S_C1;
                        C2_UNROLL8(C2_PAIR);
                    }
                }
                op[oc0 + 0] = REQUANT2(qa0);
                op[oc0 + 1] = REQUANT2(qa1);
                op[oc0 + 2] = REQUANT2(qa2);
                op[oc0 + 3] = REQUANT2(qa3);
                op[M1S_C2 + oc0 + 0] = REQUANT2(qb0);
                op[M1S_C2 + oc0 + 1] = REQUANT2(qb1);
                op[M1S_C2 + oc0 + 2] = REQUANT2(qb2);
                op[M1S_C2 + oc0 + 3] = REQUANT2(qb3);
            }
        }
        for (; x < M1S_OUT2; x++) {
            i8 *op = &a2[(y * M1S_OUT2 + x) * M1S_C2];
            for (oc0 = 0; oc0 < M1S_C2; oc0 += 4) {
                const i8 *wb = &m1s_w2[oc0 * W2OC];
                i32 qa0 = m1s_b2[oc0 + 0];
                i32 qa1 = m1s_b2[oc0 + 1];
                i32 qa2 = m1s_b2[oc0 + 2];
                i32 qa3 = m1s_b2[oc0 + 3];
                for (ky = 0; ky < 3; ky++) {
                    const i8 *xr = &p1[((y + ky) * M1S_POOL1 + x) * M1S_C1];
                    const i8 *wr = wb + (ky * 3) * M1S_C1;
                    for (kx = 0; kx < 3; kx++) {
                        const i8 *xp = xr + kx * M1S_C1;
                        const i8 *wp = wr + kx * M1S_C1;
                        C2_UNROLL8(C2_ONE);
                    }
                }
                op[oc0 + 0] = REQUANT2(qa0);
                op[oc0 + 1] = REQUANT2(qa1);
                op[oc0 + 2] = REQUANT2(qa2);
                op[oc0 + 3] = REQUANT2(qa3);
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
