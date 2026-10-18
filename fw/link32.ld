/* S7 — biến thể RAM 32 KB cho cấu hình bộ nhớ HAI CỔNG (DUAL_PORT=1).
 *
 * Lý do 32 KB: chế độ hai cổng của BSRAM GW2AR mất một nửa mật độ mỗi khối, nên
 * 64 KB hai cổng cần 64 khối trong khi chip chỉ có 46; 32 KB hai cổng cần đúng 32
 * khối — bằng số khối thiết kế một cổng đang dùng. Số đo:
 * results/pipeline/S6/kha_thi_BONHO2CONG.md.
 *
 * Firmware dùng 31.588 byte + 256 byte ngăn xếp (đo bằng ISS, hai cách độc lập)
 * = 31.844 / 32.768 byte. Còn trống 924 byte — HẸP, firmware lớn thêm phải kiểm lại.
 *
 * Tệp này là bản THÊM; fw/link.ld (64 KB) không đổi.
 * Gốc: toàn bộ firmware nằm trong RAM 32 KB bắt đầu từ 0.
 * .text.start phải ở ngay địa chỉ 0 vì PROGADDR_RESET = 0.
 */
MEMORY {
    RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 32K
}

SECTIONS {
    .text : {
        KEEP(*(.text.start))
        *(.text .text.*)
        *(.rodata .rodata.*)
        *(.srodata .srodata.*)
    } > RAM

    . = ALIGN(4);

    .data : {
        *(.data .data.*)
        *(.sdata .sdata.*)
    } > RAM

    . = ALIGN(4);

    .bss : {
        __bss_start = .;
        *(.bss .bss.*)
        *(.sbss .sbss.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > RAM

    __heap_start = .;

    /* ngăn xếp mọc xuống từ 0x8000, không cần cấp phát section */
}
