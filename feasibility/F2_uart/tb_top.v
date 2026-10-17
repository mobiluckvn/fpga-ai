// Testbench F2 — kiểm UART trước khi nạp kit.
//   1. Giải mã dòng định kỳ, so với "F2 OK 0000\r\n".
//   2. Gửi 300 byte liên tục, so echo từng byte.
//   3. Sau khi đường RX im lại, dòng định kỳ phải quay lại (kiểm cửa sổ QUIET).
// Dùng DIV nhỏ để mô phỏng nhanh; logic giống hệt bản nạp kit.
`timescale 1ns/1ps

module tb_top;
    localparam integer DIV     = 8;
    localparam integer MSG_DIV = 20_000;
    localparam integer QUIET   = 400;
    localparam integer HB_DIV  = 5_000;
    localparam real    CLKP    = 2.0;            // ns, chu kỳ clk
    localparam real    BIT_T   = DIV * CLKP;     // ns mỗi bit UART

    localparam integer NBULK = 300;

    reg        clk     = 1'b0;
    reg        line_rx = 1'b1;
    wire       line_tx;
    wire [5:0] led;

    top #(.DIV(DIV), .MSG_DIV(MSG_DIV), .QUIET(QUIET), .HB_DIV(HB_DIV)) dut (
        .clk(clk), .uart_rx(line_rx), .uart_tx(line_tx), .led(led)
    );

    always #(CLKP/2) clk = ~clk;

    integer errors = 0;

    // ---------------- monitor: giải mã liên tục đường TX của FPGA ----------------
    reg [7:0] rxq [0:8191];
    integer   rxn = 0;
    integer   mi;
    reg [7:0] mb;

    initial begin
        forever begin
            @(negedge line_tx);
            #(BIT_T * 1.5);                      // tới giữa bit dữ liệu 0
            mb = 8'd0;
            for (mi = 0; mi < 8; mi = mi + 1) begin
                mb[mi] = line_tx;
                #(BIT_T);
            end
            if (line_tx !== 1'b1) begin
                $display("LOI: bit stop sai o byte thu %0d", rxn);
                errors = errors + 1;
            end
            rxq[rxn] = mb;
            rxn = rxn + 1;
        end
    end

    // ---------------- gửi một byte vào chân RX của FPGA ----------------
    task send_byte(input [7:0] v);
        integer i;
        begin
            line_rx = 1'b0;  #(BIT_T);           // start
            for (i = 0; i < 8; i = i + 1) begin
                line_rx = v[i]; #(BIT_T);        // LSB trước
            end
            line_rx = 1'b1;  #(BIT_T);           // stop
        end
    endtask

    // ---------------- bài kiểm ----------------
    reg [7:0] sent [0:NBULK-1];
    reg [7:0] expect_msg [0:9];
    localparam integer MSGLEN = 53;
    integer   i, base, t;

    initial begin
        expect_msg[0]="F";  expect_msg[1]="2";  expect_msg[2]=" ";
        expect_msg[3]="O";  expect_msg[4]="K";  expect_msg[5]=" ";
        expect_msg[6]="0";  expect_msg[7]="0";  expect_msg[8]="0";  expect_msg[9]="0";

        // ---- 1. dòng định kỳ đầu tiên ----
        t = 0;
        while (rxn < MSGLEN && t < 2000) begin
            #(BIT_T * 20);
            t = t + 1;
        end
        if (rxn < MSGLEN) begin
            $display("LOI: khong nhan du %0d byte cua dong dinh ky (chi co %0d)", MSGLEN, rxn);
            errors = errors + 1;
        end else begin
            if (rxq[MSGLEN-2] !== 8'h0D || rxq[MSGLEN-1] !== 8'h0A) begin
                $display("LOI: dong dinh ky khong ket thuc bang CR LF (%02h %02h)",
                         rxq[MSGLEN-2], rxq[MSGLEN-1]);
                errors = errors + 1;
            end
            for (i = 0; i < 10; i = i + 1) begin
                if (rxq[i] !== expect_msg[i]) begin
                    $display("LOI dong dinh ky byte %0d: nhan %02h ('%c'), ky vong %02h ('%c')",
                             i, rxq[i], rxq[i], expect_msg[i], expect_msg[i]);
                    errors = errors + 1;
                end
            end
            if (errors == 0) begin
                $write("OK 1/3: dong dinh ky = \"");
                for (i = 0; i < MSGLEN-2; i = i + 1) $write("%c", rxq[i]);
                $display("\"");
            end
        end

        // ---- 2. echo 300 byte ----
        #(BIT_T * 4);
        base = rxn;
        for (i = 0; i < NBULK; i = i + 1) begin
            sent[i] = $random;
            send_byte(sent[i]);
        end
        // chờ echo chảy hết
        t = 0;
        while (rxn < base + NBULK && t < 2000) begin
            #(BIT_T * 2);
            t = t + 1;
        end
        if (rxn - base != NBULK) begin
            $display("LOI echo: nhan %0d byte, ky vong %0d", rxn - base, NBULK);
            errors = errors + 1;
        end
        for (i = 0; i < NBULK; i = i + 1) begin
            if (rxq[base+i] !== sent[i]) begin
                $display("LOI echo byte %0d: nhan %02h, ky vong %02h", i, rxq[base+i], sent[i]);
                errors = errors + 1;
            end
        end
        if (led[5] !== 1'b1) begin
            $display("LOI: led[5] bao fault (FIFO tran hoac loi bit stop)");
            errors = errors + 1;
        end
        $display("OK 2/3: echo %0d byte khong sai byte nao (FIFO khong tran)", NBULK);

        // ---- 3. dòng định kỳ quay lại sau khi RX im ----
        base = rxn;
        t = 0;
        while (rxn < base + MSGLEN && t < 20000) begin
            #(BIT_T * 4);
            t = t + 1;
        end
        if (rxn - base < MSGLEN) begin
            $display("LOI: dong dinh ky khong quay lai sau khi RX im (chi %0d byte)", rxn - base);
            errors = errors + 1;
        end else begin
            if (rxq[base] !== "F" || rxq[base+1] !== "2" || rxq[base+3] !== "O" || rxq[base+4] !== "K") begin
                $display("LOI: dong dinh ky sau echo khong dung dang: %c%c%c%c%c",
                         rxq[base], rxq[base+1], rxq[base+2], rxq[base+3], rxq[base+4]);
                errors = errors + 1;
            end else begin
                $display("OK 3/3: dong dinh ky quay lai, bo dem = %c%c%c%c",
                         rxq[base+6], rxq[base+7], rxq[base+8], rxq[base+9]);
            end
        end

        if (errors == 0) $display("F2_SIM_PASS: UART hai chieu dung");
        else             $display("F2_SIM_FAIL: %0d loi", errors);
        $finish;
    end
endmodule
