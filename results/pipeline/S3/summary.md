# S3 — Profile 3 tầng và phân tích · giải thích bằng số từng hệ số đã đo

Lệnh: `./cdp analyze --all` (gọi `cdp profile` bên trong). Lý thuyết: `docs/MO_HINH_CHI_PHI.md`.
Dữ liệu: `analysis.json`, `profile.json`, `chu_ky_theo_lop_ngu_nghia.csv`,
`tong_hop_14_cau_hinh.csv`. Mọi con số dưới đây do ISS đếm và mô hình chu kỳ đã kiểm
bằng tuyệt đối với Verilator ở S2 — không có hệ số tay nào.

## 1. Đẳng thức kiểm tra

Tổng chu kỳ phân loại theo 7 lớp ngữ nghĩa **= tổng chu kỳ ISS**, khớp **14/14**
cấu hình, trên tổng 10 ảnh và trên từng lớp mạng. Nghĩa là mọi chu kỳ đều được gán cho đúng
một lớp, không có chu kỳ nào bị đếm hai lần hay bỏ sót.

## 2. Mười bốn cấu hình: tỷ trọng chu kỳ theo lớp ngữ nghĩa (%)

| cấu hình | lõi | chu kỳ/ảnh | mac | load_data | store_data | addr | loop_ctrl | requant | other |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A-V0 | picorv32 | 8.987.660 | 24.3 | 40.5 | 0.9 | 11.0 | 13.1 | 6.7 | 3.5 |
| A-V1 | picorv32 | 6.217.634 | 35.2 | 47.0 | 2.4 | 1.3 | 2.4 | 9.9 | 1.8 |
| A-V2 | picorv32 | 5.758.001 | 17.4 | 28.7 | 1.4 | 16.7 | 19.9 | 10.4 | 5.5 |
| A-V1+DOT4 | picorv32 | 2.917.079 | 35.8 | 30.0 | 3.0 | 2.8 | 5.0 | 19.1 | 4.3 |
| A-V1+DOT4+C1 | picorv32 | 2.450.494 | 32.7 | 25.2 | 4.8 | 5.0 | 8.7 | 18.2 | 5.4 |
| A-V3 | picorv32 | 1.842.219 | 31.1 | 33.1 | 6.4 | 8.8 | 11.6 | 2.4 | 6.6 |
| B-V0r | mycore | 3.750.617 | 26.4 | 43.1 | 1.0 | 10.6 | 9.4 | 6.3 | 3.2 |
| B-V1r | mycore | 2.713.235 | 36.5 | 47.9 | 2.4 | 1.2 | 1.6 | 9.0 | 1.4 |
| B-V0 | mycore | 1.978.697 | 29.9 | 40.9 | 0.9 | 10.0 | 9.0 | 6.3 | 3.0 |
| B-V1 | mycore | 1.459.993 | 40.5 | 44.5 | 2.3 | 1.1 | 1.5 | 8.8 | 1.3 |
| B-V2 | mycore | 1.169.050 | 19.9 | 31.4 | 1.6 | 16.4 | 14.9 | 10.8 | 5.1 |
| B-V1+DOT4 | mycore | 631.130 | 38.4 | 30.9 | 3.0 | 2.6 | 3.4 | 18.3 | 3.4 |
| B-V1+DOT4+C1 | mycore | 487.865 | 31.9 | 28.2 | 5.4 | 5.0 | 6.6 | 18.3 | 4.7 |
| B-V3 | mycore | 365.992 | 28.5 | 37.0 | 7.2 | 8.9 | 8.8 | 4.0 | 5.6 |

## 3. Giải thích từng hệ số đã đo — chênh lệch chu kỳ TUYỆT ĐỐI theo lớp

### 1,45× — tối ưu phần mềm (nhánh A, PicoRV32)

8.987.660 → 6.217.634 chu kỳ/ảnh = **1.446×**, cắt **2.770.026** chu kỳ.

| lớp ngữ nghĩa | A-V0 | A-V1 | chênh | % của tổng cắt |
|---|---:|---:|---:|---:|
| loop_ctrl | 1.173.542 | 146.314 | 1.027.228 | 37.1 % |
| addr | 990.435 | 82.855 | 907.580 | 32.8 % |
| load_data | 3.640.176 | 2.923.281 | 716.895 | 25.9 % |
| other | 314.824 | 114.334 | 200.490 | 7.2 % |
| requant | 598.879 | 615.889 | +17.010 | -0.6 % |
| store_data | 83.439 | 148.752 | +65.313 | -2.4 % |

### 1,36× — cùng tối ưu phần mềm đó, trên mycore

1.978.697 → 1.459.993 chu kỳ/ảnh = **1.355×**, cắt **518.704** chu kỳ.

| lớp ngữ nghĩa | B-V0 | B-V1 | chênh | % của tổng cắt |
|---|---:|---:|---:|---:|
| addr | 198.087 | 16.571 | 181.516 | 35.0 % |
| load_data | 808.928 | 649.618 | 159.310 | 30.7 % |
| loop_ctrl | 177.231 | 21.587 | 155.644 | 30.0 % |
| other | 59.261 | 19.163 | 40.098 | 7.7 % |
| requant | 125.651 | 129.053 | +3.402 | -0.7 % |
| store_data | 18.542 | 33.056 | +14.514 | -2.8 % |

