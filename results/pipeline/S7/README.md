# S7 — bộ nhớ hai cổng kiểu Harvard (B-V4): phép kiểm K2 của mô hình chi phí

**Dự báo mức A, đóng băng TRƯỚC khi viết RTL: 243.641 chu kỳ (1,3047×).
Đo bằng Verilator: 243.641 chu kỳ. Sai số: 0,00 %.**

Đây là ứng viên **mức A** đầu tiên được hiện thực: không sửa một dòng mã phần mềm, không
thêm lệnh nào — chỉ hạ `λ_load` và `λ_store` từ 2 về 1. Vì `n_c` giữ nguyên nên
`ΔC = Σ n_c·Δλ_c` là **đẳng thức**, không phải chặn. Số đo xác nhận đúng như vậy.

## 1. Thiết kế

`mycore` vốn dùng **một cổng bộ nhớ chung** cho nạp lệnh và truy cập dữ liệu: ở `S_EXEC`,
lệnh load/store chiếm cổng cho dữ liệu nên lệnh kế phải nạp ở chu kỳ sau (`S_MEM`) → 2 chu kỳ.

`DUAL_PORT=1` thêm **cổng lệnh riêng** (`imem_addr`/`imem_rdata`). Ở `S_EXEC`, lõi đặt
**đồng thời** địa chỉ dữ liệu (cổng D) và địa chỉ lệnh kế (cổng I) → bỏ hẳn `S_MEM`,
load/store về **1 chu kỳ**.

Hệ quả bắt buộc: kết quả load chỉ về ở chu kỳ **sau**, đúng lúc lệnh kế cũng đang ghi
thanh ghi. Nên cần thêm:

1. **Cổng ghi thứ hai** của tệp thanh ghi (`rf2_we/rf2_wa/rf2_wd`), với cổng 1 ưu tiên
   khi trùng thanh ghi (kết quả load là của lệnh cũ hơn).
2. **Đường chuyển tiếp** (`ld_fwd`): lệnh ngay sau một load mà đọc thanh ghi vừa nạp thì
   lấy `ld_val` thay vì `regs[]`. Không có đường này thì phải chèn chu kỳ dừng cho
   **18,3 %** số load và λ_load không về được 1.

RAM phải thu từ 64 KB xuống **32 KB** vì BSRAM hai cổng của GW2AR mất một nửa mật độ mỗi
khối. Firmware liên kết bằng `fw/link32.ld` với `STACK_TOP=0x8000`
(`make fw RAMKB=32`). `fw/link.ld` và hành vi mặc định **không đổi**.

## 2. Số đo — và hai phép đối chứng

| cấu hình | RAM | `DUAL_PORT` | chu kỳ/ảnh | ms | chu kỳ/MAC | IPC | ảnh/s |
|---|---|---|---:|---:|---:|---:|---:|
| B-V3+PMAX4 (64 KB, đã đo trên kit) | 64 KB | 0 | 317.878 | 11,8 | 1,66 | 0,743 | 84,9 |
| **B-V3+PMAX4@32K** (đối chứng) | 32 KB | 0 | **317.878** | 11,8 | 1,66 | 0,743 | 84,9 |
| **B-V4** | 32 KB | **1** | **243.641** | **9,0** | **1,27** | **0,970** | **110,8** |

**Đối chứng 1 — liên kết lại 32 KB không đổi số chu kỳ.** Firmware 32 KB chạy trên lõi
MỘT cổng cho **đúng 317.878** chu kỳ, y như bản 64 KB. Hai bản chỉ khác đúng một lệnh
(`lui sp,0x8` thay vì `lui sp,0x10`), nên mọi chênh lệch dưới đây là **thuần vi kiến trúc**.
Log: `verilator_bs7ref.log`.

**Đối chứng 2 — đúng từng bit.** CRC 5 tensor × 10 ảnh **giống hệt** giữa một cổng và hai
cổng; `instret` **giống hệt** (236.313); cả 10 ảnh đều 317.878 → 243.641.
Log: `verilator_bs7dp.log`.

