/* F8 — lệnh tùy biến DOT4 qua PCPI: kiểm đúng đắn và đo tăng tốc thật.
 *
 * Chạy TRONG CÙNG MỘT firmware cả hai bản của bài A để so sánh công bằng tuyệt đối:
 *   - bản vô hướng: giống hệt kernel bài A của F7 (nhân int8 từng phần tử)
 *   - bản DOT4    : nạp 4 byte bằng `lw` rồi một lệnh DOT4 cho 4 MAC
 * Cả hai dùng CÙNG dữ liệu (f8_data.h), nên chênh chu kỳ là do lệnh, không do dữ liệu.
 *
 * Thêm phép đo ĐỘ TRỄ của lệnh DOT4: hai vòng lặp giống hệt nhau, chỉ khác một lệnh
 * (DOT4 so với ADD thường), nên chênh chia cho số vòng là số chu kỳ phụ trội của DOT4.
 *
 * In ra UART:
 *   F8,hello,<git hash>
 *   F8,mac,<MAC bài A>,<số lệnh DOT4>
 *   F8,scalar,<cycles>,<hw_count>,<instret>,<crc hex>
 *   F8,dot4,<cycles>,<hw_count>,<instret>,<crc hex>
 *   F8,lat,<n>,<cycles vòng DOT4>,<cycles vòng ADD>
 *   F8,done
 */
#include "soc.h"
#include "f8_data.h"

#ifndef GIT_HASH
#define GIT_HASH "unknown"
#endif

#ifndef LAT_N
#define LAT_N 100000u
#endif

typedef signed char   i8;
typedef unsigned char u8;
typedef int           i32;
typedef unsigned int  u32;

/* ---------- lệnh tùy biến ---------- */
/* DOT4: opcode custom-0 = 0x0B, funct3 = 0, funct7 = 0 */
static inline i32 dot4(u32 a, u32 b)
{
    i32 r;
    __asm__ (".insn r 0x0B, 0, 0, %0, %1, %2" : "=r"(r) : "r"(a), "r"(b));
    return r;
}

/* ADD thường, viết bằng asm để hai vòng đo độ trễ có cấu trúc giống hệt nhau */
static inline i32 add_ref(u32 a, u32 b)
{
    i32 r;
    __asm__ ("add %0, %1, %2" : "=r"(r) : "r"(a), "r"(b));
    return r;
}

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

/* ---------- kết quả ---------- */
static i32 res_s[F8_NPAIR];
static i32 res_d[F8_NPAIR];
static volatile i32 sink;

/* ---------- bài A, bản vô hướng (giống hệt F7) ---------- */
static void kernel_scalar(void)
{
    int p, i;
    for (p = 0; p < F8_NPAIR; p++) {
        const i8 *a = &f8_pool[f8_off[2 * p + 0]];
        const i8 *b = &f8_pool[f8_off[2 * p + 1]];
        i32 acc = 0;
        for (i = 0; i < F8_VLEN; i++)
            acc += (i32)a[i] * (i32)b[i];
        res_s[p] = acc;
    }
}

/* ---------- bài A, bản DOT4 ---------- */
static void kernel_dot4(void)
{
    int p, i;
    for (p = 0; p < F8_NPAIR; p++) {
        const u32 *a = (const u32 *)(const void *)&f8_pool[f8_off[2 * p + 0]];
        const u32 *b = (const u32 *)(const void *)&f8_pool[f8_off[2 * p + 1]];
        i32 acc = 0;
        for (i = 0; i < F8_VLEN / 4; i++)
            acc += dot4(a[i], b[i]);
        res_d[p] = acc;
    }
}

/* ---------- độ trễ: hai vòng giống hệt, khác ĐÚNG một lệnh ----------
 *
 * Toán hạng PHẢI phụ thuộc biến đếm. Lần đầu tôi viết với toán hạng hằng số và GCC
 * nhấc cả lệnh asm ra ngoài vòng lặp (asm không volatile + đầu vào bất biến -> LICM),
 * nên hai vòng trở thành giống hệt nhau và phép đo vô nghĩa (chênh 1 chu kỳ / 100.000
 * vòng). Với `^ i` và `+ i` thì không nhấc ra được, và hai vòng vẫn có cùng số lệnh
 * chuẩn bị toán hạng, nên chênh còn lại đúng là chi phí của DOT4 so với ADD.
 */
static u32 lat_loop_dot4(u32 n)
{
    u32 t0, t1, i;
    i32 acc = 0;
    t0 = rdcycle();
    for (i = 0; i < n; i++)
        acc += dot4(0x01020304u ^ i, 0x05060708u + i);
    t1 = rdcycle();
    sink = acc;
    return t1 - t0;
}

static u32 lat_loop_add(u32 n)
{
    u32 t0, t1, i;
    i32 acc = 0;
    t0 = rdcycle();
    for (i = 0; i < n; i++)
        acc += add_ref(0x01020304u ^ i, 0x05060708u + i);
    t1 = rdcycle();
    sink = acc;
    return t1 - t0;
}

int main(void)
{
    u32 cs, hws, is_, cd, hwd, id;
    u32 crc_s, crc_d;
    u32 t0, t1, i0, i1;
    u32 lat_d, lat_a;

    LED_REG = 0x01u;

    /* ---- bản vô hướng ---- */
    HWC_CTRL = 1u;
    i0 = rdinstret();
    t0 = rdcycle();
    kernel_scalar();
    t1 = rdcycle();
    i1 = rdinstret();
    hws = HWC_VALUE;
    HWC_CTRL = 0u;
    cs = t1 - t0;
    is_ = i1 - i0;

    /* ---- bản DOT4 ---- */
    HWC_CTRL = 1u;
    i0 = rdinstret();
    t0 = rdcycle();
    kernel_dot4();
    t1 = rdcycle();
    i1 = rdinstret();
    hwd = HWC_VALUE;
    HWC_CTRL = 0u;
    cd = t1 - t0;
    id = i1 - i0;

    /* ---- độ trễ DOT4 ---- */
    lat_d = lat_loop_dot4(LAT_N);
    lat_a = lat_loop_add(LAT_N);

    /* ---- CRC32: ngoài cửa sổ đo ---- */
    crc_s = crc32_buf((const u8 *)res_s, (u32)sizeof(res_s));
    crc_d = crc32_buf((const u8 *)res_d, (u32)sizeof(res_d));

    LED_REG = 0x00u;

    for (;;) {
        puts_("F8,hello,"); puts_(GIT_HASH); eol();
        puts_("F8,mac,");   put_u32(F8_MAC_A); putch(','); put_u32(F8_NDOT4); eol();

        puts_("F8,scalar,");
        put_u32(cs);  putch(','); put_u32(hws); putch(',');
        put_u32(is_); putch(','); put_hex32(crc_s); eol();

        puts_("F8,dot4,");
        put_u32(cd);  putch(','); put_u32(hwd); putch(',');
        put_u32(id);  putch(','); put_hex32(crc_d); eol();

        puts_("F8,lat,");
        put_u32(LAT_N); putch(','); put_u32(lat_d); putch(','); put_u32(lat_a); eol();

        puts_("F8,done"); eol();

        LED_REG = 0x01u;
        busy_loop(2000000u);
        LED_REG = 0x00u;
    }
    return 0;
}
