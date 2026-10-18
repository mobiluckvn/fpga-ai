# S3 — Profile 3 tầng và phân tích · ĐẠT

Báo cáo chính: **`summary.md`**. Lệnh: `./cdp analyze --all` (gọi `cdp profile` bên trong).

## Tiêu chí ĐẠT của S3 (docs/PIPELINE_PLAN.md) và kết quả

| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | `cdp profile` → profile 3 tầng theo SPEC 2.2 | **ĐẠT** — tầng 1 hàm/lớp (bảng ký hiệu ELF), tầng 2 vòng lặp (cạnh nhảy ngược), tầng 3 phân loại từng lệnh động vào 7 lớp ngữ nghĩa |
| 2 | `cdp analyze` → ILP, DLP, byte/MAC, roofline | **ĐẠT** — đường găng RAW đo trực tiếp, khoảng cách địa chỉ từng lệnh load, byte/MAC đo thật, trần bộ nhớ theo λ của từng lõi |
| 3 | **Tổng chu kỳ theo profile = ISS** | **ĐẠT, khớp tuyệt đối 14/14 cấu hình**, trên tổng 10 ảnh và trên từng lớp mạng |
| 4 | Phân loại chu kỳ giải thích định lượng các hệ số đã đo | **ĐẠT** — xem `summary.md` mục 3: 1,45× do `loop_ctrl`+`addr` (74,2 %); 2,31× do `load_data`+`mac` (97,0 %); 1,33× do `requant`+phần `mac` của phép nhân 64 bit (103,2 %) |
| 5 | Chạy cho 5 cấu hình kế hoạch nêu | **ĐẠT, vượt** — chạy **cả 14** cấu hình |

## File

| file | nội dung |
|---|---|
| `summary.md` | báo cáo: 14 cấu hình, giải thích từng hệ số, roofline/ILP, dự báo L3, pooling |
| `analysis.json` | ILP/DLP/byte-MAC/roofline/Amdahl, 14 cấu hình × 5 lớp mạng |
| `profile.json` | profile 3 tầng thô: n_c, cạnh nhảy ngược, vòng lặp, lược sử theo địa chỉ lệnh |
| `tong_hop_14_cau_hinh.csv` | 14 dòng: chu kỳ, ms, chu kỳ/MAC, tỷ trọng 7 lớp ngữ nghĩa |
| `chu_ky_theo_lop_ngu_nghia.csv` | 70 dòng (14 × 5 lớp mạng): chu kỳ từng lớp ngữ nghĩa, MAC/ck, byte/MAC, trần, ILP |
| `analyze.log` | log thô của lần chạy |

## Hai lỗi phân loại đã phải sửa (ghi lại vì là bẫy phương pháp)

1. **Trộn phạm vi đo**: tử số (chu kỳ theo lớp ngữ nghĩa) cộng dồn 10 ảnh nhưng mẫu số lấy
   trung vị **một** ảnh → tỷ trọng sai 10×, và đẳng thức kiểm tra lệch 287 chu kỳ. Cùng loại bẫy
   đã ghi ở `docs/MO_HINH_CHI_PHI.md` mục 1.3.
2. **Giải mã tĩnh không biết nhánh có nhảy hay không**: gán mọi nhánh λ=9 (nhảy) trong khi
   nhiều nhánh không nhảy (λ=5) → lệch **123.093** chu kỳ ở A-V0. Đã tách bằng số liệu **động**
   (ISS đếm số lần nhảy của từng lệnh nhánh). Trên `mycore` cả hai λ đều 1 nên lỗi này **không
   lộ ra** — đúng kiểu lỗi chỉ hiện khi đổi lõi.
