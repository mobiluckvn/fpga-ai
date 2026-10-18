# Lời gọi AI — vòng B1 số 1, chế độ mù

Loại agent: general-purpose (agent MỚI, KHÔNG kế thừa ngữ cảnh của phiên điều phối —
nếu kế thừa thì nó thấy luôn đáp án và chế độ mù mất ý nghĩa).

File duy nhất được cấp: sandbox/{TASK.md, kernels.c, PROFILE.md}.

Chỉ thị chính (nguyên văn phần ràng buộc):
  "bạn chỉ được đọc ba file trong thư mục đó. Không được đọc, liệt kê, tìm kiếm, hay
  mở bất kỳ file nào ở bất kỳ thư mục nào khác trên máy — không grep/rg/find/ls ra
  ngoài thư mục đó, không đọc tài liệu, không xem lịch sử git, không tìm mã nguồn liên
  quan ở nơi khác. Đây là điều kiện của một thí nghiệm khoa học: nếu bạn lấy thông tin
  từ bên ngoài thì kết quả thí nghiệm thành vô giá trị."

Yêu cầu giao: tối đa 3 file cand_a.c / cand_b.c / cand_c.c, mỗi bản một ý rõ ràng.

GIỚI HẠN PHẢI GHI RÕ: chế độ mù được bảo đảm bằng CHỈ THỊ, không bằng sandbox hệ điều
hành — subagent vẫn chạy trên cùng hệ thống file và về mặt kỹ thuật vẫn đọc được mọi
thứ. Vì vậy kết quả tái khám phá phải đọc kèm điều kiện này.
