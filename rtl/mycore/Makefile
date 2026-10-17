# Nhánh B — lõi RISC-V tự viết. Xem docs/BRANCH_B_PLAN.md.
#
# Nguyên tắc: dùng lại ĐÚNG các file firmware.hex của nhánh A, không biên dịch lại,
# nên chênh lệch số chu kỳ là thuần vi kiến trúc (instret phải khớp tuyệt đối).
#
# Đích: sim-bv0 sim-bv1 build-bv0 build-bv1 load-bv0 load-bv1 check-bv0 check-bv1
#       rvtests archive clean
# Cần: source ../../env/setup_env.sh

M1S        := ../../experiment/m1s
RESULTS    := ../../results/branch_b
CORE       := soc_b.v mycore.v ../uart/uart_tx.v ../uart/uart_rx.v

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst
UART_PORT  ?= /dev/cu.usbserial-20250303171
SRC_HASH   := $(shell cat $(M1S)/main.c ../../fw/weights.h | shasum -a 256 | cut -c1-12)
# Chia xung nhịp — xem ghi chú đầu top_b.v (đường vào BSRAM không được nextpnr ràng buộc)
CLKDIV     ?= 1
DIV_UART   ?= 234
# FAST_ADDR=1: địa chỉ bộ nhớ tổ hợp (1 chu kỳ/lệnh) — ĐÚNG trong mô phỏng nhưng
#   KHÔNG CHẠY trên kit vì đường vào BSRAM không được nextpnr ràng buộc.
# FAST_ADDR=0: ghi thanh ghi địa chỉ — chạy được trên kit, chậm hơn ~1,9x.
FAST_ADDR  ?= 1
BEACON     ?= 0
WITH_DOT4  ?= 0
# CSV_APPEND: ghi đè cờ --append (scripts/branch_b_measure.sh dùng để biến thể đầu
# tiên ghi mới và các biến thể sau nối thêm, bất kể thứ tự khai báo trong file này)
CSV_APPEND_SET := $(if $(filter CSV_APPEND,$(.VARIABLES)),1,)

.PHONY: all rvtests archive clean min build-min load-min
# ---------------- cổng B6: 100+ ảnh qua UART (STREAM_10K) ----------------
.PHONY: sim-bv10k build-bv10k load-bv10k run-bv10k
bv10k/firmware.hex: $(M1S)/v10k/firmware.hex
	@mkdir -p bv10k
	cp $< $@

bv10k/imgs3.bin:
	@mkdir -p bv10k
	../../.venv/bin/python ../../scripts/m1s_10k.py --n 3 --export $@

Vsoc_b10k: $(CORE) sim_main_10k_b.cpp
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    -GFAST_ADDR=1 -GWITH_DOT4=1 \
	    --top-module soc_b -Mdir obj_dir10k -o ../Vsoc_b10k $(CORE) sim_main_10k_b.cpp \
	    2>&1 | tee verilator10k.log

sim-bv10k: Vsoc_b10k bv10k/firmware.hex bv10k/imgs3.bin
	cd bv10k && ../Vsoc_b10k --imgs imgs3.bin --n 3 2>&1 | tee sim.log
	@grep -c "^M1S10K," bv10k/sim.log

bv10k/top-synth.json: top_b.v $(CORE) bv10k/firmware.hex
	cd bv10k && yosys -l yosys.log -p "read_verilog -DMYCORE_MUL_DSP ../top_b.v ../soc_b.v \
	    ../mycore.v ../../uart/uart_tx.v ../../uart/uart_rx.v; \
	    chparam -set DIV_UART 234 -set FAST_ADDR 1 -set BEACON 0 -set WITH_DOT4 1 top; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

bv10k/pnr.json: bv10k/top-synth.json $(CST)
	nextpnr-himbaechel -l bv10k/nextpnr.log --json $< --write $@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report bv10k/report.json

bv10k/top.fs: bv10k/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

build-bv10k: bv10k/top.fs
load-bv10k: bv10k/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a bv10k/load.log

N10K ?= 100
run-bv10k:
	../../.venv/bin/python ../../scripts/m1s_10k.py --port $(UART_PORT) --n $(N10K) \
	    --variant B-V1+DOT4+C1 --csv $(RESULTS)/m1s_b_$(N10K).csv \
	    --log bv10k/run_$(N10K).log 2>&1 | tee bv10k/run_stdout_$(N10K).log

# ---------------- thiết kế tối giản để khoanh vùng (cổng B3) ----------------
min/top-synth.json: top_min.v ../uart/uart_tx.v
	@mkdir -p min
	cd min && yosys -l yosys.log -p "read_verilog ../top_min.v ../../uart/uart_tx.v; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

min/pnr.json: min/top-synth.json $(CST)
	nextpnr-himbaechel -l min/nextpnr.log --json $< --write $@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report min/report.json

min/top.fs: min/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

build-min: min/top.fs
load-min: min/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a min/load.log
all: build-bv0 build-bv1

