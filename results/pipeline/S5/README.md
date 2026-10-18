# S5 — B2: sinh ứng viên phần cứng ở chế độ mù + đối chứng theo luật · ĐẠT

Lệnh: `./cdp propose --sandbox --target B-V1 --mode open|catalog` → `./cdp blind --sandbox …`
→ `./cdp propose --validate …` → `./cdp score …`; đối chứng: `./cdp propose --rules`.

Điểm xuất phát: **B-V1** (firmware A-V1 trên lõi mycore gốc, 1.459.993 chu kỳ, 54,1 ms).
Đáp án cần tái khám phá: **DOT4**, **REQ**, **bố cục dữ liệu**, và **bộ nhớ nhanh hơn**
(lý do lõi tự viết nhanh hơn PicoRV32). AI **không** được thấy bất kỳ thứ nào trong số đó.

## 1. Tiêu chí ĐẠT của S5 và kết quả

| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | ≥ 3 tệp candidates AI hợp lệ lược đồ | **ĐẠT, vượt** — **6/6** tệp hợp lệ `candidate.schema.json` |
| 2 | ≥ 8 ứng viên trải ≥ 3 tầng mỗi tệp | **ĐẠT, vượt** — **12 ứng viên trải đủ 5 tầng L1–L5** ở cả 6 lần |
| 3 | 1 tệp theo luật (không AI) hợp lệ | **ĐẠT** — 6 ứng viên, 4 tầng |
| 4 | Bảng tái khám phá (có/không, lần chạy nào) | **ĐẠT** — mục 2, chấm bằng tiêu chí máy có trích dẫn |
| 5 | Hai chế độ × 3 lần chạy độc lập | **ĐẠT** — `blind_open` ×3, `blind_catalog` ×3 |

## 2. Bảng tái khám phá

| nguồn | chế độ | ứng viên | tầng | DOT4 | REQ | LAYOUT | FASTMEM |
|---|---|---:|---|---|---|---|---|
| AI | `blind_open` #1 | 12 | L1–L5 | **có** | **có** | **có** | **có** |
| AI | `blind_open` #2 | 12 | L1–L5 | **có** | không | **có** | **có** |
| AI | `blind_open` #3 | 12 | L1–L5 | **có** | không | không | **có** |
| AI | `blind_catalog` #1 | 12 | L1–L5 | **có** | **có** | **có** | **có** |
| AI | `blind_catalog` #2 | 12 | L1–L5 | **có** | **có** | **có** | **có** |
| AI | `blind_catalog` #3 | 12 | L1–L5 | **có** | **có** | **có** | **có** |
| **luật cố định** | — | 6 | L1,L2,L3,L5 | **có** | **không** | **có** | **có** |

| | DOT4 | REQ | LAYOUT | FASTMEM |
|---|---|---|---|---|
| AI `blind_open` | **3/3** | **1/3** | **2/3** | **3/3** |
| AI `blind_catalog` | **3/3** | **3/3** | **3/3** | **3/3** |
| luật cố định | có | **không** | có | có |

## 3. Trả lời PQ3 và PQ4

**PQ3 — pipeline có tái khám phá được các tối ưu người đã làm, từ firmware mù?**
**Có.** DOT4 và bộ nhớ nhanh hơn: **7/7** lần chạy (kể cả luật cố định). Bố cục dữ liệu:
6/7. REQ: 4/7. Ở chế độ `blind_catalog` thì **cả bốn đáp án đều được tìm lại ở cả 3 lần
chạy**. Đáng chú ý, ở `blind_open` (không cấp catalog) một lần chạy tự nghĩ ra REQ chỉ từ
con số `requant 8,8 % chu kỳ`: *"gộp chuỗi làm-tròn-dịch-kẹp của requant int8 thành một
lệnh 1 chu kỳ"*.

**PQ4 — AI có hơn bộ sinh theo luật cố định không?** **Có, ở đúng một chỗ, và chỗ đó có
lý do rõ ràng.**
- Ba đáp án DOT4 / LAYOUT / FASTMEM: **luật cố định tìm được hết** — tức đây là những
  kết luận mà **chỉ cần profile là suy ra được**, không cần AI.
