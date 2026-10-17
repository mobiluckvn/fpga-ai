# Chạy mạng học sâu nén 8 bit trên lõi RISC-V tự dựng, đo trên FPGA Tang Nano 20K

**Người làm:** Vũ Trí Công · TS. Nguyễn Trung Hiếu

Công việc này đo xem một mạng nơ-ron tích chập nén xuống số nguyên 8 bit chạy nhanh chậm thế nào
trên một lõi RISC-V nằm trong FPGA, rồi đo tiếp xem mỗi cách làm nhanh hơn đóng góp bao nhiêu:
sửa phần mềm, thêm lệnh riêng cho lõi, đổi cách dựng bên trong lõi, và đổi cách xếp dữ liệu
trong bộ nhớ. Tất cả số trong tài liệu này đo trên mạch thật, không phải tính ra từ công thức.

**Số chính:** thời gian nhận dạng một ảnh giảm từ **332,9 ms xuống 13,6 ms**, nhanh hơn **24,6 lần**,
trên cùng một con FPGA và cùng một nhịp đồng hồ 27 MHz. Mỗi lớp của mạng vẫn cho ra số **giống nhau
tới từng bit** so với bản viết bằng Python dùng để đối chiếu.

---

## 1. Những gì làm được

| Việc | Số đo |
|---|---|
| Mạng nhận dạng chữ số viết tay, nén còn số nguyên 8 bit | 5.258 tham số · 192.064 phép nhân-cộng mỗi ảnh |
| Tỷ lệ đoán đúng, đo trên mạch với đủ 10.000 ảnh thử | **98,25 %**, bằng đúng bản Python đối chiếu |
| Số lần kết quả từng lớp khớp bản Python tới từng bit | **10.000 trên 10.000** |
| Lõi RISC-V tự dựng, qua bộ bài thử chuẩn `riscv-tests` | **48 trên 48** bài RV32IM, thêm bài `fence_i` |
| Số cách dựng mạch đã nạp và đo trên mạch thật | **14** |
| Thời gian một ảnh, nhanh nhất | **13,6 ms** (73,8 ảnh mỗi giây) |
| Số nhịp cho một phép nhân-cộng, nhanh nhất | **1,91** |

## 2. Mỗi cách làm nhanh hơn đóng góp bao nhiêu, và trả giá gì

| Cách làm | Nhanh thêm | Trả giá bằng mạch | Trả giá bằng bộ nhớ |
|---|---|---|---|
| Sửa phần mềm: mở vòng lặp, chạy con trỏ, giữ trọng số trong thanh ghi | 1,45 lần | **không** | — |
| **Đổi cách dựng bên trong lõi** (lõi tự dựng thay cho lõi có sẵn PicoRV32) | **4,26 lần** | **dùng ít ô logic hơn khoảng 2,4 lần** | không |
| Thêm lệnh `DOT4` (nhân-cộng bốn số 8 bit trong một lệnh) | 2,31 lần | 4 khối nhân cứng | không |
| Xếp lại ảnh thành bốn bản dịch chỗ, để lệnh `DOT4` đọc được ở lớp đầu | 1,29 lần | **không** | 3.584 byte |
| Thêm lệnh `REQ` (đưa số 32 bit về lại 8 bit trong một lệnh) | 1,33 lần | 4 khối nhân cứng | không |
| **Nhân cả năm với nhau** | **24,6 lần** | 8 trên 48 khối nhân cứng | khoảng 3,6 KB |

Đọc bảng trên theo hai điều:

**Đổi cách dựng bên trong lõi cho phần nhanh thêm lớn nhất (4,26 lần), gần gấp đôi lệnh tự thêm mạnh
nhất (2,31 lần), và là cách duy nhất vừa nhanh hơn vừa dùng ít mạch hơn.** Nếu chỉ được chọn một
việc để làm thì nên chọn việc này.

**Năm cách trên nhân được với nhau**, nên nếu làm được cả năm thì nên làm, và nên làm theo đúng thứ
tự trong bảng: mỗi lần làm nhanh hơn một phần lại làm cho phần sau đáng làm hơn, chứ không phải ít
đáng làm hơn. Mục 3 nói rõ điểm này bằng số.

## 3. Trả lời ba câu hỏi đặt ra lúc đầu

