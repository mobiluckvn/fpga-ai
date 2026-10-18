# Nhật ký làm việc

Mỗi phiên một mục, mới nhất ở trên cùng:

## 2026-10-18 — PIPELINE CDP bước S3 ĐẠT: profile 3 tầng + phân tích, giải thích bằng số mọi hệ số đã đo

Phân tích firmware ở mức lệnh động cho **cả 14 cấu hình**. Kết quả quan trọng nhất không phải các
bảng, mà là **hai trần đã đo được**, vì chúng quyết định hướng tối ưu phần cứng tiếp theo.

### Tiêu chí ĐẠT
| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | profile 3 tầng (SPEC 2.2) | **ĐẠT** — hàm/lớp · vòng lặp · 7 lớp ngữ nghĩa cho từng lệnh động |
| 2 | ILP, DLP, byte/MAC, roofline | **ĐẠT** — đo trực tiếp, không hệ số tay |
| 3 | tổng chu kỳ profile = ISS | **ĐẠT khớp tuyệt đối 14/14**, cả tổng và từng lớp mạng |
| 4 | giải thích định lượng các hệ số đã đo | **ĐẠT** (bảng dưới) |
| 5 | chạy cho 5 cấu hình | **ĐẠT, vượt** — chạy cả 14 |

### Giải thích bằng số từng hệ số đã đo (chênh lệch chu kỳ TUYỆT ĐỐI)
| hệ số | nguồn cắt chính | % của tổng cắt |
|---|---|---:|
| **1,45×** tối ưu phần mềm | `loop_ctrl` 41,4 % + `addr` 32,8 % | **74,2 %** (+ `load_data` 25,9 %) |
| **1,36×** cùng tối ưu đó trên mycore | `addr` 35,0 % + `loop_ctrl` 30,0 % | 65,0 % |
| **4,26×** vi kiến trúc (cùng firmware) | `load_data` 47,8 % + `mac` 33,5 % | 81,3 % — win **đều** trên mọi lớp |
| **2,31×** DOT4 | `load_data` 54,9 % + `mac` 42,1 % | **97,0 %** |
| **1,29×** bố cục 4 pha | `mac` 60,4 % + `load_data` 40,0 % + `requant` 18,4 %, **trả giá** +`loop_ctrl` −7,5 % +`addr` −5,4 % +`store` −4,9 % | net |
| **1,33×** REQ | `requant` 61,0 % + phần `mac` của phép nhân 64 bit 42,2 % | **103,2 %** |

Mọi dự đoán của kế hoạch S3 đều đúng: A-V0→A-V1 cắt chủ yếu `addr`/`loop_ctrl`; DOT4 cắt chủ yếu
`mac`+`load_data`; REQ cắt chủ yếu `requant`.

### Hai trần đã ĐO ĐƯỢC — đây là đóng góp chính của S3
1. **Trần của lõi phát một lệnh mỗi chu kỳ.** Dùng mô hình $\Delta C=\sum n_c\Delta\lambda_c$ (không
   viết dòng RTL nào): bộ nhớ hai cổng cho **1,283×** trên B-V3, nhân 1 chu kỳ cho 1,020×, **cả hai
   cho 1,317×** (365.992 → 277.823 chu kỳ, 13,6 → 10,3 ms) — và khi đó **IPC = 1,00**, trần tuyệt đối.
   Muốn đi xa hơn **buộc** phải rời mô hình một lệnh/chu kỳ.
2. **Trần băng thông bộ nhớ, và nó đã gần.** `conv2` ở B-V1 có **4,52 byte/MAC**, chỉ còn **3,19×** là
   đụng trần ($B = 4/\lambda_{load} = 2$ byte/chu kỳ); sau DOT4 + bố cục 4 pha còn **2,06×**. Nghĩa là
   một lệnh tính toán mạnh gấp 4 lần DOT4 sẽ **không** cho 4×. Mọi ứng viên tính toán từ S5 trở đi
   **phải kèm** giải pháp băng thông.

Thêm một chỗ chưa ai chạm tới: `pool1`+`pool2` chiếm **15,0 %** chu kỳ của B-V3 và **không** được
DOT4 hay REQ giúp gì (max-pooling không có phép nhân; 34 % chu kỳ của nó là lệnh so sánh/chọn).
Chặn Amdahl 1,177×.

### ILP: dư thừa, nên không phải rào chắn
IPC lý tưởng (đường găng RAW đo trực tiếp) là hàng trăm đến hàng nghìn ở mọi lớp, trong khi IPC
thật 0,59–0,84. Nguyên nhân: GCC dùng con trỏ chạy nên mỗi tầng vòng lặp chỉ chuỗi phụ thuộc trong
tầng của nó, không nhân lên. Vậy SIMD / phát nhiều lệnh / mảng MAC **có** chỗ để khai thác — cái
chặn chúng là cổng bộ nhớ, không phải phụ thuộc dữ liệu.

### Công cụ mới
- `cdp/profile.py`: tầng 1 (bảng ký hiệu ELF, `cdp/iss/elf.py` tự viết), tầng 2 (cạnh nhảy ngược →
  vòng lặp, số vòng, chu kỳ trong thân), tầng 3 (7 lớp ngữ nghĩa).
- `cdp/analyze.py`: byte/MAC, trần bộ nhớ theo λ của từng lõi, Amdahl theo lớp, DLP theo khoảng
  cách địa chỉ, ILP theo đường găng.
- ISS thêm 6 phép đo khi bật `profile=True`: lược sử theo địa chỉ lệnh, cạnh nhảy, số lần nhảy của
  từng nhánh, byte nạp/lưu, đường găng RAW, khoảng cách địa chỉ từng load, và **hai vết lan truyền**
  (sau `mulh` → chuỗi requantize; sau `mul`/`DOT4` → chuỗi cộng dồn MAC). Chậm hơn ~30 %.

### Bốn lỗi đã gặp và sửa (đều là bẫy phương pháp, đáng ghi vào luận văn)
1. **Trường `rd` của lệnh `store` không phải thanh ghi đích** (bit đó là phần immediate). Ghi chiều
   cao phụ thuộc vào một thanh ghi ngẫu nhiên → đường găng bị đứt, IPC lý tưởng sai.
2. **Gộp `add` cộng dồn ra khỏi `mac`** làm tỷ trọng MAC bị báo thiếu (`other` phình lên 17,1 %).
   Nhân-cộng là một phép toán; đã gộp bằng vết "sau mul". `other` còn 1,4 %.
3. **Lệnh bộ nhớ bị gán vào `requant`** ở biến thể này nhưng `store_data` ở biến thể kia → sinh
   chênh lệch GIẢ +14.518 chu kỳ. Quy tắc đã chốt: **lệnh bộ nhớ luôn thuộc lớp bộ nhớ**, vì nó
   tiêu thụ băng thông và đó là thứ roofline quan tâm.
4. **Trộn phạm vi đo** (tử số 10 ảnh, mẫu số 1 ảnh) và **giải mã tĩnh gán mọi nhánh là "nhảy"**
   (λ=9 thay vì 5 trên PicoRV32) → đẳng thức kiểm tra lệch 287 và 123.093 chu kỳ. Lỗi thứ hai
   **không lộ ra trên mycore** vì ở đó cả hai λ đều bằng 1 — đúng kiểu lỗi chỉ hiện khi đổi lõi.

### Còn thiếu: ba việc phân tích TĨNH, cần trước S5
Phân tích hiện tại chủ yếu là động. Ba thứ tĩnh thực sự cần cho việc đề xuất phần cứng còn thiếu:
(1) **áp lực thanh ghi** trong vòng nóng — lệnh mới cần 2 nguồn + 1 đích, nếu vòng đã dùng hết thì
lợi ích bị tràn thanh ghi ăn mất (đây là lý do `REQ_BENCH` đo 9,56 chu kỳ nhưng thực tế tiết kiệm
16,6); (2) **phụ thuộc mang theo vòng lặp** — quyết định một vòng có vector hoá được hợp lệ hay
không; (3) **chỗ trống trong không gian mã lệnh** (`custom-0` đã dùng `funct3` 000 và 001).
Đã hỏi người dùng có thêm bước `cdp static` trước S5 hay không — **đang chờ trả lời**.

## 2026-10-18 — PIPELINE CDP bước S2 ĐẠT: ISS RV32IM + mô hình chu kỳ khớp TUYỆT ĐỐI cả 14 cấu hình

Dựng bộ mô phỏng tập lệnh và mô hình chu kỳ — dụng cụ đo $n_c$ cho lý thuyết
`docs/MO_HINH_CHI_PHI.md`. Tiêu chí của S2 chỉ yêu cầu PicoRV32 sai số ≤ 2 %; kết quả thực tế là
**cả 14 cấu hình bằng tuyệt đối 0,0 %, từng lớp, từng ảnh**.

### Tiêu chí ĐẠT của S2 và kết quả
| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | CRC ISS = golden cho cả 14 | **ĐẠT** 14/14 (CRC32 cả 5 tensor × 10 ảnh) |
| 2 | mycore: ISS = Verilator **tuyệt đối** từng lớp | **ĐẠT** 8/8 cấu hình |
| 3 | PicoRV32: sai số từng lớp ≤ 2 % | **ĐẠT, vượt xa** — 6/6 **bằng tuyệt đối 0,0 %** |
| 4 | Thời gian ISS ≤ 30 s mỗi ảnh | **ĐẠT** — 1,4–3,0 s/ảnh (~640k lệnh/s, Python thuần) |

### Đã dựng
- `cdp/iss/core.py`: RV32IM đầy đủ, CSR `cycle`/`instret`, MMIO đúng bản đồ `soc_b.v`. Nạp **đúng
  file `firmware.hex`** mà RTL nạp, nên không có khâu dịch lại nào làm lệch được.
- 14 lớp lệnh: `alu, shift, branch_taken, branch_nt, jal, jalr, load, store, mul, div, csr, misc,
  custom_dot4, custom_req`. Tách `shift` khỏi `alu` và tách `jal`/`jalr` là **bắt buộc** (xem dưới).
- `cdp/iss/ext/{dot4,req}.py`: ngữ nghĩa lấy đúng từ `mycore.v`. REQ đã kiểm **20.000/20.000 vector
  ngẫu nhiên** khớp mô hình C trong `main.c` (`sat_rdhmul` + `rdiv_pot` + clamp).
- `cdp/iss/timing/mycore.yaml`: λ **đọc từ RTL**, không hiệu chuẩn — alu/shift/branch/jal/jalr/csr = 1,
  load/store = 2, mul/REQ = 2, div = 34, DOT4 = 1 (FAST_ADDR=1); FAST_ADDR=0 thì mọi lệnh +1 và mỗi
  truy cập dữ liệu +1 nữa.
- `cdp/iss/calibrate.py`: hiệu chuẩn PicoRV32 bằng bình phương tối thiểu trên **300 phương trình**
  (6 cấu hình × 10 ảnh × 5 lớp), $n_c$ do ISS đếm, $C$ do Verilator đo.
- Cửa sổ đo: ISS nhận ra các lần đọc `rdcycle` và ghép thành cửa sổ **đúng như firmware tự đo**, nên
  đầu ra UART của ISS có y nguyên các dòng `M1S,*` và so sánh là so hai khối cùng định dạng.

### λ hiệu chuẩn của PicoRV32: phần dư ĐÚNG 0, và λ đều NGUYÊN
alu 5 · shift 5 · branch không nhảy 5 · branch nhảy 9 · jal 5 · jalr 8 · load 9 · store 9 · mul 6 ·
csr 5 · DOT4 6 · REQ 6 (div không xuất hiện).

Mọi λ đọc được nhất quán theo một quy luật duy nhất: **số chu kỳ lệnh + 2 chu kỳ cho mỗi lần dùng bus**
(bus của `F5_soc/soc.v` tốn 2 chu kỳ mỗi truy cập). Chênh λ_load − λ_alu = 4 = đúng hai lần giá bus —
đây chính là chỗ **84,9 % chu kỳ của A-V0** biến mất.

**Phép hiệu chuẩn tự tìm lại hai tham số RTL mà nó không được cho biết**: λ_shift = λ_alu ứng với
`BARREL_SHIFTER=1`, và λ_mul = 6 ứng với `ENABLE_FAST_MUL=1` (`feasibility/F5_soc/soc.v` dòng 85, 88).

### Ba cái bẫy đã gặp và cách gỡ (đáng ghi vào luận văn)
1. **Gộp `jal` với `jalr` làm λ ra phân số 6,2 — vô nghĩa vật lý.** Mọi cửa sổ đo có 2 lệnh nhảy, trừ
   `conv1` của biến thể C1 có **7** (vì gọi thêm `conv1_prep`), nên λ gộp ra trung bình phân số. Tách
   hai lớp thì hệ thành: λ_csr + 2λ_jalr = 21 và 3λ_jal + 2λ_jalr = 31.
2. **Vẫn còn một chiều suy biến** (hai mẫu cửa sổ, ba ẩn). Gỡ bằng điều kiện λ phải **nguyên, không
   âm**: còn đúng ba nghiệm, chọn nghiệm chuẩn nhỏ nhất (5, 8, 5) — cũng là nghiệm duy nhất đọc được
   theo quy luật "+2 chu kỳ bus". Đã ghi rõ trong tài liệu: **đây là một lựa chọn, không phải một phép
   đo.**
3. **Làm tròn λ bằng `int()` cắt 8,6 → 8 làm mỗi cửa sổ thiếu 1 chu kỳ** → sai số 0,0026 %. Nhỏ nhưng là
   sai hệ thống; đã sửa bằng tìm nghiệm nguyên đúng.

### Phép kiểm K1 của lý thuyết: ĐẠT 20/20 ảnh
`./cdp iss --check-k1`. Chỉ từ **bốn con số đo** + λ đọc từ RTL, giải hệ hai ẩn ra thành phần lệnh động:
| firmware | n_mem suy ra | n_mem ISS đếm | n_mul suy ra | n_mul ISS đếm |
|---|---:|---:|---:|---:|
| v0 | 413.735 | **413.735** | 206.778 | **206.778** |
| v1 | 341.337 | **341.337** | 206.752 | **206.752** |

Kiểm chéo bằng cấu trúc mô hình, không dùng phép đo nào: 192.064 MAC + 2 × 7.344 lần requantize =
**206.752** = đúng `n_mul` của v1.

**Hai chỗ chính phép đếm của ISS đã SỬA LẠI suy đoán ban đầu của tôi** (ghi lại vì đúng tinh thần
"công cụ tất định phán quyết"):
- `dense` có **đúng 4.000** phép nhân = 4.000 MAC, **không** requantize: 10 logit giữ nguyên int32 và
  argmax lấy trực tiếp. Bản lý thuyết đầu cộng thừa 2×10.
- v0 nhiều hơn v1 **đúng 26** phép nhân, toàn bộ trong `conv1` = **một phép nhân tính chỉ số cho mỗi
  hàng đầu ra** (26 hàng). Đó là một phần cụ thể của 1,45× mà tối ưu phần mềm A-V1 đã xoá.
- Bản đầu của mô hình nghịch còn lệch 16 lệnh vì trộn hai phạm vi: `instret` firmware tự báo bao luôn
  16 lệnh **giữa** các cửa sổ, còn $C$ chỉ cộng chu kỳ **trong** cửa sổ. Quy tắc rút ra: giải hệ **trên
  từng ảnh, trong cùng một phạm vi**. Lấy trung vị riêng từng đại lượng rồi mới giải cũng sinh lệch ±1
  vì `pool1` có luồng điều khiển phụ thuộc dữ liệu.

### Việc tiếp theo
S3: profile 3 tầng + phân tích ILP/DLP/byte-MAC/roofline. Đầu vào đã có: `n_c_theo_lop.csv`
(14 cấu hình × 5 lớp mạng × 14 lớp lệnh) và lược sử thực thi theo địa chỉ lệnh (`--pc-hist`).

## 2026-10-18 — PIPELINE CDP bước S1: tái lập qua `cdp` ĐẠT trên Verilator và tổng hợp · bỏ đo kit

Bọc hai Makefile và script có sẵn bằng `cdp`, rồi tái tạo ba cấu hình đã công bố (A-V0, B-V1, B-V3).
Không viết lại một dòng nào của luồng build/sim/tổng hợp/đo — `cdp` chỉ gọi `make` và `scripts/*.py`,
đọc log, so sánh, ghi sổ cái.

### Cách giải bài "không được sửa cây cũ": cây bóng
`experiment/m1s/v*/` và `rtl/mycore/bv*/` đã nằm trong git (130 + 839 file) và là bằng chứng của giai
đoạn trước, nên chạy `make` tại chỗ là ghi đè chúng. `cdp/wrap.py` dựng **cây bóng** `pipeline/work/s1/`:
chỉ gồm symlink tới mã nguồn, sắp đúng độ sâu để mọi đường dẫn tương đối trong hai Makefile
(`../../fw`, `../../scripts`, `../../hw`, `../uart`, `../../feasibility/...`, `../../experiment/m1s`) vẫn
trỏ đúng. Riêng `results/` trong cây bóng là thư mục **thật và rỗng**, nên `make check-*` không bao giờ
ghi lên CSV số đo cũ. Nhánh B trong cây bóng dùng lại đúng `firmware.hex` mà nhánh A vừa dựng trong cùng
cây bóng, nên vẫn giữ tính chất "chênh lệch giữa hai nhánh là thuần vi kiến trúc".

### Tiêu chí ĐẠT của S1 và kết quả
| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | `cdp build/sim/synth/kit` gọi Makefile + script có sẵn | **ĐẠT** — `build` `sim` `synth` đã chạy thật; `kit` viết xong, dừng đúng chỗ khi không thấy `/dev/cu.usbserial*` |
| 2 | Đặc tả YAML cho A-V0, B-V1, B-V3 | **ĐẠT** — `pipeline/specs/s1_{av0,bv1,bv3}.yaml`, cả ba phân giải đúng cấu hình |
| 3 | Chu kỳ **bằng tuyệt đối** 8.987.660 / 1.459.993 / 365.992 | **ĐẠT** — và bằng tuyệt đối **từng lớp, từng ảnh**, không chỉ trung vị |
| 4 | CRC khớp golden | **ĐẠT** — CRC32 cả 5 tensor × 10 ảnh + dự đoán, cả ba cấu hình |
| 5 | SRC_HASH khớp | **ĐẠT** — firmware tự báo `c3966b0011df` = dấu vân tay mã nguồn hiện tại |
| 6 | Ba dòng sổ cái `origin=human_replay` | **ĐẠT** — `replay.A-V0`, `replay.B-V1`, `replay.B-V3`; 30 dòng `measurements` nguồn `verilator` |
| 7 | Đo trên kit | **BỎ** theo quyết định của người dùng (xem dưới) |

### Số đo (Verilator, qua `cdp`, log: `results/pipeline/S1/`)
| cấu hình | chu kỳ/ảnh | ms @27 MHz | chu kỳ/MAC | chu kỳ/lệnh | IPC |
|---|---:|---:|---:|---:|---:|
| A-V0 (PicoRV32) | 8.987.660 | 332,9 | 46,80 | 6,617 | 0,151 |
| B-V1 (mycore) | 1.459.993 | 54,1 | 7,60 | 1,601 | 0,625 |
| B-V3 (mycore+DOT4+REQ) | 365.992 | 13,6 | 1,91 | 1,317 | 0,759 |

Mỗi cấu hình chạy **hai lượt độc lập** → 60 dòng `measurements`, hai lượt cho số **giống nhau từng ảnh**.

