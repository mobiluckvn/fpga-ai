# S6 — đo PMAX4 trên kit thật (Tang Nano 20K, 27 MHz)

Ba phép đo, ngày 2026-10-18. Mọi số dưới đây đọc từ `check.log` / `meta.json` cùng thư mục.

## 1. Kết quả

| biến thể | chu kỳ/ảnh | ms | chu kỳ/MAC | IPC | ảnh/s | so A-V0 | run |
|---|---:|---:|---:|---:|---:|---:|---|
| B-V3 (`WITH_PMAX4=0`) | 365.992 | 13,6 | 1,91 | 0,759 | 73,8 | 24,56× | `20261018-190322-kit` |
| B-V3+PMAX4 | **317.878** | **11,8** | **1,66** | 0,743 | **84,9** | **28,27×** | `20261018-190740-kit` |

`instret = 236.313` cho bản PMAX4 (đọc từ `m1s_s6_kit.csv`).

Phân rã theo lớp của bản PMAX4 (trung vị 10 ảnh): conv1 138.213 (43,5 %) · pool1 **4.978** (1,6 %) ·
conv2 165.152 (52,0 %) · pool2 **1.921** (0,6 %) · dense 7.614 (2,4 %).
Hai lớp pooling từ 42.472 + 12.519 = 54.991 chu kỳ xuống còn 6.899 — **giảm 48.092 chu kỳ**.

## 2. Dự báo đã đóng băng TRƯỚC khi viết RTL

`../du_bao_PMAX4_truoc_khi_hien_thuc.json`, ghi trước khi sửa `rtl/mycore/mycore.v`:

| | chu kỳ | tăng tốc | vai trò |
|---|---:|---:|---|
| chặn trên Amdahl (mức C — **không** phải dự báo) | 314.561 | 1,1635× | lợi ích **nhiều nhất** có thể |
| dự báo mức B (chặn **dưới** của lợi ích) | 316.695 | 1,1557× | lợi ích **ít nhất** theo mô hình |
| **đo thật trên kit** | **317.878** | **1,1514×** | |

**Sai số dự báo: +0,37 %** (đo nhiều hơn dự báo 1.183 chu kỳ).

Thứ tự thật: `314.561  <  316.695  <  317.878` chu kỳ, tức `1,1514×  <  1,1557×  <  1,1635×`.

Đọc đúng kết quả này:

- **Chặn trên Amdahl được tôn trọng.** Lợi ích đo được (1,1514×) nhỏ hơn 1,1635× — đúng như một
  chặn trên phải thế. Mức C làm đúng việc của nó.
- **Chặn dưới mức B bị vi phạm 0,37 %.** Mô hình nói lợi ích *ít nhất* 1,1557×; thực tế chỉ
  1,1514×. Vậy **mức B không phải một chặn dưới thật**, nó là một *ước lượng* có điều kiện.
- **Và điều kiện đó đã được ghi trước, đúng hướng lệch.** `du_bao_PMAX4_truoc_khi_hien_thuc.json`
  viết sẵn: *"giả định vòng pooling viết lại gọn tới mức chỉ còn 4 nạp + 3 PMAX4 + 1 lưu cho mỗi 4
  kênh. Nếu trình biên dịch sinh thêm lệnh địa chỉ/vòng lặp thì lợi ích thấp hơn."* Lợi ích thật
  **đúng là thấp hơn** — vòng pooling sau khi viết lại vẫn còn chi phí tính địa chỉ và điều khiển
  vòng mà mô hình chưa tính. Giả định bị ghi ra trước nên khi nó không giữ, ta biết **tại sao**
  lệch, không chỉ biết **là** lệch. Đây là giới hạn đã nêu ở `docs/MO_HINH_CHI_PHI.md` mục 6.

## 3. Giá phần cứng (cùng một file RTL, chỉ khác `WITH_PMAX4`)

| | LUT4 | ALU | DFF | BSRAM | MULT18X18 | Fmax |
|---|---:|---:|---:|---:|---:|---:|
| `WITH_PMAX4=0` | 4.211 | 968 | 580 | 32 | 4 | 65,89 MHz |
| `WITH_PMAX4=1` | 4.359 | 1.008 | 580 | 32 | 4 | 55,26 MHz |
| **chênh** | **+148** (+3,5 %) | +40 | 0 | 0 | 0 | −10,6 MHz |