- **REQ là chỗ AI hơn**: luật `L1.fused_op` cần dữ liệu **n-gram mẫu lệnh** mà profile
  hiện tại chưa đo, nên luật **không đánh giá được** (ghi rõ như vậy, không coi là "luật
  sai"). AI suy ra được từ tỷ trọng chu kỳ.
- Về độ phong phú: AI 12 ứng viên trải 5 tầng mỗi lần; luật 6 ứng viên trải 4 tầng.
- **Catalog giúp rõ rệt**: REQ 1/3 → 3/3, LAYOUT 2/3 → 3/3. Vì vậy hai chế độ phải báo
  riêng, không được gộp.
- **Độ ổn định của AI chưa cao** ở chế độ không catalog (REQ 1/3, LAYOUT 2/3). Đây là số
  phải báo; không được chọn lần chạy tốt nhất.

## 4. Ứng viên MỚI — 34 ứng viên ngoài bốn đáp án đã biết

Đây là phần có giá trị nhất cho S6. Tần suất một số ý, trên 6 lần chạy AI:

| ý tưởng | số lần chạy đề xuất |
|---|---|
| nhân-cộng có thanh ghi tích luỹ riêng (MACC/FMAC/LMAC) | **5/6** |
| phát hai lệnh mỗi chu kỳ (dual-issue hẹp) | **5/6** |
| bộ sinh địa chỉ / nạp tự tăng | **5/6** |
| **lệnh max gói 4 làn cho pooling (PMAX4)** | **4/6** |
| nhân 1 chu kỳ (hạ λ_mul từ 2 xuống 1) | **4/6** |
| mở rộng tệp thanh ghi / bank tích luỹ | 1/6 |
| chia nhanh hơn (cơ số cao) | 1/6 |

**PMAX4 đáng chú ý nhất**: phân tích ở S3 đã chỉ ra `pool1`+`pool2` chiếm **15,0 %** chu
kỳ của B-V3 và **chưa có tối ưu nào chạm tới** (34 % chu kỳ của chúng là lệnh so sánh/chọn,
nên DOT4 vô dụng ở đó). AI mù tìm ra đúng ứng viên cho chỗ đó ở 4/6 lần chạy — một tối ưu
**người chưa làm**.

## 5. Chế độ mù: cơ chế và bằng chứng

Mù **có cấu trúc**, không chỉ bằng chỉ thị: mỗi lời gọi chạy trong một tiến trình `claude`
riêng với thư mục làm việc **ngoài cây dự án**, nên không nạp `CLAUDE.md` của dự án, và
prompt **không nêu đường dẫn** cây dự án (xem `blind_probe.txt`). Mọi lời gọi được ghi ở
`ai_calls/*_meta.json`, gồm **bản tự khai báo** của chính AI.

**Tự khai báo của 6/6 lần chạy**: ngữ cảnh thêm chỉ có `~/.claude/CLAUDE.md` của người dùng
(hướng dẫn cài "Vnstock", không liên quan dự án); **đọc ngoài thư mục làm việc: không có**;
**lệnh chạy ra ngoài: không có**.

**Làm sạch rò rỉ trong dữ liệu được cấp** (`cdp propose` kiểm tự động, dừng nếu còn sót):
- `static.json` bản gốc ghi *"custom-0 đã dùng funct3 000 (DOT4) và 001 (REQ)"* → với cấu
  hình B-V1 thì sự thật là **toàn bộ không gian custom còn trống**; bản sạch vừa đúng hơn
  vừa không rò.
- Bảng λ bỏ hai dòng `custom_dot4`/`custom_req` (hai lệnh đó không tồn tại ở B-V1).
- **Giữ** lớp ngữ nghĩa `requant`: đó là tên công việc trong phần mềm (đọc được từ mã C),
  không phải tên giải pháp phần cứng. Lựa chọn này ghi rõ trong `cdp/propose.py`.

Một lần chạy tự đặt tên ứng viên là `dot4` — **không phải rò rỉ**: chuỗi đó không có trong
bất kỳ file được cấp (bộ kiểm đã xác nhận sạch); đó là tên tự nhiên của phép tích vô hướng
4 làn.

## 6. Công bằng với đối chứng

Bản đầu của bộ sinh theo luật chỉ ra **1** ứng viên, vì tôi đánh giá luật trên **lớp mạng
nóng nhất** (`conv2`). Nhưng cơ hội gói 4 làn nằm ở `conv1`, nên cách đó **đánh giá thấp
đối chứng một cách không công bằng**. Đã sửa thành đánh giá **từng lớp mạng** → 6 ứng viên.
Ngoài ra 2/12 mẫu catalog **không đánh giá được** vì cần n-gram mẫu lệnh mà profile chưa
đo — ghi là "không đánh giá được", **không** coi là "luật không thoả".

## 7. File

| file | nội dung |
|---|---|
| `candidates/blind_{open,catalog}_{1,2,3}.json` | 6 tệp ứng viên AI (12 ứng viên mỗi tệp) |
| `candidates/rules.json`, `rules_eval.json` | ứng viên theo luật + kết quả đánh giá từng luật |
| `score.json`, `score.log` | chấm tái khám phá, kèm **đoạn chữ đã khớp** cho từng quyết định |
| `sandboxes/{mode}__*` | **đúng** các file đã cấp cho AI ở mỗi chế độ |
| `ai_calls/*_meta.json` | ghi nhận từng lời gọi: model, cwd trung tính, hash file, tự khai báo |
| `blind_probe.txt` | bằng chứng thực nghiệm rằng cơ chế mù chặn được rò rỉ `CLAUDE.md` |
