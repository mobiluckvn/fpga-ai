// F4 — kiểm chứng khối nhân: tích vô hướng 4 phần tử int8 mỗi chu kỳ, cộng dồn 2^20 chu kỳ.
//
// RTL này dùng CHUNG cho hai biến thể; khác nhau duy nhất ở cách build:
//   DSP:  yosys synth_gowin           -> phép nhân được ánh xạ vào khối MULT của Gowin
//   LUT:  yosys synth_gowin -nodsp    -> phép nhân bị cấm ánh xạ DSP, phải dựng bằng logic
// (nhãn in ra UART chọn bằng `-DLABEL_LUT`, chỉ đổi 3 ký tự của dòng log.)
//
// Mỗi chu kỳ: a, b lấy từ hai LFSR 32 bit (cùng đa thức với F3), dùng giá trị TRƯỚC khi bước.
//   dot = Σ_{i=0..3} $signed(a[8i+7:8i]) * $signed(b[8i+7:8i])
//   acc <= acc + dot        (32 bit, tràn thì quấn — Python tính cùng cách)
// Xong thì cứ 1 giây in: F4,<DSP|LUT>,<acc 8 hex>\r\n
//
// LED (tích cực mức thấp): led[0] nhịp tim, led[1] đã xong, led[5] acc khác hằng số kỳ vọng.

module top #(
    parameter integer DIV     = 234,
    parameter integer MSG_DIV = 27_000_000,
    parameter integer HB_DIV  = 13_500_000,
    parameter integer LOGN    = 20,                  // số chu kỳ = 2^LOGN
    parameter [31:0]  SEED_A  = 32'h12345678,
    parameter [31:0]  SEED_B  = 32'h9ABCDEF0,
    parameter [31:0]  ACC_EXPECT = 32'hFEF834C3
) (
    input  wire       clk,
    output wire       uart_tx,
    output wire [5:0] led
);
    // ---------------- hai LFSR ----------------
    reg [31:0] a = SEED_A;
    reg [31:0] b = SEED_B;

    wire a_fb = a[31] ^ a[21] ^ a[1] ^ a[0];
    wire b_fb = b[31] ^ b[21] ^ b[1] ^ b[0];

    // ---------------- tích vô hướng 4 x int8 ----------------
