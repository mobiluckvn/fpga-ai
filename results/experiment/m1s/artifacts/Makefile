# M1-S — suy luận CNN int8 đầy đủ trên SoC PicoRV32, hai biến thể.
#
#   A-V0 (v0)  : mọi lớp bằng C thẳng, SoC KHÔNG có DOT4
#   A-V2 (v2)  : conv2 + dense dùng DOT4, SoC CÓ DOT4 (WITH_DOT4=1)
#
# SoC dùng lại feasibility/F5_soc/soc.v; bản có DOT4 dùng feasibility/F8_dot4/{soc_f8,top_f8}.v
# synth_gowin -nodsp là bắt buộc cho lõi (xem docs/LOG.md mục F4/F5).
#
# Đích: weights fw-v0 fw-v2 sim-v0 sim-v2 build-v0 build-v2 load-v0 load-v2
#       check-v0 check-v2 archive clean
# Cần: source ../../env/setup_env.sh

F5         := ../../feasibility/F5_soc
F8         := ../../feasibility/F8_dot4
FWDIR      := ../../fw
RESULTS    := ../../results/experiment/m1s

CORE       := $(F5)/soc.v ../../rtl/picorv32/picorv32.v \
              ../../rtl/uart/uart_tx.v ../../rtl/uart/uart_rx.v ../../rtl/ext/pcpi_dot4.v

CROSS      := riscv-none-elf-
ARCH       := -march=rv32im -mabi=ilp32
GIT_HASH   := $(shell git -C ../.. rev-parse --short HEAD 2>/dev/null || echo nogit)
# Dấu vân tay NỘI DUNG của mã nguồn sinh ra firmware. GIT_HASH một mình KHÔNG đủ:
# firmware có thể dựng từ bản nháp chưa commit — việc đó ĐÃ xảy ra, A-V0/A-V2 từng
# được đo bằng một bản main.c chưa commit (xem docs/LOG.md). SRC_HASH đổi theo nội
# dung nên phát hiện ngay nếu một biến thể được đo bằng mã nguồn khác các biến thể kia.
SRC_HASH   := $(shell cat main.c $(FWDIR)/weights.h | shasum -a 256 | cut -c1-12)
OPT        ?= -O2
CFLAGS     := $(ARCH) $(OPT) -ffreestanding -fno-builtin -nostdlib -nostartfiles \
              -fno-pic -mno-relax -Wall -Wextra -I$(FWDIR) -I. \
              -DGIT_HASH=\"$(GIT_HASH)\" -DSRC_HASH=\"$(SRC_HASH)\"
LDF        := $(ARCH) -nostdlib -nostartfiles -T $(FWDIR)/link.ld -Wl,--gc-sections

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst
UART_PORT  ?= /dev/cu.usbserial-20250303171

.PHONY: all weights clean archive
all: build-v0 build-v1 build-v2 build-v1d build-v1dc

weights: $(FWDIR)/weights.h
$(FWDIR)/weights.h:
	cd ../../model && ../.venv-model/bin/python quantize_m1s.py

# ============================ A-V0 ============================
.PHONY: fw-v0 sim-v0 build-v0 load-v0 check-v0
fw-v0: v0/firmware.hex

v0/firmware.elf: main.c $(FWDIR)/weights.h $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p v0
	$(CROSS)gcc $(CFLAGS) $(LDF) -Wl,-Map=v0/firmware.map -o $@ $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > v0/firmware.dis
	@echo "--- kích thước A-V0 (RAM 65536 byte) ---"
	$(CROSS)size -A $@ | tee v0/firmware.size.txt

v0/firmware.hex: v0/firmware.elf
	$(CROSS)objcopy -O binary $< v0/firmware.bin
	python3 ../../scripts/bin2hex.py v0/firmware.bin $@ --words 16384

sim-v0: v0/Vsoc v0/firmware.hex
	cd v0 && ./Vsoc --stop-on "M1S,done" 2>&1 | tee sim.log
	@grep -q "M1S,done" v0/sim.log || (echo "SIM KHONG DAT"; exit 1)

