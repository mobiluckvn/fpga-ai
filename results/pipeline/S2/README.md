# S2 — ISS RV32IM + mô hình chu kỳ · ĐẠT trên cả 14 cấu hình

Lệnh: `./cdp iss --calibrate picorv32` rồi `./cdp iss --all`.
Lý thuyết: `docs/MO_HINH_CHI_PHI.md`. ISS đếm $n_c$; mô hình cho $\lambda_c$; $C=\sum n_c\lambda_c$.

## 1. Tiêu chí ĐẠT của S2 và kết quả

| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | CRC ISS = golden cho cả 14 cấu hình | **ĐẠT** 14/14 |
| 2 | mycore: chu kỳ ISS = Verilator **tuyệt đối** từng lớp | **ĐẠT** 8/8 cấu hình, 0,0 % |
| 3 | PicoRV32: sai số từng lớp ≤ 2 % | **ĐẠT, vượt xa** — 6/6 cấu hình **bằng tuyệt đối 0,0 %** |
| 4 | Thời gian ISS cho một ảnh ≤ 30 s | **ĐẠT** — 1,4 s/ảnh (chậm nhất: A-V0, 29,7 s cho 10 ảnh) |

## 2. Mười bốn cấu hình: ISS so với Verilator

| cấu hình | lõi | ISS | Verilator | từng lớp × từng ảnh | sai số | CRC |
|---|---|---:|---:|---|---:|---|
| A-V0 | picorv32 | 8.987.660 | 8.987.660 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| A-V1 | picorv32 | 6.217.634 | 6.217.634 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| A-V2 | picorv32 | 5.758.001 | 5.758.001 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| A-V1+DOT4 | picorv32 | 2.917.079 | 2.917.079 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| A-V1+DOT4+C1 | picorv32 | 2.450.494 | 2.450.494 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| A-V3 | picorv32 | 1.842.219 | 1.842.219 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| B-V0r | mycore | 3.750.617 | 3.750.617 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| B-V1r | mycore | 2.713.235 | 2.713.235 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| B-V0 | mycore | 1.978.697 | 1.978.697 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| B-V1 | mycore | 1.459.993 | 1.459.993 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| B-V2 | mycore | 1.169.050 | 1.169.050 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| B-V1+DOT4 | mycore | 631.130 | 631.130 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| B-V1+DOT4+C1 | mycore | 487.865 | 487.865 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |
| B-V3 | mycore | 365.992 | 365.992 | BẰNG TUYỆT ĐỐI | 0.0 % | khớp golden |

Sáu cấu hình PicoRV32 dùng mô hình **hiệu chuẩn** (`timing_picorv32.yaml`), tám cấu hình mycore dùng
mô hình **đọc từ RTL** (`timing_mycore.yaml`). Cả hai đều cho **bằng tuyệt đối từng lớp, từng ảnh**.

## 3. λ hiệu chuẩn của PicoRV32

Hệ 300 phương trình (6 cấu hình × 10 ảnh × 5 lớp), phần dư **0.000 %** lớn nhất.

| lớp lệnh | λ |
|---|---:|
| alu | 5 |
| shift | 5 |
| branch_taken | 9 |
| branch_nt | 5 |
| jal | 5 |
| jalr | 8 |
| load | 9 |
| store | 9 |
| mul | 6 |
| csr | 5 |
| custom_dot4 | 6 |
| custom_req | 6 |

Mọi λ đọc được nhất quán theo dạng **"số chu kỳ lệnh + 2 chu kỳ mỗi lần dùng bus"**, và phép hiệu
chuẩn tự tìm lại hai tham số RTL mà nó không được cho biết: `BARREL_SHIFTER=1` (λ_shift = λ_alu = 5)
và `ENABLE_FAST_MUL=1` (λ_mul = 6). Chi tiết và chiều suy biến đã gỡ: `docs/MO_HINH_CHI_PHI.md` 1.4.

## 4. Phép kiểm K1 — lý thuyết tự kiểm được bằng số ISS đếm

`./cdp iss --check-k1` → `k1.json`, `k1.log`.

Khẳng định: chỉ từ **bốn con số đo** (chu kỳ của cặp `FAST_ADDR=1/0`, số lệnh trong cửa sổ đo) cộng bảng
λ **đọc từ RTL**, giải hệ hai ẩn ra được thành phần lệnh động — không cần mô phỏng.

| firmware | n_mem suy ra | n_mem ISS đếm | n_mul suy ra | n_mul ISS đếm |
|---|---:|---:|---:|---:|
| v0 (C thẳng) | 413.735 | **413.735** | 206.778 | **206.778** |
| v1 (đã tối ưu) | 341.337 | **341.337** | 206.752 | **206.752** |

**20/20 ảnh khớp tuyệt đối.** Và kiểm chéo bằng cấu trúc mô hình, không dùng phép đo nào:
192.064 MAC + 2 × 7.344 lần requantize = **206.752** = đúng `n_mul` của v1.

## 4b. Dữ liệu cho S3

`n_c_theo_lop.csv` — 70 dòng (14 cấu hình × 5 lớp mạng): số lệnh động theo 14 lớp lệnh, chu kỳ và
instret trung vị của từng lớp mạng. Đây là đầu vào của profile 3 tầng ở S3.
`uart/*.txt` — đầu ra UART thô của ISS cho từng cấu hình (có đúng các dòng `M1S,*` như `sim.log`).
