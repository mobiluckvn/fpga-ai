# Người làm

- **Vũ Trí Công**
- **TS. Nguyễn Trung Hiếu**

## Nguồn ngoài dùng trong công việc này

| Nguồn | Giấy phép / chỗ lấy |
|---|---|
| `picorv32` (lõi RISC-V có sẵn, dùng làm mốc so sánh) | YosysHQ/picorv32, bản `ef203c2b` — xem `env/VERSIONS.md` |
| `riscv-tests` (bộ bài thử tập lệnh) | riscv-software-src/riscv-tests, bản `d7e86f70` |
| Môi trường chạy bài thử rút gọn (`riscv_test.h`) | lấy từ `picorv32/tests` cùng bản ghim ở trên |
| MNIST (bộ ảnh chữ số viết tay) | dấu SHA256 của từng file ghi trong `env/VERSIONS.md` |
| `yosys`, `nextpnr-himbaechel`, `apicula`, `openFPGALoader`, `verilator` | bản ghim trong `env/VERSIONS.md` |

Mọi phần còn lại — lõi RISC-V tự dựng (`rtl/mycore/`), hai lệnh tự thêm (`rtl/ext/`), mạch quanh lõi,
phần mềm chạy mạng, bản Python đối chiếu, và toàn bộ chương trình đo — do nhóm viết.
