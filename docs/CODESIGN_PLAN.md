> **ĐÃ ĐƯỢC THAY** bởi `docs/PIPELINE_PLAN.md` + `docs/PIPELINE_SPEC.md` (2026-10-18). Giữ lại làm tham khảo;
> P5 (nhánh B) đã hoàn tất trước khi kế hoạch này được dùng.

# Giai đoạn đồng thiết kế dựa trên profile (P0 → P6)

Tiếp nối giai đoạn khả thi (F0–F8, đã GO có điều kiện) và thí nghiệm chính M1-S (`docs/KET_QUA_M1S.md`).
Mục tiêu: biến cách chọn lệnh tùy biến từ "cảm tính có số đo" thành **một phương pháp có công cụ và mô hình
chi phí được kiểm chứng**. Đây là phần nòng cốt nếu đề tài phát triển thành luận án Tiến sĩ.
Kế hoạch tổng (mục 5b): https://claude.ai/code/artifact/f8fb8ed1-998c-4dbb-8fa7-dda34aba7bd3

Mọi quy tắc trong `CLAUDE.md` vẫn áp dụng (theo cổng, tối đa 3 hướng sửa, không bịa số, chỉ nạp SRAM, hỏi khi
cần thao tác vật lý, commit sau mỗi bước ĐẠT). Kết quả mỗi bước lưu ở `results/codesign/P<n>_<tên>/`.
Không sửa/xoá các thư mục `feasibility/` và `experiment/m1s/` đã có — chỉ thêm.

## Điểm xuất phát (số đo trên kit, A-V1+DOT4+C1, 27 MHz)

| Thành phần | Chu kỳ | Tỷ lệ |
|---|---:|---:|
| conv1 | 1.133.668 | 46,3 % |
| conv2 | 986.226 | 40,2 % |
| pool1 + pool2 | 291.521 | 11,9 % |
| dense | 39.057 | 1,6 % |
| **Tổng** | **2.450.494** (90,8 ms) | |
| trong đó requantize (đo riêng) | ~363.990 | ~14,9 % |

---

## P0 — Khép lại các việc còn treo
1. Điều kiện 4 của F6 (3 lần tắt/bật nguồn): nhờ người dùng rút/cắm cáp, chạy `make cycle RUN=2..4` trong
   `feasibility/F6_measure`. Cập nhật mục 7 của FEASIBILITY_REPORT.md.
2. Hoàn tất lượt chạy 10.000 ảnh trên kit (chế độ STREAM_10K) nếu chưa xong: độ chính xác trên kit phải bằng
   golden Python (98,25 %) và mọi dự đoán trùng golden.
3. Sửa dòng "Giai đoạn hiện tại" trong `CLAUDE.md` thành: giai đoạn đồng thiết kế, làm theo `docs/CODESIGN_PLAN.md`.

**ĐẠT khi**: F6 đủ 5/5; kết quả 10.000 ảnh ghi vào KET_QUA_M1S.md.

---

## P1 — Công cụ profile ba tầng
1. Bật `ENABLE_TRACE=1` của PicoRV32 chỉ trong bản Verilator (kiểm tra định dạng trace trong README picorv32).
   Trace quá lớn → chỉ ghi trong vùng do firmware bật/tắt qua một địa chỉ MMIO.
2. `scripts/profile.py <trace> <firmware.elf> --out results/codesign/P1_profile/<biến thể>/` sinh:
   - **Tầng 1 – hàm/lớp**: chu kỳ theo hàm (bảng symbol ELF); đối chiếu từng lớp với `results/experiment/m1s/m1s.csv`.
   - **Tầng 2 – khối cơ bản/vòng lặp**: tách khối từ `objdump -d`, nhận vòng lặp qua cạnh nhảy ngược; top-10
     vòng theo chu kỳ, số lần lặp, chu kỳ/lần lặp, dòng C (`addr2line`).
   - **Tầng 3 – mẫu lệnh**: trong vòng nóng, phân loại mỗi lệnh: nạp/lưu dữ liệu · MAC hữu ích · tính địa chỉ ·
     điều khiển vòng lặp · requantize · khác. Đếm n-gram opcode (n=2..6) và chuỗi phụ thuộc thanh ghi.
     Tính byte nạp/lưu trên mỗi MAC và tỷ lệ chu kỳ không phải MAC.
3. Chạy cho cả 5 biến thể M1-S. Viết `summary.md`: điểm nóng, mẫu lệnh nặng nhất, phân loại chu kỳ trước/sau
   từng tối ưu (chứng minh định lượng: tối ưu phần mềm cắt "tính địa chỉ", DOT4 cắt "MAC").

