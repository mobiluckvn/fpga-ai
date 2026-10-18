# Hồ sơ hiệu năng của `kernels.c` hiện tại

Mọi số dưới đây do một bộ mô phỏng tập lệnh đếm trực tiếp khi chạy đúng firmware
này trên lõi đích, 10 ảnh đầu vào. Không có số nào là ước lượng.

**Tổng: 954.673 chu kỳ cho một ảnh.** Mô hình có 192.064 phép nhân-cộng (MAC) cho một ảnh.

## Lõi đích: số chu kỳ mỗi lệnh

| lớp lệnh | chu kỳ |
|---|---:|
| alu | 1 |
| shift | 1 |
| branch_taken | 1 |
| branch_nt | 1 |
| jal | 1 |
| jalr | 1 |
| load | 2 |
| store | 2 |
| mul | 2 |
| div | 34 |

Lõi phát **một lệnh mỗi chu kỳ**, không đoán nhánh (nhảy hay không nhảy đều
bằng giá), không có cache. Bộ nhớ **một cổng**: mỗi lần truy cập dữ liệu chiếm
cổng nên load/store tốn 2 chu kỳ, và băng thông tối đa là
4/2 = 2 byte/chu kỳ.
Có 31 thanh ghi dùng được (x1–x31).

## Chu kỳ theo lớp mạng và theo loại công việc

| lớp mạng | chu kỳ | MAC | byte dữ liệu | byte/MAC | mac | load_data | store_data | addr | loop_ctrl | requant | other |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conv1 | 361.394 | 48.672 | 129.248 | 2.66 | 47.1 | 27.1 | 3.1 | 0.8 | 0.8 | 21.0 | 0.0 |
| pool1 | 42.472 | — | 6.800 | — | 0.0 | 25.5 | 6.4 | 10.4 | 23.6 | 0.0 | 34.1 |
| conv2 | 498.152 | 139.392 | 106.084 | 0.76 | 47.4 | 39.2 | 0.9 | 1.3 | 1.0 | 6.4 | 3.8 |
| pool2 | 12.519 | — | 2.032 | — | 0.0 | 25.7 | 6.5 | 10.0 | 23.2 | 0.0 | 34.7 |
| dense | 40.114 | 4.000 | 8.080 | 2.02 | 29.9 | 39.9 | 0.0 | 20.0 | 10.0 | 0.0 | 0.0 |

Nghĩa của các loại công việc: `mac` phép nhân và phép cộng dồn ngay sau nó · 
`load_data`/`store_data` truy cập dữ liệu · `addr` lệnh tính địa chỉ cho truy cập ·
`loop_ctrl` lệnh điều khiển vòng lặp · `requant` chuỗi lượng tử hoá lại ·
`other` còn lại.

## Các vòng lặp nóng nhất

**conv1**

| số vòng | chu kỳ/vòng | lệnh/vòng | thanh ghi dùng | **còn trống** | mang theo vòng | chuỗi phụ thuộc bắt buộc | phụ thuộc qua bộ nhớ nội vòng | nạp liên tục 1 byte |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 26.000 | 138.32 | 94.6 | 28 | **3** | x13,x17 | 1 | 0 | 43.3 % |
| 1.000 | 3609.84 | 2470.0 | 28 | **3** | x15,x29 | 3 | 0 | 43.3 % |

**pool1**

| số vòng | chu kỳ/vòng | lệnh/vòng | thanh ghi dùng | **còn trống** | mang theo vòng | chuỗi phụ thuộc bắt buộc | phụ thuộc qua bộ nhớ nội vòng | nạp liên tục 1 byte |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 11.830 | 34.61 | 28.9 | 10 | **21** | x12,x13 | 1 | 0 | 90.0 % |
| 1.560 | 271.11 | 227.8 | 14 | **17** | x6,x16,x17,x28,x29 | 3 | 0 | 90.0 % |

**conv2**

| số vòng | chu kỳ/vòng | lệnh/vòng | thanh ghi dùng | **còn trống** | mang theo vòng | chuỗi phụ thuộc bắt buộc | phụ thuộc qua bộ nhớ nội vòng | nạp liên tục 1 byte |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 14.520 | 301.23 | 184.9 | 15 | **16** | x5,x6,x10,x11,x12,x15,x16,x17,x28,x29 | 10 | 0 | 0.0 % |
| 4.840 | 911.2 | 562.3 | 18 | **13** | x5,x6,x10,x11,x16,x17,x20,x22,x28,x29 | 11 | 0 | 0.0 % |

**pool2**

| số vòng | chu kỳ/vòng | lệnh/vòng | thanh ghi dùng | **còn trống** | mang theo vòng | chuỗi phụ thuộc bắt buộc | phụ thuộc qua bộ nhớ nội vòng | nạp liên tục 1 byte |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 3.750 | 32.66 | 27.3 | 10 | **21** | x12,x13 | 1 | 0 | 95.0 % |
| 200 | 621.2 | 521.2 | 13 | **18** | x6,x16,x17,x28 | 1 | 0 | 95.0 % |

**dense**

| số vòng | chu kỳ/vòng | lệnh/vòng | thanh ghi dùng | **còn trống** | mang theo vòng | chuỗi phụ thuộc bắt buộc | phụ thuộc qua bộ nhớ nội vòng | nạp liên tục 1 byte |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 39.900 | 10.03 | 7.0 | 6 | **25** | x12,x13,x15 | 5 | 0 | 99.9 % |
| 90 | 4455.56 | 3120.0 | 11 | **20** | x6,x16,x17 | 1 | 0 | 99.6 % |

Cột **còn trống** là số thanh ghi chưa dùng trong thân vòng đó: nếu nhỏ thì thêm
biến tạm sẽ làm trình biên dịch phải tràn thanh ghi ra bộ nhớ và mất lợi ích.
`phụ thuộc qua bộ nhớ nội vòng` = 0 nghĩa là không có lệnh nạp nào trong vòng đọc
ô mà một lệnh lưu trong cùng vòng vừa ghi.

