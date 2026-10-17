// F2 — Liên lạc UART hai chiều với Mac.
//
// Hành vi:
//   1. Khi đường RX im lặng (không nhận byte nào trong QUIET chu kỳ), cứ MSG_DIV chu kỳ
//      gửi một dòng "F2 OK dddd\r\n" (dddd = bộ đếm BCD 4 chữ số, có số 0 ở đầu).
//   2. Mỗi byte nhận được đưa vào FIFO và gửi lại (echo). FIFO có ưu tiên cao hơn dòng định kỳ.
//
// Vì sao có cửa sổ im lặng QUIET: nếu dòng định kỳ chen vào giữa luồng echo thì
// phía PC không thể tách đâu là byte echo, đâu là byte của dòng thông báo — phép kiểm
// "10.240 byte echo không sai byte nào" sẽ mất nghĩa. Với QUIET, bài kiểm chia hai pha rõ ràng:
// pha 1 đọc dòng "F2 OK" (đường RX im), pha 2 gửi dữ liệu khối và nhận lại echo thuần.
// Đây là điểm thiết kế có chủ ý, khác một chút với mô tả trong FEASIBILITY_PLAN.
//
// LED (tích cực mức thấp):
//   led[0]      nhịp tim ~1 Hz (chứng tỏ xung nhịp sống)
//   led[4:1]    4 bit thấp của số byte đã nhận
//   led[5]      sáng và GIỮ nếu FIFO từng tràn hoặc UART thu từng lỗi bit stop