### Tổng hợp lại netlist: hai trong ba cấu hình ra ĐÚNG TỪNG CON SỐ
| cấu hình | LUT4 lần này | LUT4 đã ghi | Fmax lần này | Fmax đã ghi |
|---|---:|---:|---:|---:|
| A-V0 | 7.941 | 7.941 | 71,76 MHz | 71,76 MHz |
| B-V1 | 3.255 | 3.235 (**+20**) | 56,47 MHz | 53,05 MHz |
| B-V3 | 5.073 | 5.073 | 55,82 MHz | 55,82 MHz |

Việc A-V0 và B-V3 trùng khít cả LUT4, ALU, DFF, BSRAM, MULT18X18 **và** Fmax chứng minh luồng
yosys + nextpnr ở đây **tất định**. Nhờ vậy chênh +20 LUT4 của B-V1 **không phải nhiễu công cụ**: netlist
`bv1` cũ được tổng hợp từ bản `mycore.v` **chưa có** khối REQ (lệnh yosys trong `bv1/yosys.log` thậm chí
chưa có tham số `WITH_REQ`, và log đó không có một lần nhắc `req` nào), còn `mycore.v` hôm nay có khối REQ
và `WITH_REQ=0` không gấp hằng được hết. Đây là một ví dụ cụ thể cho cạm bẫy số 5 của
`KET_QUA_TONG_HOP.md`: **hiệu hai lần tổng hợp chỉ đo được chi phí phần cứng khi RTL giống hệt nhau.**
Số chu kỳ thì không đổi — vẫn bằng tuyệt đối.

### Quyết định của người dùng: BỎ bước đo kit của S1
Người dùng chốt (2026-10-18): ba cấu hình này đã có số đo kit đầy đủ, nạp lại chỉ để thấy lại số cũ nên
không có giá trị. Phép kiểm đường đo `cdp kit` gộp vào lần đo thật đầu tiên ở S6. `cdp kit` đã viết xong
và đã kiểm nhánh "không có kit" (dừng ngay, không nạp gì). Bitstream cả ba cấu hình đã dựng sẵn.
Hệ quả phải ghi rõ: tiêu chí *chu kỳ kit = Verilator bằng tuyệt đối* KHÔNG được kiểm lại trong phiên này.

### Vấn đề, đã thử
1. `cdp sim` hỏng ngay lần đầu vì `Path.relative_to` trên đường dẫn tương đối — sửa bằng `resolve()` trong
   `spec.load` và một hàm `util.rel()` hiển thị an toàn.
2. `cdp kit` ban đầu định đọc dòng `M1S,*` thô từ log của `make check-*`, nhưng `m1s_check.py` **không**
   in lại các dòng đó; nguồn đủ số duy nhất là CSV nó ghi. Đã đổi sang đọc CSV
   (`wrap.measurement_rows_from_csv`).

### Việc tiếp theo
S2 (ISS + mô hình chu kỳ) rồi S3 (profile 3 tầng + phân tích), theo yêu cầu của người dùng: tập trung vào
phân tích firmware và **dựng thành một lý thuyết** (mô hình chi phí tường minh) để dẫn ra hướng tối ưu.

## 2026-10-18 — PIPELINE CDP bước S0 ĐẠT: khung `cdp`, sổ cái, khoá kit, kiểm đặc tả

Bắt đầu giai đoạn dựng pipeline đồng thiết kế có AI hỗ trợ (`docs/PIPELINE_PLAN.md`, S0→S8).
S0 là hạ tầng: không có số đo hiệu năng mới nào, chỉ có hạ tầng để mọi số sau này truy được nguồn.

### Đã dựng
- Gói `pipeline/cdp/` + lối vào `./cdp` (tương đương `PYTHONPATH=pipeline python -m cdp`).
  Đã hiện thực: `spec`, `db`, `targets`, `lock`, `selftest`. Mười một lệnh còn lại in "chưa hiện thực"
  kèm bước dự kiến và trả mã thoát 2 (`build`/`sim`/`kit`/`synth` → S1, `iss` → S2,
  `profile`/`analyze` → S3, `propose` → S5, `estimate`/`verify` → S6, `report` → S8).
- Sổ cái `pipeline/db/ledger.sqlite` theo SPEC mục 3, **ba** bảng: `runs`, `candidates`, và
  `measurements` (thêm ngoài SPEC — S1/S2 cần so từng ảnh từng lớp, không chỉ trung vị).
  `./cdp db export` ra `ledger.csv`, `candidates.csv`, `measurements.csv`.
- Khoá kit `pipeline/runs/kit.lock` (`fcntl.flock`); file khoá chứa thông tin ai đang giữ.
- `pipeline/schemas/spec.schema.json` (tự viết từ `pipeline/specs/example_bv3.yaml`), kiểm ba lớp:
  cú pháp YAML → lược đồ → **phân giải về đúng một trong 14 cấu hình** và đối chiếu trường `expect`.
- `pipeline/cdp/targets.py`: bản ĐỌC MÁY của bảng 14 cấu hình (đích make, thư mục build, cờ `-D`,
  tham số RTL, nhãn CSV, chu kỳ trung vị). Nhờ vậy S1 chỉ cần gọi đúng đích make, không phải đoán.
- Mỗi lệnh ghi `pipeline/runs/<id>/meta.json`: git commit + sạch/bẩn, `SRC_HASH`, phiên bản
  yosys/nextpnr/verilator/openFPGALoader/riscv-gcc/make/gowin_pack (lấy bằng cách source chính
  `env/setup_env.sh`, không nhân bản logic PATH), tham số, máy, kết quả.

### Tiêu chí ĐẠT (`./cdp selftest` — log: `results/pipeline/S0/`)
| # | Tiêu chí | Kết quả |
|---|---|---|
| 1 | `cdp spec pipeline/specs/example_bv3.yaml` hợp lệ | **ĐẠT** — phân giải về **B-V3** |
| 2 | Hai tiến trình xin khoá kit, tiến trình thứ hai chờ | **ĐẠT** — A giữ 2 s, B xin sau 0,5 s, B chờ **1,53 s** |
| 3 | Sổ cái ghi / đọc / xuất CSV | **ĐẠT** |
| 4 | (tự thêm) Bảng 14 cấu hình của `cdp` = số đo thật | **ĐẠT** — cả 14 trung vị tính lại từ CSV kit **và** từ `sim.log` đều bằng số trong `KET_QUA_TONG_HOP.md`; kit = Verilator từng ảnh |

### Hai điều phát hiện khi đối chiếu số cũ (quan trọng cho S1)
1. **Trong dự án có hai định nghĩa "trung vị".** `scripts/m1s_check.py` lấy phần tử thứ 6 của 10
   (`sorted[n//2]`), còn `scripts/branch_b_table.py` dùng `statistics.median` (trung bình hai phần tử
   giữa). Chênh đúng **23 chu kỳ** ở mọi biến thể. Mọi số trong báo cáo (8.987.660 · 1.459.993 ·
   365.992) là số của `branch_b_table.py`; `m1s_check.py` in 8.987.683 · 1.460.016 · 366.015.
   `cdp` chốt dùng `statistics.median` và đã kiểm khớp **cả 14 dòng**.
2. **12/14 cấu hình đã đo được dựng từ `main.c` cũ** (`SRC_HASH=647f1d071aca`); bản hiện tại là
   `c3966b0011df` (commit `542764e` thêm mã REQ trong `#ifdef`). Firmware nhúng cả `GIT_HASH` và
   `SRC_HASH` nên **không thể** dựng lại ra file giống từng byte — nếu không kiểm trước, tiêu chí
   "bằng tuyệt đối" của S1 sẽ hỏng vì một lý do chẳng liên quan gì tới `cdp`.
   Đã thăm dò: dựng lại A-V1 từ `main.c` hiện tại rồi chạy trên `rtl/mycore/Vsoc_b1` → **đúng từng
   chu kỳ, từng lớp, từng ảnh** như `rtl/mycore/bv1/sim.log` đã ghi.
   Log: `results/pipeline/S0/recon_rebuild_av1_sim.log` · so sánh: `recon_rebuild_av1.json`.

### Quyết định ghi lại để S1 làm theo
- `cdp build` của S1 dựng **ngoài cây**: `experiment/m1s/v*/` và `rtl/mycore/bv*/` **đã nằm trong git**
  (130 + 839 file), nên dựng tại chỗ là sửa thư mục kết quả cũ — trái quy tắc. Cách làm: thư mục bóng
  có symlink tới mã nguồn để `../../fw`, `../../scripts`, `../../hw` của hai Makefile vẫn đúng, còn
  `results/` trong thư mục bóng là thư mục **thật và rỗng** để không bao giờ ghi lên CSV cũ.
- `pipeline/runs/` không vào git (đã thêm `.gitignore`); bằng chứng từng bước sao sang
  `results/pipeline/S<n>/`.

### Vấn đề, đã thử
Không có lỗi phải xử lý. Đã thêm `pyyaml 6.0.3` + `jsonschema 4.26.0` vào `.venv`.

### Việc tiếp theo / cần người dùng
- S1: bọc build/sim/kit/synth và tái tạo A-V0, B-V1, B-V3. Phần build + Verilator làm được ngay.
- **Cần kit cho phần đo**: hiện **không** thấy `/dev/cu.usbserial*` (kit chưa cắm). Tới bước đo sẽ dừng
  và xin người dùng cắm kit; chỉ nạp SRAM, có đối chứng như `scripts/branch_b_measure.sh`.

## 2026-10-17 — HOÀN TẤT: A-V3 và B-V3 đo trên kit · 14 cấu hình · 332,9 ms → 13,6 ms (24,6×)

Cổng B5 ĐẠT và biến thể A-V3 xong. Toàn bộ kế hoạch gốc (nhánh A V0–V3, nhánh B V0–V3) đã **đo trên
phần cứng thật**.

| | chu kỳ | ms | chu kỳ/MAC | so A-V0 |
|---|---:|---:|---:|---:|
| A-V3 (PicoRV32+DOT4+REQ) | 1.842.219 | 68,2 | 9,59 | 4,88× |
| **B-V3 (mycore+DOT4+REQ)** | **365.992** | **13,6** | **1,91** | **24,56×** |

Cả hai 2/2 lần đọc, CRC 5 lớp × 10 ảnh khớp golden, kit = Verilator bằng tuyệt đối. Phép đo A-V3 trên
kit cũng **xác nhận netlist A-V3 đúng chức năng** dù cách phủ của nó lạ (mục 6b của KET_QUA_NHANH_B).

### Phân rã 24,6× — và câu trả lời cho câu hỏi "nên đầu tư vào đâu"
| Hướng | Hệ số | Giá phần cứng |
|---|---|---|
| Tối ưu phần mềm | 1,45× | 0 |
| **Vi kiến trúc** | **4,26×** | **ít LUT4 hơn ~2,4 lần** |
| DOT4 | 2,31× | 4 DSP |
| Bố cục 4 pha | 1,29× | 0 |
| REQ | 1,33× | 4 DSP |

**Vi kiến trúc là hướng lớn nhất và là hướng duy nhất vừa nhanh hơn vừa rẻ hơn.**

### RQ3 có thêm bằng chứng mạnh nhất
REQ chuyển giao **gần như chính xác**: 1,330× trên PicoRV32 so với 1,333× trên lõi tự viết — lệch
0,2 %. Hợp lý vì REQ là khối tính toán thuần, ít phụ thuộc vi kiến trúc, khác với DOT4 (2,131 → 2,313)
và bố cục (1,190 → 1,294) vốn phụ thuộc chi phí cố định xung quanh.

Đã viết `docs/KET_QUA_TONG_HOP.md` (136 dòng): bảng 14 cấu hình, phân rã, RQ1/RQ2/RQ3, 7 cạm bẫy,
3 bài học phương pháp, và bảng "những gì KHÔNG kết luận được".

## 2026-10-17 — NHÁNH B cổng B6 ĐẠT: 100 và 10.000 ảnh đúng từng bit trên lõi tự viết

Tiêu chí ĐẠT của cả nhánh B trong kế hoạch gốc (*"lõi qua riscv-tests; 100 ảnh đúng từng bit"*) nay
thoả cả hai phần. Dùng chế độ `STREAM_10K` nạp ảnh qua UART trên lõi tự viết (100 ảnh nhúng sẵn không
vừa RAM 64 KB). Đã mô phỏng 3 ảnh trước khi tổng hợp: CRC logit `9377670B`/`3C922E73`/`46B2E0F3` khớp
golden từng bit.

| | 100 ảnh | **10.000 ảnh** |
|---|---|---|
| khung nhận đúng / gửi lại | 100/100 · 0 | 10.000/10.000 · **0** |
| CRC32 logit khớp golden | 100/100 | **10.000/10.000** |
| độ chính xác đo trên kit | 100 % | **98,25 %** |
| trung vị chu kỳ/ảnh | 487.846 | **487.857** |

**98,25 % bằng tuyệt đối nhánh A và bằng golden** → cùng mô hình, cùng kết quả từng bit, trên hai vi
kiến trúc khác hẳn nhau; chỉ khác thời gian 90,8 ms so với **18,1 ms**. 175 ảnh sai giống y nhánh A tới
từng cặp nhầm.

Kiểm chéo: 487.857 (10.000 ảnh, firmware STREAM_10K) so với 487.888 (10 ảnh nhúng, firmware khác) —
lệch 31 chu kỳ = 0,006 %.

### Kết quả phụ gọn: phần phụ thuộc dữ liệu nằm ở SỐ LỆNH
`instret` dao động **đúng 765**, độ lệch chuẩn **133,1** — **trùng khít** dao động chu kỳ, và **giống
hệt nhau trên cả hai lõi**. Nghĩa là mỗi lệnh thêm (nhánh so sánh trong maxpool) tốn **đúng 1 chu kỳ
trên cả hai**. Với lõi tự viết đó là giá bình thường của lệnh ALU; với PicoRV32 (6,6 chu kỳ/lệnh trung
bình) thì những lệnh này **lọt vào khe đang chờ bộ nhớ**. Suy luận phù hợp số liệu, chưa chứng minh cơ chế.

### UART đã thành nút cổ chai
18,1 ms để tính một ảnh, ~68 ms để nạp 784 byte qua UART 115200. 10.000 ảnh mất 16,7 phút, **chỉ ~3
phút là tính**. Lõi đã nhanh hơn đường nạp dữ liệu — giới hạn của **bàn đo**, không phải của thiết kế.

Đã viết tổng kết RQ3 chính thức vào `docs/KET_QUA_NHANH_B.md` mục 9: cả ba tối ưu đều giữ nguyên bậc
độ lớn khi đổi vi kiến trúc (DOT4 2,13→2,31×, bố cục 1,19→1,29×, tối ưu phần mềm 1,45→1,36×).

## 2026-10-17 — Nhánh B: số liệu TRỌN VẸN, 7 biến thể × 10 ảnh trên kit

Sau khi viết lại `scripts/branch_b_measure.sh` cho bền với sự cố, một lượt duy nhất đo xong **5 biến
thể còn lại, không một lần UART chết** (trước đó chết sau 2 phép đo). CSV: **70 dòng**, 7 biến thể.

### Hai thay đổi làm script bền — và có lẽ đã chữa luôn nguyên nhân
1. **Không bao giờ ghi đè CSV.** Trước mỗi phép đo chỉ xoá các dòng *của chính biến thể đó* rồi ghi
   nối; biến thể đã đủ 10 dòng thì bỏ qua. Nên chạy một phần vẫn tích luỹ, không mất gì. (Bản trước
   ghi đè ở biến thể đầu tiên và đã làm mất số đo **hai lần**.)
2. **Chỉ đối chứng ở đầu lượt và sau một phép đo THẤT BẠI**, không đối chứng sau mỗi lần thành công —
   một phép đo thành công đã tự chứng minh đường đo sống (CRC khớp golden + kit = Verilator). Việc này
   **giảm một nửa số lần nạp JTAG**, và lượt đo sau đó chạy liền 5 biến thể không hỏng, so với 2 trước
   đây. Giả thuyết: chính hoạt động JTAG (libusb chiếm thiết bị) làm interface UART chết. Chưa chứng
   minh được nhân quả, nhưng tương quan đủ mạnh để giữ cách làm này.

### Giá của thiết kế bảo thủ — đo được
| | `FAST_ADDR=1` (địa chỉ tổ hợp) | `FAST_ADDR=0` (ghi thanh ghi) | giá |
|---|---:|---:|---:|
| C thẳng | 1.978.720 · **73,3 ms** | 3.750.662 · 138,9 ms | **1,90×** |
| +tối ưu phần mềm | 1.460.016 · **54,1 ms** | 2.713.280 · 100,5 ms | **1,86×** |

**Thủ thuật "địa chỉ bộ nhớ tổ hợp" đáng giá 1,9× mà không tốn một cổng logic nào** — gần bằng cả lệnh
DOT4 (2,31×). Nhưng tính đúng đắn về thời gian của nó **không kiểm được bằng công cụ mã nguồn mở này**
(nextpnr không ràng buộc đường tới BSRAM); nó chỉ được chứng minh bằng chạy đúng trên kit với CRC khớp
golden. Trong thiết kế đưa vào sản xuất, đó là lý do chính đáng để chọn bản bảo thủ.

### Toàn cảnh: 12 cấu hình đã đo trên kit
Nhanh nhất **B-V1+DOT4+C1: 487.888 chu kỳ = 18,1 ms = 2,54 chu kỳ/MAC = 55,3 ảnh/giây**, **18,4×** so
với A-V0. Chậm nhất A-V0: 332,9 ms. Phân rã: 1,45× phần mềm (miễn phí) × 4,26× vi kiến trúc (tiết kiệm
58,8 % LUT4) × 2,31× DOT4 (+1.122 LUT4) × 1,29× bố cục (miễn phí).

## 2026-10-17 — NHÁNH B cổng B4 ĐẠT: DOT4 trong tầng thực thi — 18,1 ms, và RQ3 có câu trả lời

Gắn DOT4 **thẳng vào tầng thực thi** của lõi tự viết (không qua PCPI): toán hạng từ tệp thanh ghi,
4 phép nhân int8 + cây cộng, ghi về trong **cùng chu kỳ** như lệnh ALU → **1 chu kỳ**, so với **2 chu
kỳ** qua PCPI trên PicoRV32. Mã hoá giữ y nhánh A nên **dùng lại đúng firmware.hex của nhánh A**.

Phép nhân int8 cố ý dựng bằng **logic LUT** chứ không gọi `MULT18X18`: F4 đã chứng minh đường LUT đúng
trên kit còn DSP suy luận thì sai, và gọi DSP ở đây sẽ thêm độ trễ vào đường tới hạn của tầng thực thi
— đường mà nextpnr **không ràng buộc**. Trả giá +1.122 LUT4 để giữ đường ngắn.

| Biến thể | A (kit) | **B (kit)** | B nhanh hơn | chu kỳ/MAC | so A-V0 |
|---|---:|---:|---:|---:|---:|
| C thẳng + DOT4 | 213,3 ms | **43,3 ms** | 4,93× | 6,09 | 7,69× |
| +tối ưu PM + DOT4 | 108,0 ms | **23,4 ms** | 4,62× | 3,29 | 14,24× |
| **+bố cục 4 pha** | 90,8 ms | **18,1 ms** | **5,02×** | **2,54** | **18,4×** |

