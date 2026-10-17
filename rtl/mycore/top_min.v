// top_min — thiết kế TỐI GIẢN để khoanh vùng lỗi ở cổng B3.
//
// Chỉ gồm: một bộ đếm + uart_tx phát chuỗi "MIN\r\n" mỗi ~0,2 s + một LED nhấp nháy.
// KHÔNG có lõi, KHÔNG có RAM 64 KB, KHÔNG có DSP. Dùng ĐÚNG cùng Makefile, cùng
// file .cst, cùng lệnh yosys/nextpnr/gowin_pack như bản nhánh B.
//
//   Nếu bản này CŨNG im  -> lỗi ở thiết lập build trong rtl/mycore (đường dẫn, .cst,
//                           cách gọi công cụ), không phải ở soc_b/mycore.
//   Nếu bản này CHẠY     -> thiết lập build đúng, lỗi nằm trong soc_b hoặc mycore.

`default_nettype none

module top (
    input  wire       clk,
    output wire       uart_tx,
    input  wire       uart_rx,
    output wire [5:0] led
);
    localparam integer DIV = 234;        // 27e6 / 115200

    reg [22:0] div  = 23'd0;
    reg [2:0]  idx  = 3'd0;
    reg        run  = 1'b0;
    reg [7:0]  ch;
    reg [7:0]  tx_byte  = 8'd0;
    reg        tx_start = 1'b0;
    wire       tx_busy;

    always @(*) begin
        case (idx)
            3'd0:    ch = "M";
            3'd1:    ch = "I";
            3'd2:    ch = "N";
            3'd3:    ch = 8'h0D;
            default: ch = 8'h0A;
        endcase
    end

    always @(posedge clk) begin
        div      <= div + 23'd1;
        tx_start <= 1'b0;
        if (div == 23'd0 && !run) begin
            run <= 1'b1;
            idx <= 3'd0;
        end else if (run && !tx_busy && !tx_start) begin
            tx_byte  <= ch;
            tx_start <= 1'b1;
            if (idx == 3'd4) run <= 1'b0;
            else             idx <= idx + 3'd1;
        end
    end

    uart_tx #(.DIV(DIV)) u_tx (
        .clk(clk), .data(tx_byte), .start(tx_start), .busy(tx_busy), .tx(uart_tx)
    );

    // nhiều nhất một LED sáng (tích cực mức thấp), nhấp nháy ~1,6 Hz
    assign led = ~{5'b00000, div[22]};

    // giữ uart_rx không bị tối ưu mất
    wire _unused = uart_rx;
endmodule

`default_nettype wire