`ifdef PRIM_MULT
    // Hướng sửa 2 cho biến thể DSP: gọi TRỰC TIẾP primitive MULT18X18 của Gowin,
    // ở chế độ KHÔNG DẤU (ASIGN=BSIGN=0), toán hạng int8 đã mở rộng dấu lên 18 bit.
    //
    // Vì sao cách này đúng mà không cần tới cờ dấu của khối DSP:
    //   gọi x' = x mod 2^18, y' = y mod 2^18 (giá trị không dấu của toán hạng mở rộng dấu).
    //   x'y' = xy + 2^18*(...) + 2^36*(...)  =>  x'y' ≡ xy  (mod 2^18)
    //   mà |xy| <= 128*128 = 16384 < 2^17, nên DOUT[17:0] đọc như số có dấu 18 bit
    //   chính là xy. Tức ta chỉ dựa vào 18 bit thấp, không dựa vào đường ASIGN/BSIGN.
    //
    // Giao diện primitive lấy từ YosysHQ/apicula examples/dsp-mult18x18.v (ví dụ mà
    // Apicula tự kiểm thử trên kit thật: đích hil-dsp-mult18x18-tangnano20k).
    // AREG/BREG/OUT_REG/PIPE_REG = 0 => tổ hợp, dùng được tích ngay trong cùng chu kỳ.
    wire gnd_dsp = 1'b0;

    wire [17:0] dout0, dout1, dout2, dout3;

    MULT18X18 m0 (
        .A({{10{a[7]}},  a[7:0]}),   .B({{10{b[7]}},  b[7:0]}),
        .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
        .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
        .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(dout0)
    );
    defparam m0.AREG=1'b0; defparam m0.BREG=1'b0; defparam m0.OUT_REG=1'b0;
    defparam m0.PIPE_REG=1'b0; defparam m0.ASIGN_REG=1'b0; defparam m0.BSIGN_REG=1'b0;
    defparam m0.SOA_REG=1'b0; defparam m0.MULT_RESET_MODE="SYNC";

    MULT18X18 m1 (
        .A({{10{a[15]}}, a[15:8]}),  .B({{10{b[15]}}, b[15:8]}),
        .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
        .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
        .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(dout1)
    );
    defparam m1.AREG=1'b0; defparam m1.BREG=1'b0; defparam m1.OUT_REG=1'b0;
    defparam m1.PIPE_REG=1'b0; defparam m1.ASIGN_REG=1'b0; defparam m1.BSIGN_REG=1'b0;
    defparam m1.SOA_REG=1'b0; defparam m1.MULT_RESET_MODE="SYNC";

    MULT18X18 m2 (
        .A({{10{a[23]}}, a[23:16]}), .B({{10{b[23]}}, b[23:16]}),
        .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
        .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
        .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(dout2)
    );
    defparam m2.AREG=1'b0; defparam m2.BREG=1'b0; defparam m2.OUT_REG=1'b0;
    defparam m2.PIPE_REG=1'b0; defparam m2.ASIGN_REG=1'b0; defparam m2.BSIGN_REG=1'b0;
    defparam m2.SOA_REG=1'b0; defparam m2.MULT_RESET_MODE="SYNC";

    MULT18X18 m3 (
        .A({{10{a[31]}}, a[31:24]}), .B({{10{b[31]}}, b[31:24]}),
        .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
        .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
        .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(dout3)
    );
    defparam m3.AREG=1'b0; defparam m3.BREG=1'b0; defparam m3.OUT_REG=1'b0;
    defparam m3.PIPE_REG=1'b0; defparam m3.ASIGN_REG=1'b0; defparam m3.BSIGN_REG=1'b0;
    defparam m3.SOA_REG=1'b0; defparam m3.MULT_RESET_MODE="SYNC";

    wire signed [15:0] p0 = dout0[15:0];
    wire signed [15:0] p1 = dout1[15:0];
    wire signed [15:0] p2 = dout2[15:0];
    wire signed [15:0] p3 = dout3[15:0];
`elsif WIDE_MULT
    // Hướng sửa cho biến thể DSP: mở rộng dấu toán hạng lên 18 bit để yosys ánh xạ
    // vào MULT18X18 thay vì MULT9X9 (MULT9X9 cho kết quả sai byte cao trên kit).
    wire signed [17:0] aw0 = {{10{a[7]}},  a[7:0]};
    wire signed [17:0] aw1 = {{10{a[15]}}, a[15:8]};
    wire signed [17:0] aw2 = {{10{a[23]}}, a[23:16]};
    wire signed [17:0] aw3 = {{10{a[31]}}, a[31:24]};
    wire signed [17:0] bw0 = {{10{b[7]}},  b[7:0]};
    wire signed [17:0] bw1 = {{10{b[15]}}, b[15:8]};
    wire signed [17:0] bw2 = {{10{b[23]}}, b[23:16]};
    wire signed [17:0] bw3 = {{10{b[31]}}, b[31:24]};
    wire signed [35:0] q0 = aw0 * bw0;
    wire signed [35:0] q1 = aw1 * bw1;
    wire signed [35:0] q2 = aw2 * bw2;
    wire signed [35:0] q3 = aw3 * bw3;
    wire signed [15:0] p0 = q0[15:0];
    wire signed [15:0] p1 = q1[15:0];
    wire signed [15:0] p2 = q2[15:0];
    wire signed [15:0] p3 = q3[15:0];
