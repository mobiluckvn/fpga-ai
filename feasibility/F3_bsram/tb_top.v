// Testbench F3 — mô phỏng toàn bộ 64 KB (16.384 từ) với cùng pattern.hex sẽ nạp kit,
// giải mã hai dòng UART và so với CRC32 kỳ vọng do Python tính.
// Dùng DIV nhỏ để UART nhanh, nhưng KHÔNG giảm số từ: phải kiểm đúng 64 KB.
`timescale 1ns/1ps

module tb_top;
    localparam integer DIV     = 4;
    localparam integer MSG_DIV = 2_000_000;    // ~đủ dài để pha ROM+WR+RW xong trước khi in
    localparam integer HB_DIV  = 1_000_000;
    localparam real    CLKP    = 2.0;
    localparam real    BIT_T   = DIV * CLKP;

    // CRC kỳ vọng — do scripts/gen_pattern.py in ra, truyền vào bằng -D nếu muốn đổi
`ifndef CRC_ROM
    `define CRC_ROM 32'hC7CD86AA
`endif
`ifndef CRC_RW
    `define CRC_RW  32'hD63B5AB4
`endif

    reg        clk = 1'b0;
    wire       line_tx;
    wire [5:0] led;

    top #(.DIV(DIV), .MSG_DIV(MSG_DIV), .HB_DIV(HB_DIV),
          .CRC_ROM_EXPECT(`CRC_ROM), .CRC_RW_EXPECT(`CRC_RW)) dut (
        .clk(clk), .uart_tx(line_tx), .led(led)
    );

    always #(CLKP/2) clk = ~clk;

    integer errors = 0;

    // ---- monitor UART ----
    reg [7:0] rxq [0:255];
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
            if (rxn < 256) rxq[rxn] = mb;
            rxn = rxn + 1;
        end
    end

    // ---- kiểm ----
    integer i, t;
    reg [8*40:1] s;

    task show_line(input integer from, input integer len);
        integer k;
        begin
            $write("  ");
            for (k = from; k < from + len; k = k + 1)
                if (rxq[k] >= 8'h20) $write("%c", rxq[k]);
            $write("\n");
        end
    endtask

    initial begin
        // chờ đủ 33 byte = dòng ROM (17) + dòng RW (16)
        t = 0;
        while (rxn < 33 && t < 200000) begin
            #(BIT_T * 10);
            t = t + 1;
        end
        if (rxn < 33) begin
            $display("F3_SIM_FAIL: chi nhan %0d byte, ky vong >= 33", rxn);
            $finish;
        end

        $display("Dong nhan duoc:");
        show_line(0, 15);
        show_line(17, 14);

        // dòng 1: "F3,ROM," + 8 hex + CRLF
        if (rxq[0]!=="F" || rxq[1]!=="3" || rxq[2]!=="," || rxq[3]!=="R" ||
            rxq[4]!=="O" || rxq[5]!=="M" || rxq[6]!==",") begin
            $display("LOI: dong 1 sai tien to"); errors = errors + 1;
        end
        if (rxq[15]!==8'h0D || rxq[16]!==8'h0A) begin
            $display("LOI: dong 1 khong ket thuc CRLF"); errors = errors + 1;
        end
        if (dut.crc_rom !== `CRC_ROM) begin
            $display("LOI: CRC ROM = %08h, ky vong %08h", dut.crc_rom, `CRC_ROM);
            errors = errors + 1;
        end else begin
            $display("OK 1/2: CRC32 ROM = %08h khop ky vong (doc 16384 tu da khoi tao)", dut.crc_rom);
        end

        // dòng 2: "F3,RW," + 8 hex + CRLF
        if (rxq[17]!=="F" || rxq[18]!=="3" || rxq[19]!=="," || rxq[20]!=="R" ||
            rxq[21]!=="W" || rxq[22]!==",") begin
            $display("LOI: dong 2 sai tien to"); errors = errors + 1;
        end
        if (rxq[31]!==8'h0D || rxq[32]!==8'h0A) begin
            $display("LOI: dong 2 khong ket thuc CRLF"); errors = errors + 1;
        end
        if (dut.crc_rw !== `CRC_RW) begin
            $display("LOI: CRC RW = %08h, ky vong %08h", dut.crc_rw, `CRC_RW);
            errors = errors + 1;
        end else begin
            $display("OK 2/2: CRC32 RW  = %08h khop ky vong (ghi roi doc lai 16384 tu)", dut.crc_rw);
        end

        if (led[5] !== 1'b1) begin
            $display("LOI: led[5] bao CRC khong khop"); errors = errors + 1;
        end

        if (errors == 0) $display("F3_SIM_PASS: BSRAM 64 KB khoi tao dung, doc/ghi dung");
        else             $display("F3_SIM_FAIL: %0d loi", errors);
        $finish;
    end
endmodule
