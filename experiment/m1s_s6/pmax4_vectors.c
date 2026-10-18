/* Kiểm RTL của lệnh PMAX4 bằng VECTOR NGẪU NHIÊN, theo SPEC 4.3 điều 1.
 *
 * Cùng một firmware được chạy trên HAI thứ:
 *   - Verilator (RTL thật, WITH_PMAX4=1)
 *   - ISS (plugin pipeline/cdp/iss/ext/pmax4.py — mô hình tham chiếu)
 * Nếu CRC32 của toàn bộ kết quả khớp nhau thì RTL và mô hình tham chiếu đồng nhất
 * trên đúng số vector đã chạy. Một bit lệch ở bất kỳ làn nào cũng làm CRC khác.
 *
 * Sinh toán hạng bằng xorshift32 (tất định, không cần bộ nhớ), nên hai bên chạy đúng
 * cùng dãy vector. Dãy đi qua đủ các trường hợp: cả hai làn âm, một âm một dương,
 * bằng nhau, 0x80 (−128) và 0x7F (127).
 */
#include "soc.h"

typedef unsigned int u32;

#ifndef NVEC
#define NVEC 1000000u
#endif

/* start.S xoá .bss bằng `sw` nên ranh giới .bss phải thẳng hàng 4 byte. Chương trình
 * thử này không có biến .bss nào khác, nên khai báo một biến thẳng hàng để bảo đảm
 * điều đó (và dùng nó, để trình biên dịch không xoá đi). */
static u32 sink[4] __attribute__((aligned(4)));

static inline u32 pmax4(u32 a, u32 b)
{
    u32 r;
    __asm__ (".insn r 0x0B, 2, 0, %0, %1, %2" : "=r"(r) : "r"(a), "r"(b));
    return r;
}

static void putch(char c)
{
    while (UART_STAT & UART_TX_BUSY) { }
    UART_DATA = (unsigned char)c;
}

static void puts_(const char *s) { while (*s) putch(*s++); }

static void put_hex32(u32 v)
{
    int i;
    for (i = 7; i >= 0; i--) {
        u32 d = (v >> (4 * i)) & 0xFu;
        putch((char)(d < 10 ? '0' + d : 'A' + d - 10));
    }
}

static void put_u32(u32 v)
{
    char b[11];
    int n = 0;
    if (!v) { putch('0'); return; }
    while (v) { b[n++] = (char)('0' + v % 10u); v /= 10u; }
    while (n) putch(b[--n]);
}

static u32 crc_step(u32 crc, u32 word)
{
    int k, b;
    for (k = 0; k < 4; k++) {
        crc ^= (word >> (8 * k)) & 0xFFu;
        for (b = 0; b < 8; b++)
            crc = (crc & 1u) ? ((crc >> 1) ^ 0xEDB88320u) : (crc >> 1);
    }
    return crc;
}

int main(void)
{
    u32 s = 0x12345678u, a, b, crc = 0xFFFFFFFFu, i;

    for (i = 0; i < NVEC; i++) {
        s ^= s << 13; s ^= s >> 17; s ^= s << 5; a = s;
        s ^= s << 13; s ^= s >> 17; s ^= s << 5; b = s;
        /* mỗi 64 vector, ép một trường hợp biên: làn chứa 0x80 và 0x7F */
        if ((i & 63u) == 0u) { a = 0x807F8000u; b = 0x7F80007Fu; }
        crc = crc_step(crc, pmax4(a, b));
    }
    crc ^= 0xFFFFFFFFu;
    sink[0] = crc;

    puts_("PMAX4,n,"); put_u32(NVEC); puts_("\r\n");
    puts_("PMAX4,crc,"); put_hex32(sink[0]); puts_("\r\n");
    puts_("PMAX4,done\r\n");
    for (;;) { }
    return 0;
}