`else
    wire signed [15:0] p0 = $signed(a[7:0])   * $signed(b[7:0]);
    wire signed [15:0] p1 = $signed(a[15:8])  * $signed(b[15:8]);
    wire signed [15:0] p2 = $signed(a[23:16]) * $signed(b[23:16]);
    wire signed [15:0] p3 = $signed(a[31:24]) * $signed(b[31:24]);
`endif
    wire signed [17:0] dot = p0 + p1 + p2 + p3;

    reg [31:0]      acc  = 32'd0;
    reg [LOGN:0]    cnt  = {(LOGN+1){1'b0}};
    reg             done = 1'b0;

    // Chốt 4 giá trị dot đầu tiên (đã mở rộng dấu 32 bit) để chẩn đoán:
    // Python biết chính xác bốn giá trị này nên so được ngay.
    reg [31:0] d0 = 32'd0, d1 = 32'd0, d2 = 32'd0, d3 = 32'd0;
    wire [31:0] dot32 = {{(32-18){dot[17]}}, dot};

    // Chốt RIÊNG từng tích ở chu kỳ 0 để biết lane nào sai và sai thế nào.
    reg [31:0] pc0 = 32'd0, pc1 = 32'd0, pc2 = 32'd0, pc3 = 32'd0;

    always @(posedge clk) begin
        if (!done) begin
            if (cnt == 0) begin
                pc0 <= {{16{p0[15]}}, p0};
                pc1 <= {{16{p1[15]}}, p1};
                pc2 <= {{16{p2[15]}}, p2};
                pc3 <= {{16{p3[15]}}, p3};
            end
            if      (cnt == 0) d0 <= dot32;
            else if (cnt == 1) d1 <= dot32;
            else if (cnt == 2) d2 <= dot32;
            else if (cnt == 3) d3 <= dot32;
            acc <= acc + dot32;
            a   <= {a[30:0], a_fb};
            b   <= {b[30:0], b_fb};
            if (cnt == {1'b0, {LOGN{1'b1}}}) done <= 1'b1;   // đã chạy 2^LOGN chu kỳ
            else                             cnt  <= cnt + 1'b1;
        end
    end

    // ---------------- UART phát ----------------
    reg  [7:0] tx_byte  = 8'd0;
    reg        tx_start = 1'b0;
    wire       tx_busy;

    uart_tx #(.DIV(DIV)) u_tx (
        .clk(clk), .data(tx_byte), .start(tx_start),
        .busy(tx_busy), .tx(uart_tx)
    );

    // ---------------- khuôn dòng "F4,XXX,hhhhhhhh\r\n" = 17 byte ----------------
    localparam integer LINELEN = 17;

`ifdef LABEL_LUT
    localparam [23:0] LABEL = {"L", "U", "T"};
`elsif LABEL_D18
    localparam [23:0] LABEL = {"D", "1", "8"};
`elsif LABEL_PRM
    localparam [23:0] LABEL = {"P", "R", "M"};
`else
    localparam [23:0] LABEL = {"D", "S", "P"};
