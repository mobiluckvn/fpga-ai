# Câu lệnh dán vào Claude Code (chạy trong thư mục tinyml-riscv-tn20k)

## Phiên đầu tiên
```
Đọc CLAUDE.md, docs/FEASIBILITY_PLAN.md và docs/FEASIBILITY_REPORT.md. Mục tiêu phiên này là kiểm chứng
tính khả thi trên phần cứng thật, bắt đầu từ cổng F0. Làm đúng từng cổng theo thứ tự, tuân thủ các quy tắc
trong CLAUDE.md: không sang cổng sau khi cổng trước chưa ĐẠT, tối đa 3 hướng sửa rồi dừng hỏi tôi, không bịa
số, chỉ nạp SRAM, hỏi tôi khi cần xác nhận vật lý (LED, cắm kit). Trước khi bắt đầu, liệt kê ngắn những
gì bạn sẽ làm ở F0 và những gì cần tôi làm. Sau mỗi cổng: cập nhật FEASIBILITY_REPORT.md và LOG.md, commit git,
rồi báo tôi kết quả trước khi sang cổng tiếp theo.
```

## Các phiên sau
```
Đọc CLAUDE.md, docs/LOG.md (mục mới nhất) và docs/FEASIBILITY_REPORT.md. Tiếp tục từ cổng chưa ĐẠT đầu tiên
theo docs/FEASIBILITY_PLAN.md, giữ nguyên các quy tắc trong CLAUDE.md.
```

## Khi bị kẹt
```
Dừng sửa. Tóm tắt trong LOG.md: triệu chứng, 3 hướng đã thử, log lỗi đầy đủ, và các phương án dự phòng trong
FEASIBILITY_PLAN.md cho cổng này. Đề xuất phương án nên thử tiếp và lý do.
```
