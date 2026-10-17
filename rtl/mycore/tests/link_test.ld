/* RAM 64 KB tại 0x0, giống fw/link.ld của nhánh A. */
OUTPUT_ARCH( "riscv" )
ENTRY(_start)
MEMORY { ram (rwx) : ORIGIN = 0x00000000, LENGTH = 0x00010000 }
SECTIONS {
    .text : ALIGN(4) { *(.text.start) *(.text .text.*) } > ram
    .rodata : ALIGN(4) { *(.rodata .rodata.* .srodata .srodata.*) } > ram
    .data : ALIGN(4) { *(.data .data.* .sdata .sdata.*) } > ram
    .bss : ALIGN(4) { *(.bss .bss.* .sbss .sbss.* COMMON) } > ram
    _end = ALIGN(4);
}
