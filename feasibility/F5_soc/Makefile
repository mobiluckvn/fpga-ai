# F5 — SoC PicoRV32 + RAM 64 KB + UART + bộ đếm phần cứng.
#
# QUAN TRỌNG (kết quả của F4): build với `synth_gowin -nodsp`.
# ENABLE_FAST_MUL=1 tạo bộ nhân 32x32; nếu để yosys suy luận DSP thì lệnh MUL
# sẽ SAI trên kit (xem docs/LOG.md mục F4). -nodsp buộc nhân bằng logic.
#
# Đích: fw sim build load f5check check clean
# Cần: source ../../env/setup_env.sh

FWDIR      := ../../fw
HEX        := firmware.hex
SRC        := top.v soc.v ../../rtl/picorv32/picorv32.v \
              ../../rtl/uart/uart_tx.v ../../rtl/uart/uart_rx.v
SIMSRC     := soc.v ../../rtl/picorv32/picorv32.v \
              ../../rtl/uart/uart_tx.v ../../rtl/uart/uart_rx.v
BUILD      := build
RESULTS    := ../../results/feasibility/F5

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst

.PHONY: all fw sim build load f5check check clean
all: build

# ---------- firmware ----------
fw: $(HEX)

$(HEX): $(FWDIR)/main.c $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h $(FWDIR)/Makefile
	$(MAKE) -C $(FWDIR)
	cp -f $(FWDIR)/firmware.hex $(HEX)
	@mkdir -p $(BUILD)
	cp -f $(FWDIR)/firmware.size.txt $(FWDIR)/firmware.dis $(FWDIR)/firmware.bin $(BUILD)/ 2>/dev/null || true

# ---------- mô phỏng Verilator ----------
sim: $(BUILD)/Vsoc $(HEX)
	@echo "=== Verilator ==="
	$(BUILD)/Vsoc 2>&1 | tee $(BUILD)/sim.log
	@grep -q "F5,done" $(BUILD)/sim.log || (echo "SIM KHONG DAT"; exit 1)

$(BUILD)/Vsoc: $(SIMSRC) sim_main.cpp $(HEX)
	@mkdir -p $(BUILD)
	verilator --cc --exe --build -j 0 -O2 \
	    -Wno-fatal \
	    -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc \
	    -Mdir $(BUILD)/obj_dir \
	    -o ../Vsoc \
	    $(SIMSRC) sim_main.cpp 2>&1 | tee $(BUILD)/verilator.log

# ---------- tổng hợp / place&route / đóng gói ----------
build: $(BUILD)/top.fs

$(BUILD)/top-synth.json: $(SRC) $(HEX)
	@mkdir -p $(BUILD)
	yosys -l $(BUILD)/yosys.log \
	      -p "read_verilog -DSYNTHESIS $(SRC); synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json $@ -setundef"

$(BUILD)/pnr.json: $(BUILD)/top-synth.json $(CST)
	nextpnr-himbaechel -l $(BUILD)/nextpnr.log --json $< --write $@ \
	      --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) --report $(BUILD)/report.json

$(BUILD)/top.fs: $(BUILD)/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

# ---------- nạp (CHỈ SRAM) ----------
load: $(BUILD)/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a $(BUILD)/load.log

# ---------- đọc kit và so với Verilator ----------
f5check:
	python3 ../../scripts/f5_check.py --sim-log $(BUILD)/sim.log \
	    --log $(BUILD)/f5_check.log 2>&1 | tee $(BUILD)/f5_check_stdout.log

# ---------- thu kết quả ----------
check: $(BUILD)/top.fs
	@mkdir -p $(RESULTS)
	@echo "--- tài nguyên & Fmax ---"
	@python3 ../../scripts/pnr_report.py $(BUILD)/report.json | tee $(BUILD)/resources.txt
	@(printf 'bitstream: '; wc -c < $(BUILD)/top.fs | tr -d ' '; echo ' byte') | tr -d '\n' > $(BUILD)/bitstream_size.txt
	@echo >> $(BUILD)/bitstream_size.txt
	@cp -f $(HEX) $(BUILD)/firmware.hex
	@sh ../../scripts/archive_gate.sh F5 $(BUILD) soc.v top.v sim_main.cpp

clean:
	rm -rf $(BUILD) $(HEX)
	$(MAKE) -C $(FWDIR) clean