`instret` khớp tuyệt đối nhánh A ở cả ba; CRC 5 lớp × 10 ảnh khớp golden; kit = Verilator bằng tuyệt
đối; 2/2 lần đọc; đối chứng đường đo ĐẠT trước và sau từng phép đo.

### RQ3 — trả lời được
| DOT4 cho | Hệ số |
|---|---|
| PicoRV32 (PCPI, 2 chu kỳ) | **2,13×** |
| lõi tự viết (tầng thực thi, 1 chu kỳ) | **2,31×** |

**Có, và tốt hơn một chút.** Lợi ích của lệnh tùy biến chuyển giao được sang vi kiến trúc khác hẳn.
Bố cục 4 pha cũng vậy: 1,29× trên lõi tự viết so với 1,19× trên PicoRV32.

### Phân rã 18,4×, kèm giá phần cứng
1,45× phần mềm (**miễn phí**) × 4,26× vi kiến trúc (**tiết kiệm 58,8 % LUT4**) × 2,31× DOT4
(+1.122 LUT4) × 1,29× bố cục (**miễn phí**). → **Vi kiến trúc đóng góp gần gấp đôi lệnh tùy biến,
và còn rẻ hơn.** Đây là kết luận định lượng chính của nhánh B.

### Hai lỗi của chính tôi trong buổi này
1. `branch_b_measure.sh`: biến thể đo **đầu tiên** ghi CSV không `--append` nên **xoá** các dòng đã đo
   trước đó → mất dữ liệu thô của `bv0`/`bv1` (số liệu vẫn còn trong `check.log`, nhưng không còn dòng
   từng ảnh). Đã sửa: script luôn đo **đủ cả bảy** biến thể trong một lượt.
2. `bv1r` bị ghi vào CSV dù chỉ đạt **1/2** lần đọc (UART chết đúng lúc đọc lần hai). Đã xoá 10 dòng
   đó — tiêu chí dự án là 2/2, không thoả thì không ghi nhận.

Script đã làm đúng việc của nó: in `[đối chứng KHÔNG ĐẠT sau bv1r — đường UART chết, số đo sau mốc
này VÔ GIÁ TRỊ]` rồi tự dừng. Đúng như thiết kế sau bài học B3.

## 2026-10-17 — NHÁNH B cổng B3 ĐẠT: lõi tự viết chạy trên kit, 73,3 ms

Sau khi người dùng cắm lại cáp USB, đo lại trong **một lượt liên tục** với đối chứng trước/sau mỗi
phép đo (`scripts/branch_b_measure.sh`, thiết kế tối giản `top_min` phát "MIN"). Cả hai phép đo đều
có đối chứng ĐẠT (8 lần "MIN") trước và sau.

| | A-V0 | **B-V0** | A-V1 | **B-V1** |
|---|---:|---:|---:|---:|
| tổng chu kỳ | 8.987.660 | **1.978.697** | 6.217.634 | **1.459.993** |
| `instret` | 1.358.200 | **1.358.200 KHỚP** | 911.920 | **911.920 KHỚP** |
| ms @27 MHz | 332,9 | **73,3** | 230,3 | **54,1** |
| chu kỳ/MAC | 46,80 | **10,30** | 32,37 | **7,60** |
| IPC | 0,151 | **0,686** | 0,147 | **0,625** |
| nhanh hơn | — | **4,54×** | — | **4,26×** |

CRC 5 lớp × 10 ảnh khớp golden, dự đoán khớp golden, **kit = Verilator bằng tuyệt đối**, 2/2 lần đọc.

**Kết quả đáng chú ý nhất**: B-V0 (73,3 ms) **nhanh hơn A-V1+DOT4+C1 (90,8 ms) 1,24×** — kernel C
thẳng, không một lệnh tùy biến nào, trên lõi tự viết, vượt bản tối ưu hết mức *có* lệnh tùy biến trên
PicoRV32. Với khối lượng này **vi kiến trúc đáng giá hơn tập lệnh**: 4,54× từ lõi so với 2,13× từ DOT4.

**Tài nguyên**: lõi tự viết nhanh hơn 4,54× mà **nhỏ hơn 58,8 % LUT4** (3.272 so với 7.941), DFF 656
so với 1.069. Lý do: chỉ làm đúng những gì cần (RV32IM + 4 CSR đọc), không ngắt, không PCPI, và bus
1 chu kỳ đơn giản hơn máy trạng thái 2 chu kỳ.

**Lần im lặng trước đó đúng là do UART của kit chết, không phải thiết kế** — bản `FAST_ADDR=1` (địa chỉ
tổ hợp) chạy hoàn toàn đúng trên kit. Ghi nhận thêm về hiện tượng: UART chết sau mười mấy phút không
dùng cổng (trong lúc tổng hợp bitstream), đảo DTR/RTS và đổi baud không cứu được, chỉ rút/cắm lại cáp;
phần JTAG vẫn tốt. Vì vậy mọi phép đo phải gom vào một lượt liên tục ngay sau khi cắm cáp.

Tài liệu kết quả: `docs/KET_QUA_NHANH_B.md`.

## 2026-10-17 — NHÁNH B cổng B3: TẠM HOÃN, KHÔNG PHẢI KHÔNG ĐẠT — đường UART của kit đã chết

> **SỬA KẾT LUẬN.** Mục này ban đầu ghi "B3 KHÔNG ĐẠT". Sai. Sau khi khoanh vùng theo hướng người
> dùng chọn, phép **đối chứng** cho kết quả quyết định: nạp lại bitstream **nhánh A đã biết chạy**
> (`v1dc/top.fs`) thì kit **cũng không phát byte nào**, trên **cả hai** cổng serial. Vậy đường UART
> của kit đã chết, và **mọi phép đo nhánh B từ đầu buổi B3 đều vô giá trị** — không kết luận được gì
> về lõi. Cần người dùng rút/cắm lại cáp USB rồi đo lại.
>
> **Bài học phương pháp, đáng ghi vào luận văn**: khi một phép đo trả về "không có gì", việc ĐẦU TIÊN
> phải làm là chạy **đối chứng bằng một cấu hình đã biết chạy**, trước khi sửa thiết kế. Tôi đã bỏ
> qua bước đó và sửa thiết kế bốn lần trên một đường đo đã hỏng. Quy tắc "tối đa 3 hướng sửa rồi
> dừng" trong CLAUDE.md có tác dụng, nhưng nó không cứu được việc chọn SAI đối tượng để sửa.
>
> Phần ghi chép bên dưới giữ nguyên vì các bằng chứng kỹ thuật trong đó vẫn đúng và vẫn hữu ích
> (hai lỗi thật về xung nhịp, phát hiện nextpnr không ràng buộc đường tới BSRAM).

## (ghi chép gốc) NHÁNH B cổng B3 — triệu chứng và những gì đã kiểm

B2 đã ĐẠT (xem mục dưới). B3 = đưa lõi lên kit.

### Triệu chứng
Bitstream nạp thành công (`openFPGALoader`: `Done Final`, thanh ghi trạng thái `0x00006020`),
nhưng kit **không phát một byte nào** qua UART trong 5 giây (`.venv/bin/python` đọc trực tiếp:
`nhận 0 byte`). Không phải lỗi phân tích dòng — thực sự 0 byte.

### Điều làm triệu chứng này đặc biệt khó
Tôi đã thêm một **đèn hiệu phần cứng** vào `soc_b.v` (`BEACON=1`): một máy trạng thái nhỏ tự phát
`S<state><trap><8 hex PC>\n` qua UART mỗi ~0,3 s, **hoàn toàn độc lập với lõi** — nó chỉ cần xung
nhịp chạy và khối `always` hoạt động. Đã xác nhận logic này **có trong netlist**
(`grep -c bcn_div bv0/top-synth.json` = 96, `Parameter \BEACON = 1`). **Đèn hiệu cũng im.**
→ Vấn đề KHÔNG nằm ở lõi. Nó nằm ở tầng dưới: xung nhịp không tới, hoặc thiết kế bị đóng băng.

### Những gì đã kiểm và ĐÚNG (bằng chứng, không phải phỏng đoán)
| Kiểm | Kết quả |
|---|---|
| `riscv-tests` trong Verilator, cả `FAST_ADDR`=1 và 0 | 48/48 RV32IM + `fence_i` ĐẠT |
| M1-S trong Verilator, cùng file hex của nhánh A | `M1S,sum,10,10,10,10` đúng từng bit |
| Nội dung BSRAM trong netlist | **giống hệt nhánh A**: 43.925/524.288 bit khác 0 |
| Tài nguyên | BUFG 1, IOB 9, GSR 1, BSRAM 32, RAM16SDP4 32 — cùng cấu trúc nhánh A |
| IBUF xung nhịp | `u_soc.clk_IBUF_O` — **cùng tên** như nhánh A |
| `GSR.GSRI` | nối `$PACKER_VCC` (không kích hoạt) ở **cả hai** nhánh |
| Fmax nextpnr | 86,45 MHz (ràng buộc 27) |
| `openFPGALoader` | `Done Final`, `0x00006020` |

### Hai lỗi THẬT đã tìm ra trên đường đi (đều do tôi gây ra)
1. **Chia xung nhịp trên vải FPGA** → `ERROR: Hold/min time violation for clock 'posedge clk_d'`.
   Xung nhịp dẫn xuất đi đường routing thường là thực hành sai; muốn hạ tần số phải dùng rPLL.
2. **Đặt net trung gian cho xung nhịp làm MẤT ràng buộc chân.** Khi viết `wire clk_sys = clk;`,
   yosys đổi tên net nên IBUF thành `clk_sys_IBUF_O` thay vì mang tên cổng `clk`. Ràng buộc
   `IO_LOC "clk" 4` và `CLOCK_LOC "clk" BUFG` trong `.cst` **không khớp cell nào** → xung nhịp vào
   chân bất kỳ. Đây là **cạm bẫy thật của luồng mã nguồn mở**, đáng ghi vào luận văn: *đừng đặt net
   trung gian trên đường xung nhịp ở tầng top, vì ràng buộc chân khớp theo TÊN*.
   Đã sửa (nối `clk` trực tiếp, IBUF trở lại đúng tên) — **nhưng kit vẫn im**, nên đây không phải
   nguyên nhân gốc (lần dựng ĐẦU TIÊN, trước khi có `clk_sys`, cũng đã im).

### Một phát hiện độc lập, vẫn đúng và vẫn đáng ghi
`grep -c "Sink u_soc.ram\." nextpnr.log` = **0** ở **cả** nhánh A và B: nextpnr-himbaechel **không
báo đường nào kết thúc ở BSRAM**. Nhánh A không bị ảnh hưởng vì `mem_addr` của PicoRV32 là thanh ghi.
Thiết kế 1 chu kỳ/lệnh của tôi đặt cả giải mã + tệp thanh ghi + ALU lên đường vào địa chỉ BSRAM, nên
**con số Fmax mà nextpnr báo không nói gì về đường tới hạn thật của thiết kế đó**. Vì vậy tôi đã làm
sẵn biến thể `FAST_ADDR=0` (ghi thanh ghi địa chỉ, mọi đường là thanh ghi→thanh ghi): mô phỏng
3.750.362 chu kỳ, vẫn nhanh hơn A-V0 **2,40×**.

### Khoanh vùng bằng thiết kế tối giản (hướng người dùng đã chọn)
Dựng `rtl/mycore/top_min.v` — **chỉ** một bộ đếm + `uart_tx` phát "MIN\r\n" mỗi 0,2 s + một LED nhấp
nháy. Không lõi, không RAM 64 KB, không DSP; dùng đúng cùng Makefile, cùng `.cst`, cùng lệnh công cụ.
Fmax 334 MHz. Ràng buộc chân khớp hết (log nextpnr chỉ báo `btn_s1`/`btn_s2 not found`, **giống hệt**
nhánh A). **Bản tối giản cũng im.**

→ Lúc này mới chạy phép đối chứng: nạp lại `experiment/m1s/v1dc/top.fs` (bitstream nhánh A đã đo
thành công vài phút trước) → **cũng 0 byte**, trên cả `...303170` và `...303171`. Kết luận: đường UART
của kit chết, không phải thiết kế.

### Phương án đề xuất (đã không còn cần thiết — xem phần sửa kết luận ở đầu mục)
1. **Chia nhỏ để khoanh vùng**: dựng từ cùng Makefile một top **tối giản** (chỉ đèn hiệu UART, không
   có lõi). Nếu nó cũng im → lỗi ở thiết lập build trong `rtl/mycore`; nếu nó chạy → lỗi ở `soc_b`.
   Rẻ nhất (~6 phút), thu hẹp mạnh nhất.
2. **Đối chiếu bằng Gowin EDA Education** cho đúng một bitstream (CLAUDE.md đã ghi đây là phương án
   dự phòng/đối chiếu). Nếu RTL chạy với công cụ hãng thì luồng mã nguồn mở có lỗi với thiết kế này.
3. **Giữ nhánh B ở mức mô phỏng**, ghi rõ trong báo cáo là *chưa kiểm trên phần cứng*. Số liệu vẫn
   có giá trị: lõi qua `riscv-tests`, M1-S đúng từng bit, `instret` khớp tuyệt đối nhánh A, và với
   nhánh A đã chứng minh **kit = Verilator bằng tuyệt đối** ở F5–F8 và cả 5 biến thể M1-S.
4. **Chỉ báo cáo nhánh A** — phương án dự phòng ghi trong kế hoạch gốc.

Vật phẩm: `results/branch_b/B3/` (log nạp, nextpnr, yosys, so sánh netlist).

## 2026-10-17 — NHÁNH B cổng B1 ĐẠT, và SỬA SỐ LIỆU NHÁNH A (baseline sai)

### B1: lõi tự viết qua riscv-tests ngay lần đầu
`rtl/mycore/mycore.v` (478 dòng) + `rtl/mycore/soc_b.v`. Hai tầng; bộ nhớ một cổng đọc đồng bộ 1 chu kỳ.

| | PicoRV32 | **mycore** |
|---|---|---|
| RV32IM, 48 bài | 48/48 | **48/48** |
| `fence_i` | KHÔNG ĐẠT (không có Zifencei) | **ĐẠT** |
| `ma_data` | KHÔNG ĐẠT | KHÔNG ĐẠT (bắt lỗi lệch địa chỉ theo thiết kế) |

**Hai lỗi thiết kế tôi tự tìm khi rà lại TRƯỚC khi mô phỏng** — cả hai đều âm thầm, bộ kiểm đúng/sai
không bắt được:
1. `mem_addr` phải là **tổ hợp**, không phải thanh ghi. BSRAM đã có thanh ghi địa chỉ ở đầu vào; thêm
   một tầng nữa thì địa chỉ ra chậm một chu kỳ → 2 chu kỳ mỗi lệnh, IPC 0,5, mất hết mục đích. Lõi vẫn
   chạy ĐÚNG, chỉ chậm gấp đôi.
2. Hazard đọc-sau-ghi ở tệp thanh ghi: ghi qua thanh ghi trung gian thì kết quả chỉ thấy sau 2 chu kỳ,
   mà lệnh kế đã đọc ở chu kỳ sau.

Hệ quả thiết kế: **không có hình phạt rẽ nhánh** — địa chỉ lệnh kế tính xong ngay trong chu kỳ thực
thi nên lõi luôn nạp đúng, không đoán.

`rtl/mycore/tests/ipc_probe/` — 4 vòng asm có số lệnh suy ra giải tích:

| vòng | lệnh/vòng | chu kỳ/lệnh PicoRV32 | chu kỳ/lệnh mycore | nhanh hơn |
|---|---|---:|---:|---:|
| alu | 2 | 7,00 | **1,00** | 7,0× |
| mem | 5 | 7,40 | **1,40** | 5,3× |
| mul | 4 | 6,25 | **1,25** | 5,0× |
| jmp | 3 | 6,33 | **1,00** | 6,3× |

`instret` của **cả hai lõi** khớp tuyệt đối số lệnh lý thuyết → cả hai đếm đúng. Trên firmware F6 đã
hiệu chuẩn (`2n+3`), hai lõi cũng cho `instret` giống nhau từng số.

M1-S trên lõi mới, với **chính file hex của nhánh A**: `M1S,sum,10,10,10,10` ngay lần đầu.

### SỬA SỐ LIỆU NHÁNH A — baseline A-V0/A-V2 đo bằng bản nháp chưa commit
Chính phép kiểm tôi tự đặt ra cho nhánh B đã bắt được: *cùng một file hex thì `rdinstret` phải bằng
nhau tuyệt đối*. Lõi mới báo 1.358.178; số A-V0 đã công bố là 1.864.264. Chênh đó không giải thích
được bằng vi kiến trúc → chỉ còn khả năng hai số đo **không cùng firmware**. Xác nhận bằng `GIT_HASH`
nhúng trong firmware: `sim.log` của A-V0 báo `339b4fb`, hex trên đĩa báo `c718706`.

Nguyên nhân: khi thêm A-V1 tôi viết lại `conv2` *bản thẳng* (macro `MAC8` + con trỏ chạy) làm nó nhanh
hơn, nhưng **không đo lại A-V0/A-V2**. Baseline chậm hơn thực tế → mọi tỷ số bị phóng đại.

Đã **đo lại cả 5 biến thể trên kit từ một trạng thái mã nguồn duy nhất**, mỗi biến thể 2/2 lần đọc đạt:

| | A-V0 | A-V1 | A-V2 | A-V1+DOT4 | A-V1+DOT4+C1 |
|---|---:|---:|---:|---:|---:|
| tổng | **8.987.660** | 6.217.634 | **5.758.001** | 2.917.079 | **2.450.494** |
| lệnh | **1.358.200** | 911.920 | **913.105** | 460.793 | 391.278 |
| ms | **332,9** | 230,3 | **213,3** | 108,0 | **90,8** |
| so A-V0 | 1,00× | **1,45×** | **1,56×** | **3,08×** | **3,67×** |

(trước đây công bố: 12.129.818 · 1,95× · 2,11× · 4,16× · 4,95×)

### Số sửa làm ĐỔI MỘT KẾT LUẬN — và kết luận mới mạnh hơn
Trước đây tôi viết "hai tối ưu độc lập, nhân được với nhau" vì DOT4 cho 2,11× trên C thẳng và 2,13×
trên C tối ưu. Với số đúng, hai hệ số đó là **1,56×** và **2,13×** — **không** độc lập:

> **DOT4 cho lợi ích gấp 1,37 lần khi phần mềm đã được tối ưu trước.**

Lý do đọc được từ số liệu: ở C thẳng, `conv2` tốn 35,95 chu kỳ/MAC mà phần lớn là **tính chỉ số**;
DOT4 chỉ cắt phần nhân-cộng nên cắt được một phân số nhỏ. Sau khi tối ưu phần mềm, phần nhân-cộng mới
chiếm tỷ trọng lớn.

**Hệ quả cho phương pháp co-design: thứ tự có ý nghĩa.** Đo một lệnh tùy biến trên mã chưa tối ưu sẽ
**đánh giá THẤP** giá trị của nó. Và đây là câu trả lời mạnh hơn cho phản biện "tăng tốc chỉ nhờ
baseline kém": với baseline *đã tối ưu*, DOT4 vẫn cho 2,13× — **cao hơn** khi đo trên baseline kém.

Lưu ý phân rã theo chuỗi (1,4455 × 2,1315 = 3,0810 = đúng số đo tới 4 chữ số): đó **đúng do định
nghĩa**, cùng một con đường viết thành hai chặng. Nó xác nhận phép đo nhất quán, không phải phát hiện.
Trước đây tôi trình bày nó như phát hiện — đó là cách diễn giải sai, đã sửa.