**Câu 1 — lõi RISC-V mềm chạy mạng này mất bao lâu, lớp nào tốn nhiều nhịp nhất?**
Lõi có sẵn PicoRV32 với phần mềm viết thẳng: 332,9 ms một ảnh, 46,80 nhịp cho mỗi phép nhân-cộng,
trung bình chỉ làm xong 0,151 lệnh mỗi nhịp. Lớp tốn nhiều nhịp nhất đổi dần theo từng bước làm
nhanh: lớp tích chập thứ hai, rồi lớp tích chập thứ nhất, rồi bước đưa số 32 bit về 8 bit.

**Câu 2 — thêm lệnh riêng cho lõi giúp được bao nhiêu?**

| Thêm lệnh `DOT4` vào | Nhanh thêm |
|---|---|
| phần mềm viết thẳng | 1,56 lần |
| phần mềm đã sửa cho nhanh | **2,13 lần** |

Lệnh tự thêm giúp **nhiều hơn** khi phần mềm đã được sửa cho nhanh trước, hơn 1,37 lần. Lý do đọc
được từ số đo: ở phần mềm viết thẳng, phần lớn số nhịp dùng để tính địa chỉ, mà lệnh `DOT4` không
làm giảm phần đó. Suy ra một điều về cách làm: **đo một lệnh tự thêm trên phần mềm chưa sửa sẽ cho
con số thấp hơn giá trị thật của lệnh đó.**

**Câu 3 — cùng những lệnh đó, gắn vào lõi tự dựng thì còn giúp được như vậy không?**

| Cách làm | Trên lõi có sẵn | Trên lõi tự dựng | Chênh |
|---|---|---|---|
| Lệnh `DOT4` | 2,131 lần | 2,313 lần | tốt hơn 8,5 % |
| Xếp lại ảnh thành bốn bản dịch chỗ | 1,190 lần | 1,294 lần | tốt hơn 8,7 % |
| Lệnh `REQ` | 1,330 lần | 1,333 lần | **bằng nhau tới 0,2 %** |

**Còn giúp được, và còn hơn một chút.** Lệnh `REQ` chuyển sang lõi khác mà gần như không đổi con số —
đây là bằng chứng rõ nhất cho câu hỏi này, vì `REQ` chỉ làm phép tính, ít dựa vào cách dựng lõi. Hai
cách còn lại tăng nhẹ vì trên lõi tự dựng, phần việc cố định quanh chúng ít nhịp hơn: lệnh `DOT4`
chỉ mất 1 nhịp khi gắn thẳng vào tầng chạy lệnh, thay vì 2 nhịp khi đi qua cổng phụ trợ của lõi
có sẵn.

## 4. Mười bốn cách dựng mạch, tất cả đo trên mạch thật

| Tên | Lõi | Phần mềm | Nhịp một ảnh | ms | nhịp/nhân-cộng | lệnh/nhịp | ảnh/giây |
|---|---|---|---:|---:|---:|---:|---:|
| A-V0 | PicoRV32 | viết thẳng | 8.987.660 | 332,9 | 46,80 | 0,151 | 3,0 |
| A-V1 | PicoRV32 | đã sửa | 6.217.634 | 230,3 | 32,37 | 0,147 | 4,3 |
| A-V2 | PicoRV32 + `DOT4` | viết thẳng | 5.758.001 | 213,3 | 29,98 | 0,159 | 4,7 |
| A-V1+DOT4 | PicoRV32 + `DOT4` | đã sửa | 2.917.079 | 108,0 | 15,19 | 0,158 | 9,3 |
| A-V1+DOT4+C1 | PicoRV32 + `DOT4` | thêm xếp lại ảnh | 2.450.494 | 90,8 | 12,76 | 0,160 | 11,0 |
| **A-V3** | PicoRV32 + `DOT4` + `REQ` | thêm `REQ` | 1.842.219 | **68,2** | 9,59 | 0,151 | 14,7 |
| B-V0r | lõi tự dựng, địa chỉ qua thanh ghi | viết thẳng | 3.750.617 | 138,9 | 19,53 | 0,362 | 7,2 |
| B-V1r | lõi tự dựng, địa chỉ qua thanh ghi | đã sửa | 2.713.235 | 100,5 | 14,13 | 0,336 | 10,0 |
| B-V0 | lõi tự dựng | viết thẳng | 1.978.697 | 73,3 | 10,30 | 0,686 | 13,6 |
| B-V1 | lõi tự dựng | đã sửa | 1.459.993 | 54,1 | 7,60 | 0,625 | 18,5 |
| B-V2 | lõi tự dựng + `DOT4` | viết thẳng | 1.169.050 | 43,3 | 6,09 | 0,781 | 23,1 |
| B-V1+DOT4 | lõi tự dựng + `DOT4` | đã sửa | 631.130 | 23,4 | 3,29 | 0,730 | 42,8 |
| B-V1+DOT4+C1 | lõi tự dựng + `DOT4` | thêm xếp lại ảnh | 487.865 | 18,1 | 2,54 | 0,802 | 55,3 |
| **B-V3** | lõi tự dựng + `DOT4` + `REQ` | thêm `REQ` | **365.992** | **13,6** | **1,91** | 0,759 | **73,8** |

