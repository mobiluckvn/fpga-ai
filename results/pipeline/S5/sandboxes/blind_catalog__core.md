# Lõi đích: vi kiến trúc và số chu kỳ mỗi lệnh

Lõi RISC-V RV32IM tự viết, chạy trên FPGA ở **27 MHz cố định**.

| lớp lệnh | chu kỳ |
|---|---:|
| alu | 1 |
| shift | 1 |
| branch_taken | 1 |
| branch_nt | 1 |
| jal | 1 |
| jalr | 1 |
| csr | 1 |
| misc | 1 |
| load | 2 |
| store | 2 |
| mul | 2 |
| div | 34 |

Tính chất quan trọng:
- **Phát một lệnh mỗi chu kỳ**, máy trạng thái tất định, không đoán nhánh:
  nhánh nhảy hay không nhảy đều hết đúng 1 chu kỳ (không có hình phạt rẽ nhánh).
- **Không có cache.** Bộ nhớ là BSRAM trên chip, **MỘT CỔNG**: mỗi truy cập dữ
  liệu chiếm cổng nên lệnh kế phải nạp ở chu kỳ sau — đó là lý do load/store tốn
  2 chu kỳ. Băng thông tối đa 4 byte / 2 chu kỳ = 2 byte/chu kỳ.
- Nhân 32×32 dùng khối nhân cứng của FPGA, hiện tốn 2 chu kỳ; chia 34 chu kỳ (dịch-trừ 32 bước).
- Tệp thanh ghi: 31 thanh ghi dùng được (x1–x31), hai cổng đọc một cổng ghi.
- Mô hình chi phí đã kiểm: **C = Σ n_c · λ_c** (n_c = số lệnh động theo lớp),
  khớp **tuyệt đối** với mô phỏng RTL trên mọi cấu hình đã thử. Vì vậy mọi đề
  xuất đổi λ hoặc đổi n_c đều dự báo được bằng chính phương trình này.