# ---------------- mô phỏng dùng chung ----------------
# Mô hình Verilator phải dùng CÙNG FAST_ADDR với bitstream, nếu không thì phép so
# "kit = Verilator" vô nghĩa. Vì vậy tên nhị phân mang theo giá trị FAST_ADDR.
Vsoc_b$(FAST_ADDR)$(WITH_DOT4): $(CORE) sim_main_b.cpp
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    -GFAST_ADDR=$(FAST_ADDR) -GWITH_DOT4=$(WITH_DOT4) \
	    --top-module soc_b -Mdir obj_dir$(FAST_ADDR)$(WITH_DOT4) \
	    -o ../Vsoc_b$(FAST_ADDR)$(WITH_DOT4) $(CORE) sim_main_b.cpp \
	    2>&1 | tee verilator$(FAST_ADDR)$(WITH_DOT4).log

rvtests: Vsoc_b$(FAST_ADDR)$(WITH_DOT4)
	sh ../../scripts/riscv_tests.sh rvt$(FAST_ADDR)$(WITH_DOT4) ./Vsoc_b$(FAST_ADDR)$(WITH_DOT4) 2>&1 \
	    | tee $(RESULTS)/B1/riscv_tests_fa$(FAST_ADDR)_dot4$(WITH_DOT4).txt

# ---------------- B-V0 / B-V1 ----------------
# $(1) = tên biến thể nhánh B, $(2) = thư mục firmware nhánh A, $(3) = nhãn kit báo
define BVAR
.PHONY: sim-$(1) build-$(1) load-$(1) check-$(1)

$(1)/firmware.hex: $(M1S)/$(2)/firmware.hex
	@mkdir -p $(1)
	cp $$< $$@

sim-$(1): Vsoc_b$$(FAST_ADDR)$$(WITH_DOT4) $(1)/firmware.hex
	cd $(1) && ../Vsoc_b$$(FAST_ADDR)$$(WITH_DOT4) --stop-on "M1S,done" \
	    --max-cycles 400000000 2>&1 | tee sim.log
	@grep -q "M1S,sum,10,10,10,10" $(1)/sim.log || (echo "SIM KHONG DAT"; exit 1)

$(1)/top-synth.json: top_b.v $(CORE) $(1)/firmware.hex
	cd $(1) && yosys -l yosys.log -p "read_verilog -DMYCORE_MUL_DSP ../top_b.v ../soc_b.v ../mycore.v \
	    ../../uart/uart_tx.v ../../uart/uart_rx.v; \
	    chparam -set DIV_UART $(DIV_UART) -set FAST_ADDR $(FAST_ADDR) -set BEACON $(BEACON) -set WITH_DOT4 $(WITH_DOT4) top; \
	    synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json top-synth.json -setundef"

$(1)/pnr.json: $(1)/top-synth.json $(CST)
	nextpnr-himbaechel -l $(1)/nextpnr.log --json $$< --write $$@ \
	    --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	    --freq $(FREQ) --report $(1)/report.json

$(1)/top.fs: $(1)/pnr.json
	gowin_pack -d $(FAMILY) -o $$@ $$<

build-$(1): $(1)/top.fs

load-$(1): $(1)/top.fs
	openFPGALoader -b $(BOARD) $$< 2>&1 | tee -a $(1)/load.log

check-$(1):
	python3 ../../scripts/m1s_check.py --variant $(3) --sim-log $(1)/sim.log \
	    --csv $(RESULTS)/m1s_b.csv $$(if $$(CSV_APPEND_SET),$$(CSV_APPEND),$(4)) \
	    --port $(UART_PORT) --drain 2 --repeat 2 \
	    --src-hash $(SRC_HASH) --csv-label $(1) \
	    --log $(1)/check.log 2>&1 | tee $(1)/check_stdout.log
endef

# bv0/bv1  : FAST_ADDR=1 (địa chỉ tổ hợp, 1 chu kỳ/lệnh)
# bv0r/bv1r: FAST_ADDR=0 (ghi thanh ghi địa chỉ) — dựng vào thư mục RIÊNG để hai
#            bitstream cùng tồn tại, nhờ vậy đo được cả hai trong một lượt.
$(eval $(call BVAR,bv0,v0,A-V0,))
$(eval $(call BVAR,bv1,v1,A-V1,--append))
$(eval $(call BVAR,bv0r,v0,A-V0,--append))
$(eval $(call BVAR,bv1r,v1,A-V1,--append))
# Cổng B4: DOT4 trong tầng thực thi. Dùng lại ĐÚNG firmware DOT4 của nhánh A.
$(eval $(call BVAR,bv2,v2,A-V2,--append))
$(eval $(call BVAR,bv1d,v1d,A-V1+DOT4,--append))
$(eval $(call BVAR,bv1dc,v1dc,A-V1+DOT4+C1,--append))

archive:
	@mkdir -p $(RESULTS)
	@for v in bv0 bv1 bv0r bv1r bv2 bv1d bv1dc; do \
	    if [ -f $$v/report.json ]; then echo "===== $$v ====="; \
	        python3 ../../scripts/pnr_report.py $$v/report.json | tee $$v/resources.txt; fi; \
	done
	@RESULTS_BASE=results/branch_b sh ../../scripts/archive_gate.sh core . mycore.v soc_b.v top_b.v sim_main_b.cpp Makefile
	@for v in bv0 bv1 bv0r bv1r bv2 bv1d bv1dc; do [ -d $$v ] && RESULTS_BASE=results/branch_b sh ../../scripts/archive_gate.sh core/$$v $$v; done

clean:
	rm -rf bv0 bv1 bv0r bv1r bv2 bv1d bv1dc bv10k min obj_dir* Vsoc_b* rvt* verilator*.log
