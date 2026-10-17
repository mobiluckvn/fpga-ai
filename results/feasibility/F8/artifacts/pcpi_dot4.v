// DOT4 — lệnh tùy biến qua PCPI của PicoRV32.
//
//   rd = Σ_{i=0..3} int8(rs1[8i+7:8i]) * int8(rs2[8i+7:8i])     (có dấu, mở rộng dấu lên 32 bit)
//
// Mã lệnh: opcode custom-0 = 0001011, funct3 = 000, funct7 = 0000000.
// Phía C: .insn r 0x0B, 0, 0, rd, rs1, rs2
//
// Giao thức PCPI (theo chính picorv32_pcpi_fast_mul trong rtl/picorv32/picorv32.v):
//   lõi giữ pcpi_valid + pcpi_insn/rs1/rs2; khối phụ trả lời bằng pcpi_wr và pcpi_ready
//   cùng một chu kỳ. pcpi_wait = 0 vì ta luôn trả lời trong 2 chu kỳ (< timeout 16 chu kỳ
//   của lõi). Chốt chống kích lại dùng đúng dạng của fast_mul: !active[1:0].
//
// Phép nhân có HAI đường, chọn bằng cờ biên dịch:
//   PCPI_DOT4_DSP : gọi TRỰC TIẾP primitive MULT18X18 của Gowin, chế độ KHÔNG DẤU
//                   (ASIGN=BSIGN=0), toán hạng int8 mở rộng dấu lên 18 bit, lấy 16 bit
//                   thấp của DOUT đọc như số có dấu. Đây là cách duy nhất ĐÚNG trên kit
//                   theo kết quả F4 — xem docs/LOG.md mục F4.
//   (mặc định)    : phép nhân hành vi `$signed * $signed`, dùng cho mô phỏng
//                   (MULT18X18 là blackbox, không có mô hình mô phỏng) và cho bản build
//                   `-nodsp` nhân bằng logic.
//
// |rd| <= 4 * 128 * 128 = 65.536 nên 18 bit có dấu là đủ (±131.072).

module pcpi_dot4 (
    input  wire        clk,
    input  wire        resetn,

    input  wire        pcpi_valid,
    input  wire [31:0] pcpi_insn,
    input  wire [31:0] pcpi_rs1,
    input  wire [31:0] pcpi_rs2,
    output wire        pcpi_wr,
    output wire [31:0] pcpi_rd,
    output wire        pcpi_wait,
    output wire        pcpi_ready
);
    // ---------------- giải mã ----------------
    wire insn_dot4 = resetn && pcpi_valid
                  && (pcpi_insn[6:0]   == 7'b0001011)   // custom-0
                  && (pcpi_insn[14:12] == 3'b000)
                  && (pcpi_insn[31:25] == 7'b0000000);

    reg [31:0] a_q = 32'd0;
    reg [31:0] b_q = 32'd0;
    reg [1:0]  active = 2'b00;
    reg [31:0] rd_q = 32'd0;

    // ---------------- bốn phép nhân int8 ----------------
`ifdef PCPI_DOT4_DSP
    wire gnd_dsp = 1'b0;
    wire [17:0] dout0, dout1, dout2, dout3;

    MULT18X18 m0 (
        .A({{10{a_q[7]}},  a_q[7:0]}),   .B({{10{b_q[7]}},  b_q[7:0]}),
        .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
        .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
        .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(dout0)
    );
    defparam m0.AREG=1'b0; defparam m0.BREG=1'b0; defparam m0.OUT_REG=1'b0;
    defparam m0.PIPE_REG=1'b0; defparam m0.ASIGN_REG=1'b0; defparam m0.BSIGN_REG=1'b0;
    defparam m0.SOA_REG=1'b0; defparam m0.MULT_RESET_MODE="SYNC";

    MULT18X18 m1 (
        .A({{10{a_q[15]}}, a_q[15:8]}),  .B({{10{b_q[15]}}, b_q[15:8]}),
        .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
        .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
        .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(dout1)
    );
    defparam m1.AREG=1'b0; defparam m1.BREG=1'b0; defparam m1.OUT_REG=1'b0;
    defparam m1.PIPE_REG=1'b0; defparam m1.ASIGN_REG=1'b0; defparam m1.BSIGN_REG=1'b0;
    defparam m1.SOA_REG=1'b0; defparam m1.MULT_RESET_MODE="SYNC";

    MULT18X18 m2 (
        .A({{10{a_q[23]}}, a_q[23:16]}), .B({{10{b_q[23]}}, b_q[23:16]}),
        .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
        .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
        .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(dout2)
    );
    defparam m2.AREG=1'b0; defparam m2.BREG=1'b0; defparam m2.OUT_REG=1'b0;
    defparam m2.PIPE_REG=1'b0; defparam m2.ASIGN_REG=1'b0; defparam m2.BSIGN_REG=1'b0;
    defparam m2.SOA_REG=1'b0; defparam m2.MULT_RESET_MODE="SYNC";

    MULT18X18 m3 (
        .A({{10{a_q[31]}}, a_q[31:24]}), .B({{10{b_q[31]}}, b_q[31:24]}),
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
`else
    wire signed [15:0] p0 = $signed(a_q[7:0])   * $signed(b_q[7:0]);
    wire signed [15:0] p1 = $signed(a_q[15:8])  * $signed(b_q[15:8]);
    wire signed [15:0] p2 = $signed(a_q[23:16]) * $signed(b_q[23:16]);
    wire signed [15:0] p3 = $signed(a_q[31:24]) * $signed(b_q[31:24]);
`endif

    wire signed [17:0] dot = p0 + p1 + p2 + p3;

    // ---------------- bắt tay PCPI ----------------
    always @(posedge clk) begin
        if (insn_dot4 && !active[0] && !active[1]) begin
            a_q       <= pcpi_rs1;
            b_q       <= pcpi_rs2;
            active[0] <= 1'b1;
        end else begin
            active[0] <= 1'b0;
        end

        if (active[0])
            rd_q <= {{14{dot[17]}}, dot};     // mở rộng dấu 18 -> 32 bit

        active[1] <= active[0];

        if (!resetn)
            active <= 2'b00;
    end

    assign pcpi_wr    = active[1];
    assign pcpi_ready = active[1];
    assign pcpi_wait  = 1'b0;
    assign pcpi_rd    = rd_q;
endmodule
