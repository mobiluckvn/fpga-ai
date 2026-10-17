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
OPT        ?= -O2
CFLAGS     := $(ARCH) $(OPT) -ffreestanding -fno-builtin -nostdlib -nostartfiles \
              -fno-pic -mno-relax -Wall -Wextra -I$(FWDIR) -I. \
              -DGIT_HASH=\"$(GIT_HASH)\"
LDF        := $(ARCH) -nostdlib -nostartfiles -T $(FWDIR)/link.ld -Wl,--gc-sections

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst
UART_PORT  ?= /dev/cu.usbserial-20250303171

.PHONY: all weights clean archive
all: build-v0 build-v2

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
	    --port $(UART_PORT) --drain 0 --repeat 2 \
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
	    --port $(UART_PORT) --drain 0 --repeat 2 \
	    --log v2/check.log 2>&1 | tee v2/check_stdout.log

# ============================ chung ============================
archive:
	@mkdir -p $(RESULTS)
	@for v in v0 v2; do \
	    if [ -f $$v/report.json ]; then \
	        echo "===== $$v ====="; \
	        python3 ../../scripts/pnr_report.py $$v/report.json | tee $$v/resources.txt; \
	    fi; \
	done
	@RESULTS_BASE=results/experiment sh ../../scripts/archive_gate.sh m1s . main.c Makefile $(FWDIR)/weights.h
	@for v in v0 v2; do [ -d $$v ] && RESULTS_BASE=results/experiment sh ../../scripts/archive_gate.sh m1s/$$v $$v; done

clean:
	rm -rf v0 v2