v0/Vsoc: $(F5)/soc.v ../../rtl/picorv32/picorv32.v ../../rtl/uart/uart_tx.v \
         ../../rtl/uart/uart_rx.v $(F5)/sim_main.cpp v0/firmware.hex
	@mkdir -p v0
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc -Mdir v0/obj_dir -o ../Vsoc \
	    $(F5)/soc.v ../../rtl/picorv32/picorv32.v ../../rtl/uart/uart_tx.v \
	    ../../rtl/uart/uart_rx.v $(F5)/sim_main.cpp 2>&1 | tee v0/verilator.log

build-v0: v0/top.fs

v0/top-synth.json: $(F5)/top.v $(CORE) v0/firmware.hex
	@mkdir -p v0
	cd v0 && yosys -l yosys.log -p "read_verilog ../$(F5)/top.v ../$(F5)/soc.v \
	    ../../../rtl/picorv32/picorv32.v ../../../rtl/uart/uart_tx.v \
	    ../../../rtl/uart/uart_rx.v ../../../rtl/ext/pcpi_dot4.v; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

v0/pnr.json: v0/top-synth.json $(CST)
	nextpnr-himbaechel -l v0/nextpnr.log --json $< --write $@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report v0/report.json

v0/top.fs: v0/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-v0: v0/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a v0/load.log

check-v0:
	python3 ../../scripts/m1s_check.py --variant A-V0 --sim-log v0/sim.log \
	    --size v0/firmware.size.txt --csv $(RESULTS)/m1s.csv \
	    --port $(UART_PORT) --drain 2 --repeat 2 --src-hash $(SRC_HASH) \
	    --log v0/check.log 2>&1 | tee v0/check_stdout.log

# ============================ A-V2 ============================
.PHONY: fw-v2 sim-v2 build-v2 load-v2 check-v2
fw-v2: v2/firmware.hex

v2/firmware.elf: main.c $(FWDIR)/weights.h $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p v2
	$(CROSS)gcc $(CFLAGS) -DUSE_DOT4 $(LDF) -Wl,-Map=v2/firmware.map -o $@ \
	    $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > v2/firmware.dis
	@echo "--- kích thước A-V2 (RAM 65536 byte) ---"
	$(CROSS)size -A $@ | tee v2/firmware.size.txt

v2/firmware.hex: v2/firmware.elf
	$(CROSS)objcopy -O binary $< v2/firmware.bin
	python3 ../../scripts/bin2hex.py v2/firmware.bin $@ --words 16384

sim-v2: v2/Vsoc_f8 v2/firmware.hex
	cd v2 && ./Vsoc_f8 --stop-on "M1S,done" 2>&1 | tee sim.log
	@grep -q "M1S,done" v2/sim.log || (echo "SIM KHONG DAT"; exit 1)

v2/Vsoc_f8: $(F8)/soc_f8.v $(CORE) $(F8)/sim_main.cpp v2/firmware.hex
	@mkdir -p v2
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc_f8 -Mdir v2/obj_dir -o ../Vsoc_f8 \
	    $(F8)/soc_f8.v $(CORE) $(F8)/sim_main.cpp 2>&1 | tee v2/verilator.log

build-v2: v2/top.fs

v2/top-synth.json: $(F8)/top_f8.v $(CORE) v2/firmware.hex
	@mkdir -p v2
	cd v2 && yosys -l yosys.log -p "read_verilog -DPCPI_DOT4_DSP ../$(F8)/top_f8.v \
	    ../$(F5)/soc.v ../../../rtl/picorv32/picorv32.v ../../../rtl/uart/uart_tx.v \
	    ../../../rtl/uart/uart_rx.v ../../../rtl/ext/pcpi_dot4.v; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

v2/pnr.json: v2/top-synth.json $(CST)
	nextpnr-himbaechel -l v2/nextpnr.log --json $< --write $@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report v2/report.json

v2/top.fs: v2/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-v2: v2/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a v2/load.log

check-v2:
	python3 ../../scripts/m1s_check.py --variant A-V2 --sim-log v2/sim.log \
	    --size v2/firmware.size.txt --csv $(RESULTS)/m1s.csv --append \
	    --port $(UART_PORT) --drain 2 --repeat 2 --src-hash $(SRC_HASH) \
	    --log v2/check.log 2>&1 | tee v2/check_stdout.log

# ============================ A-V1 ============================
.PHONY: fw-v1 sim-v1 build-v1 load-v1 check-v1
fw-v1: v1/firmware.hex

