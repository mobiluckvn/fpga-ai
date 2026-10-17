/* F5 — mã khởi động: đặt sp ở đỉnh RAM, xoá .bss, gọi main.
 * RAM: 0x0000_0000 .. 0x0000_FFFF (64 KB). Đỉnh ngăn xếp = 0x0001_0000.
 * PROGADDR_RESET của picorv32 = 0 nên _start phải nằm ở địa chỉ 0.
 */
    .section .text.start, "ax"
    .global _start
_start:
    /* ngăn xếp ở đỉnh RAM, thẳng hàng 16 byte */
    li      sp, 0x00010000

    /* xoá .bss */
    la      a0, __bss_start
    la      a1, __bss_end
1:  bgeu    a0, a1, 2f
    sw      zero, 0(a0)
    addi    a0, a0, 4
    j       1b
2:

    /* gọi main */
    call    main

    /* main không trả về; nếu có thì treo ở đây */
3:  j       3b