### 4,26× — vi kiến trúc: đổi lõi, CÙNG firmware

6.217.634 → 1.459.993 chu kỳ/ảnh = **4.259×**, cắt **4.757.641** chu kỳ.

| lớp ngữ nghĩa | A-V1 | B-V1 | chênh | % của tổng cắt |
|---|---:|---:|---:|---:|
| load_data | 2.923.281 | 649.618 | 2.273.663 | 47.8 % |
| mac | 2.186.144 | 590.880 | 1.595.264 | 33.5 % |
| requant | 615.889 | 129.053 | 486.836 | 10.2 % |
| loop_ctrl | 146.314 | 21.587 | 124.727 | 2.6 % |
| store_data | 148.752 | 33.056 | 115.696 | 2.4 % |
| other | 114.334 | 19.163 | 95.171 | 2.0 % |
| addr | 82.855 | 16.571 | 66.284 | 1.4 % |

### 2,31× — lệnh DOT4

1.459.993 → 631.130 chu kỳ/ảnh = **2.313×**, cắt **828.863** chu kỳ.

| lớp ngữ nghĩa | B-V1 | B-V1+DOT4 | chênh | % của tổng cắt |
|---|---:|---:|---:|---:|
| load_data | 649.618 | 194.740 | 454.878 | 54.9 % |
| mac | 590.880 | 242.080 | 348.800 | 42.1 % |
| store_data | 33.056 | 19.246 | 13.810 | 1.7 % |
| requant | 129.053 | 115.502 | 13.551 | 1.6 % |
| other | 19.163 | 21.340 | +2.177 | -0.3 % |

### 1,29× — bố cục 4 pha cho conv1

631.130 → 487.865 chu kỳ/ảnh = **1.294×**, cắt **143.265** chu kỳ.

| lớp ngữ nghĩa | B-V1+DOT4 | B-V1+DOT4+C1 | chênh | % của tổng cắt |
|---|---:|---:|---:|---:|
| mac | 242.080 | 155.552 | 86.528 | 60.4 % |
| load_data | 194.740 | 137.494 | 57.246 | 40.0 % |
| requant | 115.502 | 89.085 | 26.417 | 18.4 % |
| other | 21.340 | 22.690 | +1.350 | -0.9 % |
| store_data | 19.246 | 26.336 | +7.090 | -4.9 % |
| addr | 16.570 | 24.314 | +7.744 | -5.4 % |
| loop_ctrl | 21.587 | 32.329 | +10.742 | -7.5 % |

### 1,33× — lệnh REQ

487.865 → 365.992 chu kỳ/ảnh = **1.333×**, cắt **121.873** chu kỳ.

| lớp ngữ nghĩa | B-V1+DOT4+C1 | B-V3 | chênh | % của tổng cắt |
|---|---:|---:|---:|---:|
| requant | 89.085 | 14.688 | 74.397 | 61.0 % |
| mac | 155.552 | 104.144 | 51.408 | 42.2 % |
| other | 22.690 | 20.461 | 2.229 | 1.8 % |
| load_data | 137.494 | 135.484 | 2.010 | 1.6 % |
| addr | 24.314 | 32.611 | +8.297 | -6.8 % |


## 4. Chặn trên: roofline bộ nhớ và ILP, theo từng lớp mạng

$\text{MAC/chu kỳ} \le B/b$ với $b$ = byte trên mỗi MAC (**đo**), $B$ = byte/chu kỳ bộ nhớ cấp
được = 4 byte mỗi lần truy cập / $\lambda_{load}$. mycore FAST_ADDR=1: $B=4/2=2$ byte/chu kỳ;
PicoRV32: $B=4/9=0{,}44$ byte/chu kỳ.

**B-V1** — 1.459.993 chu kỳ/ảnh, 54.1 ms

| lớp | chu kỳ | MAC/ck | byte/MAC | trần bộ nhớ | còn cách trần | giới hạn bởi | IPC thật | IPC lý tưởng |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| conv1 | 369.909 | 0.1316 | 1.149 | 1.7399 | 13.22× | compute/issue | 0.692 | 3.020 |
| pool1 | 42.472 | — | — | — | — | — | 0.841 | 3.755 |
| conv2 | 1.005.419 | 0.1386 | 4.516 | 0.4428 | 3.19× | compute/issue | 0.589 | 45.557 |
| pool2 | 12.519 | — | — | — | — | — | 0.84 | 1.060 |
| dense | 29.652 | 0.1349 | 2.038 | 0.9814 | 7.27× | compute/issue | 0.594 | 1.744 |

**B-V1+DOT4+C1** — 487.865 chu kỳ/ảnh, 18.1 ms

