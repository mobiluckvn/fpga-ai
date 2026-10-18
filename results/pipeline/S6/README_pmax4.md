# S6 phần 2 — Hiện thực ứng viên PMAX4: dự báo sai 0,37 %, đúng từng bit

Ứng viên do **bước S5 sinh ra ở chế độ mù** (4/6 lần chạy AI đề xuất), nhắm vào chỗ mà
phân tích S3 đã chỉ ra là **chưa tối ưu nào chạm tới**: `pool1`+`pool2` chiếm 15,0 %
chu kỳ của B-V3 và 34 % chu kỳ của chúng là lệnh so sánh/chọn, nên DOT4 vô dụng ở đó.

Lệnh: `custom-0 (0x0B), funct3 = 010, funct7 = 0000000` ·
`rd[i] = max( (int8)rs1[i], (int8)rs2[i] )` cho i = 0..3 · **1 chu kỳ**.

## 1. Dự báo (đóng băng TRƯỚC khi hiện thực) so với đo thật

| | chu kỳ/ảnh | tăng tốc |
|---|---:|---:|
| B-V3 (gốc) | 365.992 | 1,000× |
| **dự báo**, ghi trước khi viết một dòng nào | **316.695** | **1,1557×** |
| **đo thật (ISS, đã xác nhận bằng RTL)** | **317.878** | **1,1514×** |
| | | **sai số +0,37 %** |

Chu kỳ từng lớp: `pool1` **42.472 → 4.978** (8,5×) · `pool2` **12.519 → 1.921** (6,5×);
ba lớp còn lại không đổi một chu kỳ nào (138.213 / 165.152 / 7.614).
Số lệnh PMAX4 chạy: **1.314 mỗi ảnh** = đúng (169·2 + 25·4)·3 theo cấu trúc hình học.

### Vì sao dự báo này chính xác hơn hẳn DOT4 và REQ
| ứng viên | dự báo | đo thật | sai số |
|---|---:|---:|---:|
| DOT4 | 1,524× | 2,313× | −34,1 % |
| REQ | 1,180× | 1,333× | −11,5 % |
| **PMAX4** | **1,1557×** | **1,1514×** | **+0,37 %** |

Vòng pooling đủ đơn giản để trình biên dịch sinh ra **gần đúng** chuỗi lệnh đã giả định
(4 nạp từ + 3 PMAX4 + 1 lưu từ cho mỗi 4 kênh), nên mô hình không bỏ sót hiệu ứng phụ
nào. Với DOT4 và REQ thì việc biến đổi mã **còn cắt thêm** chi phí địa chỉ/vòng lặp mà
dự báo mức B không tính — đó là nguồn của sai số −34 % và −11,5 %.

**Kết luận cho PQ1**: độ chính xác của dự báo mức B **không phải một hằng số**, nó phụ
thuộc việc biến đổi mã có kéo theo thay đổi khác hay không. Dự báo tốt nhất (0,37 %)
đạt được khi lệnh mới **thay đúng một chỗ** trong một vòng lặp đơn giản.

## 2. Năm cổng kiểm chứng (SPEC 4.3) — ĐẠT HẾT

| cổng | kết quả |
|---|---|
| Vector ngẫu nhiên ≥ 1 triệu, RTL vs mô hình tham chiếu | **ĐẠT** — RTL và plugin ISS cho **cùng CRC `649A9D5E` trên 1.000.000 vector**; đúng 1.000.000 lệnh PMAX4 đã chạy. Dãy vector có ép trường hợp biên (−128, 127) mỗi 64 vector |
| `riscv-tests` với `WITH_PMAX4=1` | **ĐẠT 48/48** RV32IM (`fence_i` ĐẠT, `ma_data` không — đúng như lõi gốc, nằm ngoài RV32IM) |
| Đúng từng bit M1-S | **ĐẠT** — CRC32 cả 5 tensor × 10 ảnh khớp golden Python |
| ISS = Verilator **tuyệt đối** | **ĐẠT** — 317.878 = 317.878, từng lớp, từng ảnh |
| `SRC_HASH` khớp | **ĐẠT** |
| *(thêm)* Không hồi quy | **ĐẠT** — A-V0, B-V1, B-V3 với `WITH_PMAX4=0` bằng tuyệt đối số cũ |

