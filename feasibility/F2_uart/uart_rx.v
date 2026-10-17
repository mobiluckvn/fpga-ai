// UART thu, 8N1. Lấy mẫu giữa bit. Có đồng bộ hoá 2 tầng cho chân vào,
// kiểm tra lại bit start ở giữa bit (chống nhiễu) và kiểm bit stop.
// valid nhảy 1 một chu kỳ khi nhận đủ một byte hợp lệ.
// Byte có bit stop sai bị bỏ và đếm vào err_cnt (dùng để chẩn đoán).

module uart_rx #(
    parameter integer DIV = 234
) (
    input  wire       clk,
    input  wire       rx,
    output reg  [7:0] data  = 8'd0,
    output reg        valid = 1'b0,
    output reg  [7:0] err_cnt = 8'd0
);
    localparam integer CW = (DIV <= 2) ? 3 : ($clog2(DIV) + 1);

    localparam [1:0] S_IDLE = 2'd0, S_START = 2'd1, S_DATA = 2'd2, S_STOP = 2'd3;

    reg [1:0]    st = S_IDLE;
    reg [CW-1:0] c  = {CW{1'b0}};
    reg [3:0]    n  = 4'd0;
    reg [7:0]    sh = 8'd0;

    // đồng bộ hoá chân vào bất đồng bộ
    reg rx_q = 1'b1, rx_s = 1'b1;
    always @(posedge clk) begin
        rx_q <= rx;
        rx_s <= rx_q;
    end

    always @(posedge clk) begin
        valid <= 1'b0;
        case (st)
            S_IDLE: begin
                if (rx_s == 1'b0) begin          // sườn xuống = có thể là start
                    c  <= (DIV[CW-1:0] >> 1) - 1'b1;   // chờ tới giữa bit start
                    st <= S_START;
                end
            end
            S_START: begin
                if (c == {CW{1'b0}}) begin
                    if (rx_s == 1'b0) begin      // vẫn thấp => start thật
                        c  <= DIV[CW-1:0] - 1'b1;
                        n  <= 4'd8;
                        st <= S_DATA;
                    end else begin               // nhiễu
                        st <= S_IDLE;
                    end
                end else begin
                    c <= c - 1'b1;
                end
            end
            S_DATA: begin
                if (c == {CW{1'b0}}) begin
                    sh <= {rx_s, sh[7:1]};       // LSB trước
                    c  <= DIV[CW-1:0] - 1'b1;
                    if (n == 4'd1) st <= S_STOP;
                    else           n  <= n - 4'd1;
                end else begin
                    c <= c - 1'b1;
                end
            end
            S_STOP: begin
                if (c == {CW{1'b0}}) begin
                    if (rx_s == 1'b1) begin      // bit stop đúng
                        data  <= sh;
                        valid <= 1'b1;
                    end else begin
                        err_cnt <= err_cnt + 8'd1;
                    end
                    st <= S_IDLE;
                end else begin
                    c <= c - 1'b1;
                end
            end
            default: st <= S_IDLE;
        endcase
    end
endmodule
