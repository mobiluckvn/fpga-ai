// Testbench F1: kiểm tra bộ đếm tăng đúng nhịp và đầu ra LED bị đảo.
// Dùng TICK_DIV nhỏ để mô phỏng nhanh.
`timescale 1ns/1ps

module tb_top;
    localparam integer TICK_DIV = 10;

    reg        clk = 0;
    wire [5:0] led;
    integer    errors = 0;
    integer    i;
    reg [5:0]  expect_cnt;

    top #(.TICK_DIV(TICK_DIV)) dut (.clk(clk), .led(led));

    always #1 clk = ~clk;   // chu kỳ 2 ns

    initial begin
        // Sau reset ngầm: cnt = 0 => led = 6'b111111
        @(negedge clk);
        if (led !== 6'b111111) begin
            $display("LOI: led ban dau = %b, ky vong 111111", led);
            errors = errors + 1;
        end

        // Mỗi TICK_DIV chu kỳ clk thì cnt tăng 1. Kiểm 70 lần tăng (quá một vòng 64).
        for (i = 1; i <= 70; i = i + 1) begin
            repeat (TICK_DIV) @(posedge clk);
            #0.1;
            expect_cnt = i[5:0];
            if (led !== ~expect_cnt) begin
                $display("LOI tai lan tang %0d: led = %b, ky vong %b", i, led, ~expect_cnt);
                errors = errors + 1;
            end
        end

        if (errors == 0)
            $display("F1_SIM_PASS: bo dem 6 bit tang dung nhip, dau ra LED dao dung");
        else
            $display("F1_SIM_FAIL: %0d loi", errors);
        $finish;
    end
endmodule
