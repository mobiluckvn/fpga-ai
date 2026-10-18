# Nhiệm vụ: tối ưu `kernels.c` cho nhanh hơn, giữ kết quả ĐÚNG TỪNG BIT

Bạn là người tối ưu phần mềm cho hệ thống nhúng. Trong thư mục này có đúng hai file
dữ liệu bạn được đọc:

- `kernels.c` — năm hàm tính toán của một mạng tích chập lượng tử hoá 8 bit, cộng các
  hàm phụ và các đệm dữ liệu. Đây là bản hiện tại, chưa tối ưu gì.
- `PROFILE.md` — hồ sơ hiệu năng **đo thật** của chính file đó trên lõi đích: chu kỳ
  theo lớp mạng, chu kỳ theo loại công việc, các vòng lặp nóng nhất kèm số thanh ghi
  còn trống, và bảng số chu kỳ mỗi lệnh của lõi.

## Cấm tuyệt đối
1. **Không đọc bất kỳ file nào ngoài thư mục này.** Không `grep`, không `find`, không
   mở file ở thư mục khác, không đọc tài liệu, không xem lịch sử git. Toàn bộ căn cứ
   phải đến từ hai file trên. Đây là điều kiện của thí nghiệm; vi phạm làm kết quả vô giá trị.
2. **Không đổi phép toán.** Kết quả của năm hàm phải đúng **từng bit** như hiện tại:
   cùng thứ tự cộng dồn ở chỗ có thể tràn, cùng phép lượng tử hoá, cùng giá trị trọng số.
   Một công cụ tất định sẽ kiểm bằng CRC32 của cả năm tensor trung gian trên 10 ảnh;
   lệch một bit là ứng viên bị loại.
3. **Không đổi mô hình, trọng số, hay giao diện**: tên và chữ ký của năm hàm
   (`conv1`, `pool1`, `conv2`, `pool2`, `dense`) phải giữ nguyên, kể cả
   `__attribute__((noinline))`. Các mảng `a1`, `p1`, `a2`, `p2`, `logit` phải giữ nguyên
   tên, kiểu và kích thước, vì tầng ngoài đọc chúng để kiểm.
4. Không dùng lệnh hợp ngữ, không dùng lệnh tùy biến, không gọi hàm thư viện.
   Chỉ C chuẩn, biên dịch bằng `riscv-none-elf-gcc -O2 -march=rv32im`.

## Được phép
- Đổi thứ tự vòng lặp, hoán vị vòng, chia khối (blocking), hợp nhất/tách vòng.
- Bung vòng (unroll) toàn phần hoặc một phần.
- Dùng con trỏ chạy thay cho tính chỉ số bằng phép nhân.
- Giữ giá trị dùng nhiều lần trong biến cục bộ (trọng số, tổng cộng dồn, con trỏ).
- Thêm đệm dữ liệu phụ, đổi bố cục/khoảng đệm của mảng trung gian **nếu** các mảng
  bắt buộc ở điều 3 vẫn giữ nguyên tên/kiểu/kích thước và nội dung cuối cùng.
- Thêm hàm phụ `static` của riêng bạn.

## Cách làm
1. Đọc `PROFILE.md` trước. Tìm chỗ chu kỳ tập trung nhiều nhất, và xem loại công việc
   nào chiếm tỷ trọng lớn ở đó. Chú ý cột **thanh ghi còn trống**: ở vòng nào số đó nhỏ
   thì đừng thêm biến sống dài.
2. Viết **tối đa ba** ứng viên, mỗi ứng viên là một bản hoàn chỉnh của `kernels.c`:
   `cand_a.c`, `cand_b.c`, `cand_c.c` (ghi vào chính thư mục này).
   Mỗi ứng viên nên **thử một ý rõ ràng**, đừng trộn nhiều ý vào một bản — trộn thì
   không biết ý nào có tác dụng.
3. Mỗi file mở đầu bằng một khối chú thích 3–6 dòng: ý tưởng là gì, nhắm vào lớp mạng
   nào và loại công việc nào trong `PROFILE.md`, và **vì sao** bạn nghĩ nó giảm chu kỳ
   (nói theo số chu kỳ mỗi lệnh của lõi, không nói chung chung).
4. Không đoán kết quả, không viết con số tăng tốc. Công cụ sẽ đo.

Trả lời cuối cùng: liệt kê các file đã ghi, mỗi file một dòng một câu về ý tưởng.
