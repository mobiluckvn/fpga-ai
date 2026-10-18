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
#define REQ_STR_(x) #x
#define REQ_STR(x)  REQ_STR_(x)
#define REQ_INSN(ACC, M0, SH) ({                                              \
    i32 _rq;                                                                  \
    __asm__ (".insn r 0x0B, 1, " REQ_STR(SH) ", %0, %1, %2"                   \
             : "=r"(_rq) : "r"(ACC), "r"(M0));                                \
    _rq; })
#define REQUANT1(ACC) ((i8)REQ_INSN((ACC), M1S_M0_1, M1S_SH_1))
#define REQUANT2(ACC) ((i8)REQ_INSN((ACC), M1S_M0_2, M1S_SH_2))

/* ---------- đệm activation (channels-last), thẳng hàng 4 byte ---------- */
static i8  a1[M1S_OUT1 * M1S_OUT1 * M1S_C1]   __attribute__((aligned(4)));  /* 26x26x8  */
static i8  p1[M1S_POOL1 * M1S_POOL1 * M1S_C1] __attribute__((aligned(4)));  /* 13x13x8  */
static i8  a2[M1S_OUT2 * M1S_OUT2 * M1S_C2]   __attribute__((aligned(4)));  /* 11x11x16 */
static i8  p2[M1S_POOL2 * M1S_POOL2 * M1S_C2] __attribute__((aligned(4)));  /* 5x5x16   */
static i32 logit[M1S_NCLS];

/* ---------- lớp 1: Conv 3x3, 1 -> 8 kênh ---------- */
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
                    *o = REQUANT1(acc);
                    r += 1;                       /* +4 byte = x += 4 */
                    o += 4 * M1S_C1;
                }
            }
        }
    }
}

/* ---------- lớp 2: MaxPool 2x2 trên 26x26x8 -> 13x13x8 ---------- */
/* ---------- lệnh tùy biến PMAX4 (ứng viên do bước S5 sinh ra) ----------
 * custom-0, funct3 = 010, funct7 = 0000000
 *   rd[i] = max( (int8)rs1[i], (int8)rs2[i] )   cho i = 0..3
 * Ngữ nghĩa tham chiếu: pipeline/cdp/iss/ext/pmax4.py; RTL: rtl/mycore/mycore.v
 * (tham số WITH_PMAX4).
 */
static inline u32 pmax4(u32 a, u32 b)
{
    u32 r;
    __asm__ (".insn r 0x0B, 2, 0, %0, %1, %2" : "=r"(r) : "r"(a), "r"(b));
    return r;
}

static __attribute__((noinline)) void pool1(void)
{
    /* Max-pool 2x2 bằng PMAX4: activation là channels-last nên 4 KÊNH liền địa chỉ
     * gói đúng vào một từ 32 bit. Một điểm ảnh chiếm M1S_C1/4 từ, nên điểm (2y,2x+1)
     * nằm cách điểm (2y,2x) đúng M1S_C1/4 từ. Mọi địa chỉ đều thẳng hàng 4 byte vì
     * (y*OUT1 + x) * C1 luôn chia hết 4 (C1 = 8).
     *
     * `max` có tính kết hợp nên gộp theo cây cho CÙNG giá trị với vòng tuần tự của bản
     * gốc; cách phá thế bằng nhau không ảnh hưởng vì ta chỉ lưu GIÁ TRỊ. Do đó CRC phải
     * khớp golden y nguyên.
     */
    enum { WPP = M1S_C1 / 4 };          /* số từ mỗi điểm ảnh */
    int y, x, c;
    for (y = 0; y < M1S_POOL1; y++) {
        for (x = 0; x < M1S_POOL1; x++) {
            const u32 *r0 = (const u32 *)(const void *)
                            &a1[((2 * y) * M1S_OUT1 + 2 * x) * M1S_C1];
            const u32 *r1 = (const u32 *)(const void *)
                            &a1[((2 * y + 1) * M1S_OUT1 + 2 * x) * M1S_C1];
            u32 *o = (u32 *)(void *)&p1[(y * M1S_POOL1 + x) * M1S_C1];
            for (c = 0; c < WPP; c++)
                o[c] = pmax4(pmax4(r0[c], r0[c + WPP]),
                             pmax4(r1[c], r1[c + WPP]));
        }
    }
}

/* ---------- lớp 3: Conv 3x3, 8 -> 16 kênh ---------- */
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
                o[oc] = REQUANT2(acc);
            }
        }
    }
}

/* ---------- lớp 4: MaxPool 2x2 trên 11x11x16 -> 5x5x16 (lấy sàn) ---------- */
static __attribute__((noinline)) void pool2(void)
{
    /* Như pool1, với C2 = 16 -> 4 từ mỗi điểm ảnh. */
    enum { WPP2 = M1S_C2 / 4 };
    int y, x, c;
    for (y = 0; y < M1S_POOL2; y++) {
        for (x = 0; x < M1S_POOL2; x++) {
            const u32 *r0 = (const u32 *)(const void *)
                            &a2[((2 * y) * M1S_OUT2 + 2 * x) * M1S_C2];
            const u32 *r1 = (const u32 *)(const void *)
                            &a2[((2 * y + 1) * M1S_OUT2 + 2 * x) * M1S_C2];
            u32 *o = (u32 *)(void *)&p2[(y * M1S_POOL2 + x) * M1S_C2];
            for (c = 0; c < WPP2; c++)
                o[c] = pmax4(pmax4(r0[c], r0[c + WPP2]),
                             pmax4(r1[c], r1[c + WPP2]));
        }
    }
}

/* ---------- lớp 5: Dense 400 -> 10, giữ int32 ---------- */
#define NFLAT (M1S_POOL2 * M1S_POOL2 * M1S_C2)

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