## 3. Chi phí phần cứng — và cách đo nó cho đúng

Phép so **duy nhất** có nghĩa: **cùng file RTL, cùng firmware, khác đúng một tham số**.

| | `WITH_PMAX4=0` | `WITH_PMAX4=1` | chi phí của lệnh |
|---|---:|---:|---:|
| LUT4 | 4.211 | 4.359 | **+148** |
| ALU | 968 | 1.008 | **+40** |
| DFF | 580 | 580 | **0** |
| BSRAM | 32 | 32 | **0** |
| MULT18X18 | 4 | 4 | **0** |
| Fmax | 65,89 MHz | 55,26 MHz | **−10,63 MHz (−16 %)** — vẫn **2,05×** mức cần 27 MHz |

Lệnh này **không dùng khối nhân**, chỉ so sánh + chọn, nên không thêm DSP và không đụng
vào đường tới hạn của khối nhân.

### Bằng chứng MỚI cho cạm bẫy số 5 của dự án
`bv1dcr` đo **trước** khi thêm PMAX4 vào `mycore.v` cho LUT4 **5.073** / Fmax **55,82 MHz**.
`bs6off` — **cùng tham số**, `mycore.v` **tương đương logic** nhưng khác văn bản (thêm các
dây `pmax4_val` mà `WITH_PMAX4=0` làm chúng bị cắt bỏ) — cho LUT4 **4.211** / **65,89 MHz**.
Lệch **862 LUT4 (−17 %)** và **10 MHz**.

Nếu lấy hai số đó để tính chi phí của lệnh thì sẽ ra kết luận **vô lý rằng thêm lệnh làm
GIẢM 714 LUT4**. Tôi đã mắc đúng bẫy này trong phiên và phải tổng hợp lại bản
`WITH_PMAX4=0` trên cùng file RTL mới có số đúng. **Hệ quả: mọi con số "chi phí LUT của
một lệnh" chỉ đáng tin nếu nó đến từ một cặp A/B khác nhau đúng một tham số trên cùng
một file nguồn.**

## 4. Đo trên kit — ĐẠT (2026-10-18)

**317.878 chu kỳ trên kit thật, bằng tuyệt đối số Verilator. Dự báo mức B ghi trước khi
viết RTL: 316.695 — sai số +0,37 %.**

Run `kit/20261018-221645-kit` thoả **đủ** tiêu chí trong một run: CRC 5 tensor × 10 ảnh =
golden 10/10 · dự đoán khớp golden 10/10 · chu kỳ kit = Verilator bằng tuyệt đối từng ảnh ·
**2/2 lần đọc độc lập** · chốt `SRC_HASH` = `a7dca19c8cec` · 10/10 dòng CSV. Dòng 15 đã vào
bảng chính của `docs/KET_QUA_TONG_HOP.md`.

Phải mất **năm** lần thử, và nguyên nhân bốn lần hỏng trước nằm ở **script đo**, không phải
ở kit: `m1s_check.py` đóng cổng serial giữa hai lần đọc rồi mở lại, làm kẹt kênh FT2232.
Tuỳ chọn `--keep-open` sửa được ngay. Chi tiết: `kit/README.md`.

## 5. File

| file | nội dung |
|---|---|
| `du_bao_PMAX4_truoc_khi_hien_thuc.json` | **dự báo đóng băng**, kèm công thức và từng số hạng |
| `pmax4/ket_qua_pmax4.json` | kết quả đầy đủ: đo, sai số dự báo, 5 cổng kiểm, chi phí cô lập |
| `pmax4/vectors_rtl.log`, `pmax4/vectors_iss.log` | log 1 triệu vector trên RTL và trên ISS |
| `pmax4/riscv_tests_pmax4.log` | log 48 bài riscv-tests |
| `pmax4/verilator_pmax4_sim.log` | log Verilator của cấu hình mới |
| `pmax4/resources_bs6{off,ref,pmax4}.txt`, `report_*.json` | tài nguyên và Fmax ba bản tổng hợp |
| `../../experiment/m1s_s6/` | hạ tầng firmware S6 (kernel thay được) + `cand/pmax4.c` + `pmax4_vectors.c` |
| `../../rtl/mycore/mycore.v` | RTL: tham số `WITH_PMAX4`, **mặc định 0** |
