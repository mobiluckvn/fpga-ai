/* RAM 32 KB tại 0x0 — cho cấu hình bộ nhớ HAI CỔNG của S7 (DUAL_PORT=1).
 * Bản THÊM; link_test.ld (64 KB) không đổi. */
OUTPUT_ARCH( "riscv" )
ENTRY(_start)
MEMORY { ram (rwx) : ORIGIN = 0x00000000, LENGTH = 0x00008000 }
SECTIONS {
    .text : ALIGN(4) { *(.text.start) *(.text .text.*) } > ram
    .rodata : ALIGN(4) { *(.rodata .rodata.* .srodata .srodata.*) } > ram
    .data : ALIGN(4) { *(.data .data.* .sdata .sdata.*) } > ram
    .bss : ALIGN(4) { *(.bss .bss.* .sbss .sbss.* COMMON) } > ram
    _end = ALIGN(4);
}
