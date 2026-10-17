/* F5 — khai báo ngoại vi của SoC. Bản đồ bộ nhớ: xem feasibility/F5_soc/soc.v */
#ifndef SOC_H
#define SOC_H

#define UART_DATA   (*(volatile unsigned int *)0x10000000u)
#define UART_STAT   (*(volatile unsigned int *)0x10000004u)
#define UART_TX_BUSY 0x1u
#define UART_RX_VALID 0x2u

#define HWC_CTRL    (*(volatile unsigned int *)0x10000010u)
#define HWC_VALUE   (*(volatile unsigned int *)0x10000014u)

#define LED_REG     (*(volatile unsigned int *)0x10000020u)

static inline unsigned rdcycle(void)
{
    unsigned x;
    __asm__ volatile ("rdcycle %0" : "=r"(x));
    return x;
}

static inline unsigned rdcycleh(void)
{
    unsigned x;
    __asm__ volatile ("rdcycleh %0" : "=r"(x));
    return x;
}

static inline unsigned rdinstret(void)
{
    unsigned x;
    __asm__ volatile ("rdinstret %0" : "=r"(x));
    return x;
}

/* Vòng lặp rỗng viết bằng asm cố định: ĐÚNG 2 lệnh mỗi vòng, không phụ thuộc
 * tuỳ chọn tối ưu của trình biên dịch — nhờ vậy số chu kỳ là tất định. */
static inline void busy_loop(unsigned n)
{
    __asm__ volatile (
        "1:\n"
        "  addi %0, %0, -1\n"
        "  bnez %0, 1b\n"
        : "+r"(n)
        :
        : /* không clobber */
    );
}

#endif
