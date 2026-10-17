// UART phát, 8N1, không chẵn lẻ, tự chia từ xung nhịp hệ thống.
// DIV = số chu kỳ clk cho mỗi bit. @27 MHz, 115200 baud: DIV = 234.
//
// Giao thức: khi busy=0, đặt data và nhấn start=1 một chu kỳ.
// Khung phát: 1 bit start (0), 8 bit dữ liệu LSB trước, 1 bit stop (1).

module uart_tx #(
    parameter integer DIV = 234
) (
    input  wire       clk,
    input  wire [7:0] data,
    input  wire       start,
    output wire       busy,
    output wire       tx
);
    localparam integer CW = (DIV <= 2) ? 2 : $clog2(DIV);

    reg [9:0]    sh = 10'h3FF;   // nghỉ = toàn 1 => tx = 1
    reg [3:0]    n  = 4'd0;      // số bit còn lại
    reg [CW-1:0] c  = {CW{1'b0}};

    assign tx   = sh[0];
    assign busy = (n != 4'd0);

    always @(posedge clk) begin
        if (n == 4'd0) begin
            if (start) begin
                sh <= {1'b1, data, 1'b0};   // stop, d7..d0, start
                n  <= 4'd10;
                c  <= DIV[CW-1:0] - 1'b1;
            end
        end else if (c == {CW{1'b0}}) begin
            sh <= {1'b1, sh[9:1]};
            n  <= n - 4'd1;
            c  <= DIV[CW-1:0] - 1'b1;
        end else begin
            c <= c - 1'b1;
        end
    end
endmodule
