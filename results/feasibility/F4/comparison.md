| Biến thể | Cách dựng phép nhân | LUT4 | DFF | ALU | MULT9X9 | MULT18X18 | DUMMY | Fmax (MHz) | Kết quả trên kit |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| DSP | yosys tự suy luận (mul2dsp -> MULT9X9) | 771 | 291 | 234 | 4 | 0 | 4 | 225.28 | **SAI** |
| D18 | toán hạng mở rộng dấu 18 bit (yosys vẫn chọn MULT9X9) | 815 | 291 | 234 | 4 | 0 | 4 | 237.02 | **SAI** |
| PRM | gọi trực tiếp MULT18X18, chế độ không dấu | 811 | 291 | 234 | 0 | 4 | 16 | 233.64 | **ĐÚNG** (3/3 lần đọc) |
| LUT | synth_gowin -nodsp, nhân bằng logic | 1764 | 291 | 306 | 0 | 0 | 0 | 73.08 | **ĐÚNG** (3/3 lần đọc) |