### Cách chặn để không lặp lại
`GIT_HASH` không đủ. Firmware giờ in thêm **dấu vân tay NỘI DUNG**:
`SRC_HASH := $(shell cat main.c $(FWDIR)/weights.h | shasum -a 256 | cut -c1-12)`.
Kit in `M1S,src,<SRC_HASH>` và `scripts/m1s_check.py` **từ chối** ghi nhận nếu khác mã nguồn trên đĩa.
Cả 5 số đo mới mang `SRC_HASH = 647f1d071aca`.

**Điểm cốt lõi**: kiểm tính đúng đắn (CRC khớp golden) **không** bắt được lỗi này — cả hai bản firmware
đều đúng từng bit, chỉ chạy nhanh khác nhau. Một bộ số đo chỉ so sánh được khi mọi biến thể đến từ cùng
một trạng thái mã nguồn, và điều kiện đó phải do **máy** kiểm.

Không ảnh hưởng: độ chính xác 98,25 % trên 10.000 ảnh, 10.000/10.000 CRC, tài nguyên/Fmax, chi phí
requantize 49,6 chu kỳ, kết luận kit = Verilator.

## 2026-10-17 — NHÁNH B, cổng B0: hạ tầng kiểm thử riscv-tests — ĐẠT

Bắt đầu nhánh B. Kế hoạch nhánh B viết ra ở `docs/BRANCH_B_PLAN.md` (7 cổng B0–B6, tiêu chí từng
cổng, rủi ro đã nhận diện). Lý do nhánh B đáng làm, lấy từ số đo chứ không từ cảm nhận: **IPC = 0,160**
ở biến thể nhanh nhất của nhánh A, tức 6,26 chu kỳ mỗi lệnh — nguyên nhân thuộc **vi kiến trúc**
(PicoRV32 không pipeline, bus `soc.v` 2 chu kỳ mỗi truy cập), thêm lệnh tùy biến không sửa được.

### Quyết định phương pháp: kiểm hạ tầng trên lõi ĐÃ BIẾT ĐÚNG trước
Cổng B0 không viết một dòng RTL nào của lõi mới. Nó chỉ dựng bộ kiểm và **chạy trên PicoRV32**.
Lý do: nếu dùng một harness chưa được kiểm để xét lõi mới thì mỗi lần "KHÔNG ĐẠT" đều có hai cách
giải thích, và sẽ mất rất nhiều thời gian để phân biệt lỗi lõi với lỗi harness.

### Tập lệnh bắt buộc — đếm từ firmware thật
`objdump` cả 6 bản firmware nhánh A: RV32I đầy đủ + `mul` (123 lần), `mulh` (12), `mulhu` (6),
CSR `rdcycle`/`rdcycleh`/`rdinstret`, `fence` (15, coi như nop). **Không có `div`/`rem`** ở bất kỳ bản
nào. Vẫn sẽ hiện thực `div divu rem remu mulhsu` để qua *trọn bộ* `rv32um`.

### Kết quả B0
`scripts/riscv_tests.sh` + `rtl/mycore/tests/{start_test.S, link_test.ld, riscv_test.h}`:
mỗi bài kiểm là **một chương trình riêng** (`_start` → `mytest` → `mytest_ret` in "DONE"), nạp vào
`firmware.hex`, chạy trên `soc.v` của F5. PASS/FAIL báo bằng ghi ký tự vào 0x10000000 — trùng đúng
địa chỉ UART của SoC nên không phải sửa gì.

| | |
|---|---|
| **RV32IM (48 bài: 40 `rv32ui` + 8 `rv32um`)** | **ĐẠT 48/48 trên PicoRV32** → harness đúng |
| ngoài RV32IM: `ma_data` | KHÔNG ĐẠT — cần hỗ trợ truy cập lệch địa chỉ; PicoRV32 bật `CATCH_MISALIGN` |
| ngoài RV32IM: `fence_i` | KHÔNG ĐẠT — cần Zifencei |

`fence_i` không đạt **có bằng chứng từ mã nguồn**, không phải đoán: `picorv32.v:1088` giải mã
`instr_fence <= (mem_rdata_q[6:0] == 7'b0001111 && !mem_rdata_q[14:12])` — chỉ nhận `funct3 == 0`,
nên `fence.i` (`funct3 == 1`) là lệnh không hợp lệ → trap ở chu kỳ 1758.
Lõi tự viết sẽ hiện thực `fence.i` (xả lệnh đã nạp trước) nên **có thể qua được bài này**, tức hơn
PicoRV32 một bài — sẽ xác nhận bằng số đo ở B1, không hứa trước.

### Cạm bẫy
- `$CROSS gcc` trong shell script → `riscv-none-elf- gcc` (có khoảng trắng) → "command not found" cho
  cả 49 bài. Phải viết `"${CROSS}gcc"`. Triệu chứng giống hệt "toolchain hỏng", rất dễ mất thời gian.
- Lần đầu tất cả bài đều in `mytest..OK DONE` nhưng harness báo KHÔNG ĐẠT, vì tôi quên truyền
  `TEST_FUNC_TXT` nên bài nào cũng tự gọi là "mytest". Dấu hiệu nhận ra: output đúng mà kết luận sai.
- `sim_main.cpp` chỉ in khi gặp `\n`, mà `RVTEST_CODE_BEGIN` in tên bài **không có** `\n`. Nên một
  bài trap giữa đường cho log **rỗng hoàn toàn** — không phải mất output, chỉ là chưa xả bộ đệm.
  Harness của nhánh B sẽ xả phần dở khi kết thúc.

Vật phẩm: `results/branch_b/B0/` (kết quả 50 bài trên PicoRV32 + log trap của `fence_i`/`ma_data`).
Phiên bản ghim: `env/VERSIONS.md` (riscv-tests `d7e86f70`).

## 2026-10-17 — Chạy ĐỦ 10.000 ảnh test trên kit: 98,25 % là số ĐO, không phải số suy ra

Lỗ hổng duy nhất còn lại của chương nhánh A: năm biến thể chỉ chạy **10 ảnh nhúng trong firmware**,
nên 98,25 % là của golden Python, không phải của kit. RAM 64 KB không chứa nổi 10.000 ảnh (7,84 MB)
→ phải nạp ảnh qua UART.

### Giao thức, và hai tính chất làm nó tự lành
**1 byte `0xA5` + 784 byte ảnh**, host gửi theo khối 64 byte (bài học F2).
- Pixel lượng tử hoá ∈ [0,127] nên **không bao giờ** trùng `0xA5` → mất byte thì khung sau tự đồng bộ
  lại. Đây là lý do chọn đúng giá trị 0xA5 chứ không phải một byte bất kỳ.
- **Kit mời thì host mới gửi** (chỉ gửi sau một dòng hoàn chỉnh).
- Kit báo **CRC32 của chính 784 byte nó nhận được** → tách lỗi đường truyền khỏi lỗi tính toán.

### Mô phỏng trước khi tổng hợp — và nó bắt được hai lỗi
Harness Verilator cũ (F5/F8) chỉ đọc `uart_tx`, giữ `uart_rx` mức cao, nên **không kiểm được chiều
thu**. Viết `experiment/m1s/sim_main_10k.cpp` tự tạo dạng sóng 8N1 ở đúng `DIV=234` bơm vào `uart_rx`.

1. **GCC nhân bản `conv1` thành `conv1.constprop.0`** vì `conv1(img_buf)` luôn cùng một địa chỉ →
   sinh mã **khác** `v1dc`, làm bản 10k không còn so sánh được với 5 biến thể cũ.
   `scripts/cmp_layers.py` (mới) phát hiện. Sửa: `static i8 *volatile img_p = img_buf;`.
   Giá phải trả, ghi đúng: `conv1` 1.133.668 → **1.133.673** (+5 chu kỳ cho một lần đọc volatile).
2. **Thanh ghi thu chỉ giữ MỘT byte, không FIFO** (`rx_hold`/`rx_full` trong `soc.v`). Harness gửi
   ngay sau reset, trong lúc kit còn đang phát dòng `hello`, nên mọi byte bị byte sau ghi đè. Kit quét
   tìm `0xA5` mãi không thấy → mô phỏng chạy 83 triệu chu kỳ không ra phản hồi. Nếu đem thẳng lên kit
   thì chỉ thấy "treo" mà không biết vì sao. Sửa bằng quy tắc "kit mời thì host mới gửi".

Mô phỏng 3 ảnh: dự đoán 7/2/1, CRC logit `9377670B`/`3C922E73`/`46B2E0F3`, CRC ảnh
`8DF03AB1`/`317A5E14`/`C73EC552` — **khớp golden từng bit**. `make cmp-v10k`: `CMP_PASS`, cả 6 hàm
(`conv1`, `conv1_prep`, `pool1`, `conv2`, `pool2`, `dense`) trùng khít mnemonic/thanh ghi/offset.
Tài nguyên `v10k` **giống hệt** `v1dc`: LUT4 8.065, 4 MULT18X18, Fmax 71,89 MHz.

### Kết quả trên kit (30,0 phút, 27 MHz)
| | |
|---|---|
| khung nhận đúng | **10.000/10.000**, thất bại 0, **gửi lại 0 lần**, CRC ảnh lệch 0 |
| CRC32 logit = golden | **10.000/10.000 (100 %)** |
| dự đoán = golden | **10.000/10.000** |
| **độ chính xác đo trên kit** | **9.825/10.000 = 98,25 %** |

Bằng golden **tuyệt đối**. 0 lần gửi lại trên 7,85 MB cũng xác nhận lại kết luận F2.

### Hai kết quả phụ đáng giá, chỉ thấy được khi chạy 10.000 ảnh
**a) Suy luận tất định về thời gian.** Biên độ tổng chỉ **765 chu kỳ = 0,031 %**; mỗi ảnh
**90,74–90,77 ms**. `conv1` và `dense` biên độ **0** trên cả 10.000 ảnh; `conv2` lệch tối đa 2 chu kỳ
(ReLU rẽ nhánh); `pool1`/`pool2` biên độ 560/234 (maxpool rẽ nhánh theo so sánh).
→ **Phải sửa một điều đã ghi trước đây**: `pool1 = 225.600` và `pool2 = 65.921` là hằng số *với 10 ảnh
cố định*, chứ không phải vì hai lớp đó tất định. Chỉ 10.000 ảnh mới phân biệt được hai chuyện này.

**b) IPC = 0,160** (391.268 lệnh / 2.450.490 chu kỳ). Đây là lý do gốc còn 12,76 chu kỳ/MAC:
PicoRV32 không pipeline và bus RAM mất 2 chu kỳ mỗi truy cập. Nó chỉ về **nhánh B** (lõi tự viết),
không về thêm lệnh tùy biến — một lập luận định lượng cho phần sau của luận văn.

175 ảnh sai đều là lỗi *mô hình* (kit khớp golden 10.000/10.000): `4→9` 14 lần, `6→0` 11, `7→2` 11,
`8→0` 10 — đúng đặc trưng quen thuộc của CNN nhỏ trên MNIST.

### Cạm bẫy mới
- Golden từng sinh bằng `.venv-model` (numpy 1.26.4) nhưng script 10k chạy trong `.venv`
  (**numpy 2.5.4**, khác quy tắc quảng bá kiểu NEP 50). Đã kiểm: 10 CRC logit + 10 dự đoán tính lại
  trên numpy 2.5.4 **khớp từng bit** `fw/weights.h`, và đường vectorized khớp đường vô hướng. Nếu
  không khớp thì toàn bộ phép so 10.000 ảnh vô nghĩa ngay từ đầu.
- Tiến trình chạy dài ở chế độ nền có lúc bị hệ điều hành hạ ưu tiên xuống **2 % CPU** (11,5 phút
  tường chỉ dùng 14,8 s CPU). Mô phỏng nặng CPU phải chạy tiền cảnh; lần chạy 10k thì nghẽn ở UART
  nên không ảnh hưởng.
- CSV được ghi **từng dòng và flush** ngay, để 30 phút chạy không mất dữ liệu nếu bị ngắt.

Vật phẩm: `results/experiment/m1s/m1s_10k.csv` (10.000 dòng × 14 cột, 698 KB) ·
`results/experiment/m1s/v10k/` (22 file) · `experiment/m1s/v10k/stats.txt`.

## 2026-10-17 — A-V1+DOT4+C1: gỡ nút cổ chai conv1 bằng BỐ CỤC, và định lượng lệnh REQ

> **ĐÃ SỬA SỐ** — các con số của A-V0/A-V2 và mọi tỷ số so với A-V0 trong
> mục này là SAI (baseline đo bằng bản nháp chưa commit). Số đúng và cách phát hiện:
> xem mục nhật ký ngày 2026-10-17 "Sửa số liệu nhánh A" ở trên và `docs/KET_QUA_M1S.md` mục 3c.

Số liệu của bảng 2×2 chỉ đúng một chỗ để đánh tiếp: ở biến thể nhanh nhất (A-V1+DOT4), **conv1 chiếm
54,9 %** thời gian và **không dùng được DOT4** — vì `Cin=1`, 4 pixel liền nhau theo hàng thì có,
nhưng địa chỉ của chúng không chia hết 4 nên không nạp được bằng một `lw`. Nếu conv2 và dense có về 0
thì tổng cũng chỉ nhanh thêm 1,54× (Amdahl). Nên tôi làm conv1 trước REQ.

### Cách gỡ: không thêm một cổng logic nào
- Giữ **4 bản sao ảnh dịch 0/1/2/3 byte**, mỗi hàng đệm lên `PHS=32` byte:
  `ph[p][y][j] = img[y][j − p]`. Giá trị `img[y][x]` nằm ở offset `x + p`; chọn `p = (−x) & 3` thì
  `x + p` chia hết 4 → mọi lần đọc đều thẳng hàng. `x ≤ 25` nên offset xa nhất là 31 < 32, không tràn hàng.
- Trọng số conv1 nhân bản thành nhóm 4 với **tap thứ 4 = 0** (`w1x[oc][ky][0..3]`). Phép toán không
  đổi (cộng thêm `0 × pixel`), nên kết quả **vẫn khớp golden từng bit**.
- conv1 còn **3 lệnh DOT4** cho 3 hàng kernel, thay cho 9 phép nhân vô hướng.
- Chi phí: `.bss` **+3.584 byte**, sao chép **3.136 byte/ảnh** (đã tính trong số đo).

### Kết quả (trung vị 10 ảnh, kit, 27 MHz)
| | conv1 | TỔNG | ms | chu kỳ/MAC |
|---|---:|---:|---:|---:|
| A-V1+DOT4 | 1.600.258 | 2.917.102 | 108,0 | 15,19 |
| **A-V1+DOT4+C1** | **1.133.668** | **2.450.517** | **90,8** | **12,76** |

→ conv1 nhanh **1,41×**, tổng nhanh **1,19×**, tăng tốc tích luỹ so A-V0 lên **4,95×**; số lệnh
460.794 → **391.278**. Tài nguyên FPGA **không đổi** (cùng bitstream với A-V1+DOT4: LUT4 8.065,
4 MULT18X18, Fmax 71,89 MHz) — đây là lợi ích **miễn phí về phần cứng**. RAM 32.368/65.536 (49,4 %).

Kiểm tính đúng đắn: CRC32 5 lớp × 10 ảnh khớp golden, dự đoán khớp golden và khớp nhãn thật, số chu
kỳ kit = Verilator **bằng tuyệt đối** — lặp 2/2 lần đọc độc lập.

### Đo chi phí requantize (cơ sở cho lệnh REQ)
Hai vòng lặp 20.000 bước giống hệt nhau, khác đúng một thứ; toán hạng phụ thuộc biến đếm để GCC
không nhấc phép tính ra ngoài vòng (bài học từ F8):
`1.671.265 − 680.007 = 991.258` chu kỳ cho 20.000 lần → **49,6 chu kỳ/requantize**.
Mỗi ảnh requantize 7.344 giá trị (conv1 5.408 + conv2 1.936) → **363.990 chu kỳ = 14,9 %** của
A-V1+DOT4+C1. Một lệnh `REQ` ~1 chu kỳ sẽ cho **~78 ms, thêm 1,17×**.

**Kết luận cho kế hoạch**: REQ đáng làm nhưng không phải đòn lớn nhất. Đòn lớn hơn là giảm **số lệnh
trên mỗi giá trị đầu ra của conv1** (chỉ 9 MAC/đầu ra để chia sẻ chi phí cố định, so với 72 ở conv2)
— ví dụ tính nhiều kênh ra cùng lúc để dùng lại 3 từ ảnh đã nạp.

### Ghi nhận trung thực một lệch nhỏ
Thêm phần đo requantize (`REQ_BENCH`) vào bản v1dc làm mã `dense` dài thêm 4 byte (0x78 → 0x7c) và
tốn thêm **5 chu kỳ** (39.052 → 39.057). Đã kiểm `conv2`, `pool1`, `pool2` có kích thước mã **giống
hệt**, nên so sánh conv1 — thứ đang xét — không bị ảnh hưởng. Không làm tròn con số này đi.

### Cạm bẫy mới gặp
- `scripts/archive_gate.sh` ghi cứng `results/feasibility/` → thí nghiệm chính bị lưu sai chỗ; thêm
  biến môi trường `RESULTS_BASE` (thí nghiệm chính dùng `results/experiment`).
- Có lúc **hai tiến trình cùng điều khiển kit** (tôi mở vòng đo thứ hai khi vòng trước chưa xong) →
  số đọc sai. Phép kiểm nhãn biến thể trong từng block bắt được ngay ("kit báo A-V2, mong đợi A-V0").
  Quy tắc: **nạp và đo tuần tự**, không song song.

Vật phẩm: `results/experiment/m1s/` (6 archive + `m1s.csv` + log thô). Tài liệu:
`docs/KET_QUA_M1S.md`.

## 2026-10-17 — A-V1 (tối ưu phần mềm) + bảng 2×2 đầy đủ · KẾT QUẢ CHÍNH CỦA THÍ NGHIỆM

> **ĐÃ SỬA SỐ** — các con số của A-V0/A-V2 và mọi tỷ số so với A-V0 trong
> mục này là SAI (baseline đo bằng bản nháp chưa commit). Số đúng và cách phát hiện:
> xem mục nhật ký ngày 2026-10-17 "Sửa số liệu nhánh A" ở trên và `docs/KET_QUA_M1S.md` mục 3c.

Tôi tự chọn làm A-V1 trước A-V3, vì đó là khoảng trống **khoa học** lớn nhất: không có nhóm đối chứng
phần mềm thì phản biện sẽ hỏi ngay *"2,11× là nhờ lệnh tùy biến hay chỉ nhờ code tốt hơn?"* — và phát
hiện `noinline` (1,76× miễn phí) ở phiên trước cho thấy câu hỏi đó rất chính đáng.

Làm thành **bảng 2×2** trên cùng một `main.c`, hai cờ biên dịch độc lập (`OPT_KERNELS`, `USE_DOT4`):
A-V0 / A-V1 / A-V2 / A-V1+DOT4.

### Tối ưu phần mềm của A-V1 (không đổi một phép toán nào)
- **conv1**: đưa vòng kênh ra ra NGOÀI → 9 trọng số + bias nằm trong thanh ghi suốt cả mặt 26×26;
  9 phép nhân dùng **offset hằng số** (28, 56 là bước hàng ảnh) từ một con trỏ hàng; con trỏ ra chạy
  đều bước 8 byte. → 71,74 **→ 32,88** chu kỳ/MAC.
