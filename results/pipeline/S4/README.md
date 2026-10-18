# S4 — Vòng B1: tối ưu phần mềm có AI hỗ trợ, chế độ mù · ĐẠT

Lệnh: `./cdp b1 prepare` → `./cdp b1 sandbox` → (gọi subagent mù) → `./cdp b1 eval --sandbox …`

Câu hỏi nghiên cứu **PQ2**: vòng B1 có AI tái khám phá (hoặc vượt) tối ưu phần mềm
người đã làm bằng tay không?

## 1. Kết quả — hai con số, KHÔNG được trộn

| | chu kỳ/ảnh | so B-V0 | biên độ theo ảnh |
|---|---:|---:|---:|
| Điểm xuất phát B-V0 (C thẳng) | 1.978.697 | 1,000× | 0,02 % |
| **Người làm bằng tay** (B-V1, không cấp cho AI) | 1.459.993 | **1,355×** | 0,03 % |
| **AI mù, tốt nhất KHÔNG phụ thuộc dữ liệu** (`r2c`, vòng 2) | **1.249.201** | **1,584×** | **0,03 %** |
| **AI mù, tốt nhất kể cả phụ thuộc dữ liệu** (`r4a`, vòng 4) | **822.796** | **2,405×** | **13,70 %** |

**Trả lời PQ2: có, và vượt.** So sánh ngang hàng (cùng tính chất không phụ thuộc dữ
liệu, cùng 10 ảnh, cùng lõi, cùng cờ biên dịch): **1,584× so với 1,355×** — AI cắt
thêm 14,4 % chu kỳ so với bản người làm, sau **hai vòng**.

Từ vòng 3 trở đi AI dùng một **lớp tối ưu mà người không dùng**: khai thác tính thưa
(bỏ qua cả chùm phép nhân khi gặp giá trị 0, vì `p1` là đầu ra ReLU+MaxPool). Hợp lệ
và đúng từng bit, nhưng làm số chu kỳ **phụ thuộc đầu vào**: biên độ nhảy từ 0,03 %
lên 8,61 % rồi 13,70 %. Vì vậy 2,405× là **trung vị trên đúng 10 ảnh đó**
(751.615–864.301), không phải một hằng số của thiết kế.

## 2. Đường cong theo vòng (`duong_cong_b1.csv`)

| vòng | bản tốt nhất | ý tưởng | chu kỳ | so B-V0 | cải thiện | phụ thuộc dữ liệu |
|---|---|---|---:|---:|---:|---|
| 0 | `kernels_v0.c` | C thẳng, chưa tối ưu | 1.978.697 | 1,000× | — | không |
| 1 | `r1a` | conv2: chặn theo kênh ra, 8 accumulator → mỗi byte `p1` nạp 1 lần cho 8 kênh | 1.612.135 | 1,227× | 18,53 % | không |
| 2 | `r2c` | conv1: 2 kênh ra một lượt, ghim 18 trọng số, dùng chung cửa sổ 3×3 | 1.249.201 | **1,584×** | 22,51 % | không |
| 3 | `r3c` | conv2: bỏ qua chùm 8 MAC khi byte `p1` = 0 | 954.673 | 2,073× | 23,58 % | **có** |
| 4 | `r4a` | conv1: bỏ qua cặp MAC khi byte ảnh = 0 | 822.796 | **2,405×** | 13,81 % | **có** |

**12/12 ứng viên trong 4 vòng đều ĐÚNG TỪNG BIT** — không ứng viên nào bị loại vì sai
kết quả. Vòng lặp **dừng theo quyết định của người dùng ở vòng 4**, chưa tới bão hoà
(quy tắc dừng là 2 vòng liên tiếp cải thiện < 2 %; vòng 4 còn cải thiện 13,81 %).

## 3. Xác nhận trên Verilator — và một kết quả ngoài dự kiến cho PQ1

| biến thể | ISS | Verilator | từng lớp × từng ảnh | CRC vs golden |
|---|---:|---:|---|---|
| `r2c` | 1.249.201 | **1.249.201** | **bằng tuyệt đối** | khớp |
| `r4a` | 822.796 | **822.796** | **bằng tuyệt đối** | khớp |

