# Hạ tầng bước S6: thử ứng viên phần cứng TRÊN ĐỈNH B-V3: dựng firmware từ MỘT file kernel thay được.
#
# Mục đích: cho vòng tối ưu phần mềm có AI hỗ trợ sửa đúng một file (`kernels.c`),
# phần còn lại của firmware giữ nguyên để số đo so sánh được.
#
# Cờ biên dịch GIỐNG HỆT experiment/m1s/Makefile (cùng ARCH, OPT, CFLAGS, LDF, bin2hex)
# — nếu khác thì không so được với B-V0. KHÔNG định nghĩa macro tính năng nào:
# bản gốc `kernels_v3.c` phải cho đúng số của A-V0 / B-V0.
#
# Dùng:  make fw KERNELS=kernels_v3.c OUT=v0
#        make fw KERNELS=rounds/r1_a.c OUT=r1_a

FWDIR      := ../../fw
CROSS      := riscv-none-elf-
ARCH       := -march=rv32im -mabi=ilp32
OPT        ?= -O2
KERNELS    ?= kernels_v3.c
OUT        ?= v3
GIT_HASH   := $(shell git -C ../.. rev-parse --short HEAD 2>/dev/null || echo nogit)
# Dấu vân tay bao luôn file kernel đang dùng — mỗi biến thể B1 có SRC_HASH riêng.
SRC_HASH   := $(shell cat main.c $(KERNELS) $(FWDIR)/weights.h | shasum -a 256 | cut -c1-12)
CFLAGS     := $(ARCH) $(OPT) -ffreestanding -fno-builtin -nostdlib -nostartfiles \
              -fno-pic -mno-relax -Wall -Wextra -I$(FWDIR) -I. \
              -DGIT_HASH=\"$(GIT_HASH)\" -DSRC_HASH=\"$(SRC_HASH)\"
LDF        := $(ARCH) -nostdlib -nostartfiles -T $(FWDIR)/link.ld -Wl,--gc-sections

.PHONY: fw clean
fw: $(OUT)/firmware.hex

$(OUT)/firmware.elf: main.c $(KERNELS) $(FWDIR)/weights.h $(FWDIR)/start.S \
                     $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p $(OUT)
	@cp $(KERNELS) $(OUT)/kernels.c
	$(CROSS)gcc $(CFLAGS) -I$(OUT) $(LDF) -Wl,-Map=$(OUT)/firmware.map -o $@ \
	    $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > $(OUT)/firmware.dis
	$(CROSS)size -A $@ | tee $(OUT)/firmware.size.txt

$(OUT)/firmware.hex: $(OUT)/firmware.elf
	$(CROSS)objcopy -O binary $< $(OUT)/firmware.bin
	python3 ../../scripts/bin2hex.py $(OUT)/firmware.bin $@ --words 16384

clean:
	rm -rf v3 c*