- **conv2**: bung hết 9 vị trí kernel bằng offset hằng số từ một con trỏ gốc (bước hàng `p1` = 104 byte),
  mỗi vị trí gọi macro `MAC8`. → 58,50 **→ 30,13** chu kỳ/MAC.
- **dense**: bung vòng trong bước 8. → 48,14 **→ 31,56** chu kỳ/MAC.
- `MAC8` có hai bản (8 phép nhân, hoặc 2 lệnh DOT4) nên bật/tắt DOT4 không cần sửa cấu trúc vòng lặp.

### Số đo trên kit (trung vị 10 ảnh, 27 MHz) — cả 4 biến thể ĐẠT
| Lớp | A-V0 | A-V1 | A-V2 | A-V1+DOT4 |
|---|---:|---:|---:|---:|
| conv1 | 3.491.721 | 1.600.258 | 3.491.721 | 1.600.258 |
| pool1 | 225.600 | 225.600 | 225.600 | 225.600 |
| conv2 | 8.153.979 | 4.199.609 | 1.924.815 | **986.226** |
| pool2 | 65.921 | 65.921 | 65.921 | 65.921 |
| dense | 192.552 | 126.224 | 48.552 | **39.052** |
| **TỔNG** | **12.129.818** | **6.217.657** | **5.756.654** | **2.917.102** |
| lệnh | 1.864.264 | 911.920 | 912.832 | **460.794** |
| ms @27 MHz | 449,3 | 230,3 | 213,2 | **108,0** |
| chu kỳ/MAC | 63,16 | 32,37 | 29,97 | **15,19** |
| tăng tốc so A-V0 | 1,00× | **1,95×** | **2,11×** | **4,16×** |

### KẾT QUẢ QUAN TRỌNG NHẤT: hai tối ưu nhân được với nhau
| Nguồn | Hệ số |
|---|---|
| Tối ưu phần mềm một mình (A-V0→A-V1) | **1,95×** |
| DOT4 trên C thẳng (A-V0→A-V2) | 2,11× |
| **DOT4 thêm vào C đã tối ưu** (A-V1→A-V1+DOT4) | **2,13×** |
| Cả hai | **4,16×** |
| Tích hai hệ số riêng | 1,95 × 2,13 = **4,16×** |

Tích **đúng bằng** số đo. Nghĩa là lợi ích của lệnh tùy biến **không biến mất khi phần mềm đã tối ưu**
(2,13× so với 2,11×). Lý do: hai tối ưu cắt hai phần khác nhau — phần mềm bỏ **tính chỉ số**
(thấy rõ ở conv1: 71,74 → 32,88 mà không có lệnh mới nào), DOT4 bỏ **nhân-cộng** (conv2 trên nền đã
tối ưu: 30,13 → 7,08). Đây là câu trả lời trực tiếp cho phản biện "baseline code kém".

### Tính đúng đắn
Cả 4 biến thể, 2/2 lần đọc mỗi biến thể: **CRC32 200/200 khớp golden** (5 lớp × 10 ảnh × 4 biến thể),
dự đoán **40/40** khớp golden và khớp nhãn, chu kỳ kit = Verilator **bằng tuyệt đối** cả 7 cột.
`conv1`/`pool1`/`pool2` cho **đúng cùng số chu kỳ** trong từng cặp so sánh — bằng chứng mỗi cặp chỉ
khác đúng một thứ.

### Tài nguyên
A-V0 và A-V1 dùng **cùng phần cứng** (LUT4 7.941, Fmax 71,76 MHz) — chỉ khác nội dung firmware trong
BSRAM, nên **toàn bộ 1,95× của A-V1 là miễn phí về phần cứng**. A-V2/A-V1+DOT4: LUT4 8.065
(**+124, +1,6 %**), +84 DFF, 4/48 MULT18X18, Fmax 71,89 MHz (**không giảm**).
RAM: 27,5–29,3 KB / 65,5 KB; A-V1 tốn thêm ~1,7 KB `.text` vì bung vòng.

### Nút cổ chai tiếp theo
Trong A-V1+DOT4, **conv1 chiếm 54,9 %** thời gian và không dùng được DOT4 (`Cin=1` không có 4 giá trị
liền nhau thẳng hàng 4 byte). Nếu conv2 + dense về 0 cũng chỉ nhanh thêm **1,54×**. Hướng tiếp:
một lệnh phục vụ conv1 — DOT4 bản không cần thẳng hàng, hoặc lệnh nhân-cộng 3 phần tử theo hàng ảnh,
hoặc đổi bố cục conv1 (nhân bản ảnh theo 4 pha dịch).
**→ REQ của A-V3 nên nhắm vào conv1, không phải conv2.**

### Một bài học vận hành
Lần đo đầu script báo *"kit báo biến thể A-V2, mong đợi A-V0"*: tôi đã khởi động vòng đo thứ hai khi
vòng đầu còn đang nạp kit, hai tiến trình tranh nhau cùng một kit. Phép kiểm **nhãn biến thể trong mỗi
khối dữ liệu** đã chặn được một số đo sai. → Mỗi khối số đo nên tự khai báo nó thuộc biến thể nào;
chi phí gần bằng không mà chặn được loại lỗi khó thấy nhất. Cũng đã đổi `--drain 0` → `--drain 2` cho
M1-S vì mỗi khối mất ~5 giây nên xả 2 giây là an toàn.

### Việc còn lại
- **A-V3 (+REQ)** — chưa làm; theo số liệu trên nên nhắm vào conv1.
- **Nhánh B** (lõi tự viết) — chưa làm.
- Đo trên nhiều hơn 10 ảnh trên kit; đo công suất.

## 2026-10-17 — THÍ NGHIỆM CHÍNH: M1-S chạy đầy đủ trên kit, A-V0 và A-V2

Lần đầu **một mô hình CNN hoàn chỉnh đã huấn luyện** chạy suy luận trên kit và đo được số chu kỳ.
Kết quả đầy đủ: `docs/KET_QUA_M1S.md`. Số liệu gốc: `results/experiment/m1s/m1s.csv`.

### Mô hình
- Huấn luyện M1-S bằng PyTorch (8 epoch, Adam, batch 128, seed 1234): **float 98,29 %** trên
  10.000 ảnh test. Tham số 5.258 — khớp đúng con số của kế hoạch.
- Lượng tử hoá int8 sau huấn luyện, đối xứng, zero-point = 0; hiệu chuẩn thang activation trên 512
  ảnh train. requantize gemmlowp: lớp 1 `M0=1138411053, shift=8`; lớp 2 `M0=1108363094, shift=8`.
  Dense **không** requantize (giữ int32 rồi argmax) → bỏ được một cặp (M0, shift) và một lần làm tròn.
- **int8 98,25 %**, chênh float **+0,04 điểm %** — tiêu chí kế hoạch là ≤1 điểm → ĐẠT rất rộng.

### Quyết định thiết kế quan trọng: bố cục channels-last
`DOT4` nạp 4 byte liền nhau bằng `lw` nên **cần địa chỉ thẳng hàng 4 byte** (lõi bật
`CATCH_MISALIGN`). Vì vậy activation lưu theo **[H][W][C]** và trọng số conv theo
**[Cout][ky][kx][Cin]**: conv2 có `Cin=8` nên 4 kênh vào liền nhau luôn thẳng hàng, dùng đúng
2 lệnh DOT4 cho mỗi vị trí kernel, không bỏ sót MAC nào. Hệ quả: `m1s_w3` phải **hoán vị cột** so
với PyTorch (torch làm phẳng theo (C,H,W), ta theo (H,W,C)). Golden Python viết lại theo đúng bố cục
này nên mọi CRC32 và thứ tự làm phẳng khớp firmware.

**conv1 không dùng được DOT4** vì `Cin=1`: không có 4 giá trị liền nhau để cộng dồn mà vẫn thẳng hàng.
conv1 chiếm 25,3 % số MAC nhưng 28,8 % thời gian A-V0 — và trở thành nút cổ chai của A-V2.

### Số đo trên kit (trung vị 10 ảnh, 27 MHz)
| Lớp | A-V0 | A-V2 | Tăng tốc | chu kỳ/MAC V0 → V2 |
|---|---:|---:|---:|---|
| conv1 | 3.491.721 | 3.491.721 | 1,00× | 71,74 → 71,74 |
| pool1 | 225.621 | 225.621 | 1,00× | — |
| conv2 | 8.153.979 | **1.924.815** | **4,24×** | 58,50 → 13,81 |
| pool2 | 65.924 | 65.924 | 1,00× | — |
| dense | 192.552 | **48.552** | **3,97×** | 48,14 → 12,14 |
| **TỔNG** | **12.129.818** | **5.756.654** | **2,11×** | 63,16 → **29,97** |
| thời gian | 449,3 ms | 213,2 ms | | |

Tính đúng đắn, cả hai biến thể, 2/2 lần đọc: **CRC32 50/50 khớp golden** (5 lớp × 10 ảnh),
dự đoán **10/10** khớp golden và khớp nhãn, số chu kỳ kit = Verilator **bằng tuyệt đối** cả 7 cột.

Tài nguyên: A-V0 LUT4 7.941 / Fmax 71,76 MHz; A-V2 LUT4 8.065 / Fmax 71,89 MHz →
DOT4 tốn **+124 LUT4 (+1,6 %)**, +84 DFF, 4/48 MULT18X18, **Fmax không giảm**.
RAM 27.564/65.536 byte (42,1 %).

### Ba phát hiện
1. **Tăng tốc bị chặn bởi conv1, đúng dự báo ở F8.** Trong A-V2 conv1 chiếm 60,7 % thời gian.
   Giới hạn Amdahl = 12.129.818/3.783.266 = **3,21×**; DOT4 đã cắt 6.373.164 trong 8.346.552 chu kỳ
   có thể cắt = **76,4 %**. Muốn đi xa hơn phải nhắm vào conv1.
2. **Ước tính ở F7 sát**: F7 ngoại suy ≈516 ms, thực đo A-V0 là **449,3 ms** → ước tính cao hơn 15 %,
   lệch theo hướng an toàn. Nguyên nhân đúng như F7 đã nêu: conv2 có `Cin=8` nên chi phí/MAC *thấp hơn*
   conv1 (58,50 so với 71,74) do chia sẻ được phần tính chỉ số.
3. **Một cái bẫy của trình biên dịch, không liên quan phần cứng.** Ban đầu 5 lớp là hàm `static` gọi
   một lần; GCC `-O2` nội suy hết vào `main` và tràn thanh ghi → A-V0 chạy **21.350.804** chu kỳ.
   Thêm `__attribute__((noinline))` cho mỗi lớp đưa về **12.129.818** chu kỳ — **nhanh hơn 1,76 ×
   mà không đổi một dòng thuật toán**. Tệ hơn: khi chưa có `noinline`, cấp phát thanh ghi của conv1
   **thay đổi theo** việc conv2 dùng DOT4 hay không (3.803.170 so với 4.950.316 chu kỳ), làm phép so
   sánh A-V0/A-V2 mất ý nghĩa. Sau khi sửa, conv1/pool1/pool2 có **kích thước mã giống hệt** và cho
   **đúng cùng số chu kỳ** ở hai biến thể — đó là bằng chứng phép so sánh chỉ khác một thứ.
   → **Quy tắc phương pháp: khi so hai biến thể tập lệnh, cố định ranh giới hàm và phải kiểm rằng các
   lớp KHÔNG thay đổi cho ra đúng số chu kỳ cũ.**

### Hạ tầng
- `model/`: `mnist.py` (nạp idx.gz), `train_m1s.py`, `quantize_m1s.py`, `golden_m1s.py` (golden int8
  đúng từng bit, có `test_requant_equiv()` kiểm bản vector hoá khớp bản vô hướng).
- `fw/weights.h` sinh tự động: trọng số int8, bias int32, (M0, shift), 10 ảnh thử, nhãn, dự đoán
  golden và **CRC32 golden của từng lớp** — firmware tự kiểm và host kiểm lại.
- `experiment/m1s/`: firmware 5 lớp + Makefile hai biến thể, dùng lại SoC của F5 và khối DOT4 của F8.
- `scripts/m1s_check.py`: đọc kit, đối chiếu golden (đọc lại từ `weights.h`, không hard-code) và
  Verilator, ghi CSV.
- `.venv-model` riêng (Python 3.12 + torch 2.2.2 + numpy 1.26.4): Python 3.14 không có wheel torch cho
  macOS x86_64; torch 2.2.2 là bản cuối còn wheel và nó cần numpy < 2. Ghi rõ trong `env/VERSIONS.md`.
- `scripts/archive_gate.sh` thêm `RESULTS_BASE` để lưu ra `results/experiment/`.

### Hai lỗi script của tôi, đã sửa
- `m1s_check.py` dùng regex `^M1S,([a-z]+),(.*)$` bắt buộc dấu phẩy thứ hai nên dòng `M1S,done`
  không khớp và không bao giờ nhận ra khối đã đủ. Sửa thành `,?`.
- `archive_gate.sh` hard-code `results/feasibility/` nên lưu nhầm vào
  `results/feasibility/experiment/m1s`. Sửa bằng biến `RESULTS_BASE`.

### Việc còn lại của thí nghiệm chính
- **A-V1** (chỉ tối ưu phần mềm, nhóm đối chứng) — chưa làm. Lưu ý: phát hiện `noinline` ở trên thực
  chất đã là một tối ưu phần mềm 1,76×, nên A-V1 cần định nghĩa lại cho rõ đâu là "đối chứng".
- **A-V3** (+ lệnh REQ) — chưa làm. Theo số liệu trên, REQ nên nhắm vào conv1.
- **B-V*** (lõi tự viết) — chưa làm.
- Đo trên nhiều ảnh hơn 10 trên kit; đo công suất.

## 2026-10-17 — Cổng F8 (lệnh tùy biến DOT4 qua PCPI) — ĐẠT · GIAI ĐOẠN KHẢ THI HOÀN TẤT

Cả ba tiêu chí đạt, cho **cả hai biến thể** bitstream, 3/3 lần đọc mỗi bản:
CRC bản DOT4 = bản vô hướng = Python (`3D68C1ED`), chu kỳ kit = Verilator **bằng tuyệt đối**,
và có **số tăng tốc thật: 3,985×**.

### Khối DOT4 (`rtl/ext/pcpi_dot4.v`)
- `rd = Σ_{i=0..3} int8(rs1[8i+7:8i]) · int8(rs2[8i+7:8i])`, opcode custom-0 `0001011`,
  funct3 `000`, funct7 `0000000`. Phía C: `.insn r 0x0B, 0, 0, rd, rs1, rs2`.
- Giao thức PCPI lấy **đúng dạng của `picorv32_pcpi_fast_mul`** trong chính lõi: chốt toán hạng,
  thanh ghi dịch `active[1:0]`, trả lời bằng `pcpi_wr` + `pcpi_ready` cùng một chu kỳ, `pcpi_wait = 0`.
  Độ trễ 2 chu kỳ, dưới timeout 16 chu kỳ của lõi.
- Hai đường nhân chọn bằng cờ biên dịch: `PCPI_DOT4_DSP` gọi **trực tiếp `MULT18X18`** (cách PRM đã
  ĐẠT ở F4), mặc định là nhân hành vi (cho mô phỏng và cho bản `-nodsp` nhân bằng logic).
- `soc.v` thêm tham số `WITH_DOT4` (mặc định 0). **Đã kiểm hồi quy**: với `WITH_DOT4=0`, F7 cho lại
  **y hệt** 4.921.446 / 3.533.204 chu kỳ và cùng CRC — thay đổi không ảnh hưởng F5/F6/F7.

### Testbench riêng cho khối (bước 2 của kế hoạch)
`feasibility/F8_dot4/tb_dot4.v`, Icarus: **1.000.108 phép DOT4 đúng** —
1.000.000 cặp từ LFSR + 108 giá trị biên (mọi tổ hợp của {−128, −127, −1, 0, 1, 127} trên cả 4 lane,
cộng quét từng lane trong khi ba lane còn lại giữ giá trị xấu nhất). Tham chiếu tính **độc lập** trong
testbench (tách lane sang `reg signed [7:0]`, cộng dồn trong `integer`), khác cách của DUT.
Có thêm một phép kiểm quan trọng: **khối phải IM LẶNG với lệnh không phải của nó** (thử bằng `MUL`) —
nếu không nó sẽ phá lệnh `MUL`/`DIV` mà lõi xử lý qua PCPI nội bộ.

### Số đo trên kit (bài A, 102.400 MAC, 25.600 lệnh DOT4)
| Bản | chu kỳ | lệnh | CPI | chu kỳ/MAC |
|---|---:|---:|---:|---:|
| vô hướng | 4.921.446 | 717.812 | 6,86 | 48,06 |
| **DOT4** | **1.235.011** | 180.205 | 6,85 | **12,06** |

- **Tăng tốc 3,985×**; số lệnh giảm **3,983×**.
- **Tăng tốc bằng đúng tỉ lệ giảm số lệnh** vì CPI gần như không đổi → DOT4 nhanh hơn **không** nhờ
  phép nhân nhanh hơn, mà nhờ làm 4 MAC trong một lệnh trên lõi mà mỗi lệnh tốn gần 7 chu kỳ.
- **Độ trễ DOT4 đo được: đắt hơn `ADD` đúng +1,000 chu kỳ/lệnh** (vòng DOT4 3.500.041 vs vòng ADD
  3.400.041 trên 100.000 vòng).
- **Bật PCPI tốn +0 chu kỳ**: bản vô hướng trên bitstream CÓ PCPI cho đúng 4.921.446 chu kỳ, bằng
  tuyệt đối số của F7 trên bitstream KHÔNG có PCPI.
- CSV: `results/feasibility/F8/dot4.csv`.

### Chi phí phần cứng, so với chính bản nền F5
| Thiết kế | LUT4 | ΔLUT4 | DFF | ΔDFF | MULT18X18 | Fmax | ΔFmax |
|---|---:|---:|---:|---:|---:|---:|---:|
| F5 SoC (nền, không PCPI) | 7.950 | — | 1.069 | — | 0 | 70,05 | — |
| F8 + DOT4, `MULT18X18` | 8.065 | **+115** | 1.153 | +84 | **4** | 71,89 | **+1,83** |
| F8 + DOT4, nhân bằng LUT | 9.086 | +1.136 | 1.153 | +84 | 0 | 73,83 | +3,78 |

Fmax **không giảm** ở cả hai bản (nhúc nhích lên, trong phạm vi nhiễu place & route) vì DOT4 trả lời
trong 2 chu kỳ và phép nhân int8 ngắn hơn đường tới hạn hiện có (bộ nhân 32×32 bằng LUT của lõi).

### Một lỗi đo của chính tôi, bắt được trước khi lên kit
Lần đầu viết hai vòng đo độ trễ với **toán hạng hằng số**: `dot4(0x01020304, 0x05060708)`. GCC nhấc
cả lệnh asm ra ngoài vòng lặp (asm không `volatile`, đầu vào bất biến → loop-invariant code motion),
nên hai vòng trở thành giống hệt nhau và phép đo vô nghĩa — chênh **1 chu kỳ trên 100.000 vòng**.
Phát hiện bằng cách đọc disassembly: lệnh `.insn` nằm ở `2b4`, **ngoài** thân vòng bắt đầu ở `2b8`.
Sửa: cho toán hạng phụ thuộc biến đếm (`^ i`, `+ i`) ở **cả hai** vòng, nên chúng vẫn có cùng số lệnh
chuẩn bị toán hạng. Sau khi sửa, lệnh `.insn` nằm trong thân vòng và chênh thành đúng +1,000 chu kỳ/lệnh.
**Bài học**: mọi micro-benchmark bằng inline asm phải kiểm disassembly trước khi tin số đo.