module top #(
    parameter integer DIV      = 234,         // 27e6 / 115200 = 234,375 -> 234
    parameter integer MSG_DIV  = 27_000_000,  // 1 s
    parameter integer QUIET    = 3_375_000,   // 125 ms im lặng mới cho gửi dòng định kỳ
    parameter integer HB_DIV   = 13_500_000   // nhịp tim 0,5 s
) (
    input  wire       clk,
    input  wire       uart_rx,
    output wire       uart_tx,
    output wire [5:0] led
);
    // ---------------- UART ----------------
    wire [7:0] rx_data;
    wire       rx_valid;
    wire [7:0] rx_err;

    uart_rx #(.DIV(DIV)) u_rx (
        .clk(clk), .rx(uart_rx),
        .data(rx_data), .valid(rx_valid), .err_cnt(rx_err)
    );

    reg  [7:0] tx_byte  = 8'd0;
    reg        tx_start = 1'b0;
    wire       tx_busy;

    uart_tx #(.DIV(DIV)) u_tx (
        .clk(clk), .data(tx_byte), .start(tx_start),
        .busy(tx_busy), .tx(uart_tx)
    );

    // ---------------- FIFO echo (64 byte) ----------------
    localparam integer AW = 6;
    reg [7:0]    fifo [0:(1<<AW)-1];
    reg [AW-1:0] wptr = {AW{1'b0}};
    reg [AW-1:0] rptr = {AW{1'b0}};

    wire fifo_empty = (wptr == rptr);
    wire fifo_full  = ((wptr + 1'b1) == rptr);
    wire [7:0] fifo_dout = fifo[rptr];

    reg        overflow   = 1'b0;
    reg [15:0] rx_count    = 16'd0;   // byte thu hợp lệ
    reg [15:0] drop_count  = 16'd0;   // byte thu nhưng FIFO đầy
    reg [15:0] tx_count    = 16'd0;   // byte đã phát (cả echo và thông báo)
    reg [5:0]  fifo_hwm    = 6'd0;    // mức FIFO cao nhất từng thấy

    wire [5:0] fifo_level = wptr - rptr;

    always @(posedge clk) begin
        if (rx_valid) begin
            rx_count <= rx_count + 16'd1;
            if (!fifo_full) begin
                fifo[wptr] <= rx_data;
                wptr       <= wptr + 1'b1;
            end else begin
                overflow   <= 1'b1;   // dính luôn, để chẩn đoán
                drop_count <= drop_count + 16'd1;
            end
        end
        if (fifo_level > fifo_hwm) fifo_hwm <= fifo_level;
    end

    // ---------------- cửa sổ im lặng của đường RX ----------------
    reg [$clog2(QUIET+1)-1:0] quiet_c = {($clog2(QUIET+1)){1'b0}};
    wire line_quiet = (quiet_c == QUIET[$clog2(QUIET+1)-1:0]);

    always @(posedge clk) begin
        if (rx_valid)          quiet_c <= {($clog2(QUIET+1)){1'b0}};
        else if (!line_quiet)  quiet_c <= quiet_c + 1'b1;
    end

    // ---------------- hẹn giờ dòng định kỳ ----------------
    // Chỉ block này ghi msg_c / msg_tick; msg_req thuộc block trọng tài bên dưới
    // (một thanh ghi chỉ được một always block ghi).
    reg [$clog2(MSG_DIV)-1:0] msg_c    = {($clog2(MSG_DIV)){1'b0}};
    reg                       msg_tick = 1'b0;

    always @(posedge clk) begin
        msg_tick <= 1'b0;
        if (msg_c == MSG_DIV[$clog2(MSG_DIV)-1:0] - 1'b1) begin
            msg_c <= {($clog2(MSG_DIV)){1'b0}};
            if (line_quiet) msg_tick <= 1'b1;
        end else begin
            msg_c <= msg_c + 1'b1;
        end
    end

    // ---------------- bộ đếm BCD 4 chữ số ----------------
    reg [3:0] d0 = 4'd0, d1 = 4'd0, d2 = 4'd0, d3 = 4'd0;

    task bcd_inc;
        begin
            if (d0 == 4'd9) begin
                d0 <= 4'd0;
                if (d1 == 4'd9) begin
                    d1 <= 4'd0;
                    if (d2 == 4'd9) begin
                        d2 <= 4'd0;
                        d3 <= (d3 == 4'd9) ? 4'd0 : d3 + 4'd1;
                    end else d2 <= d2 + 4'd1;
                end else d1 <= d1 + 4'd1;
            end else d0 <= d0 + 4'd1;
        end
    endtask

    // ---------------- khuôn dòng "F2 OK dddd\r\n" ----------------
    localparam integer MSGLEN = 53;
    reg [5:0] msg_idx = 6'd0;
    reg       msg_act = 1'b0;

    function [7:0] hexdig;
        input [3:0] v;
        begin
            hexdig = (v < 4'd10) ? (8'h30 + v) : (8'h41 + v - 4'd10);
        end
    endfunction

    // "F2 OK dddd rx=hhhh tx=hhhh dr=hhhh er=hh ov=h hw=hh\r\n"  (51 byte)
    function [7:0] msg_char;
        input [5:0] i;
        begin
            case (i)
                6'd0:  msg_char = "F";
                6'd1:  msg_char = "2";
                6'd2:  msg_char = " ";
                6'd3:  msg_char = "O";
                6'd4:  msg_char = "K";
                6'd5:  msg_char = " ";
                6'd6:  msg_char = 8'h30 + d3;
                6'd7:  msg_char = 8'h30 + d2;
                6'd8:  msg_char = 8'h30 + d1;
                6'd9:  msg_char = 8'h30 + d0;
                6'd10: msg_char = " ";
                6'd11: msg_char = "r";
                6'd12: msg_char = "x";
                6'd13: msg_char = "=";
                6'd14: msg_char = hexdig(rx_count[15:12]);
                6'd15: msg_char = hexdig(rx_count[11:8]);
                6'd16: msg_char = hexdig(rx_count[7:4]);
                6'd17: msg_char = hexdig(rx_count[3:0]);
                6'd18: msg_char = " ";
                6'd19: msg_char = "t";
                6'd20: msg_char = "x";
                6'd21: msg_char = "=";
                6'd22: msg_char = hexdig(tx_count[15:12]);
                6'd23: msg_char = hexdig(tx_count[11:8]);
                6'd24: msg_char = hexdig(tx_count[7:4]);
                6'd25: msg_char = hexdig(tx_count[3:0]);
                6'd26: msg_char = " ";
                6'd27: msg_char = "d";
                6'd28: msg_char = "r";
                6'd29: msg_char = "=";
                6'd30: msg_char = hexdig(drop_count[15:12]);
                6'd31: msg_char = hexdig(drop_count[11:8]);
                6'd32: msg_char = hexdig(drop_count[7:4]);
                6'd33: msg_char = hexdig(drop_count[3:0]);
                6'd34: msg_char = " ";
                6'd35: msg_char = "e";
                6'd36: msg_char = "r";
                6'd37: msg_char = "=";
                6'd38: msg_char = hexdig(rx_err[7:4]);
                6'd39: msg_char = hexdig(rx_err[3:0]);
                6'd40: msg_char = " ";
                6'd41: msg_char = "o";
                6'd42: msg_char = "v";
                6'd43: msg_char = "=";
                6'd44: msg_char = 8'h30 + {7'd0, overflow};
                6'd45: msg_char = " ";
                6'd46: msg_char = "h";
                6'd47: msg_char = "w";
                6'd48: msg_char = "=";
                6'd49: msg_char = hexdig({2'b0, fifo_hwm[5:4]});
                6'd50: msg_char = hexdig(fifo_hwm[3:0]);
                6'd51: msg_char = 8'h0D;
                6'd52: msg_char = 8'h0A;
                default: msg_char = 8'h00;
            endcase
        end
    endfunction

    // ---------------- trọng tài đầu ra: FIFO echo ưu tiên, rồi dòng định kỳ ----------------
    reg msg_req = 1'b0;

    always @(posedge clk) begin
        tx_start <= 1'b0;
        if (msg_tick) msg_req <= 1'b1;
        if (tx_start) tx_count <= tx_count + 16'd1;

        if (!tx_busy && !tx_start) begin
            if (!fifo_empty) begin
                tx_byte  <= fifo_dout;
                rptr     <= rptr + 1'b1;
                tx_start <= 1'b1;
            end else if (msg_act) begin
                tx_byte  <= msg_char(msg_idx);
                tx_start <= 1'b1;
                if (msg_idx == MSGLEN - 1) begin
                    msg_idx <= 6'd0;
                    msg_act <= 1'b0;
                    bcd_inc;
                end else begin
                    msg_idx <= msg_idx + 6'd1;
                end
            end else if (msg_req && !msg_tick) begin
                msg_act <= 1'b1;
                msg_req <= 1'b0;
                msg_idx <= 6'd0;
            end
        end
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

    wire fault = overflow | (rx_err != 8'd0);
    assign led = ~{fault, rx_count[3:0], hb};
endmodule
