// F3 — BSRAM 64 KB có khởi tạo sẵn nội dung.
//
// Đây là rủi ro lớn nhất của dự án: luồng mã nguồn mở có xếp được 64 KB BSRAM và
// có nạp được nội dung khởi tạo vào bitstream hay không.
//
// Trình tự chạy một lần sau khi nạp bitstream:
//   1. Đọc toàn bộ 16.384 từ 32 bit, tính CRC32 (byte little-endian) -> crc_rom
//   2. Ghi mẫu thứ hai data2(a) = (a ^ 0xA5A5A5A5) vào toàn bộ
//   3. Đọc lại toàn bộ, tính CRC32 -> crc_rw
//   4. Sau đó cứ 1 giây in lại hai dòng (để host bắt được bất kể thời điểm mở cổng):
//        F3,ROM,xxxxxxxx
//        F3,RW,xxxxxxxx
//      Dòng kết thúc bằng \r\n, dạng CSV như quy ước trong CLAUDE.md.
//
// LED (tích cực mức thấp): led[0] nhịp tim; led[1] xong pha ROM; led[2] xong pha RW;
//   led[5] sáng giữ nếu CRC không khớp hằng số kỳ vọng nạp sẵn (chỉ để nhìn nhanh,
//   kết luận chính thức do script trên PC so sánh).