Một con số đáng chú ý: **B-V0 (73,3 ms) đã nhanh hơn A-V1+DOT4+C1 (90,8 ms)**. Nghĩa là phần mềm
viết thẳng, không một lệnh tự thêm nào, chạy trên lõi tự dựng thì nhanh hơn bản đã sửa hết mức và
có lệnh tự thêm chạy trên lõi có sẵn.

### Điều kiện để một dòng được ghi vào bảng
Một dòng chỉ được ghi khi thoả **tất cả** những điều sau:

1. Dấu kiểm CRC32 của **cả năm mảng số trung gian**, trên từng ảnh, khớp bản Python đối chiếu.
2. Chữ số mà mạch đoán ra khớp bản Python đối chiếu.
3. Số nhịp đo trên mạch **bằng đúng** số nhịp đếm được khi chạy thử mạch trên máy tính (Verilator).
4. Đo lại lần thứ hai cho cùng con số (**2 trên 2** lần đọc).
5. Phần mềm nạp vào lõi tự in ra dấu tay của chính mã nguồn đã sinh ra nó; chương trình đọc số
   **từ chối ghi nhận** nếu dấu tay đó khác mã nguồn đang có trên máy.

Các bản thuộc lõi tự dựng chạy **đúng những file phần mềm của lõi có sẵn, không dịch lại**, nên số
lệnh đã chạy (`rdinstret`) khớp nhau tới từng đơn vị giữa từng cặp. Nhờ vậy mọi chênh lệch về số
nhịp chỉ do cách dựng lõi, không do phần mềm khác nhau.

## 5. Cách hệ thống được dựng

```
Mạng → nén 8 bit → bản Python đối chiếu → file trọng số cho phần mềm lõi
                                              ↓
   lõi RISC-V  +  bộ nhớ 64 KB  +  cổng nối tiếp  +  bộ đếm nhịp  →  nạp vào FPGA
        ↑                                                               ↓
   lệnh tự thêm: DOT4, REQ                            số đo đọc về qua cổng nối tiếp
```

| Phần | Chọn gì | Vì sao |
|---|---|---|
| Mạng | hai lớp tích chập 3×3, hai lớp lấy lớn nhất 2×2, một lớp nối đầy đủ | vừa bộ nhớ 64 KB, dễ soát từng lớp |
| Nén 8 bit | trọng số và số trung gian là số nguyên 8 bit, số cộng dồn 32 bit, đưa về 8 bit bằng một phép nhân và một phép dịch | cách làm phổ biến, chỉ cần số nguyên |
| Lõi có sẵn | PicoRV32, tập lệnh RV32IM | một file, đọc được bộ đếm nhịp, có cổng gắn lệnh tự thêm |
| Lõi tự dựng | hai tầng, bộ nhớ một cổng đọc xong trong một nhịp | làm xong gần một lệnh mỗi nhịp, và không mất nhịp khi rẽ nhánh |
| Bộ nhớ | một vùng 64 KB trong FPGA, nạp sẵn phần mềm | đọc xong trong một nhịp, không phụ thuộc trạng thái khác |
| Nhịp đồng hồ | cố định 27 MHz cho mọi bản | tách rõ: số nhịp đo trên mạch, còn nhịp cao nhất lấy từ báo cáo của chương trình xếp mạch |
| Bản đối chiếu | viết lại bằng Python chỉ dùng số nguyên, cùng công thức | làm trọng tài soát từng bit |

Chương trình dùng để dựng mạch đều là chương trình mã nguồn mở: `yosys` → `nextpnr-himbaechel` →
`gowin_pack` → `openFPGALoader`; chạy thử mạch bằng `verilator`. Phiên bản từng chương trình ghi
trong `env/VERSIONS.md`.

## 6. Cách chạy lại

