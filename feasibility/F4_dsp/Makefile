# F4 — khối nhân: tích vô hướng 4 x int8, cộng dồn 2^20 chu kỳ.
#
# Hai biến thể dùng CHUNG top.v, chỉ khác cờ yosys:
#   DSP: synth_gowin            -> cho phép ánh xạ phép nhân vào khối MULT của Gowin
#   LUT: synth_gowin -nodsp     -> "do not infer DSP multipliers" (theo `yosys -p 'help synth_gowin'`)
# Nhãn trong dòng log chọn bằng -DLABEL_LUT.
#
# Đích: sim build build-dsp build-lut load-dsp load-lut f4check-dsp f4check-lut check clean
# Cần: source ../../env/setup_env.sh

SRC        := top.v ../../rtl/uart/uart_tx.v
TB         := tb_top.v
RESULTS    := ../../results/feasibility/F4

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst

.PHONY: all sim build build-dsp build-dsp18 build-prm build-lut load-dsp load-dsp18 load-prm load-lut f4check-dsp f4check-dsp18 f4check-prm f4check-lut check clean
all: build
build: build-dsp build-lut

# ---------- mô phỏng (đủ 2^20 chu kỳ) ----------
sim: build_sim/tb_top.vvp
	@echo "=== Icarus Verilog (2^20 chu kỳ tích luỹ) ==="
	vvp $< 2>&1 | tee build_sim/sim.log
	@grep -q F4_SIM_PASS build_sim/sim.log || (echo "SIM KHONG DAT"; exit 1)

build_sim/tb_top.vvp: top.v ../../rtl/uart/uart_tx.v $(TB)
	@mkdir -p build_sim
	iverilog -g2012 -o $@ $(TB) $(SRC)

# ---------- biến thể DSP ----------
build-dsp: build_dsp/top.fs

build_dsp/top-synth.json: top.v ../../rtl/uart/uart_tx.v
	@mkdir -p build_dsp
	yosys -l build_dsp/yosys.log \
	      -p "read_verilog $(SRC); synth_gowin -top top -family $(YOSYS_FAM) -json $@ -setundef"

build_dsp/pnr.json: build_dsp/top-synth.json $(CST)
	nextpnr-himbaechel -l build_dsp/nextpnr.log --json $< --write $@ \
	      --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) --report build_dsp/report.json

build_dsp/top.fs: build_dsp/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-dsp: build_dsp/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a build_dsp/load.log

f4check-dsp:
	python3 ../../scripts/f4_check.py --label DSP --log build_dsp/f4_check.log 2>&1 \
	    | tee build_dsp/f4_check_stdout.log

# ---------- biến thể DSP18: ép toán hạng 18 bit -> MULT18X18 (hướng sửa 1) ----------
build-dsp18: build_dsp18/top.fs

build_dsp18/top-synth.json: top.v ../../rtl/uart/uart_tx.v
	@mkdir -p build_dsp18
	yosys -l build_dsp18/yosys.log \
	      -p "read_verilog -DWIDE_MULT -DLABEL_D18 $(SRC); synth_gowin -top top -family $(YOSYS_FAM) -json $@ -setundef"

build_dsp18/pnr.json: build_dsp18/top-synth.json $(CST)
	nextpnr-himbaechel -l build_dsp18/nextpnr.log --json $< --write $@ \
	      --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) --report build_dsp18/report.json

build_dsp18/top.fs: build_dsp18/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-dsp18: build_dsp18/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a build_dsp18/load.log

f4check-dsp18:
	python3 ../../scripts/f4_check.py --label D18 --log build_dsp18/f4_check.log 2>&1 \
	    | tee build_dsp18/f4_check_stdout.log

# ---------- biến thể PRM: gọi trực tiếp primitive MULT18X18 (hướng sửa 2) ----------
build-prm: build_prm/top.fs

build_prm/top-synth.json: top.v ../../rtl/uart/uart_tx.v
	@mkdir -p build_prm
	yosys -l build_prm/yosys.log \
	      -p "read_verilog -DPRIM_MULT -DLABEL_PRM $(SRC); synth_gowin -top top -family $(YOSYS_FAM) -json $@ -setundef"

build_prm/pnr.json: build_prm/top-synth.json $(CST)
	nextpnr-himbaechel -l build_prm/nextpnr.log --json $< --write $@ \
	      --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) --report build_prm/report.json

build_prm/top.fs: build_prm/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-prm: build_prm/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a build_prm/load.log

f4check-prm:
	python3 ../../scripts/f4_check.py --label PRM --log build_prm/f4_check.log 2>&1 \
	    | tee build_prm/f4_check_stdout.log

# ---------- biến thể LUT ----------
build-lut: build_lut/top.fs

build_lut/top-synth.json: top.v ../../rtl/uart/uart_tx.v
	@mkdir -p build_lut
	yosys -l build_lut/yosys.log \
	      -p "read_verilog -DLABEL_LUT $(SRC); synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json $@ -setundef"

build_lut/pnr.json: build_lut/top-synth.json $(CST)
	nextpnr-himbaechel -l build_lut/nextpnr.log --json $< --write $@ \
	      --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) --report build_lut/report.json

build_lut/top.fs: build_lut/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-lut: build_lut/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a build_lut/load.log

f4check-lut:
	python3 ../../scripts/f4_check.py --label LUT --log build_lut/f4_check.log 2>&1 \
	    | tee build_lut/f4_check_stdout.log

# ---------- thu kết quả cả bốn biến thể ----------
check:
	@mkdir -p $(RESULTS)
	@for v in dsp dsp18 prm lut; do \
	    echo "===== biến thể $$v ====="; \
	    python3 ../../scripts/pnr_report.py build_$$v/report.json | tee build_$$v/resources.txt; \
	    (printf 'bitstream: build_%s/top.fs (' $$v; wc -c < build_$$v/top.fs | tr -d ' '; echo ' byte)') \
	        | tr -d '\n' > build_$$v/bitstream_size.txt; echo >> build_$$v/bitstream_size.txt; \
	done
	@python3 ../../scripts/gen_f4_expect.py > build_sim/expect.txt
	@echo "--- bảng so sánh ---"
	@python3 ../../scripts/f4_table.py . | tee $(RESULTS)/comparison.md
	@sh ../../scripts/archive_gate.sh F4 build_sim
	@for v in dsp dsp18 prm lut; do sh ../../scripts/archive_gate.sh F4/$$v build_$$v; done

clean:
	rm -rf build_dsp build_dsp18 build_prm build_lut build_sim
