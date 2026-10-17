// Testbench RIÊNG cho khối pcpi_dot4 (không có CPU).
//
// Kiểm ba thứ:
//   1. 1.000.000 cặp ngẫu nhiên (LFSR, hạt giống cố định) — so với tham chiếu tính
//      ĐỘC LẬP trong testbench: tách lane bằng phép gán sang reg signed [7:0] rồi
//      cộng dồn trong `integer` 32 bit. Cách tách lane/mở rộng dấu của TB khác hoàn
//      toàn cách của DUT, nên lỗi ở một trong hai bên sẽ lộ ra.
//   2. Giá trị biên: mọi tổ hợp của {-128, -127, -1, 0, 1, 127} đặt lên cả 4 lane,
//      cộng với quét từng lane một trong khi ba lane còn lại giữ giá trị biên.
//   3. Khối phải IM LẶNG với lệnh không phải của nó (ở đây thử opcode/funct7 của MUL)
//      — nếu không nó sẽ phá lệnh MUL của lõi.
`timescale 1ns/1ps

module tb_dot4;
    localparam integer NRAND = 1000000;

    reg clk = 1'b0;
    reg resetn = 1'b0;

    reg        pcpi_valid = 1'b0;
    reg [31:0] pcpi_insn  = 32'd0;
    reg [31:0] pcpi_rs1   = 32'd0;
    reg [31:0] pcpi_rs2   = 32'd0;
    wire       pcpi_wr;
    wire [31:0] pcpi_rd;
    wire       pcpi_wait;
    wire       pcpi_ready;

    pcpi_dot4 dut (
        .clk(clk), .resetn(resetn),
        .pcpi_valid(pcpi_valid), .pcpi_insn(pcpi_insn),
        .pcpi_rs1(pcpi_rs1), .pcpi_rs2(pcpi_rs2),
        .pcpi_wr(pcpi_wr), .pcpi_rd(pcpi_rd),
        .pcpi_wait(pcpi_wait), .pcpi_ready(pcpi_ready)
    );

    always #1 clk = ~clk;

    // mã lệnh DOT4 và một lệnh KHÔNG phải của khối (MUL: opcode 0110011, funct7 0000001)
    localparam [31:0] INSN_DOT4 = {7'b0000000, 5'd0, 5'd0, 3'b000, 5'd0, 7'b0001011};
    localparam [31:0] INSN_MUL  = {7'b0000001, 5'd0, 5'd0, 3'b000, 5'd0, 7'b0110011};

    integer errors = 0;
    integer nchecked = 0;

    // ---- tham chiếu tính độc lập trong TB ----
    function integer ref_dot4;
        input [31:0] a;
        input [31:0] b;
        integer i;
        reg signed [7:0] ax, bx;
        integer acc;
        begin
            acc = 0;
            for (i = 0; i < 4; i = i + 1) begin
                ax = a[8*i +: 8];
                bx = b[8*i +: 8];
                acc = acc + (ax * bx);
            end
            ref_dot4 = acc;
        end
    endfunction

    // ---- phát một lệnh DOT4 và kiểm kết quả ----
    task do_dot4;
        input [31:0] a;
        input [31:0] b;
        integer expect_v;
        integer got_v;
        integer guard;
        begin
            expect_v = ref_dot4(a, b);
            @(negedge clk);
            pcpi_insn  = INSN_DOT4;
            pcpi_rs1   = a;
            pcpi_rs2   = b;
            pcpi_valid = 1'b1;

            guard = 0;
            while (!pcpi_ready && guard < 16) begin
                @(negedge clk);
                guard = guard + 1;
            end
            if (!pcpi_ready) begin
                $display("LOI: khong co pcpi_ready sau %0d chu ky (a=%08h b=%08h)", guard, a, b);
                errors = errors + 1;
            end else begin
                if (!pcpi_wr) begin
                    $display("LOI: pcpi_ready nhung pcpi_wr=0 (a=%08h b=%08h)", a, b);
                    errors = errors + 1;
                end
                got_v = $signed(pcpi_rd);
                if (got_v !== expect_v) begin
                    if (errors < 10)
                        $display("LOI: a=%08h b=%08h -> rd=%0d (%08h), ky vong %0d",
                                 a, b, got_v, pcpi_rd, expect_v);
                    errors = errors + 1;
                end
                nchecked = nchecked + 1;
            end
            @(negedge clk);
            pcpi_valid = 1'b0;
            @(negedge clk);
        end
    endtask

    // ---- LFSR 32 bit, cùng đa thức với F3/F4 ----
    function [31:0] lfsr_next;
        input [31:0] s;
        begin
            lfsr_next = {s[30:0], s[31] ^ s[21] ^ s[1] ^ s[0]};
        end
    endfunction

    reg [31:0] sa, sb;
    integer k, i, j;
    reg [7:0] bnd [0:5];
    reg [31:0] va, vb;
    integer guard2;

    initial begin
        bnd[0] = 8'h80;  // -128
        bnd[1] = 8'h81;  // -127
        bnd[2] = 8'hFF;  // -1
        bnd[3] = 8'h00;  //  0
        bnd[4] = 8'h01;  //  1
        bnd[5] = 8'h7F;  //  127

        repeat (4) @(negedge clk);
        resetn = 1'b1;
        repeat (2) @(negedge clk);

        // ---- 1. khối phải im lặng với lệnh không phải của nó ----
        pcpi_insn  = INSN_MUL;
        pcpi_rs1   = 32'h1234_5678;
        pcpi_rs2   = 32'h9ABC_DEF0;
        pcpi_valid = 1'b1;
        guard2 = 0;
        while (guard2 < 20) begin
            @(negedge clk);
            if (pcpi_ready || pcpi_wr) begin
                $display("LOI: khoi tra loi lenh KHONG phai cua no (MUL)");
                errors = errors + 1;
                guard2 = 20;
            end
            guard2 = guard2 + 1;
        end
        pcpi_valid = 1'b0;
        @(negedge clk);
        if (errors == 0)
            $display("OK 1/3: im lang voi lenh khong phai cua minh");

        // ---- 2. giá trị biên ----
        // 2a. mọi tổ hợp (a_lane, b_lane) trong tập biên, đặt lên cả 4 lane
        for (i = 0; i < 6; i = i + 1)
            for (j = 0; j < 6; j = j + 1)
                do_dot4({4{bnd[i]}}, {4{bnd[j]}});
        // 2b. quét từng lane: lane 0 chạy hết tập biên, ba lane kia = -128 (xấu nhất)
        for (i = 0; i < 6; i = i + 1)
            for (j = 0; j < 6; j = j + 1) begin
                do_dot4({8'h80, 8'h80, 8'h80, bnd[i]}, {8'h80, 8'h80, 8'h80, bnd[j]});
                do_dot4({bnd[i], 8'h7F, 8'h00, 8'h01}, {bnd[j], 8'h80, 8'hFF, 8'h7F});
            end
        $display("OK 2/3: %0d gia tri bien dung", nchecked);

        // ---- 3. 1.000.000 cặp ngẫu nhiên ----
        sa = 32'h1357_2468;
        sb = 32'h8ACE_1BDF;
        for (k = 0; k < NRAND; k = k + 1) begin
            va = sa;
            vb = sb;
            do_dot4(va, vb);
            sa = lfsr_next(sa);
            sb = lfsr_next(sb);
            if (errors > 20) begin
                $display("Dung som vi qua nhieu loi");
                k = NRAND;
            end
        end

        if (errors == 0)
            $display("F8_TB_PASS: %0d phep DOT4 dung (1.000.000 ngau nhien + bien)", nchecked);
        else
            $display("F8_TB_FAIL: %0d loi tren %0d phep", errors, nchecked);
        $finish;
    end
endmodule