Phân rã theo lớp (trung vị): conv1 109.636 (45,0 %) · pool1 3.288 · conv2 123.702 (50,8 %)
· pool2 1.421 · dense 5.594. `conv2` xuống **0,89 chu kỳ/MAC** — dưới 1, vì DOT4 làm 4 MAC
mỗi lệnh.

**IPC = 0,970.** Gần một lệnh mỗi chu kỳ. Nhánh A trên PicoRV32 là 0,151.

## 3. Cổng kiểm chứng

| cổng | kết quả | log |
|---|---|---|
| ISS = Verilator, từng lớp từng ảnh | **BẰNG TUYỆT ĐỐI** (243.641/243.641) | `cdp iss --target B-V4` |
| CRC 5 tensor × 10 ảnh vs golden Python | **ĐẠT** | `verilator_bs7dp.log` |
| riscv-tests RV32IM | **48/48 ĐẠT**, `fence_i` ĐẠT | `riscv_tests_bs7dp.log` |
| `ma_data` (ngoài RV32IM) | KHÔNG ĐẠT — **y như mọi cấu hình trước**, truy cập lệch địa chỉ cố ý trap | như trên |
| `SRC_HASH` firmware tự báo | `a7dca19c8cec` ✓ | `cdp sim --spec s7_dualport.yaml` |
| Fmax ≥ 27 MHz | **ĐẠT** 53,01 MHz | `report_bs7dp.json` |
| vừa ngân sách FPGA | **ĐẠT** nhưng sát: LUT4 75,9 % | `resources_bs7dp.txt` |

## 4. Giá phần cứng — đây là chỗ ứng viên này đắt

Cùng một file RTL, chỉ khác tham số `DUAL_PORT`:

| | LUT4 | DFF | BSRAM | `RAM16SDP4` | MULT18X18 | Fmax |
|---|---:|---:|---:|---:|---:|---:|
| `DUAL_PORT=0` | 4.459 (21,5 %) | 580 | 32 × `SP` | **32** | 4 | 59,08 MHz |
| `DUAL_PORT=1` | **15.736 (75,9 %)** | 1.661 | 32 × `DPB` | **0** | 4 | 53,01 MHz |
| chênh | **+11.277** (×3,5) | +1.081 | 0 khối | −32 | 0 | −6,07 MHz |

Số khối BSRAM **không tăng** (32 → 32) đúng như phép dò khả thi đã đoán. Nhưng LUT4 tăng
**3,5 lần**. Phải truy ra nguyên nhân, không được báo cáo khi chưa hiểu.

### Nguyên nhân: cổng ghi thứ hai phá mất RAM phân tán của tệp thanh ghi

Ba lần tổng hợp Yosys, cùng mọi thứ trừ một thay đổi mỗi lần:

| | LUT1-4 | MUX2_LUT* | `RAM16SDP4` | `SP` | `DPB` |
|---|---:|---:|---:|---:|---:|
| `DUAL_PORT=0` | 4.263 | 978 | **32** | 32 | 0 |
| `DUAL_PORT=1`, **một** cổng ghi *(bản dò — SAI chức năng, chỉ để quy trách nhiệm diện tích)* | 5.943 | 2.538 | **32** | 0 | 32 |
| `DUAL_PORT=1`, **hai** cổng ghi *(bản thật)* | **14.667** | **8.637** | **0** | 0 | 32 |

- bản thân bộ nhớ hai cổng: **+1.680 LUT**
- **riêng cổng ghi thứ hai: +8.724 LUT, +6.099 MUX**

Lý do: tệp thanh ghi 32×32 với **một** cổng ghi và hai cổng đọc tổ hợp được Yosys map vào
**32 khối `RAM16SDP4`** (RAM phân tán của GW2A). Thêm cổng ghi thứ hai thì nó **không map
được nữa** (`RAM16SDP4` 32 → 0) và rơi về flip-flop cộng mux 32:1 cho mỗi bit.

