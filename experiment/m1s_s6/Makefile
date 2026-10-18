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
# WEIGHTS: header trọng số. Mặc định là của M1-S — giữ nguyên mọi hành vi cũ.
# Mô hình giữ lại (S8) truyền WEIGHTS=../../fw/weights_m1l.h. Header được CHÉP vào
# $(OUT)/ y như kernels.c, và -I$(OUT) đứng TRƯỚC -I$(FWDIR) để bản chép thắng.
WEIGHTS    ?= $(FWDIR)/weights.h
GIT_HASH   := $(shell git -C ../.. rev-parse --short HEAD 2>/dev/null || echo nogit)
# Dấu vân tay bao luôn file kernel đang dùng — mỗi biến thể B1 có SRC_HASH riêng.
SRC_HASH   := $(shell cat main.c $(KERNELS) $(WEIGHTS) | shasum -a 256 | cut -c1-12)
CFLAGS     := $(ARCH) $(OPT) -ffreestanding -fno-builtin -nostdlib -nostartfiles \
              -fno-pic -mno-relax -Wall -Wextra -I$(FWDIR) -I. \
              -DGIT_HASH=\"$(GIT_HASH)\" -DSRC_HASH=\"$(SRC_HASH)\"
# RAMKB: 64 (mặc định, như cũ) hoặc 32 cho cấu hình bộ nhớ HAI CỔNG của S7.
# Mặc định giữ nguyên script liên kết, đỉnh ngăn xếp và số từ của hex -> firmware
# mặc định giống hệt từng bit bản trước.
RAMKB      ?= 64
ifeq ($(RAMKB),32)
  LDSCRIPT := $(FWDIR)/link32.ld
  STACKTOP := 0x00008000
  HEXWORDS := 8192
else
  LDSCRIPT := $(FWDIR)/link.ld
  STACKTOP := 0x00010000
  HEXWORDS := 16384
endif
CFLAGS     += -DSTACK_TOP=$(STACKTOP)
LDF        := $(ARCH) -nostdlib -nostartfiles -T $(LDSCRIPT) -Wl,--gc-sections

.PHONY: fw clean
fw: $(OUT)/firmware.hex

$(OUT)/firmware.elf: main.c $(KERNELS) $(WEIGHTS) $(FWDIR)/start.S \
                     $(LDSCRIPT) $(FWDIR)/soc.h
	@mkdir -p $(OUT)
	@cp $(KERNELS) $(OUT)/kernels.c
	@cp $(WEIGHTS) $(OUT)/weights.h
	$(CROSS)gcc -I$(OUT) $(CFLAGS) $(LDF) -Wl,-Map=$(OUT)/firmware.map -o $@ \
	    $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > $(OUT)/firmware.dis
	$(CROSS)size -A $@ | tee $(OUT)/firmware.size.txt

$(OUT)/firmware.hex: $(OUT)/firmware.elf
	$(CROSS)objcopy -O binary $< $(OUT)/firmware.bin
	python3 ../../scripts/bin2hex.py $(OUT)/firmware.bin $@ --words $(HEXWORDS)

clean:
	rm -rf v3 c*
