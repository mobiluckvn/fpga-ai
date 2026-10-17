// F5 — vỏ cho kit Tang Nano 20K: tạo reset đồng bộ sau khi nạp bitstream.
module top #(
    parameter integer DIV     = 234,
    parameter         HEXFILE = "firmware.hex"
) (
    input  wire       clk,
    output wire       uart_tx,
    input  wire       uart_rx,
    output wire [5:0] led
);
    // Giữ reset khoảng 1024 chu kỳ sau khi cấu hình xong.
    reg [10:0] rst_c  = 11'd0;
    reg        resetn = 1'b0;
    always @(posedge clk) begin
        if (rst_c == 11'd1023) resetn <= 1'b1;
        else                   rst_c  <= rst_c + 11'd1;
    end

    soc #(.DIV(DIV), .HEXFILE(HEXFILE)) u_soc (
        .clk(clk), .resetn(resetn),
        .uart_tx(uart_tx), .uart_rx(uart_rx), .led(led),
        .dbg_tx_valid(), .dbg_tx_byte(), .dbg_trap()
    );
endmodule