```bash
source env/setup_env.sh
openFPGALoader --detect -b tangnano20k          # phải thấy GW2A(R)-18(C)

# huấn luyện mạng và nén 8 bit (chỉ cần máy tính, không cần mạch)
cd model && ../.venv-model/bin/python train_m1s.py && ../.venv-model/bin/python quantize_m1s.py

# lõi có sẵn: năm bản. Mỗi bản cần một file nạp riêng vì phần mềm nằm trong bộ nhớ của FPGA.
cd ../experiment/m1s
for v in v0 v1 v2 v1d v1dc v1dcr; do make fw-$v sim-$v build-$v; done
for v in v0 v1 v2 v1d v1dc v1dcr; do make load-$v check-$v; done   # nạp và đo LẦN LƯỢT

# lõi tự dựng: soát bằng bộ bài thử chuẩn trước, rồi mới đo mạng
cd ../../rtl/mycore
make rvtests FAST_ADDR=1 WITH_DOT4=1 WITH_REQ=1
for v in bv0 bv1 bv2 bv1d bv1dc bv1dcr; do make sim-$v build-$v FAST_ADDR=1 WITH_DOT4=1 WITH_REQ=1; done
sh ../../scripts/branch_b_measure.sh            # đo một lượt, có bước đối chứng

# đo đủ 10.000 ảnh (ảnh nạp vào qua cổng nối tiếp)
make build-bv10k load-bv10k && make run-bv10k N10K=10000
```

Ba điều bắt buộc khi dựng mạch, tìm ra trong lúc làm:

1. `synth_gowin` **phải** có `-family gw2a`; mặc định là `gw1n`.
2. `synth_gowin` **phải** có `-nodsp`. Khối nhân cứng do `yosys` tự chọn **cho số sai trên mạch
   thật** trong khi chạy thử trên máy tính vẫn đúng. Phải gọi thẳng khối `MULT18X18`.
3. **Không** dùng `gowin_pack -c`; file nén không nạp được.

## 7. Những gì soát được và những gì không

| Khẳng định | Mức chắc chắn |
|---|---|
| Số nhịp từng lớp, từng bản | **đo**; bằng đúng số đếm khi chạy thử trên máy tính; 2 trên 2 lần đọc |
| Giống nhau tới từng bit: 5 mảng × 10 ảnh, và 10.000 trên 10.000 ảnh | **đo** trên cả hai lõi |
| Tỷ lệ đoán đúng 98,25 % | **đo trên mạch**, đủ 10.000 ảnh thử |
| Lõi tự dựng qua 48 trên 48 bài `riscv-tests` RV32IM và cả bài `fence_i` | **đo**; lõi có sẵn qua 48 bài nhưng trượt `fence_i` |
| Số khối nhớ và số khối nhân cứng của từng phần | **chính xác**; truy từng khối về đúng dòng mã trong mạch đã xếp |
| Nhịp cao nhất của mạch, ở mọi bản, hơn 2 lần mức cần 27 MHz | **đo** từ báo cáo của `nextpnr` |
| Số ô logic **tăng thêm** khi thêm một lệnh | **không nói được** — xem `docs/KET_QUA_NHANH_B.md` mục 6b: đổi một tham số làm tổng số ô logic xê dịch tới 1.545 vì chương trình chọn cách phủ khác |
| Nhịp cao nhất của bản tính địa chỉ bộ nhớ ngay trong nhịp chạy lệnh | **chưa chắc** — `nextpnr` không tính đường vào khối nhớ |
| Điện năng tiêu thụ | chưa đo, chưa có thiết bị |

## 8. Bảy chỗ dễ sai, đã ghi lại để không mất thời gian lần sau

1. **Khối nhân cứng do `yosys` tự chọn cho số sai trên mạch thật**, chạy thử trên máy tính vẫn đúng.
2. **`gowin_pack -c`** sinh file nạp không dùng được.
3. **Đặt một dây trung gian cho nhịp đồng hồ ở tầng ngoài cùng làm mất ràng buộc chân.** `yosys` đổi
   tên dây nên dòng `IO_LOC "clk"` không khớp khối nào; cả mạch im lặng hoàn toàn, **không một lời
   cảnh báo**. Ràng buộc chân khớp theo **tên**, nên phải nối thẳng chân nhịp đồng hồ.
4. **`nextpnr` không tính đường vào khối nhớ** (không có đường nào kết thúc ở khối nhớ, ở cả hai lõi),
   nên con số nhịp cao nhất nó báo không nói gì về bản tính địa chỉ ngay trong nhịp chạy lệnh.
