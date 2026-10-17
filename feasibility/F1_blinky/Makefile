# F1 — Blinky, luồng mã nguồn mở cho Tang Nano 20K
#
# Tham số đã ĐỐI CHIẾU (2026-10-17) với YosysHQ/apicula @ master, examples/Makefile:
#   %-tangnano20k-synth.json: yosys ... -p "read_verilog $^; synth_gowin -json $@ -family gw2a -setundef"
#   %-tangnano20k.json:       nextpnr-himbaechel --json $< --write $@ \
#                               --device GW2AR-LV18QN88C8/I7 --vopt family=GW2A-18C --vopt cst=tangnano20k.cst
#                             (NEXTPNR_FLAGS = --timing-allow-fail -r)
#   %-tangnano20k.fs:         gowin_pack -c -d GW2A-18C -o $@ $<
# Lưu ý: synth_gowin mặc định -family gw1n => BẮT BUỘC truyền -family gw2a cho GW2AR-18.
# Ở đây KHÔNG dùng --timing-allow-fail: muốn biết timing thật có đạt 27 MHz hay không.
#
# Đích: sim build load check clean
# Cần: source ../../env/setup_env.sh

TOP        := top
SRC        := top.v
TB         := tb_top.v
BUILD      := build
RESULTS    := ../../results/feasibility/F1

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst

.PHONY: all sim build load check clean
all: build

# ---------- mô phỏng ----------
sim: $(BUILD)/tb_top.vvp
	@echo "=== Icarus Verilog ==="
	vvp $< 2>&1 | tee $(BUILD)/sim.log
	@grep -q F1_SIM_PASS $(BUILD)/sim.log || (echo "SIM KHONG DAT"; exit 1)

$(BUILD)/tb_top.vvp: $(SRC) $(TB)
	@mkdir -p $(BUILD)
	iverilog -g2012 -o $@ $(TB) $(SRC)

# ---------- tổng hợp / place&route / đóng gói ----------
build: $(BUILD)/$(TOP).fs

$(BUILD)/$(TOP)-synth.json: $(SRC)
	@mkdir -p $(BUILD)
	yosys -l $(BUILD)/yosys.log \
	      -p "read_verilog $(SRC); synth_gowin -top $(TOP) -family $(YOSYS_FAM) -json $@ -setundef"

$(BUILD)/pnr.json: $(BUILD)/$(TOP)-synth.json $(CST)
	nextpnr-himbaechel -l $(BUILD)/nextpnr.log \
	      --json $< --write $@ \
	      --device "$(DEVICE)" \
	      --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) \
	      --report $(BUILD)/report.json

$(BUILD)/$(TOP).fs: $(BUILD)/pnr.json
	gowin_pack -c -d $(FAMILY) -o $@ $<

# ---------- nạp (CHỈ SRAM, không ghi flash) ----------
load: $(BUILD)/$(TOP).fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a $(BUILD)/load.log

# ---------- thu kết quả ----------
# Lưu TOÀN BỘ vật phẩm (bitstream, netlist, log) + manifest SHA256 vào results/feasibility/F1/
check: $(BUILD)/$(TOP).fs
	@mkdir -p $(RESULTS)
	@echo "--- tài nguyên & Fmax (từ report.json) ---"
	@python3 ../../scripts/pnr_report.py $(BUILD)/report.json | tee $(BUILD)/resources.txt
	@ls -l $(BUILD)/$(TOP).fs | awk '{print "bitstream: "$$NF" ("$$5" byte)"}' | tee $(BUILD)/bitstream_size.txt
	@sh ../../scripts/archive_gate.sh F1 $(BUILD)

clean:
	rm -rf $(BUILD)
