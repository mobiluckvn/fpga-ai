# TinyML trên lõi RISC-V – Tang Nano 20K

Thí nghiệm: đo số chu kỳ suy luận CNN int8 (MNIST, M1-S ≈192K MAC) trên lõi RISC-V mềm
trong FPGA GW2AR-18, rồi thêm lệnh tùy biến (DOT4, REQ) để giảm số chu kỳ.

Kế hoạch đầy đủ: https://claude.ai/code/artifact/f8fb8ed1-998c-4dbb-8fa7-dda34aba7bd3

## Biến thể
| Mã | Mô tả |
|---|---|
| A-V0 | PicoRV32 RV32IM, kernel C thẳng |
| A-V1 | + tối ưu phần mềm (nhóm đối chứng) |
| A-V2 | + DOT4 |
| A-V3 | + DOT4 + REQ |
| B-V* | lõi tự viết, các bước tương ứng |

## Quy ước
- Xung nhịp cố định 27 MHz cho mọi biến thể; Fmax lấy từ báo cáo timing.
- Một số đo chỉ được ghi nhận khi: CSR mcycle = Verilator, bộ đếm phần cứng lệch đúng hằng số,
  CRC32 từng lớp khớp golden Python.
- Log: variant,model,commit,img,layer,cycles,instret,hw_count,crc32,pred

## Thư mục
env/ rtl/{soc,picorv32,mycore,ext} sim/ fw/ model/ scripts/ results/ report/

## Giai đoạn hiện tại: kiểm chứng khả thi (F0 → F8)
- Hướng dẫn cho Claude Code: `CLAUDE.md`
- Các cổng kiểm chứng: `docs/FEASIBILITY_PLAN.md`
- Kết quả: `docs/FEASIBILITY_REPORT.md` · Nhật ký: `docs/LOG.md`
- Câu lệnh mở đầu: `PROMPT_CLAUDE_CODE.md`