Cả hai đều ĐẠT ràng buộc 27 MHz. Giá: 148 LUT4 cho 1,1514× — xem mục 5 về cách so sánh này
từng bị tôi làm sai.

## 4. Mức bảo đảm của từng dòng — nói thẳng điều còn thiếu

Tiêu chí ghi nhận của dự án đòi **đồng thời**: CRC 5 tensor × 10 ảnh khớp golden · dự đoán khớp
golden · chu kỳ kit = Verilator bằng tuyệt đối · **2/2 lần đọc độc lập** · **chốt `SRC_HASH`**.

| dòng | CRC + dự đoán + kit=Verilator | 2/2 lần đọc | chốt `SRC_HASH` | kết luận |
|---|---|---|---|---|
| B-V3 | ĐẠT | **2/2** | **có** (`c3966b0011df`) | **thoả đủ trong một run** |
| B-V3+PMAX4, run `190740` | ĐẠT | **2/2** | không chốt | thiếu chốt hash |
| B-V3+PMAX4, run `190840` | ĐẠT ở lần đọc 1 | **1/2** | **có** (`a7dca19c8cec`) | UART chết ở lần đọc 2 |
| B-V3+PMAX4, run `214915` | ĐẠT ở lần đọc 1 | **1/2** | **có** (`a7dca19c8cec`) | UART chết ở lần đọc 2 (**y hệt**) |
| B-V3+PMAX4, run `220038` | ĐẠT ở lần đọc 1 | **1/2** | **có** (`a7dca19c8cec`) | chết ở lần đọc 2 **dù là lần truyền dài ĐẦU TIÊN sau khi cắm cáp** |

Hai run PMAX4 nạp **cùng một tệp nhị phân, giống từng bit**:
`firmware.hex sha256 = e477ee612247d892abc3c82cf34f0bb1490acbd3d34c6cfaf2e4bbcca7bfd3f7`
ở cả hai `meta.json`. Nên lần đọc 1 của run `190840` chứng minh chính tệp đã cho 2/2 ở run `190740`
có `SRC_HASH = a7dca19c8cec` khớp mã nguồn hiện tại. Mọi tiêu chí **đều** có bằng chứng, nhưng
**rải trên hai run** thay vì một run duy nhất.

Vì vậy **dòng B-V3+PMAX4 chưa được đưa vào bảng chính** của `docs/KET_QUA_TONG_HOP.md`. Nó chỉ vào
bảng chính sau một run duy nhất đạt 2/2 **và** có chốt hash.

### Lần thử 3 (run `214915`, 2026-10-18 sau khi cắm lại cáp) — và quy luật UART đã thấy được

Sau khi người dùng rút/cắm lại cáp USB, tôi đo **B-V4 trước** (vì đó là mục tiêu của S7) rồi mới đo
PMAX4. Kết quả: **B-V4 đạt 2/2 trong một run**, còn PMAX4 ngay sau đó lại chết đúng ở lần đọc 2 —
lần thứ ba cùng một kiểu.

Xếp theo thứ tự thời gian của phiên, quy luật hiện ra rõ:

| thứ tự | việc | độ dài truyền | kết quả |
|---|---|---|---|
| 1 | cắm lại cáp, đối chứng `min` | ngắn (~50 byte) | ĐẠT |
| 2 | B-V4 lần đọc 1 | **dài** (~4,8 KB) | ĐẠT |
| 3 | B-V4 lần đọc 2 | **dài** | ĐẠT |
| 4 | đối chứng `min` trước PMAX4 | ngắn | ĐẠT ("MIN" 9 lần) |
| 5 | PMAX4 lần đọc 1 | **dài** (~9,4 KB tồn) | ĐẠT |
| 6 | PMAX4 lần đọc 2 | **dài** | **0 byte — chết** |

Từ đó tôi rút ra: kênh UART chịu được khoảng **ba lần truyền dài** sau mỗi lần cắm lại cáp rồi
chết, nên cứ đo cấu hình quan trọng nhất trước là xong.

### Lần thử 4 (run `220038`) — GIẢ THUYẾT TRÊN BỊ BÁC BỎ

Người dùng cắm lại cáp. Tôi đo **PMAX4 trước tiên**, không chạy gì khác trước nó — tức lần truyền
dài **đầu tiên** sau khi cắm cáp. Kết quả: đối chứng trước ĐẠT ("MIN" 8 lần), **lần đọc 1 ĐẠT**
(xả 4.548 byte tồn, CRC 10/10, chu kỳ = Verilator), **lần đọc 2 nhận 0 dòng thô**, đối chứng sau
0 byte cả hai cổng.

