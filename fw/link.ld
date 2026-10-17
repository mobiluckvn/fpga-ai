/* F5 — script liên kết: toàn bộ firmware nằm trong RAM 64 KB bắt đầu từ 0.
 * .text.start phải ở ngay địa chỉ 0 vì PROGADDR_RESET = 0.
 */
MEMORY {
    RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 64K
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

    /* ngăn xếp mọc xuống từ 0x10000, không cần cấp phát section */
}
