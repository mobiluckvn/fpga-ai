/* ---------------------------------------------------------------------------
 * cand_b — conv1: đưa vòng kênh ra (oc) ra NGOÀI cùng, giữ 9 trọng số trong
 * thanh ghi, bung hẳn 3x3 bằng độ dời hằng số.
 * PROFILE: conv1 = 724.328 chu kỳ (36,6% tổng) cho chỉ 48.672 MAC ⇒ 14,9
 * chu kỳ/MAC, trong đó addr 18,8% + loop_ctrl 15,1% = 34% là phí thuần, còn
 * load_data 28,4% gồm cả 48.672 lần nạp lại trọng số. Với oc ngoài cùng, 9
 * trọng số bất biến nằm trong thanh ghi (vòng này còn 25 thanh ghi trống),
 * 9 byte ảnh đọc bằng lb với độ dời tức thì ⇒ xoá toàn bộ nạp trọng số
 * (2 chu kỳ mỗi lần) và hai vòng ky/kx (nhánh 1 chu kỳ + alu địa chỉ).
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

/* ---------- lớp 1: Conv 3x3, 1 -> 8 kênh — oc ra ngoài cùng ----------
 * Mỗi accumulator vẫn cộng theo đúng thứ tự (ky=0..2, kx=0..2) như bản gốc
 * và cùng toán hạng, nên giá trị int32 trước requant giống từng bit.
 * Con trỏ ảnh chạy 1 byte mỗi x; 9 độ dời hằng số 0,1,2, S,S+1,S+2, 2S,2S+1,
 * 2S+2 (S = M1S_IMG) nằm gọn trong trường tức thì của lb.
 * Con trỏ ra chạy đúng M1S_C1 byte mỗi x, nên không cần nhân chỉ số.
 */
static __attribute__((noinline)) void conv1(const i8 *img)
{
    int y, x, oc;
    for (oc = 0; oc < M1S_C1; oc++) {
        const i8 *w = &m1s_w1[oc * 9];
        const i32 w0 = w[0], w1 = w[1], w2 = w[2];
        const i32 w3 = w[3], w4 = w[4], w5 = w[5];
        const i32 w6 = w[6], w7 = w[7], w8 = w[8];
        const i32 bias = m1s_b1[oc];
        for (y = 0; y < M1S_OUT1; y++) {
            const i8 *p = &img[y * M1S_IMG];
            i8 *op = &a1[(y * M1S_OUT1) * M1S_C1 + oc];
            for (x = 0; x < M1S_OUT1; x++) {
                i32 acc = bias;
                acc += (i32)p[0] * w0;
                acc += (i32)p[1] * w1;
                acc += (i32)p[2] * w2;
                acc += (i32)p[M1S_IMG + 0] * w3;
                acc += (i32)p[M1S_IMG + 1] * w4;
                acc += (i32)p[M1S_IMG + 2] * w5;
                acc += (i32)p[2 * M1S_IMG + 0] * w6;
                acc += (i32)p[2 * M1S_IMG + 1] * w7;
                acc += (i32)p[2 * M1S_IMG + 2] * w8;
                *op = REQUANT1(acc);
                p += 1;
                op += M1S_C1;
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

/* ---------- lớp 3: Conv 3x3, 8 -> 16 kênh (KHÔNG đổi, để cô lập ý tưởng) ---------- */
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
                    REQUANT2(acc);
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