v1/firmware.elf: main.c $(FWDIR)/weights.h $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p v1
	$(CROSS)gcc $(CFLAGS) -DOPT_KERNELS $(LDF) -Wl,-Map=v1/firmware.map -o $@ $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > v1/firmware.dis
	@echo "--- kích thước A-V1 (RAM 65536 byte) ---"
	$(CROSS)size -A $@ | tee v1/firmware.size.txt

v1/firmware.hex: v1/firmware.elf
	$(CROSS)objcopy -O binary $< v1/firmware.bin
	python3 ../../scripts/bin2hex.py v1/firmware.bin $@ --words 16384

sim-v1: v1/Vsoc v1/firmware.hex
	cd v1 && ./Vsoc --stop-on "M1S,done" 2>&1 | tee sim.log
	@grep -q "M1S,done" v1/sim.log || (echo "SIM KHONG DAT"; exit 1)

v1/Vsoc: $(F5)/soc.v ../../rtl/picorv32/picorv32.v ../../rtl/uart/uart_tx.v \
         ../../rtl/uart/uart_rx.v $(F5)/sim_main.cpp v1/firmware.hex
	@mkdir -p v1
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc -Mdir v1/obj_dir -o ../Vsoc \
	    $(F5)/soc.v ../../rtl/picorv32/picorv32.v ../../rtl/uart/uart_tx.v \
	    ../../rtl/uart/uart_rx.v $(F5)/sim_main.cpp 2>&1 | tee v1/verilator.log

build-v1: v1/top.fs

v1/top-synth.json: $(F5)/top.v $(CORE) v1/firmware.hex
	@mkdir -p v1
	cd v1 && yosys -l yosys.log -p "read_verilog ../$(F5)/top.v ../$(F5)/soc.v \
	    ../../../rtl/picorv32/picorv32.v ../../../rtl/uart/uart_tx.v \
	    ../../../rtl/uart/uart_rx.v ../../../rtl/ext/pcpi_dot4.v; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

v1/pnr.json: v1/top-synth.json $(CST)
	nextpnr-himbaechel -l v1/nextpnr.log --json $< --write $@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report v1/report.json

v1/top.fs: v1/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-v1: v1/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a v1/load.log

check-v1:
	python3 ../../scripts/m1s_check.py --variant A-V1 --sim-log v1/sim.log \
	    --size v1/firmware.size.txt --csv $(RESULTS)/m1s.csv --append \
	    --port $(UART_PORT) --drain 2 --repeat 2 --src-hash $(SRC_HASH) \
	    --log v1/check.log 2>&1 | tee v1/check_stdout.log

# ============================ A-V1+DOT4 ============================
.PHONY: fw-v1d sim-v1d build-v1d load-v1d check-v1d
fw-v1d: v1d/firmware.hex

v1d/firmware.elf: main.c $(FWDIR)/weights.h $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p v1d
	$(CROSS)gcc $(CFLAGS) -DUSE_DOT4 -DOPT_KERNELS $(LDF) -Wl,-Map=v1d/firmware.map -o $@ \
	    $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > v1d/firmware.dis
	@echo "--- kích thước A-V1+DOT4 (RAM 65536 byte) ---"
	$(CROSS)size -A $@ | tee v1d/firmware.size.txt

v1d/firmware.hex: v1d/firmware.elf
	$(CROSS)objcopy -O binary $< v1d/firmware.bin
	python3 ../../scripts/bin2hex.py v1d/firmware.bin $@ --words 16384

sim-v1d: v1d/Vsoc_f8 v1d/firmware.hex
	cd v1d && ./Vsoc_f8 --stop-on "M1S,done" 2>&1 | tee sim.log
	@grep -q "M1S,done" v1d/sim.log || (echo "SIM KHONG DAT"; exit 1)

v1d/Vsoc_f8: $(F8)/soc_f8.v $(CORE) $(F8)/sim_main.cpp v1d/firmware.hex
	@mkdir -p v1d
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc_f8 -Mdir v1d/obj_dir -o ../Vsoc_f8 \
	    $(F8)/soc_f8.v $(CORE) $(F8)/sim_main.cpp 2>&1 | tee v1d/verilator.log

build-v1d: v1d/top.fs