5. **Lấy hiệu hai lần dựng mạch không đo được phần mạch tăng thêm của một lệnh.**
6. **Đo riêng một đoạn nhỏ cho con số thấp hơn mức tiết kiệm thật**: đo riêng bước đưa số về 8 bit
   được 9,56 nhịp, nhưng trong vòng lặp thật nó tốn 16,6 nhịp, thấp hơn 1,74 lần, vì vòng lặp đo
   riêng không có cảnh tranh thanh ghi và nạp hằng số.
7. **Để trình dịch gộp hàm vào nhau làm sai phép so sánh**: khi `-O2` gộp cả năm lớp vào hàm chính,
   cách dùng thanh ghi của lớp tích chập thứ nhất **đổi theo việc lớp thứ hai có dùng lệnh `DOT4`
   hay không** (3.803.170 so với 4.950.316 nhịp) dù mã nguồn như nhau. Phải đánh dấu từng lớp là
   không gộp.

## 9. Ba điều học được về cách làm

1. **Khi một phép đo không trả về gì, việc đầu tiên là đo lại bằng một cách dựng đã biết chắc là
   chạy được, trước khi sửa thiết kế.** Tôi đã sửa thiết kế bốn lần trong khi nguyên nhân là cổng
   nối tiếp của mạch đã hỏng. Quy tắc "thử tối đa ba hướng sửa rồi dừng" có tác dụng, nhưng không
   cứu được việc chọn sai thứ để sửa. Việc đối chứng nay nằm sẵn trong `scripts/branch_b_measure.sh`.
2. **Một bộ số chỉ so sánh được với nhau khi mọi bản đến từ cùng một trạng thái mã nguồn, và điều
   đó phải do máy soát.** Hai bản A-V0 và A-V2 từng được đo bằng một bản mã nguồn chưa lưu, nên mọi
   tỷ lệ bị cao hơn thật (4,95 lần thành 3,67 lần). Soát tính đúng đắn **không** phát hiện được:
   cả hai bản phần mềm đều cho số đúng tới từng bit, chỉ chạy nhanh chậm khác nhau. Nay phần mềm tự
   in ra dấu tay của mã nguồn đã sinh ra nó.
3. **Soát chính bộ đo trên một đối tượng đã biết là đúng, trước khi dùng nó xét đối tượng mới.**
   Bước đầu của phần lõi tự dựng chủ ý không viết một dòng mạch nào: chỉ dựng bộ bài thử rồi chạy
   trên lõi có sẵn. Nhờ vậy khi lõi mới trượt một bài thì chỉ còn một cách giải thích.

## 10. Thư mục và tài liệu

| Đường dẫn | Nội dung |
|---|---|
| `docs/KET_QUA_TONG_HOP.md` | bảng 14 cách dựng, phân tách đóng góp, ba câu hỏi, các chỗ dễ sai |
| `docs/FEASIBILITY_REPORT.md` | chín bước soát khả thi trên mạch, F0 đến F8 |
| `docs/KET_QUA_M1S.md` | số đo chi tiết của lõi có sẵn |
| `docs/KET_QUA_NHANH_B.md` | số đo chi tiết của lõi tự dựng, và cảnh báo về số ô logic |
| `docs/HUONG_DAN.md` | từng câu lệnh để chạy lại |
| `docs/LOG.md` | nhật ký từng buổi làm, mới nhất ở trên |
| `rtl/mycore/` | lõi RISC-V tự dựng, mạch quanh lõi, bộ bài thử |
| `rtl/ext/` | lệnh tự thêm `DOT4` và `REQ` gắn vào lõi có sẵn |
| `model/` | huấn luyện mạng, nén 8 bit, bản Python đối chiếu |
| `experiment/m1s/` | phần mềm chạy mạng và cách dựng từng bản của lõi có sẵn |
| `results/` | toàn bộ số thô, báo cáo của chương trình xếp mạch, và dấu SHA256 của từng file |
| `env/VERSIONS.md` | phiên bản từng chương trình và mã nguồn ngoài |

## 11. Quy ước dùng trong tài liệu

- Mọi bản chạy ở **27 MHz**. Nhịp cao nhất của mạch lấy từ báo cáo của `nextpnr`, không phải đo.
- Một số đo chỉ được ghi nhận khi thoả cả năm điều ở mục 4.
- Dòng số đo ghi dạng CSV: `bản,mạng,mã nguồn,ảnh,lớp,nhịp,số lệnh,bộ đếm cứng,CRC32,chữ số đoán`.
- Chỉ nạp vào bộ nhớ tạm của FPGA, không ghi vào bộ nhớ lâu dài của mạch.
