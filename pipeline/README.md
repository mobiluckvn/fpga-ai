# pipeline/ — CDP: đồng thiết kế phần mềm–vi kiến trúc có AI hỗ trợ

Đặc tả: `../docs/PIPELINE_SPEC.md` · Kế hoạch: `../docs/PIPELINE_PLAN.md`

Một lệnh duy nhất: `./cdp <lệnh>` ở gốc dự án (tương đương
`PYTHONPATH=pipeline .venv/bin/python -m cdp <lệnh>`). Mã thoát: `0` ĐẠT · `1`
KHÔNG ĐẠT · `2` chưa hiện thực.

| Thư mục | Nội dung |
|---|---|
| `cdp/` | mã nguồn công cụ (Python 3 + pyyaml + jsonschema + numpy) |
| `cdp/iss/` | ISS RV32IM, `ext/` plugin lệnh, `timing/` mô hình chu kỳ theo lõi (S2) |
| `catalog/` | mẫu tối ưu chung L1–L5 |
| `prompts/` | prompt cho AI (`propose.md`; S4 cần thêm `sw_opt.md`) |
| `schemas/` | JSON schema: `spec.schema.json`, `candidate.schema.json` |
| `specs/` | đặc tả thí nghiệm YAML |
| `db/` | sổ cái SQLite `ledger.sqlite` + CSV xuất |
| `runs/` | mỗi lần chạy một thư mục (`meta.json` + log thô); `kit.lock`. KHÔNG vào git |

## Các lệnh

| Lệnh | Bước | Trạng thái | Việc làm |
|---|---|---|---|
| `spec` | S0 | **xong** | kiểm YAML theo schema, phân giải về đúng 1 trong 14 cấu hình |
| `db init\|export\|show` | S0 | **xong** | sổ cái: 3 bảng `runs`, `candidates`, `measurements`; xuất CSV |
| `targets` | S0 | **xong** | in bảng 14 cấu hình đã đo (bản đọc máy của `KET_QUA_TONG_HOP.md`) |
| `lock --hold N` | S0 | **xong** | giữ khoá kit N giây (một kit, tuần tự) |
| `selftest` | S0 | **xong** | 4 phép tự kiểm hạ tầng; kết quả vào `results/pipeline/S0/` |
| `build` `sim` `kit` `synth` | S1 | chưa | bọc Makefile + script có sẵn |
| `iss` | S2 | chưa | ISS RV32IM + plugin lệnh + mô hình chu kỳ |
| `profile` `analyze` | S3 | chưa | profile 3 tầng, ILP/DLP/byte-MAC/roofline |
| `propose` | S5 | chưa | sinh ứng viên (AI mù và theo luật) |
| `estimate` `verify` | S6 | chưa | phễu dự báo → hiện thực → đo |
| `report` | S8 | chưa | bảng + biểu đồ cho bài báo |

## Bất biến của gói này

1. **Không sinh số.** Mọi con số đến từ ISS / Verilator / nextpnr / kit. `cdp` chỉ
   gọi công cụ, đọc log, so sánh, ghi sổ.
2. **Mọi lệnh ghi khoá tái lập** vào `runs/<id>/meta.json`: git commit (+ sạch/bẩn),
   `SRC_HASH`, phiên bản công cụ, tham số, máy.
3. **Mọi truy cập kit qua `cdp/kitlock.py`** (`fcntl.flock` trên `runs/kit.lock`).
4. **Không sửa cây cũ.** `feasibility/`, `experiment/m1s/`, `rtl/mycore/`, `results/`
   cũ chỉ ĐỌC; `cdp build` của S1 sẽ dựng ngoài cây.