v1d/top-synth.json: $(F8)/top_f8.v $(CORE) v1d/firmware.hex
	@mkdir -p v1d
	cd v1d && yosys -l yosys.log -p "read_verilog -DPCPI_DOT4_DSP ../$(F8)/top_f8.v \
	    ../$(F5)/soc.v ../../../rtl/picorv32/picorv32.v ../../../rtl/uart/uart_tx.v \
	    ../../../rtl/uart/uart_rx.v ../../../rtl/ext/pcpi_dot4.v; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

v1d/pnr.json: v1d/top-synth.json $(CST)
	nextpnr-himbaechel -l v1d/nextpnr.log --json $< --write $@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report v1d/report.json

v1d/top.fs: v1d/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-v1d: v1d/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a v1d/load.log

check-v1d:
	python3 ../../scripts/m1s_check.py --variant A-V1+DOT4 --sim-log v1d/sim.log \
	    --size v1d/firmware.size.txt --csv $(RESULTS)/m1s.csv --append \
	    --port $(UART_PORT) --drain 2 --repeat 2 --src-hash $(SRC_HASH) \
	    --log v1d/check.log 2>&1 | tee v1d/check_stdout.log

# ============================ A-V1+DOT4+C1 ============================
.PHONY: fw-v1dc sim-v1dc build-v1dc load-v1dc check-v1dc
fw-v1dc: v1dc/firmware.hex

v1dc/firmware.elf: main.c $(FWDIR)/weights.h $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p v1dc
	$(CROSS)gcc $(CFLAGS) -DUSE_DOT4 -DOPT_KERNELS -DCONV1_DOT4 -DREQ_BENCH $(LDF) -Wl,-Map=v1dc/firmware.map -o $@ \
	    $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > v1dc/firmware.dis
	@echo "--- kích thước A-V1+DOT4+C1 (RAM 65536 byte) ---"
	$(CROSS)size -A $@ | tee v1dc/firmware.size.txt

v1dc/firmware.hex: v1dc/firmware.elf
	$(CROSS)objcopy -O binary $< v1dc/firmware.bin
	python3 ../../scripts/bin2hex.py v1dc/firmware.bin $@ --words 16384

sim-v1dc: v1dc/Vsoc_f8 v1dc/firmware.hex
	cd v1dc && ./Vsoc_f8 --stop-on "M1S,done" 2>&1 | tee sim.log
	@grep -q "M1S,done" v1dc/sim.log || (echo "SIM KHONG DAT"; exit 1)

v1dc/Vsoc_f8: $(F8)/soc_f8.v $(CORE) $(F8)/sim_main.cpp v1dc/firmware.hex
	@mkdir -p v1dc
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc_f8 -Mdir v1dc/obj_dir -o ../Vsoc_f8 \
	    $(F8)/soc_f8.v $(CORE) $(F8)/sim_main.cpp 2>&1 | tee v1dc/verilator.log

build-v1dc: v1dc/top.fs

v1dc/top-synth.json: $(F8)/top_f8.v $(CORE) v1dc/firmware.hex
	@mkdir -p v1dc
	cd v1dc && yosys -l yosys.log -p "read_verilog -DPCPI_DOT4_DSP ../$(F8)/top_f8.v \
	    ../$(F5)/soc.v ../../../rtl/picorv32/picorv32.v ../../../rtl/uart/uart_tx.v \
	    ../../../rtl/uart/uart_rx.v ../../../rtl/ext/pcpi_dot4.v; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

v1dc/pnr.json: v1dc/top-synth.json $(CST)
	nextpnr-himbaechel -l v1dc/nextpnr.log --json $< --write $@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report v1dc/report.json

v1dc/top.fs: v1dc/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-v1dc: v1dc/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a v1dc/load.log

check-v1dc:
	python3 ../../scripts/m1s_check.py --variant A-V1+DOT4+C1 --sim-log v1dc/sim.log \
	    --size v1dc/firmware.size.txt --csv $(RESULTS)/m1s.csv --append \
	    --port $(UART_PORT) --drain 2 --repeat 2 --src-hash $(SRC_HASH) \
	    --log v1dc/check.log 2>&1 | tee v1dc/check_stdout.log

