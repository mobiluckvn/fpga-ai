# S6 phần 1 — `cdp estimate`: dự báo cho mọi ứng viên, GHI TRƯỚC khi hiện thực

Lệnh: `./cdp estimate`. Nguyên tắc SPEC 0.3: **dự báo ghi vào sổ cái trước khi hiện
thực, và không được sửa lùi.** Mọi $n_c$ lấy từ ISS (đo), mọi $\lambda$ đọc từ RTL.
Không có hệ số tay nào.

## 1. Ba mức dự báo — độ tin cậy khác nhau hẳn, không được trộn

| mức | áp dụng cho | công thức | độ tin cậy |
|---|---|---|---|
| **A** đổi λ | L3 (vi kiến trúc) | $\Delta C=\sum_c n_c(\lambda_{cũ}-\lambda_{mới})$ | **chính xác theo mô hình** — mô hình này đã khớp tuyệt đối với RTL trên 14 cấu hình (S2) và trên mã mới do AI sinh (S4) |
| **B** gộp/vector hoá một mẫu lệnh | L1, L2 | $\Delta C=n_{nhóm}(\sum\lambda_{bị\ thay}-\sum\lambda_{mới})$ | **chặn dưới** — không tính phần biến đổi mã cắt thêm chi phí địa chỉ/vòng lặp |
| **C** chặn trên Amdahl | mọi ứng viên | tăng tốc $\le 1/(1-f)$ | **chặn trên**, không phải dự báo |

## 2. Dự báo cấu trúc cho các ứng viên ưu tiên

| ứng viên | tầng | cơ sở | mức | dự báo chu kỳ | tăng tốc dự báo | đo thật | sai số |
|---|---|---|---|---:|---:|---:|---:|
| DOT4 (nhân-cộng SIMD 4 làn int8) | L2 | B-V1 | B | 958.121 | 1,524× | **631.130 (2,313×)** | **−34,1 %** |
| Bố cục dữ liệu cho conv1 dùng được lệnh 4 làn | L2 | B-V1+DOT4 | B | 460.778 | 1,370× | **487.865 (1,294×)** | **+5,9 %** |
| REQ (gộp lượng tử hoá lại thành một lệnh) | L1 | B-V1+DOT4+C1 | B2 | 413.468 | 1,180× | **365.992 (1,333×)** | **−11,5 %** |
| PMAX4 (max gói 4 làn cho pooling) | L2 | B-V3 | C | — | ≤ 1,164× | chưa đo | — |
| **Bộ nhớ hai cổng** (load/store 2→1 ck) | L3 | **B-V3** | **A** | **285.167** | **1,283×** | chưa đo | — |
| Bộ nhớ hai cổng | L3 | B-V1 | A | 1.118.656 | 1,305× | chưa đo | — |
| Nhân 1 chu kỳ (λ_mul 2→1) | L3 | B-V1 | A | 1.253.241 | 1,165× | chưa đo | — |
| Nhân 1 chu kỳ (λ_mul 2→1) | L3 | B-V3 | A | 365.992 | **1,000×** | chưa đo | — |
| Hạ λ lệnh lượng tử hoá lại (2→1 ck) | L3 | B-V3 | A | 358.648 | 1,021× | chưa đo | — |
| Bộ nhớ hai cổng + mọi phép nhân 1 ck | L3 | B-V1 | A | 911.904 | 1,601× | chưa đo | — |
| Bộ nhớ hai cổng + mọi phép nhân 1 ck | L3 | **B-V3** | A | **277.823** | **1,317×** | chưa đo | — |

Hai chỗ cần đọc kỹ:
- **"Nhân 1 chu kỳ" trên B-V3 cho đúng 1,000×** — không phải lỗi: ở B-V3 thì
  $n_{mul}=0$ (mọi MAC đã là lệnh 4 làn, requantize đã là một lệnh). Muốn hạ chi phí số
  học ở B-V3 thì phải hạ λ của **chính lệnh lượng tử hoá lại** (dòng dưới, 1,021×).
- Dòng cuối (1,317× trên B-V3) cho $C = 277.823$ = đúng $N$, tức **IPC = 1,00** — trần
  tuyệt đối của lõi phát một lệnh mỗi chu kỳ, đúng như `S3/summary.md` mục 5 đã nêu.

## 3. Trả lời PQ1 cho tầng L1/L2 — KHÔNG cần viết thêm RTL

Ba ứng viên trên đã có số đo thật từ giai đoạn trước, nên so được ngay:

| | dự báo | đo thật | sai số |
|---|---:|---:|---:|
| DOT4 | 1,524× | 2,313× | **−34,1 %** |
| Bố cục dữ liệu | 1,370× | 1,294× | **+5,9 %** |
| REQ | 1,180× | 1,333× | **−11,5 %** |
| | | **|sai số| trung bình** | **17,2 %** |