`endif

    function [7:0] hexdig;
        input [3:0] v;
        begin
            hexdig = (v < 4'd10) ? (8'h30 + v) : (8'h41 + v - 4'd10);
        end
    endfunction

    // Bảy dòng, cùng khuôn 17 byte "F4,TTT,hhhhhhhh\r\n":
    //   <LABEL> = acc (dòng theo đúng kế hoạch)
    //   AEN/BEN = trạng thái LFSR a/b khi kết thúc
    //   D00..D03 = bốn giá trị dot đầu tiên, đã mở rộng dấu 32 bit
    localparam integer NLINE = 8;

    function [23:0] line_tag;
        input [2:0] i;
        begin
            case (i)
                3'd0: line_tag = LABEL;
                3'd1: line_tag = {"A", "E", "N"};
                3'd2: line_tag = {"B", "E", "N"};
                3'd3: line_tag = {"D", "0", "0"};
                3'd4: line_tag = {"P", "0", "0"};
                3'd5: line_tag = {"P", "0", "1"};
                3'd6: line_tag = {"P", "0", "2"};
                default: line_tag = {"P", "0", "3"};
            endcase
        end
    endfunction

    function [31:0] line_val;
        input [2:0] i;
        begin
            case (i)
                3'd0: line_val = acc;
                3'd1: line_val = a;
                3'd2: line_val = b;
                3'd3: line_val = d0;
                3'd4: line_val = pc0;
                3'd5: line_val = pc1;
                3'd6: line_val = pc2;
                default: line_val = pc3;
            endcase
        end
    endfunction

    function [7:0] line_char;
        input [2:0] ln;
        input [4:0] i;
        reg [23:0] tg;
        reg [31:0] vl;
        begin
            tg = line_tag(ln);
            vl = line_val(ln);
            case (i)
                5'd0:  line_char = "F";
                5'd1:  line_char = "4";
                5'd2:  line_char = ",";
                5'd3:  line_char = tg[23:16];
                5'd4:  line_char = tg[15:8];
                5'd5:  line_char = tg[7:0];
                5'd6:  line_char = ",";
                5'd7:  line_char = hexdig(vl[31:28]);
                5'd8:  line_char = hexdig(vl[27:24]);
                5'd9:  line_char = hexdig(vl[23:20]);
                5'd10: line_char = hexdig(vl[19:16]);
                5'd11: line_char = hexdig(vl[15:12]);
                5'd12: line_char = hexdig(vl[11:8]);
                5'd13: line_char = hexdig(vl[7:4]);
                5'd14: line_char = hexdig(vl[3:0]);
                5'd15: line_char = 8'h0D;
                default: line_char = 8'h0A;
            endcase
        end
    endfunction

    // ---------------- hẹn giờ in ----------------
    reg [$clog2(MSG_DIV)-1:0] msg_c    = {($clog2(MSG_DIV)){1'b0}};
    reg                       msg_tick = 1'b0;
    always @(posedge clk) begin
        msg_tick <= 1'b0;
        if (msg_c == MSG_DIV[$clog2(MSG_DIV)-1:0] - 1'b1) begin
            msg_c    <= {($clog2(MSG_DIV)){1'b0}};
            msg_tick <= 1'b1;
        end else begin
            msg_c <= msg_c + 1'b1;
        end
    end

    reg       want = 1'b0;
    reg       sending = 1'b0;
    reg [4:0] msg_idx = 5'd0;
    reg [2:0] line_no = 3'd0;

    always @(posedge clk) begin
        tx_start <= 1'b0;
        if (msg_tick && done) want <= 1'b1;

        if (!sending) begin
            if (want) begin
                want    <= 1'b0;
                msg_idx <= 5'd0;
                line_no <= 3'd0;
                sending <= 1'b1;
            end
        end else if (!tx_busy && !tx_start) begin
            tx_byte  <= line_char(line_no, msg_idx);
            tx_start <= 1'b1;
            if (msg_idx == LINELEN - 1) begin
                msg_idx <= 5'd0;
                if (line_no == NLINE - 1) begin
                    line_no <= 3'd0;
                    sending <= 1'b0;
                end else begin
                    line_no <= line_no + 3'd1;
                end
            end else begin
                msg_idx <= msg_idx + 5'd1;
            end
        end
    end

    // ---------------- LED ----------------
    reg [$clog2(HB_DIV)-1:0] hb_c = {($clog2(HB_DIV)){1'b0}};
    reg                      hb   = 1'b0;
    always @(posedge clk) begin
        if (hb_c == HB_DIV[$clog2(HB_DIV)-1:0] - 1'b1) begin
            hb_c <= {($clog2(HB_DIV)){1'b0}};
            hb   <= ~hb;
        end else begin
            hb_c <= hb_c + 1'b1;
        end
    end

    wire bad = done && (acc != ACC_EXPECT);
    assign led = ~{bad, 3'b000, done, hb};
endmodule