# ============ A-V1+DOT4+C1, chế độ 10.000 ảnh qua UART (v10k) ============
# Phần cứng GIỐNG HỆT v1dc (cùng DOT4); chỉ firmware khác: ảnh đến từ UART thay vì
# nhúng sẵn, nên chạy được đủ tập test 10.000 ảnh trên kit.
.PHONY: fw-v10k sim-v10k build-v10k load-v10k run-v10k cmp-v10k
fw-v10k: v10k/firmware.hex

v10k/firmware.elf: main.c $(FWDIR)/weights.h $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p v10k
	$(CROSS)gcc $(CFLAGS) -DUSE_DOT4 -DOPT_KERNELS -DCONV1_DOT4 -DSTREAM_10K $(LDF) \
	    -Wl,-Map=v10k/firmware.map -o $@ $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > v10k/firmware.dis
	@echo "--- kích thước v10k (RAM 65536 byte) ---"
	$(CROSS)size -A $@ | tee v10k/firmware.size.txt

v10k/firmware.hex: v10k/firmware.elf
	$(CROSS)objcopy -O binary $< v10k/firmware.bin
	python3 ../../scripts/bin2hex.py v10k/firmware.bin $@ --words 16384

v10k/imgs3.bin:
	@mkdir -p v10k
	../../.venv/bin/python ../../scripts/m1s_10k.py --n 3 --export $@

v10k/Vsoc_10k: $(F8)/soc_f8.v $(CORE) sim_main_10k.cpp v10k/firmware.hex
	@mkdir -p v10k
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc_f8 -Mdir v10k/obj_dir -o ../Vsoc_10k \
	    $(F8)/soc_f8.v $(CORE) sim_main_10k.cpp 2>&1 | tee v10k/verilator.log

sim-v10k: v10k/Vsoc_10k v10k/imgs3.bin
	cd v10k && ./Vsoc_10k --imgs imgs3.bin --n 3 2>&1 | tee sim.log
	@grep -c "^M1S10K," v10k/sim.log

build-v10k: v10k/top.fs

v10k/top-synth.json: $(F8)/top_f8.v $(CORE) v10k/firmware.hex
	@mkdir -p v10k
	cd v10k && yosys -l yosys.log -p "read_verilog -DPCPI_DOT4_DSP ../$(F8)/top_f8.v \
	    ../$(F5)/soc.v ../../../rtl/picorv32/picorv32.v ../../../rtl/uart/uart_tx.v \
	    ../../../rtl/uart/uart_rx.v ../../../rtl/ext/pcpi_dot4.v; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

v10k/pnr.json: v10k/top-synth.json $(CST)
	nextpnr-himbaechel -l v10k/nextpnr.log --json $< --write $@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report v10k/report.json

v10k/top.fs: v10k/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-v10k: v10k/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a v10k/load.log

N10K ?= 10000
run-v10k:
	../../.venv/bin/python ../../scripts/m1s_10k.py --port $(UART_PORT) --n $(N10K) \
	    --variant A-V1+DOT4+C1 --csv $(RESULTS)/m1s_10k.csv --log v10k/run.log \
	    2>&1 | tee v10k/run_stdout.log

# bằng chứng các lớp tính toán KHÔNG đổi giữa v1dc (đã kiểm kit=Verilator) và v10k
cmp-v10k:
	python3 ../../scripts/cmp_layers.py v1dc/firmware.dis v10k/firmware.dis \
	    conv1 conv1_prep pool1 conv2 pool2 dense requant sat_rdhmul rdiv_pot

# ============================ chung ============================
archive:
	@mkdir -p $(RESULTS)
	@for v in v0 v1 v2 v1d v1dc v10k; do \
	    if [ -f $$v/report.json ]; then \
	        echo "===== $$v ====="; \
	        python3 ../../scripts/pnr_report.py $$v/report.json | tee $$v/resources.txt; \
	    fi; \
	done
	@RESULTS_BASE=results/experiment sh ../../scripts/archive_gate.sh m1s . main.c Makefile $(FWDIR)/weights.h
	@for v in v0 v1 v2 v1d v1dc v10k; do [ -d $$v ] && RESULTS_BASE=results/experiment sh ../../scripts/archive_gate.sh m1s/$$v $$v; done

clean:
	rm -rf v0 v1 v2 v1d v1dc v10k
