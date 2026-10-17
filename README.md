# TinyML trên lõi RISC-V — Tang Nano 20K

Thí nghiệm: đo số chu kỳ suy luận CNN int8 (MNIST, M1-S ≈ 192K MAC) trên lõi RISC-V mềm trong
FPGA GW2AR-18, rồi thêm lệnh tùy biến (DOT4, REQ) để giảm số chu kỳ.

Kế hoạch đầy đủ: https://claude.ai/code/artifact/f8fb8ed1-998c-4dbb-8fa7-dda34aba7bd3

## Trạng thái: giai đoạn kiểm chứng khả thi — **F0 → F7 xong, kết luận GO CÓ ĐIỀU KIỆN**

| Cổng | Rủi ro | Kết quả |
|---|---|---|
| F0 | Công cụ trên Mac, nhận kit | ĐẠT |
| F1 | Luồng mã nguồn mở sinh bitstream chạy thật | ĐẠT |
| F2 | UART hai chiều | ĐẠT — 0/10.240 byte sai |
| F3 | **BSRAM 64 KB có khởi tạo** (rủi ro lớn nhất) | **ĐẠT, không cần dự phòng** — 32/46 khối |
| F4 | Khối nhân DSP | ĐẠT có dự phòng — phải gọi `MULT18X18` trực tiếp |
| F5 | SoC PicoRV32 chạy firmware C | ĐẠT — số chu kỳ kit = Verilator **bằng tuyệt đối** |
| F6 | Độ tin cậy phép đo | ĐẠT 4/5 điều kiện (xem mục 7 của báo cáo) |
| F7 | Kernel int8 thật | ĐẠT — CRC kit = Python, **48,06 / 72,59 chu kỳ/MAC** |
| F8 | DOT4 qua PCPI | chưa làm |

Chi tiết: **[docs/FEASIBILITY_REPORT.md](docs/FEASIBILITY_REPORT.md)** ·
Cách chạy lại: **[docs/HUONG_DAN.md](docs/HUONG_DAN.md)** ·
Nhật ký: [docs/LOG.md](docs/LOG.md) · Kế hoạch: [docs/FEASIBILITY_PLAN.md](docs/FEASIBILITY_PLAN.md)

## Ba quy tắc build bắt buộc (phát hiện ở giai đoạn này)

1. `synth_gowin` **phải** có `-family gw2a` (mặc định là `gw1n`).
2. `synth_gowin` **phải** có `-nodsp`: DSP do yosys tự suy luận cho phép nhân int8 có dấu
   **cho kết quả sai trên kit** (mô phỏng vẫn đúng). Khối nhân int8 phải **gọi primitive
   `MULT18X18` trực tiếp**.
3. **Không** dùng `gowin_pack -c`: bitstream nén không nạp được.

## Bắt đầu nhanh

```bash
source env/setup_env.sh
openFPGALoader --detect -b tangnano20k          # phải thấy GW2A(R)-18(C)
cd feasibility/F5_soc && make fw sim build load f5check
```

## Biến thể của thí nghiệm chính (chưa làm)

| Mã | Mô tả |
|---|---|
| A-V0 | PicoRV32 RV32IM, kernel C thẳng |
| A-V1 | + tối ưu phần mềm (nhóm đối chứng) |
| A-V2 | + DOT4 |
| A-V3 | + DOT4 + REQ |
| B-V* | lõi tự viết, các bước tương ứng |

## Quy ước

- Xung nhịp cố định **27 MHz** cho mọi biến thể; Fmax lấy từ báo cáo timing của nextpnr.
- Một số đo chỉ được ghi nhận khi: `rdcycle` = Verilator (bằng tuyệt đối), bộ đếm phần cứng lệch
  đúng một hằng số, CRC32 từng lớp khớp golden Python.
- Log dạng CSV: `variant,model,commit,img,layer,cycles,instret,hw_count,crc32,pred`
- Chỉ nạp SRAM, không ghi flash.
