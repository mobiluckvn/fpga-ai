// CRC32 chuẩn (như zlib.crc32): đa thức phản chiếu 0xEDB88320, khởi tạo 0xFFFFFFFF,
// đảo bit ở bước kết thúc. Hàm xử lý MỘT byte, bit thấp trước — bung 8 bước thành
// mạng XOR tổ hợp nên chỉ tốn 1 chu kỳ mỗi byte.
//
// Dùng:  crc_next = crc32_byte(crc_cur, data_byte);
//        crc_final = crc_cur ^ 32'hFFFFFFFF;

`ifndef CRC32_VH
`define CRC32_VH

function automatic [31:0] crc32_byte;
    input [31:0] crc_in;
    input [7:0]  data;
    reg   [31:0] c;
    integer      i;
    begin
        c = crc_in ^ {24'd0, data};
        for (i = 0; i < 8; i = i + 1) begin
            c = c[0] ? ((c >> 1) ^ 32'hEDB88320) : (c >> 1);
        end
        crc32_byte = c;
    end
endfunction

`endif