`include "crc32.v"

module top #(
    parameter integer DIV      = 234,          // 27e6/115200
    parameter integer AW       = 14,           // 2^14 từ = 16384 từ = 64 KB
    parameter         HEXFILE  = "pattern.hex",
    parameter integer MSG_DIV  = 27_000_000,   // 1 s
    parameter integer HB_DIV   = 13_500_000,
    parameter [31:0]  CRC_ROM_EXPECT = 32'hC7CD86AA,
    parameter [31:0]  CRC_RW_EXPECT  = 32'hD63B5AB4
) (
    input  wire       clk,
    output wire       uart_tx,
    output wire [5:0] led
);
    localparam integer WORDS = (1 << AW);
    localparam [31:0]  MASK2 = 32'hA5A5A5A5;

    // ---------------- mã trạng thái (khai báo sớm vì khối bộ nhớ dùng S_WR) ----------------
    localparam [3:0] S_RD_REQ   = 4'd0,   // phát địa chỉ đọc
                     S_RD_WAIT  = 4'd1,   // chờ 1 chu kỳ cho đọc đồng bộ
                     S_CRC      = 4'd2,   // nạp 4 byte vào CRC
                     S_RD_NEXT  = 4'd3,
                     S_WR       = 4'd4,   // ghi mẫu thứ hai
                     S_PH_DONE  = 4'd5,
                     S_IDLE     = 4'd6,
                     S_SEND     = 4'd7;

    reg [3:0] st = S_RD_REQ;

    // ---------------- BSRAM 64 KB, một cổng, đọc đồng bộ ----------------
    reg [31:0] mem [0:WORDS-1];
    initial begin
        $readmemh(HEXFILE, mem);
    end

    reg [AW-1:0] addr  = {AW{1'b0}};
    reg [31:0]   rdata = 32'd0;

    // we/wdata là TỔ HỢP theo trạng thái và địa chỉ hiện tại. Nếu dùng thanh ghi thì ở
    // chu kỳ we có hiệu lực, addr đã tăng lên 1 -> ghi lệch một ô.
    wire         we    = (st == S_WR);
    wire [31:0]  wdata = {{(32-AW){1'b0}}, addr} ^ MASK2;

    always @(posedge clk) begin
        if (we) mem[addr] <= wdata;
        rdata <= mem[addr];
    end

    // ---------------- UART phát ----------------
    reg  [7:0] tx_byte  = 8'd0;
    reg        tx_start = 1'b0;
    wire       tx_busy;

    uart_tx #(.DIV(DIV)) u_tx (
        .clk(clk), .data(tx_byte), .start(tx_start),
        .busy(tx_busy), .tx(uart_tx)
    );

    reg [1:0]  bytei = 2'd0;
    reg [31:0] crc   = 32'hFFFFFFFF;
    reg [31:0] crc_rom = 32'd0;
    reg [31:0] crc_rw  = 32'd0;
    reg [1:0]  phase = 2'd0;     // 0 = đọc ROM, 1 = ghi RW, 2 = đọc lại RW, 3 = xong
    reg        rom_done = 1'b0;
    reg        rw_done  = 1'b0;

    wire [7:0] crc_in_byte = (bytei == 2'd0) ? rdata[7:0]   :
                             (bytei == 2'd1) ? rdata[15:8]  :
                             (bytei == 2'd2) ? rdata[23:16] : rdata[31:24];

    // ---------------- khuôn dòng ra ----------------
    // "F3,ROM,xxxxxxxx\r\n" = 17 byte ; "F3,RW,xxxxxxxx\r\n" = 16 byte
    localparam integer LINELEN = 17;
    reg [4:0]  msg_idx  = 5'd0;
    reg        line_sel = 1'b0;   // 0 = dòng ROM, 1 = dòng RW
    reg        sending  = 1'b0;

    function [7:0] hexdig;
        input [3:0] v;
        begin
            hexdig = (v < 4'd10) ? (8'h30 + v) : (8'h41 + v - 4'd10);
        end
    endfunction

    function [7:0] nib;        // chữ số hex thứ i (0 = cao nhất) của một từ 32 bit
        input [31:0] w;
        input [2:0]  i;
        begin
            case (i)
                3'd0: nib = hexdig(w[31:28]);
                3'd1: nib = hexdig(w[27:24]);
                3'd2: nib = hexdig(w[23:20]);
                3'd3: nib = hexdig(w[19:16]);
                3'd4: nib = hexdig(w[15:12]);
                3'd5: nib = hexdig(w[11:8]);
                3'd6: nib = hexdig(w[7:4]);
                default: nib = hexdig(w[3:0]);
            endcase
        end
    endfunction

    function [7:0] line_char;
        input       sel;        // 0 = ROM, 1 = RW
        input [4:0] i;
        begin
            if (sel == 1'b0) begin
                case (i)                       // F3,ROM,xxxxxxxx\r\n
                    5'd0:  line_char = "F";
                    5'd1:  line_char = "3";
                    5'd2:  line_char = ",";
                    5'd3:  line_char = "R";
                    5'd4:  line_char = "O";
                    5'd5:  line_char = "M";
                    5'd6:  line_char = ",";
                    5'd7:  line_char = nib(crc_rom, 3'd0);
                    5'd8:  line_char = nib(crc_rom, 3'd1);
                    5'd9:  line_char = nib(crc_rom, 3'd2);
                    5'd10: line_char = nib(crc_rom, 3'd3);
                    5'd11: line_char = nib(crc_rom, 3'd4);
                    5'd12: line_char = nib(crc_rom, 3'd5);
                    5'd13: line_char = nib(crc_rom, 3'd6);
                    5'd14: line_char = nib(crc_rom, 3'd7);
                    5'd15: line_char = 8'h0D;
                    default: line_char = 8'h0A;
                endcase
            end else begin
                case (i)                       // F3,RW,xxxxxxxx\r\n  (16 byte, chèn 0 ở cuối)
                    5'd0:  line_char = "F";
                    5'd1:  line_char = "3";
                    5'd2:  line_char = ",";
                    5'd3:  line_char = "R";
                    5'd4:  line_char = "W";
                    5'd5:  line_char = ",";
                    5'd6:  line_char = nib(crc_rw, 3'd0);
                    5'd7:  line_char = nib(crc_rw, 3'd1);
                    5'd8:  line_char = nib(crc_rw, 3'd2);
                    5'd9:  line_char = nib(crc_rw, 3'd3);
                    5'd10: line_char = nib(crc_rw, 3'd4);
                    5'd11: line_char = nib(crc_rw, 3'd5);
                    5'd12: line_char = nib(crc_rw, 3'd6);
                    5'd13: line_char = nib(crc_rw, 3'd7);
                    5'd14: line_char = 8'h0D;
                    default: line_char = 8'h0A;
                endcase
            end
        end
    endfunction

    // dòng RW ngắn hơn 1 byte: bỏ byte cuối khi sel=1
    wire [4:0] line_last = line_sel ? 5'd15 : 5'd16;

    // ---------------- hẹn giờ in lại ----------------
    reg [$clog2(MSG_DIV)-1:0] msg_c = {($clog2(MSG_DIV)){1'b0}};
    reg                       msg_tick = 1'b0;
    always @(posedge clk) begin
        msg_tick <= 1'b0;
        if (msg_c == MSG_DIV[$clog2(MSG_DIV)-1:0] - 1'b1) begin
            msg_c    <= {($clog2(MSG_DIV)){1'b0}};
            msg_tick <= 1'b1;
        end else begin
            msg_c <= msg_c + 1'b1;
        end
    end

    reg want_send = 1'b0;

    always @(posedge clk) begin
        tx_start <= 1'b0;
        if (msg_tick && rw_done) want_send <= 1'b1;

        case (st)
            // ---- đọc toàn bộ và tính CRC ----
            S_RD_REQ: begin
                st <= S_RD_WAIT;
            end
            S_RD_WAIT: begin               // rdata có hiệu lực ở chu kỳ sau
                bytei <= 2'd0;
                st    <= S_CRC;
            end
            S_CRC: begin
                crc <= crc32_byte(crc, crc_in_byte);
                if (bytei == 2'd3) st <= S_RD_NEXT;
                else               bytei <= bytei + 2'd1;
            end
            S_RD_NEXT: begin
                if (addr == WORDS - 1) begin
                    st <= S_PH_DONE;
                end else begin
                    addr <= addr + 1'b1;
                    st   <= S_RD_WAIT;     // địa chỉ mới -> chờ 1 chu kỳ
                end
            end

            // ---- ghi mẫu thứ hai ----
            S_WR: begin
                if (addr == WORDS - 1) begin
                    addr <= {AW{1'b0}};
                    st   <= S_PH_DONE;
                end else begin
                    addr <= addr + 1'b1;
                end
            end

            // ---- kết thúc một pha ----
            S_PH_DONE: begin
                case (phase)
                    2'd0: begin                       // xong đọc ROM
                        crc_rom  <= crc ^ 32'hFFFFFFFF;
                        rom_done <= 1'b1;
                        crc      <= 32'hFFFFFFFF;
                        addr     <= {AW{1'b0}};
                        phase    <= 2'd1;
                        st       <= S_WR;
                    end
                    2'd1: begin                       // xong ghi
                        phase <= 2'd2;
                        addr  <= {AW{1'b0}};
                        st    <= S_RD_WAIT;
                    end
                    default: begin                    // xong đọc lại
                        crc_rw  <= crc ^ 32'hFFFFFFFF;
                        rw_done <= 1'b1;
                        phase   <= 2'd3;
                        st      <= S_IDLE;
                    end
                endcase
            end

            // ---- in lại hai dòng mỗi giây ----
            S_IDLE: begin
                if (want_send) begin
                    want_send <= 1'b0;
                    line_sel  <= 1'b0;
                    msg_idx   <= 5'd0;
                    sending   <= 1'b1;
                    st        <= S_SEND;
                end
            end
            S_SEND: begin
                if (!tx_busy && !tx_start) begin
                    tx_byte  <= line_char(line_sel, msg_idx);
                    tx_start <= 1'b1;
                    if (msg_idx == line_last) begin
                        msg_idx <= 5'd0;
                        if (line_sel == 1'b0) begin
                            line_sel <= 1'b1;         // tiếp dòng RW
                        end else begin
                            sending <= 1'b0;
                            st      <= S_IDLE;
                        end
                    end else begin
                        msg_idx <= msg_idx + 5'd1;
                    end
                end
            end

            default: st <= S_IDLE;
        endcase
    end

    // ---------------- LED ----------------
    reg [$clog2(HB_DIV)-1:0] hb_c = {($clog2(HB_DIV)){1'b0}};
    reg                      hb   = 1'b0;
    always @(posedge clk) begin
        if (hb_c == HB_DIV[$clog2(HB_DIV)-1:0] - 1'b1) begin
            hb_c <= {($clog2(HB_DIV)){1'b0}};
            hb   <= ~hb;
        end else begin
            hb_c <= hb_c + 1'b1;
        end
    end

    wire bad = (rom_done && (crc_rom != CRC_ROM_EXPECT)) ||
               (rw_done  && (crc_rw  != CRC_RW_EXPECT));

    assign led = ~{bad, 2'b00, rw_done, rom_done, hb};
endmodule