**ĐẠT khi**: một lệnh duy nhất sinh đủ ba tầng; tổng chu kỳ theo trace = Verilator = kit cho từng lớp;
phân loại chu kỳ giải thích được hệ số 1,45× và 2,13× đã đo.

---

## P2 — Mô hình chi phí và mô hình trần (roofline)
1. Từ P1, ước lượng cho mỗi kernel: P (MAC song song), B (byte/chu kỳ thực tế của đường nạp), R (mức tái sử
   dụng), b (byte/MAC). Vẽ biểu đồ trần, đặt 5 biến thể lên đó.
2. Xây mô hình dự báo chu kỳ theo lớp: chu kỳ = Σ (số lệnh mỗi loại × chu kỳ/lệnh của loại đó trên PicoRV32,
   kể cả độ trễ PCPI). Hiệu chuẩn trên A-V0, **kiểm trên 4 biến thể còn lại** (không hiệu chuẩn lại).
3. Mô hình chi phí phần cứng: LUT/DFF/MULT/Fmax cho mỗi khối mở rộng (đã có DOT4: +124 LUT4, +4 MULT18X18).

**ĐẠT khi**: mô hình dự báo được tổng chu kỳ của 4 biến thể kiểm tra với sai số mục tiêu ≤ 10 %
(ghi sai số thật, kể cả khi vượt — khi đó phân tích vì sao).

---

## P3 — Vòng đồng thiết kế thứ hai
Ứng viên (dùng P1/P2 để **dự báo trước** lợi ích, rồi mới làm; xếp theo lợi ích/chi phí dự báo):

| Ứng viên | Nhắm vào | Loại | Ghi chú |
|---|---|---|---|
| conv1 tính nhiều kênh ra cùng lúc, dùng lại từ ảnh đã nạp | conv1 (46 %) | phần mềm, miễn phí | KET_QUA_M1S mục 5.6 gợi ý |
| REQ (requantize 1 lệnh) | ~14,9 % | lệnh mới | ước tính ~1,17× |
| MAX4 (max từng byte của 2 từ đã gói) | pool (11,9 %) | lệnh mới, SIMD | rẻ: so sánh 4 byte |
| MAC4.ACC (bộ tích luỹ nội bộ) | conv2 | lệnh mới | bỏ `add` sau DOT4 |
| Load hậu-tăng / vòng lặp phần cứng | tính địa chỉ, điều khiển | ILP, gộp lệnh | sửa lõi, không chỉ PCPI |

Với mỗi ứng viên được làm: biến thể mới (giữ kỷ luật "chỉ khác một thứ", cố định ranh giới hàm bằng
`noinline`, các lớp không đổi phải ra **đúng** số chu kỳ cũ), CRC khớp từng bit, kit = Verilator, ghi
**dự báo so với đo**.

**ĐẠT khi**: ít nhất 3 ứng viên có cặp số (dự báo, đo) và tài nguyên; cập nhật bảng tăng tốc tích luỹ.

---

## P4 — Kiểm tra tính phổ quát
1. Nhóm thiết kế: M1-S, M1-L (gấp đôi kênh), một autoencoder Dense nhỏ.
2. Mô hình giữ lại (không dùng khi chọn lệnh): KWS DS-CNN có lớp depthwise (kiểm vừa 64 KB trước;
   không vừa → thu nhỏ, ghi rõ).
3. Chạy mọi biến thể lệnh trên cả nhóm; báo tăng tốc trên mô hình giữ lại so với nhóm thiết kế.

**ĐẠT khi**: có bảng tăng tốc theo mô hình × biến thể, đúng từng bit với golden cho mọi mô hình.

---

## P5 — Nhánh B: lõi tự viết
Khi người dùng cung cấp lõi: qua `riscv-tests`, gắn DOT4/REQ vào tầng thực thi, chạy lại P1–P4.
So sánh: cùng lệnh, khác vi kiến trúc (đa chu kỳ có PCPI so với pipeline tích hợp).

## P6 — Số liệu ASIC (không đặt chip)
Bọc phần phụ thuộc công nghệ (bộ nhớ, bộ nhân) trong wrapper; chạy LibreLane/OpenLane 2 cho lõi + khối
mở rộng ở GF180MCU hoặc SKY130 (Docker trên Mac). Lấy diện tích, timing, công suất ước tính cho từng biến thể.

---

## Sản phẩm cuối giai đoạn
`docs/KET_QUA_CODESIGN.md`: bảng tăng tốc tích luỹ, biểu đồ trần, bảng dự báo–đo của mô hình, bảng tính
phổ quát, chi phí FPGA (và ASIC nếu đã làm P6).