### Giới hạn của kết quả, cần nói rõ trong luận văn
3,985× là tăng tốc của **bài tích vô hướng**, không phải của cả mô hình. Bài conv1 ở F7 tốn
72,59 chu kỳ/MAC, trong đó phần chỉ số 2 chiều và requantize **không** được DOT4 cắt. Tăng tốc thật
của một lớp conv sẽ **nhỏ hơn 3,985×** và chỉ đo được ở giai đoạn thí nghiệm chính. Đây cũng là lý do
kế hoạch có thêm lệnh REQ.

### Trạng thái cuối giai đoạn khả thi
Chín cổng F0 → F8 **đã làm xong**. Kết luận: **GO CÓ ĐIỀU KIỆN**, ba điều kiện và 11 đề xuất điều chỉnh
ở `docs/FEASIBILITY_REPORT.md`. Việc duy nhất còn treo: điều kiện 4 của F6 (ba lần tắt/bật nguồn),
người thực hiện đã quyết định bỏ — báo cáo ghi rõ là "KHÔNG KIỂM", không ghi là đã đạt.

## 2026-10-17 — Cổng F7 (kernel int8 thật, đúng từng bit) — ĐẠT

Cả ba tiêu chí đều đạt: **CRC trên kit = Python** cho cả hai bài, **chu kỳ kit = Verilator bằng
tuyệt đối** (cả `cycles`, `hw_count`, `instret`), và **có số chu kỳ/MAC**. Lặp lại 3/3 lần đọc độc lập.

