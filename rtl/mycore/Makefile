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
FAST_ADDR  ?= 0
BEACON     ?= 0

.PHONY: all rvtests archive clean min build-min load-min
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
Vsoc_b$(FAST_ADDR): $(CORE) sim_main_b.cpp
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal -CFLAGS "$(TN20K_CXX_INC)" \
	    -GFAST_ADDR=$(FAST_ADDR) \
	    --top-module soc_b -Mdir obj_dir$(FAST_ADDR) -o ../Vsoc_b$(FAST_ADDR) $(CORE) sim_main_b.cpp \
	    2>&1 | tee verilator$(FAST_ADDR).log

rvtests: Vsoc_b$(FAST_ADDR)
	sh ../../scripts/riscv_tests.sh rvt$(FAST_ADDR) ./Vsoc_b$(FAST_ADDR) 2>&1 \
	    | tee $(RESULTS)/B1/riscv_tests_mycore_fastaddr$(FAST_ADDR).txt

# ---------------- B-V0 / B-V1 ----------------
# $(1) = tên biến thể nhánh B, $(2) = thư mục firmware nhánh A, $(3) = nhãn kit báo
define BVAR
.PHONY: sim-$(1) build-$(1) load-$(1) check-$(1)

$(1)/firmware.hex: $(M1S)/$(2)/firmware.hex
	@mkdir -p $(1)
	cp $$< $$@

sim-$(1): Vsoc_b$$(FAST_ADDR) $(1)/firmware.hex
	cd $(1) && ../Vsoc_b$$(FAST_ADDR) --stop-on "M1S,done" --max-cycles 400000000 2>&1 | tee sim.log
	@grep -q "M1S,sum,10,10,10,10" $(1)/sim.log || (echo "SIM KHONG DAT"; exit 1)

$(1)/top-synth.json: top_b.v $(CORE) $(1)/firmware.hex
	cd $(1) && yosys -l yosys.log -p "read_verilog -DMYCORE_MUL_DSP ../top_b.v ../soc_b.v ../mycore.v \
	    ../../uart/uart_tx.v ../../uart/uart_rx.v; \
	    chparam -set DIV_UART $(DIV_UART) -set FAST_ADDR $(FAST_ADDR) -set BEACON $(BEACON) top; \
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
	    --csv $(RESULTS)/m1s_b.csv $(4) --port $(UART_PORT) --drain 2 --repeat 2 \
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

archive:
	@mkdir -p $(RESULTS)
	@for v in bv0 bv1 bv0r bv1r; do \
	    if [ -f $$v/report.json ]; then echo "===== $$v ====="; \
	        python3 ../../scripts/pnr_report.py $$v/report.json | tee $$v/resources.txt; fi; \
	done
	@RESULTS_BASE=results/branch_b sh ../../scripts/archive_gate.sh core . mycore.v soc_b.v top_b.v sim_main_b.cpp Makefile
	@for v in bv0 bv1 bv0r bv1r; do [ -d $$v ] && RESULTS_BASE=results/branch_b sh ../../scripts/archive_gate.sh core/$$v $$v; done

clean:
	rm -rf bv0 bv1 bv0r bv1r min obj_dir* Vsoc_b* rvt* verilator*.log
