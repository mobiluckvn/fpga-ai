/* Môi trường chạy riscv-tests rút gọn (theo cách picorv32/tests làm).
 * Mỗi bài kiểm là MỘT chương trình riêng: _start -> mytest -> mytest_ret.
 *   RVTEST_PASS (trong riscv_test.h) in "<tên bài>..OK\n" rồi nhảy tới mytest_ret
 *   RVTEST_FAIL in "...ERROR\n" rồi ebreak  -> harness thấy trap = KHÔNG ĐẠT
 * mytest_ret in "DONE\n" làm mốc kết thúc để harness dừng mô phỏng.
 * UART ghi tại 0x10000000, đúng bản đồ bộ nhớ của soc.v (F5).
 */
    .section .text.start
    .global _start
_start:
#ifndef STACK_TOP
#define STACK_TOP 0x00010000
#endif
    li      sp, STACK_TOP
    jal     ra, mytest

    .global mytest_ret
mytest_ret:
    li      a0, 0x10000000
    li      a1, 'D'
    sw      a1, 0(a0)
    li      a1, 'O'
    sw      a1, 0(a0)
    li      a1, 'N'
    sw      a1, 0(a0)
    li      a1, 'E'
    sw      a1, 0(a0)
    li      a1, '\n'
    sw      a1, 0(a0)
1:  j       1b
