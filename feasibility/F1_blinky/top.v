// F1 — Blinky: kiểm chứng luồng yosys -> nextpnr-himbaechel -> gowin_pack -> openFPGALoader
//
// 6 LED hiển thị một bộ đếm nhị phân 6 bit. Bit thấp nhất đổi trạng thái mỗi TICK giây.
// LED trên Tang Nano 20K tích cực mức thấp (ghi 0 => sáng) nên đầu ra bị đảo.
//
// CLK_HZ   : tần số xung nhịp vào (27 MHz, thạch anh trên kit, không PLL)
// TICK_DIV : số chu kỳ giữa hai lần tăng bộ đếm. 13_500_000 @27MHz = 0,5 s
//            => bit0 đổi mỗi 0,5 s, tức nháy 1 Hz (chu kỳ sáng-tối 1 s).
// Mô phỏng ghi đè TICK_DIV cho nhỏ lại.

module top #(
    parameter integer TICK_DIV = 13_500_000
) (
    input  wire       clk,
    output wire [5:0] led
);
    // Đủ rộng cho TICK_DIV-1; 24 bit chứa được 13_499_999 (< 16_777_216).
    localparam integer DIV_W = (TICK_DIV <= 2)      ? 1  :
                               (TICK_DIV <= 256)    ? 8  :
                               (TICK_DIV <= 65536)  ? 16 : 24;

    reg [DIV_W-1:0] div = {DIV_W{1'b0}};
    reg [5:0]       cnt = 6'd0;

    always @(posedge clk) begin
        if (div == TICK_DIV[DIV_W-1:0] - 1'b1) begin
            div <= {DIV_W{1'b0}};
            cnt <= cnt + 6'd1;
        end else begin
            div <= div + 1'b1;
        end
    end

    assign led = ~cnt;   // tích cực mức thấp
endmodule
