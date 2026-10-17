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

| | float32 (PyTorch) | int8 (golden Python) | **int8 ĐO TRÊN KIT** |
|---|---|---|---|
| Độ chính xác (10.000 ảnh test MNIST) | **98,29 %** | **98,25 %** | **98,25 %** (9.825/10.000) |

Cả **10.000 ảnh test** đã được nạp vào kit qua UART và kit tự suy luận: **10.000/10.000 CRC32 logit
khớp golden Python từng bit**, 0 lần phải gửi lại trên 7,85 MB truyền. Thời gian mỗi ảnh nằm trong
**90,74 – 90,77 ms** — dao động **0,031 %** trên 10.000 ảnh, tức suy luận **tất định về thời gian**.

| Biến thể | Mô tả | Chu kỳ/ảnh | @27 MHz | chu kỳ/MAC | Tăng tốc |
|---|---|---:|---:|---:|---:|
| A-V0 | C thẳng | 8.987.660 | 332,9 ms | 46,80 | 1,00× |
| **A-V1** | **+ tối ưu phần mềm** (đối chứng) | 6.217.634 | 230,3 ms | 32,37 | **1,45×** |
| A-V2 | C thẳng + DOT4 | 5.758.001 | 213,3 ms | 29,98 | 1,56× |
| **A-V1+DOT4** | **tối ưu phần mềm + DOT4** | 2.917.079 | 108,0 ms | 15,19 | **3,08×** |
| **A-V1+DOT4+C1** | **+ bố cục 4 pha cho conv1** | **2.450.494** | **90,8 ms** | **12,76** | **3,67×** |
| A-V3 | + lệnh REQ | | | | chưa làm — đã định lượng ~1,17× |
| **B-V0** | **lõi tự viết, C thẳng** | **1.978.697** | **73,3 ms** | **10,30** | **4,54×** |
| **B-V1** | **lõi tự viết + tối ưu phần mềm** | **1.459.993** | **54,1 ms** | **7,60** | **6,16×** |
| B-V2/B-V3 | lõi tự viết + DOT4/REQ | | | | chưa làm |

**Kết quả nhánh B**: lõi RISC-V tự viết (`rtl/mycore/`, 2 tầng, bộ nhớ 1 chu kỳ, không hình phạt rẽ
nhánh) qua **48/48** bài `riscv-tests` RV32IM **cộng `fence_i`** mà PicoRV32 trượt. Chạy **đúng các
file firmware.hex của nhánh A** nên `rdinstret` **khớp tuyệt đối** → chênh lệch là thuần vi kiến trúc.
**B-V0 (73,3 ms) nhanh hơn A-V1+DOT4+C1 (90,8 ms) 1,24×**: kernel C thẳng, không một lệnh tùy biến
nào, vượt bản tối ưu hết mức *có* lệnh tùy biến trên PicoRV32. Lõi tự viết còn **nhỏ hơn 58,8 % LUT4**
(3.272 so với 7.941). Với khối lượng này, **vi kiến trúc đáng giá hơn tập lệnh**: 4,54× từ lõi so với
2,13× từ DOT4. Chi tiết: **[docs/KET_QUA_NHANH_B.md](docs/KET_QUA_NHANH_B.md)**.

**Kết quả quan trọng nhất**: lệnh tùy biến cho lợi ích **LỚN HƠN** khi phần mềm đã tối ưu —
DOT4 cho **1,56×** trên C thẳng nhưng **2,13×** trên C đã tối ưu (gấp 1,37 lần). Hai tối ưu
**không độc lập**, và tương tác thuận lợi. Hệ quả: đo một lệnh tùy biến trên mã chưa tối ưu sẽ
**đánh giá thấp** giá trị của nó.

**Kết quả thứ hai**: nút cổ chai conv1 (54,9 % thời gian, `Cin=1` nên không dùng được DOT4) gỡ được
**bằng bố cục dữ liệu, không thêm phần cứng** — 4 bản sao ảnh dịch 0/1/2/3 byte (3.584 byte `.bss`)
làm mọi phép đọc thẳng hàng 4 byte, cho thêm **1,19×** → **3,67×**. Giới hạn của một lệnh tùy biến
có thể nằm ở **bố cục** chứ không ở bản thân lệnh.

**Cơ hội còn lại, đã đo**: requantize tốn **49,6 chu kỳ/lần** × 7.344 lần/ảnh = **14,9 %** thời gian
→ một lệnh `REQ` cho thêm **~1,17×** (→ ~78 ms). Đáng làm, nhưng nhỏ hơn DOT4 nhiều.

DOT4 trả **+124 LUT4 (+1,6 %)** và **không giảm Fmax**; A-V1 và bước +C1 thì **miễn phí hoàn toàn về
phần cứng** (cùng bitstream). Mọi số đo đều có: CRC32 từng lớp khớp golden Python (**250/250**), dự
đoán khớp golden (**50/50**), và số chu kỳ trên kit **bằng tuyệt đối** số chu kỳ trong Verilator; cộng
thêm **10.000/10.000** CRC logit khớp golden ở lần chạy đủ tập test.

## Quy ước

- Xung nhịp cố định **27 MHz** cho mọi biến thể; Fmax lấy từ báo cáo timing của nextpnr.
- Một số đo chỉ được ghi nhận khi: `rdcycle` = Verilator (bằng tuyệt đối), bộ đếm phần cứng lệch
  đúng một hằng số, CRC32 từng lớp khớp golden Python.
- Log dạng CSV: `variant,model,commit,img,layer,cycles,instret,hw_count,crc32,pred`
- Chỉ nạp SRAM, không ghi flash.
