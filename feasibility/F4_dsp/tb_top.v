// Testbench F4 — chạy ĐỦ 2^20 chu kỳ tích luỹ (không rút gọn), giải mã dòng UART,
// so với ACC kỳ vọng do scripts/gen_f4_expect.py tính.
`timescale 1ns/1ps

module tb_top;
    localparam integer DIV     = 4;
    localparam integer MSG_DIV = 1_100_000;    // in ngay sau khi xong 2^20 chu kỳ
    localparam integer HB_DIV  = 500_000;
    localparam real    CLKP    = 2.0;
    localparam real    BIT_T   = DIV * CLKP;

`ifndef ACC_EXPECT
    `define ACC_EXPECT 32'hFEF834C3
`endif

    reg        clk = 1'b0;
    wire       line_tx;
    wire [5:0] led;

    top #(.DIV(DIV), .MSG_DIV(MSG_DIV), .HB_DIV(HB_DIV), .LOGN(20),
          .ACC_EXPECT(`ACC_EXPECT)) dut (
        .clk(clk), .uart_tx(line_tx), .led(led)
    );

    always #(CLKP/2) clk = ~clk;

    integer errors = 0;

    reg [7:0] rxq [0:63];
    integer   rxn = 0;
    integer   mi;
    reg [7:0] mb;

    initial begin
        forever begin
            @(negedge line_tx);
            #(BIT_T * 1.5);
            mb = 8'd0;
            for (mi = 0; mi < 8; mi = mi + 1) begin
                mb[mi] = line_tx;
                #(BIT_T);
            end
            if (line_tx !== 1'b1) begin
                $display("LOI: bit stop sai o byte %0d", rxn);
                errors = errors + 1;
            end
            if (rxn < 64) rxq[rxn] = mb;
            rxn = rxn + 1;
        end
    end

    integer i, t;

    initial begin
        t = 0;
        while (rxn < 17 && t < 400000) begin
            #(BIT_T * 20);
            t = t + 1;
        end
        if (rxn < 17) begin
            $display("F4_SIM_FAIL: chi nhan %0d byte, ky vong 17", rxn);
            $finish;
        end

        $write("Dong nhan duoc: \"");
        for (i = 0; i < 15; i = i + 1) $write("%c", rxq[i]);
        $display("\"");

        if (rxq[0]!=="F" || rxq[1]!=="4" || rxq[2]!=="," || rxq[6]!==",") begin
            $display("LOI: dong sai khuon"); errors = errors + 1;
        end
        if (rxq[15]!==8'h0D || rxq[16]!==8'h0A) begin
            $display("LOI: dong khong ket thuc CRLF"); errors = errors + 1;
        end
        if (dut.acc !== `ACC_EXPECT) begin
            $display("LOI: acc = %08h, ky vong %08h", dut.acc, `ACC_EXPECT);
            errors = errors + 1;
        end else begin
            $display("OK: acc = %08h khop Python sau 2^20 = 1048576 chu ky", dut.acc);
        end
        if (dut.a !== 32'hBC64D7E9 || dut.b !== 32'hC8B82DCC) begin
            $display("LOI: LFSR cuoi a=%08h b=%08h, ky vong BC64D7E9 / C8B82DCC",
                     dut.a, dut.b);
            errors = errors + 1;
        end else begin
            $display("OK: trang thai LFSR cuoi khop Python (a=%08h b=%08h)", dut.a, dut.b);
        end
        if (led[5] !== 1'b1) begin
            $display("LOI: led[5] bao acc khong khop"); errors = errors + 1;
        end

        if (errors == 0) $display("F4_SIM_PASS: khoi nhan int8 dung");
        else             $display("F4_SIM_FAIL: %0d loi", errors);
        $finish;
    end
endmodule