### Ràng buộc phải giải trước khi viết code
Kế hoạch ghi "100 cặp vector int8 dài 1.024". Lưu rời cần 100 × 2 × 1024 = **204.800 byte**, vượt RAM
64 KB tới 139.264 byte. **Sai lệch có chủ ý**: lưu một **pool 8.192 byte** int8 và lấy 100 cặp **cửa sổ**
khác offset trong pool (`off_a = (i·71) mod span`, `off_b = (i·131 + 3000) mod span`). Vẫn là 100 phép
tích vô hướng dài 1.024 trên dữ liệu khác nhau, nhưng chỉ tốn 8 KB. Chính bước 5 của F7 ("kiểm tra dung
lượng") là lý do buộc phải làm vậy.

### Dữ liệu và golden
- `scripts/gen_f7_data.py` (numpy, seed `0x5EEDF007`) sinh `f7_data.h` và in CRC32 kỳ vọng.
- Bài A: 100 × 1.024 = **102.400 MAC**; dot nhỏ/lớn = −434.947 / 403.186; **CRC32 = 64F298C2**.
- Bài B: Conv 3×3, 1→8 kênh, ảnh 28×28 int8, ra 26×26×8 (không đệm biên) = **48.672 MAC** — đúng con số
  của kế hoạch và đúng lớp conv1 của M1-S. Bias int32, **ReLU trên int32**, rồi requantize
  `(M0 int32, shift)` kiểu gemmlowp. `acc` lớn nhất sau ReLU = 31.227 → chọn `M0 = 1936565777`,
  `shift = 8` để đầu ra rơi vào **0..110** (không bão hoà, không dồn về 0). **CRC32 = 661C5304**.
- Hai hàm requantize `sat_rdhmul` (SaturatingRoundingDoublingHighMul) và `rdiv_pot`
  (RoundingDivideByPOT) được cài **y hệt** ở Python và C, nên khớp từng bit. Bản C dùng
  `(int64_t)a*(int64_t)b` → lệnh `mulh` của rv32im; CRC khớp cũng đồng thời chứng minh `mulh` đúng
  trên kit (bổ sung cho khoá `arith` của F5 chỉ kiểm `mul`/`div`/`rem`).
- CRC32 trong firmware tính **ngoài cửa sổ đo**, không tính vào số chu kỳ của kernel.

### Số đo (kit = Verilator bằng tuyệt đối, 3/3 lần)
| Bài | MAC | chu kỳ | hw_count | instret | CPI | chu kỳ/MAC | thời gian @27 MHz |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — dot int8 1024 ×100 | 102.400 | 4.921.446 | 4.921.485 | 717.812 | 6,86 | **48,06** | 182,3 ms |
| B — conv1 3×3 1→8 kênh | 48.672 | 3.533.204 | 3.533.252 | 570.232 | 6,20 | **72,59** | 130,9 ms |

CSV: `results/feasibility/F7/kernel.csv`.

**Dung lượng**: `.text` 11.296 + `.bss` 5.808 = **17.104 / 65.536 byte (26,1 %)**. Trong `.text` có
9.480 byte dữ liệu tĩnh (pool 8.192 + ảnh 784 + w 72 + bias 32 + offset 400). Còn dư 48 KB.

**Tài nguyên FPGA**: y hệt F5/F6 (RTL không đổi): BSRAM 32/46, LUT4 7.950, Fmax 70,05 MHz.

### Ước tính THÔ cho M1-S — ghi rõ là ước tính
Ngoại suy từ chu kỳ/MAC của bài B (72,59) cho 192.064 MAC: **≈ 13,94 triệu chu kỳ ≈ 516 ms @27 MHz**.
Ba lý do nó có thể lệch, đã ghi vào báo cáo: (a) MaxPool và Dense có chi phí/MAC khác conv; (b) conv2
có 16 kênh vào nên tỉ lệ nạp lại trọng số khác conv1; (c) chu kỳ/MAC của conv1 đã gồm chi phí
requantize cho 5.408 điểm đầu ra, phần này không tỉ lệ với số MAC.

### Hai nhận xét đáng ghi cho các bước sau
1. **Conv đắt hơn dot 1,51 lần trên mỗi MAC** (72,59 so với 48,06) dù cùng là nhân-cộng int8. Chênh này
   đến từ chỉ số 2 chiều, nạp lại trọng số cho từng vị trí, và requantize. **Đó chính là khoảng trống
   DOT4 ở F8 nhắm vào** — và cũng là lời cảnh báo rằng DOT4 chỉ cắt được phần nhân-cộng, không cắt
   phần chỉ số.
2. **Chênh `hw_count − cycles` ở F7 là 39 (bài A) và 48 (bài B)**, không phải 24 như F6. Không mâu thuẫn:
   F6 chứng minh chênh đó là hằng số **theo độ dài đoạn đo**; giá trị hằng số phụ thuộc chuỗi lệnh giữa
   lúc ghi `HWC_CTRL` và lúc đọc `HWC_VALUE`, mà hai bài có đoạn mã bao quanh khác nhau.
   **Kết luận thực dụng: hiệu chuẩn chênh này cho từng điểm đo, không dùng một hằng số chung.**

### Việc tiếp theo
- **F8** — lệnh tùy biến DOT4 qua PCPI. Theo F4, khối nhân phải **gọi trực tiếp `MULT18X18`** (cách PRM);
  cần giữ cả đường LUT để mô phỏng đối chiếu vì `MULT18X18` là blackbox không có mô hình mô phỏng.
  Bài A của F7 sẽ được viết lại với `dot4()` để so trực tiếp với 4.921.446 chu kỳ hiện tại.
- Không cần người dùng làm gì ở F8.

## 2026-10-17 — Cổng F6 (độ tin cậy của phép đo) — ĐANG LÀM, 4/5 bước xong

**Chưa đánh ĐẠT**: bước 4 (đo lại qua 3 lần tắt/bật nguồn kit) cần người dùng rút/cắm cáp USB,
người dùng chọn **hoãn làm sau**. Theo quy tắc 1 trong CLAUDE.md, **không sang F7** khi F6 chưa ĐẠT.

### Cách làm
- Dùng **đúng SoC của F5** (`feasibility/F5_soc/soc.v`, `top.v`), chỉ thay firmware
  (`feasibility/F6_measure/main.c`) — nên mọi kết luận vẫn áp dụng cho nền tảng đã kiểm ở F5.
- Firmware in CSV: `F6,cal,<delta>,<số lần>` cho từng giá trị overhead khác nhau;
  `F6,len,<N>,<mcycle>,<hwc>,<instret>` cho 5 độ dài; `F6,hi,...` cho bài `rdcycleh`.
- `scripts/f6_check.py` đọc kit, so với log Verilator, kiểm từng điều kiện ĐẠT và ghi
  `results/feasibility/F6/measure.csv` (cộng dồn qua các lần bật nguồn).

### Kết quả 4 điều kiện đã kiểm
1. **Overhead là hằng số**: đo `rdcycle` hai lần liên tiếp 1.000 lần → **đúng một giá trị duy nhất:
   5 chu kỳ**, xuất hiện 1000/1000 lần. Cả trên kit và trong Verilator.
2. **`hw_count − mcycle` là hằng số**: **24 chu kỳ** ở cả 5 độ dài.

   | N | mcycle | hw_count | instret | hw−mcycle |
   |---:|---:|---:|---:|---:|
   | 10 | 141 | 165 | 23 | 24 |
   | 100 | 1.401 | 1.425 | 203 | 24 |
   | 1.000 | 14.001 | 14.025 | 2.003 | 24 |
   | 10.000 | 140.001 | 140.025 | 20.003 | 24 |
   | 100.000 | 1.400.001 | 1.400.025 | 200.003 | 24 |

3. **Kit = Verilator bằng tuyệt đối** ở cả 5 độ dài, cho cả ba cột.
4. **`rdcycleh`**: `busy_loop(320.000.000)` → `rdcycleh` **0 → 1**, `rdcycle` 115.922.609 → 300.955.328.
   Tổng = 2^32 + 300.955.328 − 115.922.609 = **4.480.000.015 chu kỳ** = **165,9 s @27 MHz**.
   Mô hình 14 chu kỳ/vòng cho 4.480.000.000 → **lệch đúng 15 chu kỳ** (vào/ra vòng lặp + đọc counter).

**Mô hình chu kỳ suy ra**: `mcycle = 14·N + 1`, `instret = 2·N + 3` — đúng tuyệt đối ở cả 5 độ dài.
Mỗi vòng 2 lệnh tốn đúng 14 chu kỳ (7 chu kỳ/lệnh với bus 1 chu kỳ chờ). Đây là cơ sở để F7
ngoại suy số chu kỳ/MAC.

### Ba lỗi của chính tôi, đã sửa
1. `f6_check.py` lúc đầu **xả 1,5 s bộ đệm trước khi đọc** (cách làm đúng ở F3) nhưng ở F6 thì sai:
   khối đo đầu tiên được in ngay sau reset và nằm sẵn trong bộ đệm, nên bị xả mất; sau đó kit im
   166 s để chạy bài `rdcycleh` → không đọc được gì. Sửa: dùng `--drain 0` cho F6.
2. `parse_block` trả về cả khối **chưa đầy đủ** (chưa thấy `F6,done`) → báo thiếu độ dài 100.000.
   Sửa: chỉ trả về khối đã thấy `F6,done`.
3. Script thử cổng JTAG (`...170`) trước với timeout 12–15 s, tiêu hết cửa sổ in của kit.
   Sửa: Makefile truyền `--port /dev/cu.usbserial-20250303171` (cổng UART đã xác định ở F2).
   Thêm đích `make cycle RUN=n` (nạp lại SRAM rồi đo ngay) và `make f6check-hi`.

### Thay đổi firmware do phản hồi của người dùng
Người dùng phản hồi **"LED sáng hết chói mắt quá"**. Firmware F5/F6 trước đó bật cả 6 LED
(`LED_REG = 0x3F`) trong lúc nghỉ. Đã sửa **chính sách LED: nhiều nhất MỘT LED sáng, tắt hết khi
rảnh**, cho cả `fw/main.c` (F5) và `feasibility/F6_measure/main.c`. Đồng thời nạp ngay bitstream
F4-PRM để tắt đèn cho người dùng trong lúc sửa.
Ghi chú về F5: thay đổi này chỉ ở các lệnh ghi LED **nằm ngoài cửa sổ đo**, nên không ảnh hưởng
bất kỳ số đo nào của F5; vật phẩm đã lưu của F5 là của bản đã kiểm chứng.
Cũng vì chờ 166 s mỗi lần bật nguồn là quá lâu, firmware F6 đổi sang chạy bài `rdcycleh`
**sau 5 khối in** (`HI_AFTER=5`) thay vì sau khối đầu.

### Quyết định của người dùng (cùng ngày, sau khi đọc kết quả 4/5 bước)
Người dùng quyết định **bỏ điều kiện 4** (3 lần tắt/bật nguồn) và coi F6 là xong, rồi yêu cầu
viết tài liệu tổng kết giai đoạn khả thi.

Cách ghi nhận trong báo cáo (để trung thực): F6 ghi là **ĐẠT với 4/5 điều kiện kiểm được**, và
điều kiện 4 ghi rõ là **"KHÔNG KIỂM — bỏ theo quyết định của người thực hiện"**, chứ KHÔNG ghi là
đã kiểm và đạt. Mục 7 của `docs/FEASIBILITY_REPORT.md` nêu rủi ro còn lại, ba quan sát làm rủi ro
đó nhỏ (hơn 20 lần nạp SRAM trong F1–F6 đều cho số giống nhau; 3 lần đọc độc lập ở cả F5 và F6;
mô hình `mcycle = 14·N + 1` khớp tuyệt đối trải 4 bậc độ lớn và được xác nhận lại ở quy mô 4,48 tỷ
chu kỳ), và đề nghị chạy điều kiện 4 trước khi lấy số đo chính thức cho luận văn.

### Tài liệu đã viết
- `docs/FEASIBILITY_REPORT.md` — viết lại thành báo cáo hoàn chỉnh 8 mục, kết luận
  **GO CÓ ĐIỀU KIỆN** kèm 9 đề xuất điều chỉnh cho kế hoạch thí nghiệm chính.
- `docs/HUONG_DAN.md` — hướng dẫn dựng lại môi trường và chạy lại mọi phép đo, kèm bảng
  "những cái bẫy đã gặp".
- `README.md` — cập nhật trạng thái và ba quy tắc build bắt buộc.

### Việc tiếp theo
- F7 (kernel int8 thật) và F8 (DOT4 qua PCPI) — chưa làm.
- Nếu muốn hoàn tất điều kiện 4 của F6 về sau: rút/cắm cáp rồi
  `cd feasibility/F6_measure && make cycle RUN=2` (lặp `RUN=3`, `RUN=4`).

## 2026-10-17 — Cổng F5 (SoC PicoRV32 chạy firmware C) — ĐẠT

Tiêu chí quan trọng nhất của cổng này — **`F5,loop` trên kit bằng TUYỆT ĐỐI Verilator** — đã đạt:
**14.006 chu kỳ** cho `busy_loop(1000)`, lặp lại 3/3 lần đọc độc lập. Ngoài ra 7 khoá khác cũng
khớp tuyệt đối.

### Lõi và tham số (ghim ở env/VERSIONS.md)
- `YosysHQ/picorv32` commit **`ef203c2b0a3fb793280f5114941416c425c5b461`** (2026-09-07),
  `rtl/picorv32/picorv32.v`, sha256 `0836050971b3c6…`.
- Tham số đã **đối chiếu README của picorv32 tại chính commit đó**:
  `ENABLE_COUNTERS=1, ENABLE_COUNTERS64=1, ENABLE_REGS_16_31=1, ENABLE_REGS_DUALPORT=1,
  BARREL_SHIFTER=1, COMPRESSED_ISA=0, ENABLE_MUL=0, ENABLE_FAST_MUL=1, ENABLE_DIV=1,
  ENABLE_IRQ=0, ENABLE_PCPI=0, PROGADDR_RESET=0, STACKADDR=0x00010000`.
  README xác nhận hai điều kế hoạch đã nêu: đặt cả `ENABLE_MUL` và `ENABLE_FAST_MUL` thì
  `ENABLE_MUL` bị bỏ qua; các lõi PCPI nội bộ (mul/div) chạy không cần `ENABLE_PCPI`.

### SoC (`feasibility/F5_soc/soc.v`)
- Bản đồ bộ nhớ đúng như kế hoạch: RAM 64 KB tại 0x0000_0000; UART data 0x1000_0000,
  status 0x1000_0004 (bit0 tx_busy, bit1 rx_valid); bộ đếm phần cứng ctrl 0x1000_0010 /
  value 0x1000_0014; LED 0x1000_0020.
- RAM: `reg [31:0] ram[0:16383]` + `$readmemh`, **ghi theo byte** theo `mem_wstrb`.
  Đã kiểm trước khi viết: `share/yosys/gowin/brams.txt` khai báo `byte 9;` và `wrbe_separate;`
  nên BSRAM của Gowin hỗ trợ ghi theo byte → kết quả: **BSRAM 32/46**, không rơi xuống LUTRAM.
- Bus: mỗi truy cập **đúng 2 chu kỳ** (1 chu kỳ chờ) cho cả RAM và ngoại vi → số chu kỳ tất định,
  giống nhau giữa Verilator và kit.
- `dbg_tx_valid/dbg_tx_byte` chỉ dùng cho Verilator để in UART ra stdout ngay. **Khối `uart_tx` thật
  vẫn được dùng ở cả hai môi trường**, nên `tx_busy` diễn ra y như nhau và không làm lệch số chu kỳ.

### Firmware (`fw/`)
- `start.S` đặt `sp = 0x00010000`, xoá `.bss`, gọi `main`; `_start` nằm **đúng tại địa chỉ 0**
  (kiểm bằng `nm`: `00000000 T _start`) vì `PROGADDR_RESET = 0`.
- `link.ld`: tất cả trong RAM 64 KB, `.text.start` được `KEEP` ở đầu.
- `main.c` in các dòng CSV: `hello` (git hash nhúng lúc biên dịch), `cycle`, `loopn`, `loop`,
  `hwc`, `instret`, `arith`, `ram`, `done`.
- `busy_loop` viết bằng asm cố định (`addi` + `bnez`, đúng 2 lệnh/vòng) nên không phụ thuộc
  mức tối ưu của trình biên dịch.
- Kích thước: **`.text` = 1.220 byte**, `.bss` = 0 (log: `artifacts/firmware.size.txt`).
- `scripts/bin2hex.py`: .bin → hex từ 32 bit little-endian, đệm 0 cho đủ 16.384 từ.

### Số đo (kit = Verilator, khớp tuyệt đối 3/3 lần)
| khoá | giá trị | ý nghĩa |
|---|---|---|
| `hello` | d2a80f1 | git hash nhúng trong firmware |
| `loopn` | 1000 | số vòng của busy_loop |
| **`loop`** | **14.006** | `rdcycle` sau − trước (≈14,0 chu kỳ/vòng = 7,0 chu kỳ/lệnh với 1 chu kỳ chờ) |
| `hwc` | 14.035 | bộ đếm phần cứng cho cùng đoạn → **chênh 29 chu kỳ** so với `rdcycle` |
| `instret` | 2.004 | 2.000 lệnh của vòng lặp + 4 lệnh ngoài |
| `arith` | C91C7978 | tổng vài phép MUL/MULH/DIV/REM → **lệnh nhân/chia đúng trên kit** |
| `ram` | EFEEC031 | tổng kiểm 8 từ `.rodata` → **`$readmemh` nạp firmware đúng** |

Tài nguyên: **BSRAM 32/46** · LUT4 **7.950**/20.736 (38,3 %) · DFF 1.069 · ALU 754 ·
RAM16SDP4 32 (tệp thanh ghi) · IOB 9 · **Fmax 70,05 MHz** @ ràng buộc 27 MHz.

### Hai quyết định đáng ghi
1. **Bắt buộc `synth_gowin -nodsp` cho SoC** — hệ quả trực tiếp của F4. `ENABLE_FAST_MUL=1` tạo bộ
   nhân 32×32; nếu để yosys suy luận DSP thì lệnh `MUL` sẽ sai trên kit. Khoá `arith` khớp tuyệt đối
   chứng minh cách này đúng. Giá phải trả: LUT4 lên 7.950 (38,3 %) và Fmax 70,05 MHz (vẫn dư 2,6 lần).
   F8 vẫn dùng được DSP cho DOT4 vì đó là **gọi primitive trực tiếp**, `-nodsp` chỉ tắt phần *suy luận*.
2. UART in ra stdout trong Verilator bằng cách **bắt lệnh ghi lên bus**, không giải mã dạng sóng chân TX
   → mô phỏng nhanh mà vẫn giữ đúng thời gian của `uart_tx` thật.

### Vấn đề gặp phải
- **Verilator không biên dịch được trên máy này**: `fatal error: 'cstddef' file not found`.
  Nguyên nhân: `/Library/Developer/CommandLineTools/usr/include/c++/v1` thiếu nội dung
  (CLT 26.5.0), nên `clang++` không thấy libc++; `-isysroot` **không** cứu được vì clang chỉ tìm
  libc++ trong đường của toolchain. Thư viện vẫn có trong SDK.
  Cách khắc phục đã đưa vào `env/setup_env.sh`: tự thử biên dịch `#include <cstddef>`, nếu thất bại
  thì đặt `TN20K_CXX_INC=-I$(xcrun --show-sdk-path)/usr/include/c++/v1`; Makefile của F5 truyền cờ
  này cho verilator qua `-CFLAGS`. Các phiên sau không phải xử lý lại.
- `scripts/archive_gate.sh` ban đầu lưu cả thư mục `obj_dir` của Verilator (42 file, 3,4 MB file .o/.a).
  Đã lọc: bỏ `obj_dir/` và `*.o/*.a/*.d/*.dat`. Còn 21 file, 2,6 MB.

### Việc tiếp theo / cần người dùng
- F6 (độ tin cậy của phép đo). **Cổng này CẦN người dùng**: bước 4 của kế hoạch yêu cầu
  rút/cắm nguồn kit 3 lần rồi nạp lại SRAM, để kiểm số đo có giống hệt qua các lần bật nguồn.
  Tôi sẽ hỏi trước khi tới bước đó.
- Dữ liệu sẵn có cho F6: chênh `hwc − loop` = **29 chu kỳ** ở độ dài 1.000 vòng; F6 sẽ kiểm hằng số
  này ở các độ dài 10/100/1k/10k/100k.

## 2026-10-17 — Cổng F4 (khối nhân DSP) — ĐẠT CÓ DỰ PHÒNG

Kết luận ngắn: **phép nhân int8 có dấu do yosys tự suy luận vào DSP cho kết quả SAI trên kit này.**
Cách dùng được là **gọi trực tiếp primitive `MULT18X18` ở chế độ không dấu**. Biến thể nhân bằng
logic (`-nodsp`) cũng đúng nhưng tốn 2,2 lần LUT và Fmax thấp hơn 3,2 lần.

### Thiết kế
- Mỗi chu kỳ: hai LFSR 32 bit (cùng đa thức với F3, hạt giống 0x12345678 / 0x9ABCDEF0) sinh a, b;
  tính `dot = Σ_{i=0..3} $signed(a[8i+7:8i]) * $signed(b[8i+7:8i])`; `acc <= acc + dot` (32 bit, quấn).
  Chạy đúng 2^20 = 1.048.576 chu kỳ (≈38,8 ms @27 MHz) rồi cứ 1 giây in 8 dòng.
- `scripts/gen_f4_expect.py` tính giá trị kỳ vọng: **ACC = FEF834C3**, LFSR cuối a=BC64D7E9, b=C8B82DCC,
  dot nằm trong khoảng −52213..49098 (biên lý thuyết ±65536).
- **Bốn biến thể dùng CHUNG một `top.v`**, khác nhau bằng cờ build (nên so sánh được công bằng):
  | nhãn | cách dựng |
  |---|---|
  | DSP | `synth_gowin` (mặc định) — yosys tự ánh xạ phép nhân vào DSP |
  | D18 | như trên nhưng toán hạng mở rộng dấu lên 18 bit (`-DWIDE_MULT`) |
  | PRM | gọi trực tiếp `MULT18X18`, `ASIGN=BSIGN=0`, toán hạng mở rộng dấu 18 bit (`-DPRIM_MULT`) |
  | LUT | `synth_gowin -nodsp` — "do not infer DSP multipliers" |
- Mô phỏng Icarus chạy **đủ 2^20 chu kỳ**: `F4_SIM_PASS`, acc và cả trạng thái LFSR cuối khớp Python.

### Kết quả trên kit (cả bốn build từ cùng một top.v cuối cùng)
| Biến thể | Cách dựng | LUT4 | DFF | ALU | MULT9X9 | MULT18X18 | DUMMY | Fmax (MHz) | Trên kit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| DSP | yosys suy luận (mul2dsp → MULT9X9) | 771 | 291 | 234 | 4 | 0 | 4 | 225,28 | **SAI** |
| D18 | toán hạng 18 bit (yosys vẫn chọn MULT9X9) | 815 | 291 | 234 | 4 | 0 | 4 | 237,02 | **SAI** |
| **PRM** | **MULT18X18 trực tiếp, không dấu** | **811** | 291 | 234 | 0 | **4** | 16 | **233,64** | **ĐÚNG 3/3** |
| LUT | `-nodsp`, nhân bằng logic | 1764 | 291 | 306 | 0 | 0 | 0 | 73,08 | **ĐÚNG 3/3** |

### Chẩn đoán (trước khi sửa, theo quy tắc 3 "không bịa số")
1. Kit báo `acc = 27959EC3`, Python và Icarus đều cho `FEF834C3`. Quét Python: **không** có số chu kỳ nào
   trong 1..2^21 cho ra giá trị của kit, và **không** có cách hiểu dấu nào (có/không dấu, các kiểu cắt bit,
   mở rộng dấu ở mọi độ rộng 8..18) khớp cả bốn giá trị dot đầu — nên không phải lỗi quy ước dấu đơn giản.
2. Thêm 8 dòng chẩn đoán vào thiết kế: trạng thái LFSR cuối, 4 giá trị `dot` đầu, rồi **từng tích riêng**.
   - **LFSR cuối ĐÚNG** (a=BC64D7E9, b=C8B82DCC) → LFSR và số chu kỳ không sai.
   - **Từng tích SAI**, và **8 bit thấp của mỗi tích luôn đúng**:
     | lane | toán hạng | kỳ vọng | kit |
     |---|---|---|---|
     | P00 | 120 × −16 | −1920 (F880) | −6016 (E880) |
     | P01 | 86 × −34 | −2924 (F494) | −24428 (A094) |
     | P02 | 52 × −68 | −3536 (F230) | +23088 (5A30) |
     | P03 | 18 × −102 | −1836 (F8D4) | +7380 (1CD4) |
   - Cùng RTL đó với `-nodsp` thì **đúng** → lỗi ở đường suy luận/ánh xạ DSP, không ở RTL của tôi.

### Ba hướng sửa đã thử (quy tắc 2)
1. **Mở rộng dấu toán hạng lên 18 bit** để yosys chọn MULT18X18 → **thất bại**: `wreduce` của yosys rút
   lại toán hạng về 8 bit, report vẫn cho `MULT9X9 = 4`, kết quả sai y hệt (`27959EC3`, `D00 = 00000018`).
2. **Gọi trực tiếp primitive `MULT18X18`**, `ASIGN=BSIGN=0` (không dấu), toán hạng int8 mở rộng dấu lên
   18 bit, các tham số `AREG=BREG=OUT_REG=PIPE_REG=0` (tổ hợp) → **THÀNH CÔNG**, acc = FEF834C3, 3/3 lần.
   Lý do đúng mà không cần đường cờ dấu của DSP: với x' = x mod 2^18, y' = y mod 2^18 thì
   x'·y' ≡ x·y (mod 2^18), và |x·y| ≤ 128·128 = 16384 < 2^17, nên `DOUT[17:0]` đọc như số có dấu 18 bit
   chính là x·y. Giao diện primitive lấy từ `YosysHQ/apicula` `examples/dsp-mult18x18.v` — ví dụ mà
   Apicula tự kiểm thử trên kit thật (đích `hil-dsp-mult18x18-tangnano20k` trong examples/Makefile).
3. Hướng 3 (phương án dự phòng của kế hoạch: dùng biến thể LUT) **không cần dùng tới**, nhưng vẫn đã
   kiểm và nó đúng — giữ làm đường lùi.

### Ý nghĩa cho các cổng sau
- **F8 (DOT4 qua PCPI) nên dùng cách PRM**: tiết kiệm **953 LUT4** (811 so với 1764) và Fmax **cao hơn
  3,2 lần** (233,64 so với 73,08 MHz) so với nhân bằng logic.
- Nếu về sau có chỗ nào để yosys tự suy luận phép nhân thì **phải kiểm lại trên kit**, không tin mô phỏng:
  mô phỏng Icarus đúng trong khi phần cứng sai, vì Icarus không mô phỏng khối DSP thật.
- `MULT18X18` trong thư viện của yosys là **blackbox không có mô hình mô phỏng** → biến thể PRM chỉ kiểm
  được trên kit, không mô phỏng được. Khi dùng ở F8 cần giữ cả đường LUT để mô phỏng đối chiếu.

### Lỗi nhỏ của chính tôi, đã sửa
- `f4_check.py` dùng regex nhãn `[A-Z]{3}` nên không nhận nhãn `D18` (có chữ số) → đổi thành `[A-Z0-9]{3}`.
- Lệnh `ls -l | awk` trong Makefile bị make nuốt dấu `$` → thay bằng `wc -c`.

### Việc tiếp theo / cần người dùng
- F5 (SoC PicoRV32 chạy firmware C). Ngân sách tài nguyên sau F3/F4: BSRAM 32/46 cho RAM 64 KB,
  còn 14 khối; MULT18X18 còn 44/48. Không cần người dùng làm gì.
- Kit đang chạy biến thể LUT của F4 (bản nạp cuối cùng trong vòng kiểm).

## 2026-10-17 — Cổng F3 (BSRAM 64 KB có khởi tạo) — ĐẠT, KHÔNG cần phương án dự phòng

**Đây là rủi ro lớn nhất của cả dự án và nó đã được giải quyết.** Luồng mã nguồn mở suy luận được
64 KB BSRAM có nội dung khởi tạo, nạp được nội dung vào bitstream, và kit đọc lại đúng từng bit.

### Thiết kế
- `scripts/gen_pattern.py`: sinh `pattern.hex` = 16.384 từ 32 bit (65.536 byte) từ LFSR Fibonacci 32 bit,
  đa thức x^32+x^22+x^2+x^1+1, hạt giống **0xACE12345**. In CRC32 kỳ vọng (zlib: 0xEDB88320, init
  0xFFFFFFFF, đảo cuối) trên dòng byte **little-endian của từng từ**.
- `feasibility/F3_bsram/top.v`: `reg [31:0] mem [0:16383]` + `initial $readmemh("pattern.hex", mem)`,
  một cổng, **đọc đồng bộ 1 chu kỳ**. Máy trạng thái 3 pha chạy một lần sau khi nạp bitstream:
  (1) đọc toàn bộ → CRC32 → `crc_rom`; (2) ghi `data2(a) = a ^ 0xA5A5A5A5` vào toàn bộ;
  (3) đọc lại toàn bộ → CRC32 → `crc_rw`. Sau đó cứ 1 giây in lại hai dòng
  `F3,ROM,xxxxxxxx` và `F3,RW,xxxxxxxx` (CSV, kết thúc `\r\n`) để host bắt được bất kể lúc nào mở cổng.
- `crc32.v`: hàm CRC32 một byte, bung 8 bước thành mạng XOR tổ hợp → 1 chu kỳ/byte.
  Một lượt đọc hết 64 KB mất 6 chu kỳ/từ × 16.384 ≈ 98.304 chu kỳ ≈ 3,6 ms @27 MHz.
- UART phát: dùng lại khối **đã kiểm chứng ở F2**, đặt tại `rtl/uart/uart_tx.v` (bản sao y nguyên của
  `feasibility/F2_uart/uart_tx.v`, SHA256 giống nhau — xem `rtl/uart/README.md`). Làm vậy để F3, F5–F8
  dùng cùng một khối, tránh phân nhánh; thư mục F2 vẫn giữ bản riêng làm hồ sơ của cổng đó.

### Kết quả
- `make sim` (Icarus, **mô phỏng đủ 16.384 từ, không rút gọn**): `F3_SIM_PASS`.
  Hai dòng giải mã được: `F3,ROM,C7CD86AA` và `F3,RW,D63B5AB4`, khớp đúng CRC Python.
- Tổng hợp: **BSRAM 32/46 (69,6 %)** — đúng như kế hoạch dự đoán (~32/46). **Còn dư 14 khối (30 %)**
  cho các cổng sau. LUT4 865/20736 · DFF 207 · ALU 250 · IOB 8 (clk + TX + 6 LED) · MULT 0.
- **Fmax = 157,36 MHz** @ ràng buộc 27 MHz → ĐẠT (dư ~5,8 lần).
- Bitstream `top.fs` = 7.261.470 byte (không nén).
- **Trên kit**: `scripts/f3_check.py --repeat 3` → **F3_PASS 3/3 lần đọc độc lập**:
  `CRC_ROM=C7CD86AA`, `CRC_RW=D63B5AB4`, cả hai khớp giá trị Python tính lại tại chỗ
  (script không hard-code CRC, nó gọi lại `gen_pattern.py`).
  Log: `results/feasibility/F3/artifacts/f3_check.log`.

### Phép phản chứng (tự thêm, không có trong kế hoạch)
Vì đây là cổng quan trọng nhất, tôi kiểm thêm rằng nội dung đọc được **thật sự đến từ `pattern.hex`**
chứ không phải trùng hợp:
- Sinh lại `pattern.hex` với hạt giống **0x13572468** (CRC ROM kỳ vọng đổi thành **454701B8**,
  CRC RW kỳ vọng **giữ nguyên D63B5AB4** vì mẫu RW không phụ thuộc hạt giống), build lại, nạp lại.
- Kit báo đúng: `F3,ROM,454701B8` (đổi) và `F3,RW,D63B5AB4` (không đổi).
- ⇒ Dữ liệu khởi tạo đi đúng đường `pattern.hex → yosys → gowin_pack → bitstream → BSRAM`.
- Bằng chứng lưu ở `results/feasibility/F3/falsification/`. Sau đó đã khôi phục mẫu chuẩn
  (`sha256 pattern.hex = 86ee138c…`, đối chiếu lại bằng `cmp` với bản sinh lại) và nạp lại bitstream chuẩn.

### Vấn đề gặp phải
1. **Lỗi lệch một ô khi ghi** (bắt được khi đọc lại code trước lúc mô phỏng, chưa kịp gây hậu quả):
   ban đầu để `we`/`wdata` là thanh ghi, nên ở chu kỳ `we` có hiệu lực thì `addr` đã tăng 1 → ghi sai ô.
   Sửa: `we` và `wdata` thành **tổ hợp** theo `st` và `addr` hiện tại.
2. **Dữ liệu tồn trong bộ đệm driver khi đổi bitstream**: lần đọc đầu sau khi nạp bitstream mới vẫn trả
   về dòng của bitstream **cũ** (đã thấy cả với dòng `F2 OK ...` lẫn `F3,ROM,C7CD86AA` cũ).
   `reset_input_buffer()` của pyserial không đủ. Sửa: `f3_check.py` **đọc bỏ 1,5 s** trước khi thu
   (tham số `--drain`). Sau khi sửa: 3/3 lần đọc đạt. Ghi nhận cho các cổng sau: **mọi script đọc UART
   sau khi nạp bitstream mới phải xả bộ đệm trước.**
3. Cảnh báo của yosys: 128 cảnh báo, chỉ 4 thông điệp khác nhau, tất cả phát sinh trong file techmap
   của chính yosys (`share/yosys/gowin/brams_map.v:114`, dạng `Range select [34:27] out of bounds on
   signal PORT_A_WR_DATA`), xuất hiện 32 lần = một lần mỗi khối BSRAM. Đó là các lane bit chẵn lẻ thứ 9
   mà thiết kế 32 bit không dùng. **Không gây hậu quả**: pha RW (ghi rồi đọc lại toàn bộ 64 KB) cho CRC
   đúng từng bit, tức đường ghi 32 bit hoàn toàn nguyên vẹn.

### Nguồn đã đối chiếu
- Chân cắm: đã đối chiếu ở F1, không làm lại.
- Khả năng khởi tạo BSRAM của luồng: `YosysHQ/apicula` có sẵn các ví dụ `bsram-pROM-tangnano20k`,
  `bsram-SP-tangnano20k`, `bsram-SDPB`, `bsram-DPB` trong `examples/Makefile` (đã xem ở F1) → luồng
  được thiết kế để làm việc này. Ở đây ta dùng cách **để yosys tự suy luận** từ `$readmemh`
  (phương án chính của kế hoạch), nên không cần tới phương án dự phòng (b) là gọi primitive SP/SDPB
  trực tiếp.

### Việc tiếp theo / cần người dùng
- F4 (khối nhân DSP): hai biến thể DSP và LUT, so với giá trị Python, ghi LUT/FF/MULT/Fmax từng biến thể.
  Chip có sẵn MULT18X18 48, MULT9X9 96 (số từ report.json của F1). Không cần người dùng làm gì.
- Kit đang chạy bitstream F3 chuẩn, mỗi giây in hai dòng CRC.

## 2026-10-17 — Cổng F2 (UART hai chiều) — ĐẠT

- **Làm gì**: viết UART TX/RX 8N1 tự chia nhịp, testbench Icarus, build, nạp SRAM, kiểm 10.240 byte echo
  qua cổng serial thật. Phát sinh hai vấn đề phải chẩn đoán, cả hai đã kết luận bằng số đo.

### Thiết kế
- `uart_tx.v`: thanh ghi dịch 10 bit (start + 8 dữ liệu LSB trước + stop), bộ chia DIV chu kỳ/bit.
  Khoảng nghỉ giữa hai khung = 2 chu kỳ → chu kỳ khung 2.342 chu kỳ, **nhanh hơn** host (2.343,75) nên
  không dồn ứ.
- `uart_rx.v`: máy trạng thái IDLE→START→DATA→STOP, đồng bộ hoá chân vào 2 tầng, **kiểm lại bit start
  ở giữa bit** (chống nhiễu), kiểm bit stop; byte sai bit stop bị bỏ và đếm vào `err_cnt`.
- `top.v`: FIFO 64 byte cho echo (yosys ánh xạ thành 8× RAM16SDP4), trọng tài phát **ưu tiên echo**
  rồi mới tới dòng định kỳ.
- **Sai số baud**: DIV = round(27.000.000/115.200) = **234** → baud thực **115.384,62** (**+0,1603 %**).
  Lệch tích luỹ tới giữa bit stop = 0,0152 bit (ngưỡng an toàn 0,5 bit). Chi tiết: `artifacts/baud_calc.txt`.
- **Cửa sổ im lặng (khác kế hoạch, có chủ ý)**: dòng định kỳ chỉ phát khi đường RX im >125 ms.
  Lý do: nếu dòng thông báo chen vào giữa luồng echo thì phía PC không thể tách byte echo khỏi byte
  thông báo, phép kiểm "10.240 byte không sai byte nào" sẽ mất nghĩa. Nhờ vậy bài kiểm chia hai pha sạch.
- **Dòng định kỳ mang theo chẩn đoán** (thêm vào khi gỡ lỗi, giữ lại vì rất hữu ích):
  `F2 OK dddd rx=hhhh tx=hhhh dr=hhhh er=hh ov=h hw=hh` — số byte thu, số byte phát, số byte bị bỏ vì
  FIFO đầy, số lỗi bit stop, cờ FIFO từng tràn, mức FIFO cao nhất. Vẫn bắt đầu bằng `F2 OK ` như kế hoạch.

### Kết quả
- `make sim` (Icarus): `F2_SIM_PASS` — 3 bài: giải mã đúng dòng định kỳ; echo 300 byte liên tục không sai
  byte nào; dòng định kỳ quay lại sau khi RX im (kiểm cửa sổ QUIET).
- Tổng hợp: **Fmax 187,48 MHz** @ ràng buộc 27 MHz. LUT4 883/20736 · DFF 236/15552 · ALU 386 ·
  IOB 9/384 (clk + TX + RX + 6 LED) · **RAM16SDP4 8/648** (FIFO) · BSRAM 0. Không warning nào từ yosys/nextpnr.
- **Cổng UART của FPGA = `/dev/cu.usbserial-20250303171`** (interface B của FT2232).
  `...170` không trả dữ liệu — đó là interface A, dành cho JTAG. Quy tắc 9 (thử cả hai cổng) đã trả lời.
- `scripts/uart_check.py` — ĐẠT cả ba pha, chạy lại 2/2 lần:
  - Pha 1: nhận dòng `F2 OK 0085 rx=3C00 tx=4DB2 dr=0000 er=00 ov=0 hw=01` sau 0,20 s.
  - Pha 2: **10.240 byte echo khớp 100 %, 0 byte sai**, khối 64 byte, 1,951 s → 5.248 byte/s
    (≈52.485 bit/s; thấp hơn trần 115.200 bit/s vì theo nhịp gửi-rồi-chờ-echo từng khối).
  - Pha 3: bộ đếm trong FPGA **rx tăng đúng 10.240**, `dr=0`, `er=0`, `ov=0`, FIFO cao nhất **1/63**.
  - Log: `results/feasibility/F2/artifacts/uart_check.log` và `uart_check_sweep.log`.

### Vấn đề 1 — bitstream nén không nạp được
- Triệu chứng: `openFPGALoader -b tangnano20k build/top.fs` → `FsParser: checksum data is truncated`,
  `Error: Failed to claim FPGA device: can't parse file`.
- Đã thử: (a) sinh lại file nén hai lần → cùng kích thước 1.130.734 byte, cùng lỗi (tái lập 2/2);
  (b) sinh bản **không nén** (`gowin_pack -d GW2A-18C` không có `-c`) → 4.618.782 byte, **nạp bình thường**.
- Kết luận: `gowin_pack -c` của apycula 0.35.dev5 sinh file mà openFPGALoader v1.1.1 không parse được cho
  thiết kế này (F1 nén lại nạp được → lỗi phụ thuộc thiết kế). **Đã bỏ `-c` khỏi Makefile của mọi cổng.**
- Hệ quả: bitstream F1 cũng được build lại không nén và nạp SRAM 3/3 lần OK
  (`results/feasibility/F1/load_3times_uncompressed.txt`); cùng `pnr.json` với bản nén mà người dùng
  đã xác nhận LED chạy đúng.

### Vấn đề 2 — mất byte khi host ghi khối lớn (lỗi NGOÀI FPGA)
- Triệu chứng ban đầu: với khối 256 byte, echo sai từ offset 32; 10.240 byte chỉ về 833.
- Chẩn đoán (3 hướng, theo quy tắc 2):
  1. **Thêm bộ đếm vào FPGA** rồi đo: FPGA báo `rx` tăng ĐÚNG số byte đã gửi (67/128/256/1024/10240),
     `dr=0` (không bỏ byte vì FIFO đầy), `er=0` (không lỗi bit stop), `ov=0`, mức FIFO cao nhất **1**.
     Với n=67: `tx` tăng 120 = 67 byte echo + 53 byte một dòng thông báo → **FPGA phát đủ cả 67 byte**.
     Kiểm tra nội dung: chỉ thiếu đúng byte thứ 33, các byte khác đúng thứ tự → mất byte, không sai khung.
     ⇒ Lỗi nằm ở cầu USB/driver, không phải ở FPGA.
  2. **Luồng đọc riêng trên host** (ghi 10.240 byte một lần, thread khác đọc liên tục):
     host chỉ nhận 1.151/10.240 → **không cứu được**, nên nguyên nhân không phải host đọc chậm.
  3. **Chia khối ghi**: quét 16/32/64/65/66/67/68/96/128/256 byte →
     **≤66 byte nguyên vẹn, ≥67 byte mất byte**. Với khối 64: 10.240 byte, 0 sai.
- Kết luận: giới hạn của cầu FT2232 + driver macOS khi host `write()` vượt một gói USB (64 byte).
  Luồng đo chốt ở **khối 64 byte**.
- **Ảnh hưởng tới các cổng sau**: kênh thu số đo của dự án là FPGA→PC (dòng CSV) — không bị ảnh hưởng.
  Mọi script gửi dữ liệu PC→FPGA phải chia khối ≤64 byte. Cần ghi nhận: bài kiểm hiện tại chạy theo
  nhịp gửi-chờ nên chỉ đạt ~53 kbit/s; **chưa đo thông lượng FPGA→PC liên tục ở full baud** — việc này
  sẽ tự nhiên được kiểm ở F5–F7 khi firmware in dòng log dài.

### Lỗi của chính tôi, đã sửa
- Lần đầu đặt mốc bộ đếm `rx` cho pha 3 **trước** phần quét ngưỡng, nên pha 3 báo "rx tăng 15360,
  kỳ vọng 10240" (đúng = 10.240 + 5.120 byte của phần quét). Đã sửa: lấy lại mốc ngay trước pha 2.
- `msg_req` ban đầu bị hai `always` block cùng ghi (xung đột driver) → tách thành xung `msg_tick`
  ở block hẹn giờ, còn `msg_req` thuộc block trọng tài.

### Nguồn đã đối chiếu
- Chân cắm: đã đối chiếu ở F1 (`uart_tx`=69, `uart_rx`=70 khớp giữa `uart/src/top.cst` của Sipeed và
  `examples/tangnano20k.cst` của Apicula). Không đối chiếu lại.
- `gowin_pack -h` cho ý nghĩa `-c, --compress`.

### Việc tiếp theo / cần người dùng
- Kit hiện đang chạy lại **F1 blinky** (bản không nén). Nếu anh nhìn thấy 6 LED vẫn đếm nhị phân như cũ
  thì bản không nén cũng đã được xác nhận bằng mắt — chỉ cần nói "LED vẫn chạy", không phải làm gì thêm.
- F3 (BSRAM 64 KB có khởi tạo) — đây là **rủi ro lớn nhất** của cả dự án. Không cần người dùng làm gì
  ngoài giữ kit cắm nguyên.

## 2026-10-17 — Cổng F1 (Blinky bằng luồng mã nguồn mở) — ĐẠT
- **Làm gì**: đối chiếu chân cắm với nguồn chính thức, viết `hw/tangnano20k.cst` và
  `feasibility/F1_blinky/` (top.v, tb_top.v, Makefile), mô phỏng, build, nạp SRAM, nhờ người dùng xem LED.
- **Nguồn đã đối chiếu** (quy tắc 6, làm TRƯỚC lần build đầu):
  - `sipeed/TangNano-20K-example` @ main: `led/blink_leds/src/blink_leds.cst` (clk=4, leds[0..5]=15..20),
    `uart/src/top.cst` (uart_tx=69, uart_rx=70, rst=88), `hdmi/src/hdmi.cst` (I_key=87, I_rst=88),
    `picorv32/src/fpga_project.cst` (ser_tx=69, resetn=88, Part Number GW2AR-LV18QN88C8/I7).
  - `YosysHQ/apicula` @ master, `examples/tangnano20k.cst`: clk=4 + `CLOCK_LOC "clk" BUFG`,
    led[0..5]=15..20, key_i=87, rst_i=88, TXD=69, RXD=70.
  - **Hai nguồn khớp nhau trên mọi chân dự án cần** → mọi giá trị "phải xác minh" trong FEASIBILITY_PLAN
    đều đúng: clock 27 MHz chân 4; LED0–LED5 chân 15–20; UART TX 69 / RX 70; S1 88 / S2 87; LVCMOS33.
  - LED **tích cực mức thấp**: xác nhận bằng `led/blink_leds/src/blink_leds.v` của Sipeed —
    dòng cuối là `assign leds = ~leds_value;`.
  - `YosysHQ/apicula` @ master, `examples/Makefile` — tham số luồng:
    `synth_gowin -json $@ -family gw2a -setundef`;
    `nextpnr-himbaechel --json $< --write $@ --device GW2AR-LV18QN88C8/I7 --vopt family=GW2A-18C --vopt cst=...`;
    `gowin_pack -c -d GW2A-18C -o $@ $<`.
- **Hai khác biệt so với Makefile phác trong kế hoạch** (đều lấy từ nguồn chính thức, không đoán):
  1. **`synth_gowin -family gw2a` là BẮT BUỘC** — `help synth_gowin` nói mặc định là `gw1n`.
     Thiếu cờ này thì tổng hợp cho sai họ chip.
  2. `gowin_pack -c` (`--compress`) — dùng theo examples/Makefile của Apicula (đó cũng là tham số
     họ chạy trong các bài kiểm thử trên kit thật). Không bắt buộc, nhưng theo nguồn cho chắc.
  Cố ý **không** dùng `--timing-allow-fail` (Apicula đặt mặc định cờ này) vì dự án cần biết timing
  thật có đạt 27 MHz hay không.
- **Thiết kế**: bộ đếm nhị phân 6 bit, tăng mỗi `TICK_DIV = 13_500_000` chu kỳ = 0,5 s @27 MHz
  → LED0 nháy 1 Hz, LED5 đổi mỗi 16 s, một vòng 32 s. `assign led = ~cnt` (tích cực mức thấp).
- **Kết quả / output quan trọng**:
  - `make sim` (Icarus 14.0): `F1_SIM_PASS: bo dem 6 bit tang dung nhip, dau ra LED dao dung`
    (testbench chạy 70 lần tăng, quá một vòng 64, với TICK_DIV=10).
  - `make build`: yosys + nextpnr + gowin_pack chạy sạch, **không có warning/error** trong nextpnr.log.
  - **Fmax = 347,58 MHz** cho `clk_IBUF_I_O`, ràng buộc 27 MHz → PASS (dư ~12,9 lần).
  - Tài nguyên: LUT4 30/20736 · DFF 30/15552 · ALU 34/15552 · MUX2_LUT5 2 · IOB **7**/384
    (6 LED + 1 clk, đúng số chân mong đợi) · BUFG 1/24 · BSRAM 0/46.
  - Bitstream `build/top.fs` = **730.982 byte**.
  - Ràng buộc chân có hiệu lực: trong `pnr.json` cả 7 IOB và BUFG đều có
    `BEL_STRENGTH = 5` (STRENGTH_LOCKED), tức nextpnr đã khóa vị trí theo .cst chứ không tự đặt.
  - `make load` → `openFPGALoader -b tangnano20k build/top.fs` (KHÔNG có `-f`, chỉ SRAM):
    **3/3 lần đều thành công**, mỗi lần kết thúc bằng `DONE`, exit=0
    (log: `results/feasibility/F1/load_3times.txt`).
  - **Người dùng xác nhận**: LED chạy đúng pattern và đúng tốc độ (bộ đếm nhị phân, LED0 ~1 Hz).
- **Số liệu phụ thu được cho các cổng sau** (từ report.json, hữu ích để lập ngân sách tài nguyên):
  chip có **BSRAM 46** khối, **MULT18X18 48**, MULT9X9 96, MULT36X36 12, MULTALU18X18 24,
  MULTADDALU18X18 24, ALU54D 24, LUT4 20.736, DFF 15.552, rPLL 2, RAM16SDP4 648.
  → F3 kỳ vọng dùng ~32/46 BSRAM là hợp lý; F4 có sẵn khối nhân để ánh xạ.
- **Vấn đề, đã thử**: chỉ một lỗi nhỏ của riêng tôi: Makefile ban đầu đặt đích `.PHONY: build` trùng tên
  thư mục `build/` → make báo "Circular build/top-synth.json <- build dependency dropped". Sửa bằng cách
  bỏ rule tạo thư mục và dùng `mkdir -p` trong từng recipe. Không liên quan tới phần cứng hay luồng công cụ.
- **Việc tiếp theo / cần người dùng**:
  - F2 (UART hai chiều): viết UART TX/RX 115200 8N1, mô phỏng, nạp, rồi chạy `scripts/uart_check.py`
    (10.240 byte echo). Chưa biết trong hai cổng `cu.usbserial-2025030317{0,1}` cổng nào là UART của FPGA —
    script sẽ thử cả hai, như quy tắc 9.
  - Không cần người dùng làm gì ở F2 ngoài việc giữ kit cắm nguyên.
- **Bổ sung sau F2**: bitstream của F1 đã được build lại **không nén** (xem mục F2, vấn đề 1) và
  nạp SRAM 3/3 lần OK; số byte bitstream trong báo cáo đổi từ 730.982 (nén) sang 4.618.782 (không nén).

## 2026-10-17 — Cổng F0 (Môi trường trên Mac) — ĐẠT
- **Làm gì**: dựng toàn bộ môi trường công cụ mã nguồn mở trên máy Mac, `git init`, xác nhận kit được nhận.
- **Máy**: `uname -m` = x86_64 (Intel), macOS 26.6.2 build 25G83 → tải bản **darwin-x64** (không phải arm64).
- **Kết quả / lệnh / output quan trọng**:
  - OSS CAD Suite `2026-10-16` (`oss-cad-suite-darwin-x64-20261016.tgz`) → `~/tools/oss-cad-suite`.
    Gỡ quarantine bằng `./activate` theo README của gói ("Removing quarantine flag from all files and directories... Done").
  - Phiên bản (log: `results/feasibility/F0/tool_versions.txt`): yosys 0.70+145 (a31d95ea0) ·
    nextpnr-himbaechel 0.11.1-63-g44a6c739 · openFPGALoader v1.1.1 · verilator 5.053 devel · iverilog 14.0 devel ·
    `gowin_pack` có sẵn trong gói (apycula 0.35.dev5+g2db53c01c) → **không cần** `pip install apycula`.
  - `nextpnr-himbaechel --list-uarch` → `gatemate, gowin`. Với `--device GW2AR-LV18QN88C8/I7` nó in
    "Using uarch 'gowin' for device 'GW2AR-LV18QN88C8/I7'" → **chuỗi device trong kế hoạch là đúng**.
    `--vopt help` liệt kê `family=`, `cst=`, `ireg_in_iob`, ... đúng như Makefile dự kiến ở F1.
    Có `share/nextpnr/himbaechel/gowin/chipdb-GW2A-18C.bin` → family `GW2A-18C` dùng được.
    (Log: `results/feasibility/F0/uarch_and_synth.txt`, gồm cả `yosys -p 'help synth_gowin'`.)
  - `yosys help synth_gowin`: **CÓ** tùy chọn `-family <gw1n|gw2a|gw5a>`, **mặc định là `gw1n`**.
    (Ghi chú sửa lỗi: trong lần ghi đầu tiên của mục F0 tôi kết luận sai là "không có tùy chọn họ chip"
    vì đã đọc thiếu phần cuối của `help synth_gowin`. Đã kiểm lại: tùy chọn tồn tại và **bắt buộc**
    phải truyền `-family gw2a` cho GW2AR-18, đúng như examples/Makefile của Apicula.)
  - riscv-none-elf-gcc **15.2.0** (xPack v15.2.0-1, darwin-x64) → `~/tools/xpack-riscv-none-elf-gcc-15.2.0-1`.
    Biên dịch thử `-march=rv32im -mabi=ilp32 -O2`: sinh đúng `mul a0,a0,a1` → nhánh M hoạt động
    (log: `results/feasibility/F0/gcc_test.txt`).
  - `.venv` (python 3.14.7) + numpy 2.5.4 + pyserial 3.5.
  - `env/setup_env.sh`: export PATH cho 3 bộ công cụ + biến dùng chung `TN20K_DEVICE/FAMILY/BOARD/FREQ/CST`.
  - **Kit được nhận**: `openFPGALoader --detect -b tangnano20k` → `idcode 0x81b`, Gowin, family GW2A,
    model **GW2A(R)-18(C)**, irlength 8. `--scan-usb` → `0403:6010 FTDI2232 SIPEED "USB Debugger" serial 2025030317`.
    (Log: `results/feasibility/F0/openfpgaloader_detect.txt`.)
  - **Cổng serial**: `/dev/cu.usbserial-20250303170` và `/dev/cu.usbserial-20250303171` (cùng VID:PID 0403:6010,
    hai interface của FT2232). Cả hai mở được @115200, chưa có dữ liệu (đúng, vì FPGA chưa có bitstream).
    (Log: `results/feasibility/F0/serial_ports.txt`.)
  - `git init` xong, `.gitignore` loại `.venv/`, `build/`, `obj_dir/`, `*.fs`, tarball công cụ.
- **Nguồn đã đối chiếu**:
  - README trong gói OSS CAD Suite (`~/tools/oss-cad-suite/README`) — cách gỡ quarantine trên macOS bằng `./activate`.
  - `nextpnr-himbaechel --help`, `--list-uarch`, `--vopt help` (nguồn chính thức của công cụ, thay cho đoán tham số).
  - `yosys -p 'help synth_gowin'`.
  - Chưa đối chiếu chân cắm với repo ví dụ của Sipeed, và chưa đối chiếu Makefile với `examples/himbaechel/`
    của Apicula — **việc này thuộc F1, làm trước lần build đầu** (quy tắc 6 trong CLAUDE.md).
- **Vấn đề, đã thử**: không có lỗi nào phải xử lý. Ghi nhận khác biệt so với kế hoạch:
  máy là **Intel x86_64**, không phải arm64; `gowin_pack` đã có trong gói nên bỏ bước `pip install apycula`.
  Phần cứng USB báo FTDI FT2232 (`0403:6010`) chứ không phải BL616 như CLAUDE.md ghi — không ảnh hưởng,
  JTAG và UART vẫn hiện thành hai cổng `cu.usbserial-*` như mong đợi.
- **Việc tiếp theo / cần người dùng**:
  - F1 (Blinky): đối chiếu `.cst` với ví dụ chính thức của Sipeed, build bằng yosys/nextpnr/gowin_pack,
    nạp SRAM, rồi **cần người dùng xác nhận LED có chạy và chạy đúng tốc độ**.
  - Kit đang cắm và nhận được — giữ nguyên dây/cổng USB này.
