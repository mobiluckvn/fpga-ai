# CLAUDE.md — TinyML trên lõi RISC-V, Tang Nano 20K

## Bối cảnh
Dự án nghiên cứu của Vũ Trí Công (học viên cao học PTIT). Mục tiêu dài hạn: đo số chu kỳ suy luận CNN int8
trên lõi RISC-V mềm trong FPGA Tang Nano 20K, rồi thêm lệnh tùy biến (DOT4, REQ) để giảm số chu kỳ.
Kế hoạch đầy đủ: https://claude.ai/code/artifact/f8fb8ed1-998c-4dbb-8fa7-dda34aba7bd3

**Giai đoạn hiện tại: DỰNG VÀ ĐO PIPELINE ĐỒNG THIẾT KẾ CÓ AI HỖ TRỢ (CDP).**
Làm theo `docs/PIPELINE_PLAN.md` (S0 → S8), đặc tả trong `docs/PIPELINE_SPEC.md`. Giai đoạn khả thi (F0–F8),
nhánh A và nhánh B đã xong — xem `docs/KET_QUA_TONG_HOP.md`. Không sửa/xoá các thư mục kết quả đã có.

## Phần cứng và máy
- Kit: Sipeed Tang Nano 20K, FPGA GW2AR-LV18QN88C8/I7 (họ GW2A-18C), thạch anh 27 MHz,
  cầu nối USB BL616 (JTAG + UART). Cắm vào máy Mac đang chạy Claude Code.
- Máy: macOS (kiểm tra `uname -m`: arm64 hay x86_64 trước khi tải công cụ).

## Luồng công cụ (mã nguồn mở là chính)
Yosys (`synth_gowin`) → nextpnr-himbaechel (uarch gowin) → gowin_pack (Apicula) → openFPGALoader.
Mô phỏng: Verilator, Icarus. Phần mềm: xPack `riscv-none-elf-gcc`, `-march=rv32im -mabi=ilp32`.
Python: venv tại `.venv` (numpy, pyserial; torch chỉ khi tới giai đoạn mô hình).
Gowin EDA Education (có bản macOS) CHỈ là phương án dự phòng / đối chiếu, không dùng làm luồng chính.

## Quy tắc làm việc (bắt buộc)
1. **Theo cổng.** Mỗi cổng F<n> có tiêu chí ĐẠT rõ ràng. Chưa ĐẠT thì không sang cổng sau.
2. **Giới hạn thử.** Một cổng thất bại: thử tối đa 3 hướng sửa khác nhau. Vẫn hỏng → DỪNG, ghi rõ vào
   `docs/LOG.md` (triệu chứng, đã thử gì, log lỗi, phương án dự phòng đề xuất) và hỏi người dùng.
3. **Không bịa số.** Mọi con số trong báo cáo phải lấy từ output thật của công cụ hoặc kit. Lưu log thô vào
   `results/feasibility/F<n>/`. Ước tính phải ghi rõ là ước tính.
4. **Xác nhận vật lý do người dùng làm.** Claude Code không nhìn thấy LED, không cắm/rút cáp. Khi cần
   (LED nháy, cắm lại kit, bấm nút), hỏi người dùng và chờ trả lời.
5. **Chỉ nạp vào SRAM** (`openFPGALoader -b tangnano20k file.fs`). KHÔNG ghi flash (`-f`) trừ khi người
   dùng yêu cầu.
6. **Đối chiếu nguồn chính thức trước lần build đầu**: chân cắm (file .cst) với repo ví dụ chính thức của
   Sipeed cho Tang Nano 20K; tham số nextpnr/gowin_pack với `examples/himbaechel/` trong repo Apicula
   (YosysHQ/apicula); `yosys -p 'help synth_gowin'` để biết tùy chọn họ chip. Ghi nguồn đã đối chiếu vào LOG.
7. **Ghim phiên bản.** Ghi phiên bản mọi công cụ và commit hash của mã ngoài (vd. picorv32) vào
   `env/VERSIONS.md`.
8. **Git.** `git init` ở F0. Commit sau mỗi cổng ĐẠT: `F<n>: <tóm tắt>`. Không commit `.venv`, file build.
9. **Cổng serial**: tự tìm bằng `ls /dev/cu.usbserial*` (BL616 thường hiện hai cổng; thử cả hai).
   Script luôn có timeout và đóng cổng sau khi dùng.
10. **Cập nhật báo cáo**: sau mỗi cổng, điền `docs/FEASIBILITY_REPORT.md` (ĐẠT/KHÔNG ĐẠT + số đo + đường
    dẫn log). Ghi nhật ký từng phiên vào `docs/LOG.md`.

## Cấu trúc thư mục
- `feasibility/F<n>_<tên>/` — mỗi cổng một thư mục tự chứa: RTL, Makefile, script kiểm tra.
- `hw/tangnano20k.cst` — ràng buộc chân dùng chung (sau khi đã đối chiếu).
- `rtl/`, `fw/`, `sim/`, `model/`, `scripts/` — dùng cho giai đoạn thí nghiệm chính sau này.
- `results/feasibility/F<n>/` — log thô, báo cáo nextpnr, CSV.
- `docs/` — FEASIBILITY_PLAN.md (việc cần làm), FEASIBILITY_REPORT.md (kết quả), LOG.md (nhật ký).

## Quy ước kỹ thuật
- Xung nhịp hệ thống: 27 MHz trực tiếp từ thạch anh, không PLL (trừ khi thử Fmax).
- UART 115200 8N1. Dòng log dạng CSV, kết thúc `\r\n`.
- Checksum dùng CRC32 chuẩn (đa thức 0xEDB88320, như `zlib.crc32` trong Python).
- Makefile mỗi cổng có các đích: `sim`, `build`, `load`, `check`, `clean`.