**Đây là tương tác vi kiến trúc ↔ nguyên thuỷ FPGA mà mô hình λ hoàn toàn không thấy** —
đúng giới hạn số 2 đã ghi trước ở `docs/MO_HINH_CHI_PHI.md`: *"không mô hình hoá chi phí
LUT"*. Mô hình dự báo **chu kỳ** đúng tuyệt đối và **không nói gì** về diện tích.

### So hiệu quả hai ứng viên đã hiện thực

| ứng viên | tăng tốc | LUT4 thêm | LUT4 cho mỗi 1 % tăng tốc |
|---|---:|---:|---:|
| PMAX4 | 1,1514× | +148 | **9,8** |
| bộ nhớ hai cổng | 1,3047× | +11.277 | **370** |

Chênh **38 lần** về hiệu quả diện tích. Cả hai đều ĐẠT ràng buộc, nhưng nếu phải chọn một
dưới ngân sách LUT chặt thì PMAX4 thắng áp đảo.

## 5. Bước tiếp theo mà kết quả này chỉ ra

Cổng ghi thứ hai là **77 %** chi phí LUT của ứng viên. Có kỹ thuật FPGA chuẩn để làm tệp
thanh ghi nhiều cổng ghi mà vẫn dùng RAM phân tán: giữ **hai bản sao** tệp thanh ghi (mỗi
bản một cổng ghi) cộng một **bảng giá trị sống** (live value table) 32 × 1 bit cho biết bản
nào mới hơn. Dự kiến tốn ~64 `RAM16SDP4` + vài chục LUT thay vì +8.724 LUT. Chưa làm, chưa
đo — ghi lại làm ứng viên tiếp theo, và lần này dự báo **diện tích** cũng phải ghi trước.

## 6. Lệnh tái lập

```bash
# firmware 32 KB
cd experiment/m1s_s6 && make fw KERNELS=cand/pmax4.c OUT=cdp32 RAMKB=32
# mô phỏng: đối chứng một cổng, rồi hai cổng
cd rtl/mycore
make sim-bs7ref FAST_ADDR=1 WITH_DOT4=1 WITH_REQ=1 WITH_PMAX4=1 DUAL_PORT=0
make sim-bs7dp  FAST_ADDR=1 WITH_DOT4=1 WITH_REQ=1 WITH_PMAX4=1 DUAL_PORT=1
# bộ kiểm kiến trúc trên lõi hai cổng (RAM 32 KB)
RVT_LD=link_test32.ld RVT_WORDS=8192 RVT_STACK=0x00008000 \
  make rvtests FAST_ADDR=1 WITH_DOT4=1 WITH_REQ=1 WITH_PMAX4=1 DUAL_PORT=1
# tổng hợp + Fmax
make build-bs7dp FAST_ADDR=1 WITH_DOT4=1 WITH_REQ=1 WITH_PMAX4=1 DUAL_PORT=1
# qua pipeline
./cdp sim --spec pipeline/specs/s7_dualport.yaml
./cdp iss --target "B-V4"
```

## 7. Đo trên kit — ĐẠT (2026-10-18, lần thử 2)

**243.641 chu kỳ trên kit thật, bằng tuyệt đối số Verilator và bằng tuyệt đối dự báo mức A
đã đóng băng trước khi viết RTL. Sai số dự báo: 0,00 %.**

Run `pipeline/runs/20261018-214712-kit` (log thô: `kit/20261018-214712-kit/`):