| lớp | chu kỳ | MAC/ck | byte/MAC | trần bộ nhớ | còn cách trần | giới hạn bởi | IPC thật | IPC lý tưởng |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| conv1 | 226.643 | 0.2148 | 1.668 | 1.1988 | 5.58× | compute/issue | 0.822 | 13.903 |
| pool1 | 42.472 | — | — | — | — | — | 0.841 | 4.633 |
| conv2 | 198.594 | 0.7019 | 1.152 | 1.7362 | 2.47× | compute/issue | 0.771 | 14.179 |
| pool2 | 12.519 | — | — | — | — | — | 0.84 | 1.295 |
| dense | 7.615 | 0.5253 | 2.02 | 0.9901 | 1.88× | compute/issue | 0.735 | 823 |

**B-V3** — 365.992 chu kỳ/ảnh, 13.6 ms

| lớp | chu kỳ | MAC/ck | byte/MAC | trần bộ nhớ | còn cách trần | giới hạn bởi | IPC thật | IPC lý tưởng |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| conv1 | 138.213 | 0.3522 | 1.591 | 1.2573 | 3.57× | compute/issue | 0.754 | 7.778 |
| pool1 | 42.472 | — | — | — | — | — | 0.841 | 4.633 |
| conv2 | 165.152 | 0.844 | 1.148 | 1.7425 | 2.06× | compute/issue | 0.737 | 12.300 |
| pool2 | 12.519 | — | — | — | — | — | 0.84 | 1.295 |
| dense | 7.614 | 0.5253 | 2.02 | 0.9901 | 1.88× | compute/issue | 0.735 | 823 |

Hai điều đọc ra ngay:

1. **ILP dư thừa ở mọi lớp** (IPC lý tưởng hàng trăm đến hàng nghìn, IPC thật 0,59–0,84). Nguyên
   nhân: GCC dùng con trỏ chạy nên mỗi tầng vòng lặp chỉ chuỗi phụ thuộc trong tầng của nó,
   không nhân lên. ⟹ **ILP không phải rào chắn**; rào chắn là độ rộng phát lệnh và cổng bộ nhớ.
2. **Rào bộ nhớ là thật và đã gần**: `conv2` ở B-V1 có 4,52 byte/MAC, còn **3,19×** là đụng trần;
   sau DOT4 + bố cục 4 pha, `conv2` chỉ còn **2,06×**. Một lệnh tính toán mạnh gấp 4 lần DOT4 sẽ
   **không** cho 4× — nó đụng rào băng thông trước.

## 5. Dự báo ứng viên L3 ngay từ mô hình — chưa viết một dòng RTL nào

L3 chỉ đổi $\lambda$, nên $\Delta C=\sum_c n_c\,\Delta\lambda_c$ tính trực tiếp từ $n_c$ ISS đã đếm.

| cấu hình | C đo | $n_{mem}$ | $n_{mul}$ | $n_{REQ}$ | bộ nhớ 2 cổng | nhân 1 ck | **cả hai** | IPC khi đó |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B-V1 | 1.459.993 | 341.337 | 206.752 | 0 | 1.305× | 1.165× | **1.601×** | 1.00 |
| B-V1+DOT4 | 631.130 | 106.993 | 63.360 | 0 | 1.204× | 1.112× | **1.370×** | 1.00 |
| B-V1+DOT4+C1 | 487.865 | 81.915 | 14.688 | 0 | 1.202× | 1.031× | **1.247×** | 1.00 |
| B-V3 | 365.992 | 80.825 | 0 | 7.344 | 1.283× | 1.020× | **1.317×** | 1.00 |

> **Kết luận chiến lược.** Toàn bộ phần còn lại của hướng *làm mỗi lệnh rẻ hơn* chỉ còn
> **1.317×** trên B-V3 (365.992 → 277.823 chu kỳ, 13.6 ms → 10.3 ms).
> Khi đạt được, IPC = 1,00 — **trần tuyệt đối của một lõi phát một lệnh mỗi chu kỳ**. Muốn đi xa
> hơn **buộc** phải rời mô hình đó (SIMD rộng hơn, phát nhiều lệnh, khối tăng tốc), và vì rào bộ
> nhớ ở mục 4, mọi hướng đó phải **kèm** giải pháp băng thông.

## 6. Hai lớp pooling: chỗ chưa ai chạm tới

Ở B-V3, `pool1` + `pool2` chiếm **15.0 %** tổng chu kỳ (54.991 chu kỳ)
và **chưa có bất kỳ tối ưu phần cứng nào** nhắm vào chúng (DOT4 và REQ đều không chạm tới).

| lớp | load_data | other | loop_ctrl | addr | store_data |
|---|---:|---:|---:|---:|---:|
| pool1 | 25.5 % | 34.1 % | 23.6 % | 10.3 % | 6.4 % |
| pool2 | 25.7 % | 34.7 % | 23.2 % | 10.0 % | 6.5 % |

`other` ở đây là lệnh so sánh/chọn giá trị lớn nhất — max-pooling không có phép nhân nào, nên
DOT4 không giúp được gì. Chặn Amdahl: xoá sạch hai lớp này cho tối đa **1.177×**.
Đây là ứng viên mà S5 nên tự tìm ra (lệnh lấy max 4 làn, hoặc gộp pooling vào conv).
