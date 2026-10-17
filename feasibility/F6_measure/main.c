/* F6 — kiểm độ tin cậy của phép đo chu kỳ, chạy trên SoC của F5 (không đổi RTL).
 *
 * In ra UART (CSV, kết thúc \r\n):
 *   F6,cal,<delta>,<số lần>     — hiệu chuẩn: đo rdcycle hai lần liên tiếp CAL_N lần,
 *                                 in từng giá trị delta khác nhau kèm số lần xuất hiện.
 *                                 Kỳ vọng: CHỈ MỘT giá trị duy nhất.
 *   F6,len,<N>,<mcycle>,<hwc>,<instret>
 *                               — cùng một đoạn busy_loop(N) đo đồng thời bằng rdcycle,
 *                                 bộ đếm phần cứng và rdinstret. Kỳ vọng: hwc − mcycle
 *                                 là HẰNG SỐ ở mọi N.
 *   F6,done
 *   F6,hi,<h0>,<h1>,<c0>,<c1>,<vòng>
 *                               — chạy MỘT LẦN sau HI_AFTER khối in: vòng lặp vượt 2^32 chu kỳ
 *                                 (~166 s @27 MHz) để xác nhận rdcycleh tăng.
 *
 * Verilator dừng ở "F6,done" nên không phải mô phỏng phần rdcycleh dài.
 *
 * CHÍNH SÁCH LED: nhiều nhất MỘT LED sáng, và tắt hết khi rảnh. Bật cả 6 LED thì
 * quá chói khi ngồi cạnh kit (người dùng đã phản hồi ở F6).
 */
#include "soc.h"

#ifndef GIT_HASH
#define GIT_HASH "unknown"
#endif

#ifndef CAL_N
#define CAL_N 1000u
#endif

/* số vòng để vượt 2^32 chu kỳ: ~14 chu kỳ/vòng -> 320e6 vòng ≈ 4,48e9 chu kỳ */
#ifndef HI_N
#define HI_N 320000000u
#endif

/* số khối in trước khi chạy bài rdcycleh dài */
#ifndef HI_AFTER
#define HI_AFTER 5u
#endif

#define NLEN 5
#define NBUCKET 16

static const unsigned lengths[NLEN] = { 10u, 100u, 1000u, 10000u, 100000u };

static unsigned res_mcycle[NLEN];
static unsigned res_hwc[NLEN];
static unsigned res_instret[NLEN];

static unsigned cal_val[NBUCKET];
static unsigned cal_cnt[NBUCKET];
static unsigned cal_used;
static unsigned cal_overflow;

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

static void put_u32(unsigned v)
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

static void eol(void) { puts_("\r\n"); }

/* ---------- hiệu chuẩn: rdcycle hai lần liên tiếp ---------- */
static void calibrate(void)
{
    unsigned k, j;

    cal_used = 0;
    cal_overflow = 0;

    for (k = 0; k < CAL_N; k++) {
        unsigned t0 = rdcycle();
        unsigned t1 = rdcycle();
        unsigned d  = t1 - t0;

        for (j = 0; j < cal_used; j++) {
            if (cal_val[j] == d) {
                cal_cnt[j]++;
                break;
            }
        }
        if (j == cal_used) {
            if (cal_used < NBUCKET) {
                cal_val[cal_used] = d;
                cal_cnt[cal_used] = 1u;
                cal_used++;
            } else {
                cal_overflow++;
            }
        }
    }
}

/* ---------- đo một độ dài ---------- */
static void measure(unsigned idx)
{
    unsigned i0, i1, t0, t1, h1;
    unsigned n = lengths[idx];

    HWC_CTRL = 1u;            /* xoá và chạy */
    i0 = rdinstret();
    t0 = rdcycle();
    busy_loop(n);
    t1 = rdcycle();
    i1 = rdinstret();
    h1 = HWC_VALUE;
    HWC_CTRL = 0u;            /* dừng */

    res_mcycle[idx]  = t1 - t0;
    res_hwc[idx]     = h1;
    res_instret[idx] = i1 - i0;
}

int main(void)
{
    unsigned i;
    unsigned hi_h0 = 0, hi_h1 = 0, hi_c0 = 0, hi_c1 = 0;
    unsigned hi_done = 0;
    unsigned blocks  = 0;

    LED_REG = 0x01u;   /* chỉ 1 LED, tắt ngay sau khi đo xong */

    calibrate();
    for (i = 0; i < NLEN; i++)
        measure(i);

    LED_REG = 0x00u;

    for (;;) {
        puts_("F6,hello,"); puts_(GIT_HASH); eol();
        for (i = 0; i < cal_used; i++) {
            puts_("F6,cal,");
            put_u32(cal_val[i]); putch(',');
            put_u32(cal_cnt[i]); eol();
        }
        if (cal_overflow) {
            puts_("F6,calovf,"); put_u32(cal_overflow); eol();
        }
        for (i = 0; i < NLEN; i++) {
            puts_("F6,len,");
            put_u32(lengths[i]);    putch(',');
            put_u32(res_mcycle[i]); putch(',');
            put_u32(res_hwc[i]);    putch(',');
            put_u32(res_instret[i]);eol();
        }
        if (hi_done) {
            puts_("F6,hi,");
            put_u32(hi_h0); putch(',');
            put_u32(hi_h1); putch(',');
            put_u32(hi_c0); putch(',');
            put_u32(hi_c1); putch(',');
            put_u32(HI_N);  eol();
        }
        puts_("F6,done"); eol();
        blocks++;

        /* Bài rdcycleh chạy MỘT LẦN và chỉ sau HI_AFTER khối in, để mỗi lần bật nguồn
         * host đọc được số đo ngay mà không phải chờ ~166 s. */
        if (!hi_done && blocks >= HI_AFTER) {
            /* chạy một lần: vòng lặp vượt 2^32 chu kỳ để kiểm rdcycleh */
            LED_REG = 0x01u;
            hi_h0 = rdcycleh();
            hi_c0 = rdcycle();
            busy_loop(HI_N);
            hi_c1 = rdcycle();
            hi_h1 = rdcycleh();
            hi_done = 1u;
            LED_REG = 0x00u;
        } else {
            busy_loop(2000000u);   /* nghỉ giữa hai lần in */
        }
    }
    return 0;
}