| tiêu chí ghi nhận | kết quả |
|---|---|
| đối chứng TRƯỚC (`min/top.fs`) | ĐẠT — "MIN" 8 lần trên `...171` |
| CRC 5 tensor × 10 ảnh vs golden Python | **ĐẠT 10/10** |
| dự đoán khớp golden | **10/10** (nhãn `[7,2,1,0,4,1,4,9,5,9]`) |
| chu kỳ kit = Verilator **từng ảnh** | **BẰNG TUYỆT ĐỐI** (10/10 ảnh đều 243.641) |
| **2/2 lần đọc độc lập** | **ĐẠT** (`lần_đọc_đạt=2/2`) |
| chốt `SRC_HASH` | **có** (`a7dca19c8cec`) |
| số dòng CSV | 10/10 |

Tức **thoả đủ mọi tiêu chí trong MỘT run duy nhất** — điều dòng PMAX4 vẫn còn thiếu.

Phân rã trên kit (trung vị): conv1 109.636 (45,0 %) · pool1 3.288 · conv2 123.702 (50,8 %) ·
pool2 1.421 · dense 5.594. **9,0 ms · 110,8 ảnh/s · 1,27 chu kỳ/MAC · 36,89× so A-V0.**

Dòng B-V4 đã vào bảng chính của `docs/KET_QUA_TONG_HOP.md` (dòng 16).

### Lần thử 1 — 2026-10-18, run `pipeline/runs/20261018-212201-kit`

Trước phép đo, đường UART được kiểm riêng bằng thiết kế đã biết chạy (`min/top.fs`): đọc được
40 byte, thấy "MIN" 8 lần. Rồi chạy `./cdp kit --spec pipeline/specs/s7_dualport.yaml`:

| bước | kết quả |
|---|---|
| firmware `cdp32` (RAMKB=32) | rc=0 · sha256 `2c5641d3d800a8c4…` |
| tổng hợp `bs7dp` trong cây bóng | rc=0 · 1.139,6 s · bitstream 7.261.470 byte |
| **đối chứng TRƯỚC** (`min/top.fs`) | ĐẠT — "MIN" **1.342 lần** trên `...171` |
| nạp `bs7dp/top.fs` (SRAM) | rc=0 |
| `m1s_check.py` 2/2 lượt | **0 dòng thô** → `M1S_FAIL` |
| **đối chứng SAU** (`min/top.fs`) | **KHÔNG ĐẠT — 0 byte cả hai cổng** |

**Phân loại: đường đo chết, không phải lỗi thiết kế.** Cùng một thiết kế `min` phát 1.342 lần
"MIN" trước phép đo và 0 byte sau phép đo. JTAG vẫn sống suốt (`idcode 0x81b`, nạp `DONE`).
Đúng triệu chứng đã ghi nhiều lần của kênh UART trên FT2232: chết trong lần truyền dài
(M1-S in ~4.650 byte/lượt), không chết với chuỗi ngắn.

Ba hướng gỡ không cần tay người, tất cả **thất bại**: (1) nạp lại `min` rồi đọc 3 s;
(2) đảo DTR/RTS rồi đọc lại; (3) `openFPGALoader --reset` → nạp lại `min` → đọc 6 s.
Hết ba hướng → dừng, cần người dùng rút/cắm lại cáp USB (quy tắc 2 và 4).

CSV được `csv_restore()` trả nguyên trạng: 0 dòng mới, không mất dòng cũ.

### Kết quả phụ: luồng tổng hợp tái lập TỪNG BIT

Lần tổng hợp này chạy trong cây bóng `pipeline/work/s1`, độc lập với lần dựng trước ở
`rtl/mycore/bs7dp/`. Hai bitstream **giống hệt từng bit** (7.261.470 byte, sha256
`22bbbe32918954ef…`), và `report.json` khớp hoàn toàn cả ba trường `utilization`, `fmax`
(53,011024475 MHz), `critical_paths`. Tức luồng yosys → nextpnr-himbaechel → gowin_pack là
**tất định** cho thiết kế này, kể cả ở mức chiếm chip 75,9 % — mọi số tài nguyên và Fmax trong
mục 4 đều dựng lại được.
