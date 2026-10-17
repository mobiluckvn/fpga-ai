# F8 — lệnh tùy biến DOT4 qua PCPI.
#
# SoC là của F5 (feasibility/F5_soc/soc.v) với WITH_DOT4 = 1, cộng khối
# rtl/ext/pcpi_dot4.v. Firmware chạy CẢ HAI bản của bài A trong một lần nạp.
#
# Hai biến thể bitstream (để trả lời "DSP hay LUT cho DOT4?"):
#   dsp : pcpi_dot4 gọi TRỰC TIẾP MULT18X18  (-DPCPI_DOT4_DSP) — cách ĐẠT ở F4
#   lut : pcpi_dot4 nhân hành vi -> `-nodsp` dựng bằng logic
# Cả hai đều build lõi với -nodsp (bắt buộc, xem F4/F5).
#
# Đích: data fw tbdot4 sim build-dsp build-lut load-dsp load-lut f8check check clean
# Cần: source ../../env/setup_env.sh

SOCDIR     := ../F5_soc
FWDIR      := ../../fw
HEX        := firmware.hex
DATA       := f8_data.h
CORE       := $(SOCDIR)/soc.v ../../rtl/picorv32/picorv32.v \
              ../../rtl/uart/uart_tx.v ../../rtl/uart/uart_rx.v ../../rtl/ext/pcpi_dot4.v
SIMSRC     := soc_f8.v $(CORE)
SYNSRC     := top_f8.v $(CORE)
RESULTS    := ../../results/feasibility/F8

CROSS      := riscv-none-elf-
ARCH       := -march=rv32im -mabi=ilp32
GIT_HASH   := $(shell git -C ../.. rev-parse --short HEAD 2>/dev/null || echo nogit)
OPT        ?= -O2
LAT_N      ?= 100000
CFLAGS     := $(ARCH) $(OPT) -ffreestanding -fno-builtin -nostdlib -nostartfiles \
              -fno-pic -mno-relax -Wall -Wextra -I$(FWDIR) -I. \
              -DGIT_HASH=\"$(GIT_HASH)\" -DLAT_N=$(LAT_N)u

DEVICE     := GW2AR-LV18QN88C8/I7
FAMILY     := GW2A-18C
YOSYS_FAM  := gw2a
BOARD      := tangnano20k
FREQ       := 27
CST        := ../../hw/tangnano20k.cst
UART_PORT  ?= /dev/cu.usbserial-20250303171

.PHONY: all data fw tbdot4 sim build build-dsp build-lut load-dsp load-lut \
        f8check-dsp f8check-lut check clean
all: build
build: build-dsp build-lut

# ---------- dữ liệu ----------
data: $(DATA)
$(DATA):
	python3 ../../scripts/gen_f8_data.py --out $@

# ---------- testbench RIÊNG cho khối DOT4 (1.000.000 cặp + biên) ----------
tbdot4: build/tb_dot4.vvp
	@echo "=== Icarus: testbench khối pcpi_dot4 ==="
	vvp $< 2>&1 | tee build/tb_dot4.log
	@grep -q F8_TB_PASS build/tb_dot4.log || (echo "TB KHOI KHONG DAT"; exit 1)

build/tb_dot4.vvp: tb_dot4.v ../../rtl/ext/pcpi_dot4.v
	@mkdir -p build
	iverilog -g2012 -o $@ tb_dot4.v ../../rtl/ext/pcpi_dot4.v

# ---------- firmware ----------
fw: $(HEX)

build/firmware.elf: main.c $(DATA) $(FWDIR)/start.S $(FWDIR)/link.ld $(FWDIR)/soc.h
	@mkdir -p build
	$(CROSS)gcc $(CFLAGS) $(ARCH) -nostdlib -nostartfiles -T $(FWDIR)/link.ld \
	    -Wl,--gc-sections -Wl,-Map=build/firmware.map -o $@ $(FWDIR)/start.S main.c
	$(CROSS)objdump -D $@ > build/firmware.dis
	@echo "--- kích thước firmware (RAM 65536 byte) ---"
	$(CROSS)size -A $@ | tee build/firmware.size.txt
	@echo "--- kiểm lệnh DOT4 đã sinh ra (opcode 0x0B) ---"
	@grep -c "0x0b\|\.insn\|custom" build/firmware.dis > /dev/null || true
	@$(CROSS)objdump -d $@ | grep -m3 -E "0b$$|unknown|\.insn" || true

$(HEX): build/firmware.elf
	$(CROSS)objcopy -O binary $< build/firmware.bin
	python3 ../../scripts/bin2hex.py build/firmware.bin $@ --words 16384

