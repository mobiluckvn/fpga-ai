# Firmware cho SoC F5 (PicoRV32, rv32im).
#
# Sinh: firmware.elf -> firmware.bin -> firmware.hex (từ 32 bit, little-endian)
# GIT_HASH nhúng vào firmware để dòng "F5,hello,<hash>" truy nguyên được.
#
# Cần: source ../env/setup_env.sh

CROSS   := riscv-none-elf-
CC      := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE    := $(CROSS)size

ARCH    := -march=rv32im -mabi=ilp32
GIT_HASH := $(shell git -C .. rev-parse --short HEAD 2>/dev/null || echo nogit)
LOOP_N  ?= 1000

CFLAGS  := $(ARCH) -Os -ffreestanding -fno-builtin -nostdlib -nostartfiles \
           -fno-pic -mno-relax -Wall -Wextra \
           -DGIT_HASH=\"$(GIT_HASH)\" -DLOOP_N=$(LOOP_N)u
LDFLAGS := $(ARCH) -nostdlib -nostartfiles -T link.ld -Wl,--gc-sections -Wl,-Map=firmware.map

RAM_WORDS ?= 16384

.PHONY: all clean size
all: firmware.hex size

firmware.elf: start.S main.c link.ld soc.h
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ start.S main.c
	$(OBJDUMP) -D $@ > firmware.dis

firmware.bin: firmware.elf
	$(OBJCOPY) -O binary $< $@

firmware.hex: firmware.bin
	python3 ../scripts/bin2hex.py $< $@ --words $(RAM_WORDS)

size: firmware.elf
	@$(SIZE) -A firmware.elf | tee firmware.size.txt
	@echo "GIT_HASH nhúng: $(GIT_HASH)"

clean:
	rm -f firmware.elf firmware.bin firmware.hex firmware.dis firmware.map firmware.size.txt
