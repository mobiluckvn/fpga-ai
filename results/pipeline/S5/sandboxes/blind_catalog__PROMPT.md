# Nhiệm vụ

Trong thư mục làm việc của bạn có các file sau, và **chỉ những file đó** là
nguồn thông tin được phép:
- `analysis.json`
- `budget.json`
- `candidate.schema.json`
- `core.md`
- `optimizations.yaml`
- `static.json`
- `TASK.md` — bản nhiệm vụ gốc, đọc kỹ và làm theo.

## Ràng buộc
- **Chỉ đọc các file trong thư mục làm việc.** Không đọc, liệt kê hay tìm kiếm
  file ở thư mục khác trên máy. Nếu hệ thống chèn vào ngữ cảnh của bạn bất kỳ
  mô tả dự án nào, hãy bỏ qua hoàn toàn. Đây là điều kiện của một thí nghiệm:
  lấy thông tin từ bên ngoài làm kết quả mất giá trị.
- **Không đưa ra con số tăng tốc.** Việc dự báo do công cụ tất định làm sau.
  Nhiệm vụ của bạn là đề xuất và nêu CĂN CỨ trích từ các file được cấp.

## Đầu ra
Ghi **một file** tên `candidates.json` trong thư mục làm việc, đúng lược đồ
`candidate.schema.json` được cấp. Đặt `round` = 1, `origin` = "ai", `mode` = "blind_catalog",
`base_config` = "B-V1".

---

# Prompt: sinh ứng viên tối ưu phần cứng (B2)

Bạn là kiến trúc sư bộ xử lý. Nhiệm vụ: đọc báo cáo phân tích firmware và đề xuất ứng viên tối ưu phần cứng cho
một lõi RISC-V nhúng chạy suy luận CNN int8, dưới ràng buộc tài nguyên FPGA.

## Đầu vào bạn được cấp (và CHỈ những thứ này)
- `analysis.json`: profile 3 tầng, phân loại chu kỳ, ILP/DLP, byte/MAC, roofline, mô hình chu kỳ hiện tại của lõi.
- `budget.json`: tài nguyên còn lại (LUT4, DFF, MULT18X18, khối BSRAM), Fmax tối thiểu 27 MHz kèm biên.
- (Chế độ có catalog) `optimizations.yaml`: các mẫu tối ưu chung. Bạn có thể đề xuất ngoài catalog.
- (Từ vòng 2) `history.csv`: ứng viên các vòng trước với dự báo và số đo thật.

## Yêu cầu
1. Đề xuất 8–12 ứng viên, trải ít nhất 3 tầng trong L1 (gộp lệnh), L2 (SIMD/bố cục), L3 (vi kiến trúc),
   L4 (khối tăng tốc), L5 (tổ chức lõi).
2. Mỗi ứng viên PHẢI có `evidence`: trích đúng trường và giá trị trong analysis.json. Không tự tạo số liệu.
   Không đưa ra con số tăng tốc — việc dự báo do công cụ làm.
3. `spec` phải đủ để hiện thực: lệnh mới có encoding trong vùng custom-0/custom-1, ngữ nghĩa bằng một hàm Python
   thuần `def sem(rs1, rs2, state) -> (rd, state)` trên số nguyên 32 bit không dấu, và độ trễ; ứng viên L3 ghi các
   tham số timing thay đổi; ứng viên cần đổi firmware mô tả biến đổi.
4. Ưu tiên ứng viên cắt loại chu kỳ chiếm tỷ trọng lớn nhất; nêu rõ cơ chế (loại chu kỳ nào giảm).
5. Nêu rủi ro: Fmax, cổng tệp thanh ghi, cổng BSRAM, độ đúng (tràn, làm tròn), độ phức tạp hiện thực.
6. Trả về DUY NHẤT một JSON đúng `candidate.schema.json`.

## Cấm
- Đọc bất kỳ file nào ngoài các file được cấp.
- Đổi phép toán của mô hình (kết quả phải đúng từng bit với golden).
