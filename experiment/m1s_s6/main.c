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

#define VARIANT "A-V1+DOT4+C1+REQ"

typedef signed char   i8;
typedef unsigned char u8;
typedef int           i32;
typedef unsigned int  u32;
typedef long long     i64;

/* ---------- lệnh tùy biến DOT4 ---------- */
static inline i32 dot4(u32 a, u32 b)
{
    i32 r;
    __asm__ (".insn r 0x0B, 0, 0, %0, %1, %2" : "=r"(r) : "r"(a), "r"(b));
    return r;
}

/* ---------- cộng dồn 8 kênh vào liền địa chỉ ----------
 * Dùng cho conv2 (Cin = 8, channels-last). Hai bản cho cùng một phép tính, nên
 * CRC32 của a2 phải giống nhau ở mọi biến thể.
 */
#define MAC8(XP, WP)  (dot4(((const u32 *)(const void *)(XP))[0],                  \
                            ((const u32 *)(const void *)(WP))[0])                  \
                     + dot4(((const u32 *)(const void *)(XP))[1],                  \
                            ((const u32 *)(const void *)(WP))[1]))

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

/* ---------- 5 kernel nằm ở file riêng (hạ tầng S4/B1) ----------
 * Mọi biến đổi của vòng B1 chỉ được sửa file này; phần còn lại của main.c
 * giữ nguyên để số đo so sánh được. Xem pipeline/cdp/b1/prepare.py.
 */
#include "kernels.c"



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
