# F7 — kernel int8 thật, đúng từng bit. Dùng ĐÚNG SoC của F5
# (feasibility/F5_soc/soc.v, top.v), chỉ thay firmware.
#
# Firmware build với -O2 (theo kế hoạch: "kernel C thẳng, -O2").
# synth_gowin -nodsp là bắt buộc — xem kết quả F4 trong docs/LOG.md.
#
# Đích: data fw sim build load f7check check clean
# Cần: source ../../env/setup_env.sh

SOCDIR     := ../F5_soc
FWDIR      := ../../fw
HEX        := firmware.hex
DATA       := f7_data.h
SRC        := $(SOCDIR)/top.v $(SOCDIR)/soc.v ../../rtl/picorv32/picorv32.v \
              ../../rtl/uart/uart_tx.v ../../rtl/uart/uart_rx.v
SIMSRC     := $(SOCDIR)/soc.v ../../rtl/picorv32/picorv32.v \
              ../../rtl/uart/uart_tx.v ../../rtl/uart/uart_rx.v
BUILD      := build
RESULTS    := ../../results/feasibility/F7

CROSS      := riscv-none-elf-
ARCH       := -march=rv32im -mabi=ilp32
GIT_HASH   := $(shell git -C ../.. rev-parse --short HEAD 2>/dev/null || echo nogit)
OPT        ?= -O2
CFLAGS     := $(ARCH) $(OPT) -ffreestanding -fno-builtin -nostdlib -nostartfiles \
              -fno-pic -mno-relax -Wall -Wextra -I$(FWDIR) -I. \
              -DGIT_HASH=\"$(GIT_HASH)\"
LDFLAGS    := $(ARCH) -nostdlib -nostartfiles -T $(FWDIR)/link.ld \
              -Wl,--gc-sections -Wl,-Map=$(BUILD)/firmware.map

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst
UART_PORT  ?= /dev/cu.usbserial-20250303171

.PHONY: all data fw sim build load f7check check clean
all: build

# ---------- dữ liệu + golden ----------
data: $(DATA)

$(DATA):
	python3 ../../scripts/gen_f7_data.py --out $@

# ---------- firmware ----------
fw: $(HEX)

$(BUILD)/firmware.elf: main.c $(DATA) $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p $(BUILD)
	$(CROSS)gcc $(CFLAGS) $(LDFLAGS) -o $@ $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > $(BUILD)/firmware.dis
	@echo "--- kích thước firmware (RAM 65536 byte) ---"
	$(CROSS)size -A $@ | tee $(BUILD)/firmware.size.txt

$(HEX): $(BUILD)/firmware.elf
	$(CROSS)objcopy -O binary $< $(BUILD)/firmware.bin
	python3 ../../scripts/bin2hex.py $(BUILD)/firmware.bin $@ --words 16384

# ---------- mô phỏng Verilator ----------
sim: $(BUILD)/Vsoc $(HEX)
	@echo "=== Verilator ==="
	$(BUILD)/Vsoc --stop-on "F7,done" 2>&1 | tee $(BUILD)/sim.log
	@grep -q "F7,done" $(BUILD)/sim.log || (echo "SIM KHONG DAT"; exit 1)

$(BUILD)/Vsoc: $(SIMSRC) $(SOCDIR)/sim_main.cpp $(HEX)
	@mkdir -p $(BUILD)
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal \
	    -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc -Mdir $(BUILD)/obj_dir -o ../Vsoc \
	    $(SIMSRC) $(SOCDIR)/sim_main.cpp 2>&1 | tee $(BUILD)/verilator.log

# ---------- bitstream ----------
build: $(BUILD)/top.fs

$(BUILD)/top-synth.json: $(SRC) $(HEX)
	@mkdir -p $(BUILD)
	yosys -l $(BUILD)/yosys.log \
	      -p "read_verilog $(SRC); synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json $@ -setundef"

$(BUILD)/pnr.json: $(BUILD)/top-synth.json $(CST)
	nextpnr-himbaechel -l $(BUILD)/nextpnr.log --json $< --write $@ \
	      --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) --report $(BUILD)/report.json

$(BUILD)/top.fs: $(BUILD)/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load: $(BUILD)/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a $(BUILD)/load.log

# ---------- đọc kit, so CRC với Python và so chu kỳ với Verilator ----------
f7check:
	python3 ../../scripts/f7_check.py --sim-log $(BUILD)/sim.log \
	    --size $(BUILD)/firmware.size.txt --csv $(RESULTS)/kernel.csv \
	    --port $(UART_PORT) --drain 0 --repeat 3 \
	    --log $(BUILD)/f7_check.log 2>&1 | tee $(BUILD)/f7_check_stdout.log

# ---------- thu kết quả ----------
check: $(BUILD)/top.fs
	@mkdir -p $(RESULTS)
	@python3 ../../scripts/pnr_report.py $(BUILD)/report.json | tee $(BUILD)/resources.txt
	@(printf 'bitstream: '; wc -c < $(BUILD)/top.fs | tr -d ' '; echo ' byte') | tr -d '\n' > $(BUILD)/bitstream_size.txt
	@echo >> $(BUILD)/bitstream_size.txt
	@python3 ../../scripts/gen_f7_data.py --out $(BUILD)/f7_data_check.h > $(BUILD)/data_info.txt
	@cmp -s $(DATA) $(BUILD)/f7_data_check.h && echo "f7_data.h tái lập đúng" || echo "CẢNH BÁO: f7_data.h khác bản sinh lại"
	@rm -f $(BUILD)/f7_data_check.h
	@cp -f $(HEX) $(BUILD)/firmware.hex
	@sh ../../scripts/archive_gate.sh F7 $(BUILD) main.c $(DATA)

clean:
	rm -rf $(BUILD) $(HEX) $(DATA)