**Dự báo mức B lệch tới 34 %, và lệch có hệ thống theo hướng dự báo THIẾU** ở hai ứng
viên gộp lệnh. Nguyên nhân đã truy được: mức B chỉ tính các lệnh **bị thay trực tiếp**,
còn việc biến đổi mã để dùng lệnh mới **còn cắt thêm** chi phí tính địa chỉ và điều
khiển vòng — chính các khoản mà `S3/summary.md` mục 3 đã đo (DOT4 cắt thêm 1,7 %
`store_data` và 1,6 % `requant`; bố cục thì **trả giá thêm** +addr +loop_ctrl +store,
nên ở đó dự báo lại THỪA +5,9 %).

Hệ quả cho phương pháp: **mức B dùng để xếp hạng ứng viên thì được, dùng để cam kết một
con số thì không.** Mức A (đổi λ) mới là mức có thể cam kết — và chưa ứng viên nào ở
mức A có số đo đối chứng, nên đó là việc của phần đo kit.

## 4. Dự báo được tới đâu? 78 ứng viên của S5

| tầng | ứng viên | mức A (chính xác) | mức B (chặn dưới) | chỉ có chặn trên |
|---|---:|---:|---:|---:|
| L1 | 20 | 1 | 18 | 1 |
| L2 | 20 | 0 | 10 | 10 |
| L3 | 20 | 18 | 0 | 2 |
| L4 | 9 | 6 | 3 | 0 |
| L5 | 9 | 7 | 1 | 1 |
| **tổng** | **78** | **32** | **32** | **14** |

Và một kết luận về chính chặn trên Amdahl: **nó không phân biệt được các ứng viên.**
Hầu hết ứng viên đều nhắm `mac`+`load_data`, cộng lại 85 % chu kỳ, nên chặn trên của
chúng gần như bằng nhau (trung vị và lớn nhất đều ~6,65×). Vì vậy **không dùng chặn trên
để chọn top-K**; phải dùng mức A hoặc B.

## 5. Đề nghị top-K để hiện thực (chờ người dùng quyết)

| hạng | ứng viên | dự báo | vì sao |
|---|---|---|---|
| 1 | **Bộ nhớ hai cổng / tách lệnh-dữ liệu** | **1,283× trên B-V3 (mức A, chính xác)** | lợi ích lớn nhất trong các dự báo **có thể cam kết**; không thêm lệnh mới, **không đổi firmware**; 7/7 lần chạy S5 đều đề xuất |
| 2 | **PMAX4** (max gói 4 làn cho pooling) | ≤ 1,164× (chặn trên) | nhắm đúng 15,0 % chu kỳ mà **chưa tối ưu nào chạm tới**; 4/6 lần chạy AI đề xuất; cần 1 lệnh mới + đổi `pool1`/`pool2` |
| 3 | Hạ λ lệnh lượng tử hoá lại 2→1 | 1,021× (mức A) | rất nhỏ, nhưng **gần như miễn phí** nếu đã mở khối nhân khi làm hạng 1 |
| 4 | MACC/FMAC có thanh ghi tích luỹ riêng | chưa dự báo được | 5/6 lần chạy AI đề xuất, nhưng đặc tả chưa đủ để tính mức B — cần làm rõ trước |

**Cảnh báo phải ghi**: nếu làm cả hạng 1 và hạng 2 thì **không được nhân hai hệ số với
nhau** rồi coi là dự báo. Hai hướng tác động lên các số hạng khác nhau của $\sum n_c\lambda_c$
nên *xấp xỉ* nhân được (lập luận ở `docs/MO_HINH_CHI_PHI.md` mục 2), nhưng đó là một
**giả thuyết cần đo**, không phải một dự báo.

## 6. File lưu lại cho báo cáo

| file | nội dung |
|---|---|
| `estimates_priority.json` | dự báo cấu trúc đầy đủ: công thức, từng số hạng $n_c(\lambda_{cũ}-\lambda_{mới})$, độ tin cậy |
| `du_bao_vs_do.csv` | bảng gọn dự báo vs đo thật, có cột sai số |
| `estimates_all_candidates.csv` | 78 ứng viên: lớp bị nhắm, tỷ trọng, chặn trên, có dự báo được không |
| `estimates_full.json` | hợp của hai phần trên, nguyên dạng |
| `estimate.log` | log thô của lần chạy |
| `so_cai_candidates.csv` | **sổ cái**: 90 dòng `candidates` trạng thái `estimated`, có `predicted_cycles`/`predicted_speedup`, git commit, run_id |