Mô hình chu kỳ ở S2 được kiểm trên 14 cấu hình **đã biết**. Đây là lần đầu nó dự báo
cho **mã hoàn toàn mới** (do AI sinh, cấu trúc vòng lặp khác hẳn, có cả nhánh phụ
thuộc dữ liệu) — và vẫn **đúng tuyệt đối**. Đó là bằng chứng mạnh hơn cho PQ1 so với
việc chỉ khớp trên các cấu hình đã hiệu chuẩn.

## 4. Hạ tầng mù và cổng kiểm của nó

`experiment/m1s_b1/` (thư mục MỚI, không sửa `experiment/m1s/`): `main.c` + một file
`kernels.c` thay được. `pipeline/cdp/b1/prepare.py` giải các chỉ thị tiền xử lý của sáu
macro tính năng ở trạng thái **không định nghĩa** rồi cắt vùng kernel ra — nhờ vậy
subagent không thấy bản đã tối ưu bằng tay nằm cùng file trong `main.c` gốc.

**Cổng kiểm bắt buộc trước khi dùng** (bài học số 3 của dự án: kiểm hạ tầng đo trên
đối tượng đã biết đúng trước): firmware dựng từ `kernels_v0.c` cho **đúng 1.978.697
chu kỳ, bằng tuyệt đối từng lớp từng ảnh** như B-V0, CRC khớp golden. Nếu không kiểm
trước thì mọi sai lệch sau này sẽ bị gán cho AI thay vì cho hạ tầng.

## 5. Ba điều kiện phải đọc kèm

1. **Chế độ mù chỉ là mù MỘT PHẦN.** Subagent được cấp đúng 3 file
   (`kernels.c`, `PROFILE.md`, `TASK.md`) và bị cấm đọc ra ngoài, nhưng **hệ thống tự
   chèn `CLAUDE.md` của dự án vào ngữ cảnh của nó ở cả 4 vòng** — subagent **tự khai
   báo** việc này mỗi vòng. `CLAUDE.md` có câu nêu đích danh *"thêm lệnh tùy biến
   (DOT4, REQ)"*. Với S4 thì gần như vô hại (nhiệm vụ **cấm** dùng lệnh tùy biến hay
   hợp ngữ, và `CLAUDE.md` không nói gì về biến đổi vòng lặp), nhưng đây là **rò rỉ
   phải chặn trước S5**, nơi DOT4/REQ chính là đáp án cần tái khám phá.
   Chi tiết: `sandboxes/ai_meta_r1.json`.
2. **Chế độ mù bảo đảm bằng CHỈ THỊ, không bằng sandbox hệ điều hành** — subagent chạy
   trên cùng hệ thống file nên về mặt kỹ thuật vẫn đọc được mọi thứ. Mỗi vòng nó đều
   tự báo đã chạy lệnh gì ra ngoài sandbox (chỉ `command -v` tìm trình biên dịch và
   một `ls ~/.local/xPacks`, đều không trả về gì).
3. **Chưa đo trên kit.** Mọi số là ISS + Verilator. Theo quyết định trước đó, phép đo
   kit được gộp vào lần đo thật đầu tiên ở S6.

## 6. File

| file | nội dung |
|---|---|
| `duong_cong_b1.csv` | đường cong 5 điểm: chu kỳ, tăng tốc, cải thiện, biên độ, có/không phụ thuộc dữ liệu |
| `rounds/round{1..4}.json` | mọi ứng viên từng vòng: chu kỳ, đúng bit, chu kỳ từng lớp |
| `rounds/round{1..4}.log` | log thô của từng lần chấm |
| `sandboxes/r{1..4}_PROFILE.md` | **đúng** hồ sơ đã cấp cho subagent mỗi vòng |
| `sandboxes/ai_*` | ghi nhận lời gọi AI: hash từng file được cấp, danh sách thông tin bị giữ lại |
| `verilator/{r2c,r4a}_sim.log` | log Verilator xác nhận hai bản tốt nhất |
| `b1_state.json` | trạng thái vòng lặp (bản tốt nhất, lịch sử) |
| `../../experiment/m1s_b1/rounds/*.c` | **mã nguồn** 12 ứng viên |
