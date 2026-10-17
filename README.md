# TinyML trên lõi RISC-V — Tang Nano 20K

Thí nghiệm: đo số chu kỳ suy luận CNN int8 (MNIST, M1-S ≈ 192K MAC) trên lõi RISC-V mềm trong
FPGA GW2AR-18, rồi thêm lệnh tùy biến (DOT4, REQ) để giảm số chu kỳ.

Kế hoạch đầy đủ: https://claude.ai/code/artifact/f8fb8ed1-998c-4dbb-8fa7-dda34aba7bd3

## Trạng thái: giai đoạn kiểm chứng khả thi **ĐÃ HOÀN TẤT** (F0 → F8) — kết luận **GO CÓ ĐIỀU KIỆN**

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
| F8 | DOT4 qua PCPI | **ĐẠT — tăng tốc 3,985× trên kit, +115 LUT4, Fmax không giảm** |

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

## Thí nghiệm chính — M1-S đã chạy thật trên kit

Mô hình M1-S (CNN int8, MNIST, 192.064 MAC) đã huấn luyện, lượng tử hoá và **chạy suy luận đầy đủ
trên kit**. Chi tiết: **[docs/KET_QUA_M1S.md](docs/KET_QUA_M1S.md)**.

| | float32 | int8 |
|---|---|---|
| Độ chính xác (10.000 ảnh test MNIST) | **98,29 %** | **98,25 %** (chênh +0,04 điểm %) |

| Biến thể | Mô tả | Chu kỳ/ảnh | @27 MHz | chu kỳ/MAC | Tăng tốc |
|---|---|---:|---:|---:|---:|
| A-V0 | C thẳng | 12.129.818 | 449,3 ms | 63,16 | 1,00× |
| **A-V1** | **+ tối ưu phần mềm** (đối chứng) | 6.217.657 | 230,3 ms | 32,37 | **1,95×** |
| A-V2 | C thẳng + DOT4 | 5.756.654 | 213,2 ms | 29,97 | 2,11× |
| **A-V1+DOT4** | **tối ưu phần mềm + DOT4** | **2.917.102** | **108,0 ms** | **15,19** | **4,16×** |
| A-V3 | + lệnh REQ | | | | chưa làm |
| B-V* | lõi tự viết | | | | chưa làm |

**Kết quả quan trọng nhất**: hai tối ưu **nhân được với nhau** — 1,95× (phần mềm) × 2,13× (DOT4 thêm
vào code đã tối ưu) = **4,16×**, đúng bằng số đo. Tức lợi ích của lệnh tùy biến **không biến mất khi
phần mềm đã tối ưu**.

DOT4 trả **+124 LUT4 (+1,6 %)** và **không giảm Fmax**; A-V1 thì **miễn phí hoàn toàn về phần cứng**
(cùng bitstream với A-V0). Mọi số đo đều có: CRC32 từng lớp khớp golden Python (**200/200**), dự đoán
khớp golden (**40/40**), và số chu kỳ trên kit **bằng tuyệt đối** số chu kỳ trong Verilator.

## Quy ước

- Xung nhịp cố định **27 MHz** cho mọi biến thể; Fmax lấy từ báo cáo timing của nextpnr.
- Một số đo chỉ được ghi nhận khi: `rdcycle` = Verilator (bằng tuyệt đối), bộ đếm phần cứng lệch
  đúng một hằng số, CRC32 từng lớp khớp golden Python.
- Log dạng CSV: `variant,model,commit,img,layer,cycles,instret,hw_count,crc32,pred`
- Chỉ nạp SRAM, không ghi flash.
