/* ---------------------------------------------------------------------------
 * cand_b — conv1: tính ô ra 2x2 cho MỘT kênh ra, ghim 9 trọng số (hết tràn).
 * PROFILE: conv1 = 361.394 chu kỳ / 48.672 MAC; load_data 27,1% = 97.968 chu kỳ
 * = ~49.000 lệnh nạp, gấp ĐÔI 24.336 byte ảnh mà thuật toán thật cần — dấu hiệu
 * tràn thanh ghi: vòng nóng conv1 dùng 28 thanh ghi, chỉ còn 3 trống vì giữ 18
 * trọng số của 2 kênh ra, nên mỗi tap phải nạp lại 1 trọng số (2 chu kỳ/MAC).
 * Ô 2x2 x 1 kênh: 16 byte ảnh cho 36 MAC (0,89 chu kỳ nạp/MAC) với chỉ 9 w +
 * 4 acc + 4 byte ảnh = 17 thanh ghi sống, không còn gì phải tràn.
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

/* ---------- lớp 1: Conv 3x3, 1 -> 8 kênh — ô ra 2x2, một kênh ra mỗi lượt ---
 * Bốn accumulator của ô 2x2 cùng dùng 4 hàng ảnh x 4 cột: nạp 4 byte của một
 * hàng ảnh rồi bắn hết các tap mà hàng đó đóng góp (hàng y+k đóng góp tap
 * 3k..3k+2 cho ô ra hàng trên và tap 3(k-1).. cho ô ra hàng dưới). Mỗi
 * accumulator vẫn cộng bias rồi tap 0..8 theo đúng thứ tự cũ ⇒ đúng từng bit.
 * Hai ô ra hàng trên được requant và ghi xong trước khi nạp hàng ảnh thứ 4, để
 * đỉnh áp lực thanh ghi chỉ ở 9 w + 4 acc + 4 byte ảnh.
 */

/* một điểm ra đơn lẻ — chỉ dùng cho viền lẻ (M1S_OUT1 chẵn thì bị loại bỏ) */
#define CONV1_ONE(YY, XX)                                                 \
    do {                                                                  \
        const i8 *q0 = &img[(YY) * M1S_IMG + (XX)];                       \
        const i8 *q1 = q0 + M1S_IMG;                                      \
        const i8 *q2 = q1 + M1S_IMG;                                      \
        i32 e = bias;                                                     \
        e += (i32)q0[0] * w0; e += (i32)q0[1] * w1; e += (i32)q0[2] * w2;  \
        e += (i32)q1[0] * w3; e += (i32)q1[1] * w4; e += (i32)q1[2] * w5;  \
        e += (i32)q2[0] * w6; e += (i32)q2[1] * w7; e += (i32)q2[2] * w8;  \
        a1[((YY) * M1S_OUT1 + (XX)) * M1S_C1 + oc] = REQUANT1(e);         \
    } while (0)

static __attribute__((noinline)) void conv1(const i8 *img)
{
    int oc, y, x;
    for (oc = 0; oc < M1S_C1; oc++) {
        const i8 *wk = &m1s_w1[oc * 9];
        const i32 bias = m1s_b1[oc];
        const i32 w0 = wk[0], w1 = wk[1], w2 = wk[2];
        const i32 w3 = wk[3], w4 = wk[4], w5 = wk[5];
        const i32 w6 = wk[6], w7 = wk[7], w8 = wk[8];
        for (y = 0; y + 1 < M1S_OUT1; y += 2) {
            for (x = 0; x + 1 < M1S_OUT1; x += 2) {
                const i8 *r = &img[y * M1S_IMG + x];
                i8 *op = &a1[(y * M1S_OUT1 + x) * M1S_C1 + oc];
                i32 s00 = bias, s01 = bias, s10 = bias, s11 = bias;
                i32 g0, g1, g2, g3;
                /* hàng ảnh y+0: tap 0..2 của hai ô ra hàng trên */
                g0 = r[0]; g1 = r[1]; g2 = r[2]; g3 = r[3];
                s00 += g0 * w0; s00 += g1 * w1; s00 += g2 * w2;
                s01 += g1 * w0; s01 += g2 * w1; s01 += g3 * w2;
                /* hàng ảnh y+1: tap 3..5 hàng trên, tap 0..2 hàng dưới */
                r += M1S_IMG;
                g0 = r[0]; g1 = r[1]; g2 = r[2]; g3 = r[3];
                s00 += g0 * w3; s00 += g1 * w4; s00 += g2 * w5;
                s01 += g1 * w3; s01 += g2 * w4; s01 += g3 * w5;
                s10 += g0 * w0; s10 += g1 * w1; s10 += g2 * w2;
                s11 += g1 * w0; s11 += g2 * w1; s11 += g3 * w2;
                /* hàng ảnh y+2: tap 6..8 hàng trên, tap 3..5 hàng dưới */
                r += M1S_IMG;
                g0 = r[0]; g1 = r[1]; g2 = r[2]; g3 = r[3];
                s00 += g0 * w6; s00 += g1 * w7; s00 += g2 * w8;
                s01 += g1 * w6; s01 += g2 * w7; s01 += g3 * w8;
                s10 += g0 * w3; s10 += g1 * w4; s10 += g2 * w5;
                s11 += g1 * w3; s11 += g2 * w4; s11 += g3 * w5;
                op[0] = REQUANT1(s00);
                op[M1S_C1] = REQUANT1(s01);
                /* hàng ảnh y+3: tap 6..8 của hai ô ra hàng dưới */
                r += M1S_IMG;
                g0 = r[0]; g1 = r[1]; g2 = r[2]; g3 = r[3];
                s10 += g0 * w6; s10 += g1 * w7; s10 += g2 * w8;
                s11 += g1 * w6; s11 += g2 * w7; s11 += g3 * w8;
                op[M1S_OUT1 * M1S_C1] = REQUANT1(s10);
                op[M1S_OUT1 * M1S_C1 + M1S_C1] = REQUANT1(s11);
            }
            if (x < M1S_OUT1) {           /* cột lẻ cuối (OUT1 lẻ) */
                CONV1_ONE(y, x);
                CONV1_ONE(y + 1, x);
            }
        }
        if (y < M1S_OUT1) {               /* hàng lẻ cuối (OUT1 lẻ) */
            for (x = 0; x < M1S_OUT1; x++)
                CONV1_ONE(y, x);
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

/* ---------- lớp 3: Conv 3x3, 8 -> 16 kênh — chia khối 8 kênh ra (KHÔNG đổi) ---------- */
#define W2OC (9 * M1S_C1)

#define CONV2_STEP(C)                                       \
    do {                                                    \
        i32 xv = xp[(C)];                                   \
        acc0 += xv * (i32)wp[(C) + 0 * W2OC];               \
        acc1 += xv * (i32)wp[(C) + 1 * W2OC];               \
        acc2 += xv * (i32)wp[(C) + 2 * W2OC];               \
        acc3 += xv * (i32)wp[(C) + 3 * W2OC];               \
        acc4 += xv * (i32)wp[(C) + 4 * W2OC];               \
        acc5 += xv * (i32)wp[(C) + 5 * W2OC];               \
        acc6 += xv * (i32)wp[(C) + 6 * W2OC];               \
        acc7 += xv * (i32)wp[(C) + 7 * W2OC];               \
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