# ---------- mô phỏng Verilator (đường nhân hành vi) ----------
sim: build/Vsoc_f8 $(HEX)
	@echo "=== Verilator (DOT4, nhân hành vi) ==="
	build/Vsoc_f8 --stop-on "F8,done" 2>&1 | tee build/sim.log
	@grep -q "F8,done" build/sim.log || (echo "SIM KHONG DAT"; exit 1)

build/Vsoc_f8: $(SIMSRC) sim_main.cpp $(HEX)
	@mkdir -p build
	verilator --cc --exe --build -j 0 -O2 -Wno-fatal \
	    -CFLAGS "$(TN20K_CXX_INC)" \
	    --top-module soc_f8 -Mdir build/obj_dir -o ../Vsoc_f8 \
	    $(SIMSRC) sim_main.cpp 2>&1 | tee build/verilator.log

# ---------- biến thể DSP: DOT4 gọi MULT18X18 trực tiếp ----------
build-dsp: build_dsp/top.fs

build_dsp/top-synth.json: $(SYNSRC) $(HEX)
	@mkdir -p build_dsp
	yosys -l build_dsp/yosys.log \
	      -p "read_verilog -DPCPI_DOT4_DSP $(SYNSRC); synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json $@ -setundef"

build_dsp/pnr.json: build_dsp/top-synth.json $(CST)
	nextpnr-himbaechel -l build_dsp/nextpnr.log --json $< --write $@ \
	      --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) --report build_dsp/report.json

build_dsp/top.fs: build_dsp/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-dsp: build_dsp/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a build_dsp/load.log

f8check-dsp:
	python3 ../../scripts/f8_check.py --sim-log build/sim.log --variant dsp \
	    --size build/firmware.size.txt --csv $(RESULTS)/dot4.csv \
	    --f7-csv ../../results/feasibility/F7/kernel.csv \
	    --port $(UART_PORT) --drain 0 --repeat 3 \
	    --log build_dsp/f8_check.log 2>&1 | tee build_dsp/f8_check_stdout.log

# ---------- biến thể LUT: DOT4 nhân bằng logic ----------
build-lut: build_lut/top.fs

build_lut/top-synth.json: $(SYNSRC) $(HEX)
	@mkdir -p build_lut
	yosys -l build_lut/yosys.log \
	      -p "read_verilog $(SYNSRC); synth_gowin -top top -family $(YOSYS_FAM) -nodsp -json $@ -setundef"

build_lut/pnr.json: build_lut/top-synth.json $(CST)
	nextpnr-himbaechel -l build_lut/nextpnr.log --json $< --write $@ \
	      --device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST) \
	      --freq $(FREQ) --report build_lut/report.json

build_lut/top.fs: build_lut/pnr.json
	gowin_pack -d $(FAMILY) -o $@ $<

load-lut: build_lut/top.fs
	openFPGALoader -b $(BOARD) $< 2>&1 | tee -a build_lut/load.log

f8check-lut:
	python3 ../../scripts/f8_check.py --sim-log build/sim.log --variant lut \
	    --size build/firmware.size.txt --csv $(RESULTS)/dot4.csv --append \
	    --f7-csv ../../results/feasibility/F7/kernel.csv \
	    --port $(UART_PORT) --drain 0 --repeat 3 \
	    --log build_lut/f8_check.log 2>&1 | tee build_lut/f8_check_stdout.log

# ---------- thu kết quả ----------
check:
	@mkdir -p $(RESULTS)
	@for v in dsp lut; do \
	    if [ -f build_$$v/report.json ]; then \
	        echo "===== biến thể $$v ====="; \
	        python3 ../../scripts/pnr_report.py build_$$v/report.json | tee build_$$v/resources.txt; \
	        (printf 'bitstream: '; wc -c < build_$$v/top.fs | tr -d ' '; echo ' byte') \
	            | tr -d '\n' > build_$$v/bitstream_size.txt; echo >> build_$$v/bitstream_size.txt; \
	    fi; \
	done
	@python3 ../../scripts/gen_f8_data.py --out build/f8_data_check.h > build/data_info.txt
	@cmp -s $(DATA) build/f8_data_check.h && echo "f8_data.h tái lập đúng" || echo "CẢNH BÁO: f8_data.h khác bản sinh lại"
	@rm -f build/f8_data_check.h
	@cp -f $(HEX) build/firmware.hex
	@sh ../../scripts/archive_gate.sh F8 build main.c $(DATA) tb_dot4.v soc_f8.v top_f8.v ../../rtl/ext/pcpi_dot4.v
	@for v in dsp lut; do [ -d build_$$v ] && sh ../../scripts/archive_gate.sh F8/$$v build_$$v; done

clean:
	rm -rf build build_dsp build_lut $(HEX) $(DATA)