**Giả thuyết "ba lần truyền dài" là SAI.** Nó dự đoán lần thử 4 sẽ qua; nó không qua.

### Điều còn đứng vững, và nghi can tiếp theo

Qua bốn run PMAX4: **lần đọc 1 luôn ĐẠT, lần đọc 2 hoặc ĐẠT (run `190740`) hoặc mất sạch**
(0 dòng thô, không phải dữ liệu sai). Riêng B-V4 qua được cả hai lần đọc.

Nghi can ở phía phần mềm, chưa kiểm chứng: `scripts/m1s_check.py` **đóng cổng serial sau mỗi lần
đọc rồi mở lại** cho lần sau — `read_kit()` kết thúc bằng `finally: ser.close()`, rồi vòng lặp
`for attempt in range(1, args.repeat+1)` gọi lại `read_kit()`. Trong khoảng cổng đóng, kit **vẫn
phát liên tục**, nên bộ đệm của FT2232 đầy và kênh có thể kẹt ở đúng nhịp mở lại.

Cách kiểm giả thuyết này mà **không** nới tiêu chí: thêm tuỳ chọn **giữ cổng mở** xuyên suốt hai
lần đọc (đọc hai khối báo cáo liên tiếp từ cùng một luồng, thay vì đóng/mở giữa chừng). Hai lần
đọc vẫn độc lập về nội dung — thậm chí chặt hơn, vì không có gì bị khởi động lại ở giữa. Tuỳ chọn
phải **mặc định tắt** để mọi số đã ghi nhận trước đây giữ nguyên cách đo.

PMAX4 nay có **bốn** run với lần đọc 1 đạt đủ nội dung và **một** run đạt 2/2 (không chốt hash),
tất cả trên cùng một tệp nhị phân giống từng bit. Thiếu duy nhất vẫn là một run gộp cả hai điều kiện.

## 5. Phân loại nguyên nhân thất bại — và hai lỗi của tôi

**Thất bại của run `190840` là lỗi đường đo, không phải lỗi thiết kế.** Phép đối chứng chứng minh:

| | đối chứng trước | đo | đối chứng sau |
|---|---|---|---|
| run `190840` | **ĐẠT** — 9 lần "MIN" ở `...171`, 0 ở `...170` | lần 1 ĐẠT, lần 2 **0 dòng thô** | **0/0 ở cả hai cổng** |

Kiểm lại sau đó bằng tay: `openFPGALoader` nạp `min/top.fs` vào SRAM **thành công** (JTAG tốt), nhưng
đọc 8.000 byte từ cả hai cổng được **0 byte**. Đúng triệu chứng đã ghi trong `docs/LOG.md`: UART của
cầu BL616 chết sau vài phép đo, JTAG vẫn tốt, chỉ rút/cắm lại cáp USB mới hồi phục.

Hai lỗi của tôi trong bước này, ghi lại vì đều là bài học:

1. **So sánh LUT4 giữa hai bản RTL khác nhau.** Lần đầu tôi lấy LUT4 của bản PMAX4 (4.359) trừ
   LUT4 của `bv1dcr` dựng từ bản RTL **cũ** (5.073) và ra kết luận vô lý *"thêm một lệnh tiết kiệm
   714 LUT4"*. Sửa bằng cách dựng `WITH_PMAX4=0` trên **đúng file RTL đó** (4.211) → giá thật
   **+148 LUT4**. Đây là bằng chứng mới cho cạm bẫy số 5 của dự án: hai văn bản RTL tương đương
   logic có thể lệch tới 862 LUT4 và 10 MHz.
2. **`cdp kit` ghi nối CSV mà không xoá dòng cũ**, khiến `m1s_s6.csv` có 20 dòng cho một biến thể.
   `scripts/branch_b_measure.sh` đã có cơ chế `drop()` đúng cho việc này. Đã thêm `csv_drop()` vào
   `pipeline/cdp/kit.py`. Lần này vô hại — cả 20 dòng đều là 317.878 nên trung vị không đổi — nhưng
   nếu hai lần đo khác nhau thì trung vị sẽ vô nghĩa.

Xem mục 2 về điểm quan trọng hơn cả hai lỗi trên: dự báo mức B tự nhận là chặn dưới nhưng bị
số đo vượt qua 0,37 %, và lời giả định ghi trước đã chỉ đúng nguyên nhân.
