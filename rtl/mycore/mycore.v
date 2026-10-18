// mycore — lõi RISC-V RV32IM tự viết cho nhánh B (xem docs/BRANCH_B_PLAN.md).
//
// MỤC TIÊU: nâng IPC. Nhánh A đo được IPC = 0,160 trên PicoRV32 + bus 2 chu kỳ.
//
// CÁCH LÀM — hai tầng, bộ nhớ MỘT cổng đọc đồng bộ 1 chu kỳ:
//
//   Hợp đồng bộ nhớ: đặt địa chỉ ở chu kỳ n  ->  dữ liệu có ở chu kỳ n+1.
//
//   Trong chu kỳ S_EXEC, lệnh đang nằm trên mem_rdata (nạp từ chu kỳ trước). Lõi
//   giải mã, đọc thanh ghi, tính toán, ghi về, VÀ đặt địa chỉ của lệnh kế tiếp —
//   tất cả trong một chu kỳ. Vì địa chỉ kế tiếp được tính xong trong chính chu kỳ
//   đó, lõi KHÔNG đoán nhánh và KHÔNG có hình phạt rẽ nhánh: nhảy hay không nhảy
//   đều hết đúng 1 chu kỳ.
//
//   Chỉ khi lệnh cần truy cập dữ liệu (load/store) thì cổng bộ nhớ bị chiếm, nên
//   lệnh kế phải nạp ở chu kỳ sau -> load/store hết 2 chu kỳ (S_EXEC + S_MEM).
//   Nhân/chia hết 2 / ~34 chu kỳ (S_MD).
//
//   IPC kỳ vọng = 1 / (1 + tỷ lệ lệnh truy cập bộ nhớ + chi phí nhân/chia).
//   Đây là kỳ vọng thiết kế, số thật lấy từ đo.
//
// PHẠM VI: RV32IM đầy đủ (kể cả div/rem mà firmware không dùng, để qua trọn bộ
// riscv-tests), CSR chỉ đọc cycle/cycleh/instret/instreth, fence và fence.i = nop,
// ecall/ebreak/lệnh lạ/truy cập lệch địa chỉ = trap.
//
// Bộ nhân: mặc định dùng toán tử `*` (mô phỏng, hoặc tổng hợp thành logic LUT).
// Định nghĩa MYCORE_MUL_DSP khi tổng hợp để gọi MULT18X18 TRỰC TIẾP — bài học F4:
// để yosys tự suy luận DSP cho kết quả SAI TRÊN KIT dù mô phỏng vẫn đúng.

`default_nettype none

module mycore #(
    parameter [31:0] RESET_PC    = 32'h0000_0000,
    parameter        WITH_MULDIV = 1,
    // FAST_ADDR=1: địa chỉ bộ nhớ là TỔ HỢP -> 1 chu kỳ/lệnh. Đúng trong mô phỏng,
    //   nhưng KHÔNG CHẠY ĐƯỢC TRÊN KIT: đường "dữ liệu BSRAM -> giải mã -> tệp thanh
    //   ghi -> ALU -> địa chỉ BSRAM" không được nextpnr ràng buộc (xem top_b.v).
    // FAST_ADDR=0: ghi thanh ghi địa chỉ -> mọi đường đều thanh ghi->thanh ghi, chạy
    //   được trên kit, trả giá 1 chu kỳ thêm cho MỖI truy cập bộ nhớ (kể cả nạp lệnh).
    parameter        FAST_ADDR   = 1,
    parameter        WITH_DOT4   = 0,
    parameter        WITH_REQ    = 0,
    // WITH_PMAX4=1: thêm lệnh PMAX4 (ứng viên sinh ra ở bước S5 của pipeline CDP).
    // Mặc định 0 -> lõi giữ nguyên hành vi cũ từng bit, mọi số đo trước vẫn tái lập được.
    parameter        WITH_PMAX4  = 0,
    // DUAL_PORT=1: bộ nhớ hai cổng kiểu Harvard — cổng lệnh riêng (imem_*) và cổng dữ
    //   liệu riêng (mem_*). Nhờ đó ở S_EXEC lõi đặt được ĐỒNG THỜI địa chỉ dữ liệu và
    //   địa chỉ lệnh kế -> load/store hết 1 chu kỳ thay vì 2 (bỏ hẳn trạng thái S_MEM).
    //   Kết quả load về ở chu kỳ SAU, nên cần (a) cổng ghi thứ hai của tệp thanh ghi và
    //   (b) đường CHUYỂN TIẾP cho lệnh ngay sau dùng thanh ghi vừa nạp — 18,3 % số load
    //   trong tải này (results/pipeline/S6/kha_thi_BONHO2CONG.md).
    //   Chỉ dùng với FAST_ADDR=1. Mặc định 0 -> lõi giữ nguyên hành vi cũ từng bit.
    parameter        DUAL_PORT   = 0
) (
    input  wire        clk,
    input  wire        resetn,

    // mem_addr/mem_wstrb/mem_wdata/mem_valid là TỔ HỢP, không qua thanh ghi.
    // Lý do: BSRAM đã có thanh ghi địa chỉ ở đầu vào. Nếu lõi lại thêm một tầng
    // thanh ghi nữa thì địa chỉ ra chậm một chu kỳ -> mỗi lệnh mất 2 chu kỳ
    // (IPC 0,5) và mất hết mục đích của thiết kế này.
    output reg  [31:0] mem_addr,
    output reg  [31:0] mem_wdata,
    output reg  [3:0]  mem_wstrb,
    output reg         mem_valid,
    input  wire [31:0] mem_rdata,

    // Cổng LỆNH, chỉ dùng khi DUAL_PORT=1 (khi =0 thì imem_valid=0 và lệnh vẫn lấy
    // từ mem_rdata như cũ). Cũng là tổ hợp, cùng lý do như mem_addr.
    output reg  [31:0] imem_addr,
    output reg         imem_valid,
    input  wire [31:0] imem_rdata,

    output reg         trap,
    output wire [31:0] dbg_pc,
    output wire [31:0] dbg_instr,
    output wire [2:0]  dbg_state
);
    // ---------------- mã lệnh ----------------
    localparam [6:0] OP_LUI    = 7'b0110111;
    localparam [6:0] OP_AUIPC  = 7'b0010111;
    localparam [6:0] OP_JAL    = 7'b1101111;
    localparam [6:0] OP_JALR   = 7'b1100111;
    localparam [6:0] OP_BRANCH = 7'b1100011;
    localparam [6:0] OP_LOAD   = 7'b0000011;
    localparam [6:0] OP_STORE  = 7'b0100011;
    localparam [6:0] OP_OPIMM  = 7'b0010011;
    localparam [6:0] OP_OP     = 7'b0110011;
    localparam [6:0] OP_MISC   = 7'b0001111;
    localparam [6:0] OP_SYSTEM = 7'b1110011;
    localparam [6:0] OP_CUSTOM = 7'b0001011;

    localparam [2:0] S_FETCH = 3'd0,   // địa chỉ lệnh đang ở đầu vào BSRAM, chờ 1 chu kỳ
                     S_EXEC  = 3'd1,   // giải mã + thực thi + ghi về (+ nạp lệnh kế nếu FAST_ADDR)
                     S_MEM   = 3'd2,   // dữ liệu load đã về / store đã ghi
                     S_MD    = 3'd3,   // nhân / chia nhiều chu kỳ
                     S_MEMW  = 3'd4;   // chỉ khi FAST_ADDR=0: địa chỉ dữ liệu đang ở BSRAM

    reg [2:0]  state;
    // chỉ dùng khi FAST_ADDR=0
    reg [31:0] addr_r;
    reg [31:0] wdata_r;
    reg [3:0]  wstrb_r;
    reg        valid_r;
    reg [31:0] pc;            // địa chỉ lệnh ĐANG thực thi trong S_EXEC
    reg [31:0] pc_ret;        // địa chỉ lệnh kế, giữ lại khi phải qua S_MEM/S_MD

    // ---------------- tệp thanh ghi ----------------
    // Ghi tệp thanh ghi bằng tín hiệu TỔ HỢP, ghi ngay ở sườn kết thúc chu kỳ tính
    // ra kết quả. Nếu dùng thanh ghi trung gian thì kết quả chỉ thấy được sau 2 chu
    // kỳ, còn lệnh kế đã đọc ở chu kỳ sau -> lỗi đọc-sau-ghi.
    reg [31:0] regs [0:31];
    reg        rf_we;
    reg [4:0]  rf_wa;
    reg [31:0] rf_wd;
`ifdef MYCORE_SIM_INIT
    integer ri;
    initial for (ri = 0; ri < 32; ri = ri + 1) regs[ri] = 32'd0;
`endif

    // ---------------- giải mã ----------------
    wire [31:0] instr = (DUAL_PORT != 0) ? imem_rdata : mem_rdata;
    wire [6:0]  opc   = instr[6:0];
    wire [4:0]  rd    = instr[11:7];
    wire [2:0]  f3    = instr[14:12];
    wire [4:0]  rs1   = instr[19:15];
    wire [4:0]  rs2   = instr[24:20];
    wire [6:0]  f7    = instr[31:25];

    wire [31:0] imm_i = {{20{instr[31]}}, instr[31:20]};
    wire [31:0] imm_s = {{20{instr[31]}}, instr[31:25], instr[11:7]};
    wire [31:0] imm_b = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
    wire [31:0] imm_u = {instr[31:12], 12'd0};
    wire [31:0] imm_j = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};

    // ---------------- tách dữ liệu load ----------------
    // Khối này nằm TRƯỚC rv1/rv2 vì đường chuyển tiếp của DUAL_PORT cần ld_val.
    // Nó chỉ phụ thuộc ld_off/ld_f3/mem_rdata nên dời lên không đổi hành vi.
    reg [2:0]  ld_f3;
    reg [1:0]  ld_off;
    reg [4:0]  ld_rd;
    reg        ld_is;
    // ld_pend (chỉ DUAL_PORT=1): chu kỳ NÀY đang có kết quả load chờ ghi về.
    reg        ld_pend;

    reg [7:0]  ld_b;
    reg [15:0] ld_h;
    reg [31:0] ld_val;
    always @(*) begin
        case (ld_off)
            2'd0: ld_b = mem_rdata[7:0];
            2'd1: ld_b = mem_rdata[15:8];
            2'd2: ld_b = mem_rdata[23:16];
            2'd3: ld_b = mem_rdata[31:24];
        endcase
        ld_h = ld_off[1] ? mem_rdata[31:16] : mem_rdata[15:0];
        case (ld_f3)
            3'b000:  ld_val = {{24{ld_b[7]}},  ld_b};      // lb
            3'b001:  ld_val = {{16{ld_h[15]}}, ld_h};      // lh
            3'b100:  ld_val = {24'd0, ld_b};               // lbu
            3'b101:  ld_val = {16'd0, ld_h};               // lhu
            default: ld_val = mem_rdata;                   // lw
        endcase
    end


    // CHUYỂN TIẾP (chỉ DUAL_PORT=1): ở chu kỳ ngay sau một lệnh load, dữ liệu nạp mới
    // nằm trên mem_rdata và CHƯA vào tệp thanh ghi (nó được ghi ở cuối chu kỳ này).
    // Lệnh đang chạy mà đọc đúng thanh ghi đó thì phải lấy giá trị chuyển tiếp, nếu
    // không sẽ đọc giá trị cũ. Không có đường này thì phải chèn một chu kỳ dừng và
    // λ_load không về được 1.
    wire ld_fwd = (DUAL_PORT != 0) && ld_pend && (ld_rd != 5'd0);
    wire [31:0] rv1 = (rs1 == 5'd0) ? 32'd0
                    : (ld_fwd && (ld_rd == rs1)) ? ld_val : regs[rs1];
    wire [31:0] rv2 = (rs2 == 5'd0) ? 32'd0
                    : (ld_fwd && (ld_rd == rs2)) ? ld_val : regs[rs2];

    // ---------------- ALU ----------------
    wire        is_imm = (opc == OP_OPIMM);
    wire [31:0] alu_b  = is_imm ? imm_i : rv2;
    wire [4:0]  shamt  = is_imm ? instr[24:20] : rv2[4:0];
    wire        do_sub = (opc == OP_OP) && f7[5];

    wire [31:0] sum    = do_sub ? (rv1 - alu_b) : (rv1 + alu_b);
    wire        lt_s   = ($signed(rv1) < $signed(alu_b));
    wire        lt_u   = (rv1 < alu_b);
    wire        sra_i  = (opc == OP_OPIMM) ? instr[30] : f7[5];

    reg [31:0] alu_r;
    always @(*) begin
        case (f3)
            3'b000: alu_r = sum;
            3'b001: alu_r = rv1 << shamt;
            3'b010: alu_r = {31'd0, lt_s};
            3'b011: alu_r = {31'd0, lt_u};
            3'b100: alu_r = rv1 ^ alu_b;
            3'b101: alu_r = sra_i ? $signed($signed(rv1) >>> shamt) : (rv1 >> shamt);
            3'b110: alu_r = rv1 | alu_b;
            3'b111: alu_r = rv1 & alu_b;
        endcase
    end

    // ---------------- lệnh tùy biến DOT4 (cổng B4) ----------------
    // Gắn THẲNG vào tầng thực thi, không qua PCPI: toán hạng đọc từ tệp thanh ghi,
    // kết quả ghi về trong CÙNG chu kỳ như một lệnh ALU thường -> **1 chu kỳ**.
    // Trên PicoRV32 cùng lệnh này mất 2 chu kỳ vì phải đi qua giao diện PCPI.
    //
    // Mã hoá giống nhánh A (rtl/ext/pcpi_dot4.v) để **dùng được đúng firmware đó**:
    //   custom-0 (opcode 0001011), funct3 = 000, funct7 = 0000000
    //   rd = sum_{i=0..3} (int8)rs1[i] * (int8)rs2[i]
    //
    // Phép nhân int8 để yosys dựng bằng LOGIC LUT, không gọi DSP: ở F4 đã chứng minh
    // đường LUT ĐÚNG trên kit, còn DSP do yosys tự suy luận thì SAI. Không gọi
    // MULT18X18 trực tiếp ở đây vì nó sẽ thêm độ trễ DSP vào đường tới hạn của tầng
    // thực thi — đường đó đã không được nextpnr ràng buộc (xem docs/KET_QUA_NHANH_B.md).
    wire signed [15:0] dp0 = $signed(rv1[7:0])   * $signed(rv2[7:0]);
    wire signed [15:0] dp1 = $signed(rv1[15:8])  * $signed(rv2[15:8]);
    wire signed [15:0] dp2 = $signed(rv1[23:16]) * $signed(rv2[23:16]);
    wire signed [15:0] dp3 = $signed(rv1[31:24]) * $signed(rv2[31:24]);
    wire signed [17:0] dot = dp0 + dp1 + dp2 + dp3;
    wire [31:0] dot4_val = {{14{dot[17]}}, dot};

    wire is_dot4 = (WITH_DOT4 != 0) && (opc == OP_CUSTOM)
                && (f3 == 3'b000) && (f7 == 7'b0000000);

    // ---------------- lệnh tùy biến PMAX4 (ứng viên bước S5) ----------------
    // Lấy max CÓ DẤU theo 4 làn 8 bit, gắn thẳng tầng thực thi -> **1 chu kỳ**, như DOT4.
    //   custom-0 (0001011), funct3 = 010, funct7 = 0000000
    //   rd[i] = max( (int8)rs1[i], (int8)rs2[i] )  cho i = 0..3
    // Dùng cho max-pooling: activation là channels-last nên 4 kênh liền địa chỉ gói
    // đúng vào một từ 32 bit. Ngữ nghĩa tham chiếu: pipeline/cdp/iss/ext/pmax4.py
    // (một nguồn sự thật duy nhất; RTL phải khớp nó trên vector ngẫu nhiên).
    // Chỉ là so sánh + chọn, không dùng khối nhân, nên không đụng đường tới DSP.
    wire signed [7:0] pm_a0 = rv1[7:0],   pm_b0 = rv2[7:0];
    wire signed [7:0] pm_a1 = rv1[15:8],  pm_b1 = rv2[15:8];
    wire signed [7:0] pm_a2 = rv1[23:16], pm_b2 = rv2[23:16];
    wire signed [7:0] pm_a3 = rv1[31:24], pm_b3 = rv2[31:24];
    wire [31:0] pmax4_val = {
        (pm_a3 > pm_b3) ? rv1[31:24] : rv2[31:24],
        (pm_a2 > pm_b2) ? rv1[23:16] : rv2[23:16],
        (pm_a1 > pm_b1) ? rv1[15:8]  : rv2[15:8],
        (pm_a0 > pm_b0) ? rv1[7:0]   : rv2[7:0]
    };

    wire is_pmax4 = (WITH_PMAX4 != 0) && (opc == OP_CUSTOM)
                 && (f3 == 3'b010) && (f7 == 7'b0000000);

    // ---------------- lệnh tùy biến REQ (cổng B5) ----------------
    // Thay cả hàm requant() kiểu gemmlowp bằng MỘT lệnh:
    //   custom-0, funct3 = 001, funct7 = số bit dịch (hằng số lúc biên dịch)
    //   rd = clamp( RoundingDivideByPOT( SatRoundingDoublingHighMul(ReLU(rs1), rs2),
    //                                    funct7 ), 0, 127 )
    //
    // Dùng LẠI bộ nhân 32x32 của khối nhân/chia (4 x MULT18X18) nên chỉ thêm phần
    // cộng/dịch/so sánh. Đi qua trạng thái S_MD như lệnh `mul` -> **2 chu kỳ**.
    //
    // Vì sao phép nhân KHÔNG DẤU là đủ và vẫn đúng từng bit so với mã C có dấu:
    // ReLU đặt acc >= 0, còn m0 từ quantize_multiplier luôn nằm trong [2^30, 2^31)
    // nên dương. Hai toán hạng không âm -> tích không dấu trùng tích có dấu, và
    // nhánh `nudge` âm cùng trường hợp đặc biệt 0x80000000 không bao giờ chạy tới.
    wire is_req = (WITH_REQ != 0) && (opc == OP_CUSTOM) && (f3 == 3'b001);

    // ---------------- rẽ nhánh ----------------
    reg br_take;
    always @(*) begin
        case (f3)
            3'b000:  br_take = (rv1 == rv2);
            3'b001:  br_take = (rv1 != rv2);
            3'b100:  br_take = lt_s;
            3'b101:  br_take = !lt_s;
            3'b110:  br_take = lt_u;
            3'b111:  br_take = !lt_u;
            default: br_take = 1'b0;
        endcase
    end
    // blt/bge/bltu/bgeu so rv1 với rv2, không với imm — alu_b = rv2 vì opc != OPIMM.

    // ---------------- địa chỉ dữ liệu ----------------
    wire [31:0] ld_addr = rv1 + imm_i;
    wire [31:0] st_addr = rv1 + imm_s;
    wire [31:0] d_addr  = (opc == OP_STORE) ? st_addr : ld_addr;

    wire mis_h = d_addr[0];
    wire mis_w = (d_addr[1:0] != 2'b00);
    wire ld_mis = (f3 == 3'b001 || f3 == 3'b101) ? mis_h :
                  (f3 == 3'b010)                 ? mis_w : 1'b0;
    wire st_mis = (f3 == 3'b001) ? mis_h :
                  (f3 == 3'b010) ? mis_w : 1'b0;

    reg [3:0]  st_strb;
    reg [31:0] st_data;
    always @(*) begin
        case (f3)
            3'b000: begin                                  // sb
                st_strb = 4'b0001 << d_addr[1:0];
                st_data = {4{rv2[7:0]}};
            end
            3'b001: begin                                  // sh
                st_strb = d_addr[1] ? 4'b1100 : 4'b0011;
                st_data = {2{rv2[15:0]}};
            end
            default: begin                                 // sw
                st_strb = 4'b1111;
                st_data = rv2;
            end
        endcase
    end

    // ---------------- bộ đếm CSR ----------------
    reg [63:0] cnt_cycle;
    reg [63:0] cnt_instret;
    reg [31:0] csr_val;
    always @(*) begin
        case (instr[31:20])
            12'hC00: csr_val = cnt_cycle[31:0];
            12'hC80: csr_val = cnt_cycle[63:32];
            12'hC02: csr_val = cnt_instret[31:0];
            12'hC82: csr_val = cnt_instret[63:32];
            default: csr_val = 32'd0;
        endcase
    end
    wire csr_ok = (instr[31:20] == 12'hC00) || (instr[31:20] == 12'hC80)
               || (instr[31:20] == 12'hC02) || (instr[31:20] == 12'hC82);

    // ---------------- nhân / chia ----------------
    reg [31:0] md_a, md_b;
    reg [2:0]  md_f3;
    reg [4:0]  md_rd;
    reg [5:0]  md_cnt;
    reg        md_is_div;

    // Nhân 32x32 -> 64 không dấu, rồi chỉnh dấu. Một bộ nhân không dấu phục vụ
    // cả mul/mulh/mulhsu/mulhu:
    //   signed(a)*signed(b)   = u - (a31 ? b<<32 : 0) - (b31 ? a<<32 : 0)
    //   signed(a)*unsigned(b) = u - (a31 ? b<<32 : 0)
    wire [63:0] prod_u;
    // Phải dùng `ifdef TIỀN XỬ LÝ, không dùng generate: Verilator vẫn phân tích nhánh
    // generate không được chọn, và MULT18X18 là blackbox không có mô hình mô phỏng
    // -> lỗi "missing module". F8 đã gặp đúng chuyện này.
`ifdef MYCORE_MUL_DSP
            // Bốn phép nhân 16x16 KHÔNG DẤU ghép thành 32x32 -> 64:
            //   a*b = al*bl + (al*bh + ah*bl)<<16 + ah*bh<<32
            // Gọi MULT18X18 TRỰC TIẾP ở chế độ không dấu (ASIGN=BSIGN=0), toán hạng
            // 16 bit mở rộng 0 lên 18 bit. Đây là cách duy nhất ĐÚNG TRÊN KIT theo
            // kết quả F4: để yosys tự suy luận DSP cho kết quả SAI trên kit dù mô
            // phỏng vẫn đúng (xem docs/LOG.md mục F4).
            wire gnd_dsp = 1'b0;
            wire [35:0] d00, d01, d10, d11;

            MULT18X18 m00 (
                .A({2'b00, md_a[15:0]}), .B({2'b00, md_b[15:0]}),
                .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
                .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
                .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(d00)
            );
            defparam m00.AREG=1'b0; defparam m00.BREG=1'b0; defparam m00.OUT_REG=1'b0;
            defparam m00.PIPE_REG=1'b0; defparam m00.ASIGN_REG=1'b0; defparam m00.BSIGN_REG=1'b0;
            defparam m00.SOA_REG=1'b0; defparam m00.MULT_RESET_MODE="SYNC";

            MULT18X18 m01 (
                .A({2'b00, md_a[15:0]}), .B({2'b00, md_b[31:16]}),
                .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
                .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
                .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(d01)
            );
            defparam m01.AREG=1'b0; defparam m01.BREG=1'b0; defparam m01.OUT_REG=1'b0;
            defparam m01.PIPE_REG=1'b0; defparam m01.ASIGN_REG=1'b0; defparam m01.BSIGN_REG=1'b0;
            defparam m01.SOA_REG=1'b0; defparam m01.MULT_RESET_MODE="SYNC";

            MULT18X18 m10 (
                .A({2'b00, md_a[31:16]}), .B({2'b00, md_b[15:0]}),
                .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
                .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
                .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(d10)
            );
            defparam m10.AREG=1'b0; defparam m10.BREG=1'b0; defparam m10.OUT_REG=1'b0;
            defparam m10.PIPE_REG=1'b0; defparam m10.ASIGN_REG=1'b0; defparam m10.BSIGN_REG=1'b0;
            defparam m10.SOA_REG=1'b0; defparam m10.MULT_RESET_MODE="SYNC";

            MULT18X18 m11 (
                .A({2'b00, md_a[31:16]}), .B({2'b00, md_b[31:16]}),
                .SIA({18{gnd_dsp}}), .SIB({18{gnd_dsp}}),
                .ASIGN(gnd_dsp), .BSIGN(gnd_dsp), .ASEL(gnd_dsp), .BSEL(gnd_dsp),
                .CE(1'b1), .CLK(clk), .RESET(gnd_dsp), .SOA(), .SOB(), .DOUT(d11)
            );
            defparam m11.AREG=1'b0; defparam m11.BREG=1'b0; defparam m11.OUT_REG=1'b0;
            defparam m11.PIPE_REG=1'b0; defparam m11.ASIGN_REG=1'b0; defparam m11.BSIGN_REG=1'b0;
            defparam m11.SOA_REG=1'b0; defparam m11.MULT_RESET_MODE="SYNC";

            wire [63:0] t00 = {32'd0, d00[31:0]};
            wire [63:0] t01 = {16'd0, d01[31:0], 16'd0};
            wire [63:0] t10 = {16'd0, d10[31:0], 16'd0};
            wire [63:0] t11 = {d11[31:0], 32'd0};
            assign prod_u = t00 + t01 + t10 + t11;
`else
    // Mô phỏng, và bản tổng hợp nhân bằng logic LUT.
    assign prod_u = md_a * md_b;
`endif

    wire need_ca = (md_f3 == 3'b001 || md_f3 == 3'b010) && md_a[31];   // mulh, mulhsu
    wire need_cb = (md_f3 == 3'b001)                    && md_b[31];   // mulh
    wire [63:0] prod_s = prod_u - (need_ca ? {md_b, 32'd0} : 64'd0)
                                - (need_cb ? {md_a, 32'd0} : 64'd0);

    // Chia dịch-trừ 32 bước trên trị tuyệt đối.
    reg [31:0] dvd, dvs, quo, rmd;
    reg        q_neg, r_neg;
    wire [32:0] rmd_sh  = {rmd, dvd[31]};
    wire        rmd_ge  = (rmd_sh >= {1'b0, dvs});
    wire [32:0] rmd_sub = rmd_sh - {1'b0, dvs};

    wire        div_signed   = (md_f3 == 3'b100) || (md_f3 == 3'b110);  // div, rem (đã chốt)
    wire        div_signed_d = (f3    == 3'b100) || (f3    == 3'b110);  // div, rem (đang giải mã)
    wire [31:0] quo_fin = q_neg ? (~quo + 32'd1) : quo;
    wire [31:0] rmd_fin = r_neg ? (~rmd + 32'd1) : rmd;

    // REQ: (ab + 2^30) >> 31, rồi chia-làm-tròn theo luỹ thừa 2, rồi kẹp [0,127]
    reg  [4:0]  req_sh;
    reg         md_is_req;
    wire [63:0] req_t64  = prod_u + 64'h0000_0000_4000_0000;
    wire [31:0] req_t    = req_t64[62:31];
    wire [31:0] req_mask = (32'd1 << req_sh) - 32'd1;
    wire [31:0] req_rem  = req_t & req_mask;
    wire [31:0] req_thr  = req_mask >> 1;
    wire [31:0] req_q    = (req_t >> req_sh) + ((req_rem > req_thr) ? 32'd1 : 32'd0);
    wire [31:0] req_val  = (req_q > 32'd127) ? 32'd127 : req_q;

    reg [31:0] md_res;
    always @(*) begin
      if (md_is_req) md_res = req_val;
      else
        case (md_f3)
            3'b000:  md_res = prod_u[31:0];                 // mul
            3'b001:  md_res = prod_s[63:32];                // mulh
            3'b010:  md_res = prod_s[63:32];                // mulhsu
            3'b011:  md_res = prod_u[63:32];                // mulhu
            3'b100:  md_res = quo_fin;                      // div
            3'b101:  md_res = quo;                          // divu
            3'b110:  md_res = rmd_fin;                      // rem
            default: md_res = rmd;                          // remu
        endcase
    end

    // ---------------- phân loại lệnh ----------------
    wire is_muldiv = ((opc == OP_OP) && (f7 == 7'b0000001) && (WITH_MULDIV != 0))
                  || is_req;
    wire is_csr    = (opc == OP_SYSTEM) && (f3 != 3'b000);
    wire is_sys0   = (opc == OP_SYSTEM) && (f3 == 3'b000);   // ecall / ebreak / mret...

    reg illegal;
    always @(*) begin
        case (opc)
            OP_LUI, OP_AUIPC, OP_JAL, OP_BRANCH, OP_STORE: illegal = 1'b0;
            OP_JALR:   illegal = (f3 != 3'b000);
            OP_LOAD:   illegal = (f3 == 3'b011) || (f3 == 3'b110) || (f3 == 3'b111);
            OP_OPIMM:  illegal = 1'b0;
            OP_OP:     illegal = !((f7 == 7'b0000000) ||
                                   (f7 == 7'b0100000 && (f3 == 3'b000 || f3 == 3'b101)) ||
                                   (f7 == 7'b0000001 && (WITH_MULDIV != 0)));
            OP_MISC:   illegal = 1'b0;                       // fence, fence.i = nop
            OP_SYSTEM: illegal = is_csr ? !csr_ok : 1'b0;
            OP_CUSTOM: illegal = !(is_dot4 || is_req || is_pmax4);
            default:   illegal = 1'b1;
        endcase
    end

    // ---------------- địa chỉ lệnh kế ----------------
    reg [31:0] next_pc;
    always @(*) begin
        case (opc)
            OP_JAL:    next_pc = pc + imm_j;
            OP_JALR:   next_pc = (rv1 + imm_i) & ~32'd1;
            OP_BRANCH: next_pc = br_take ? (pc + imm_b) : (pc + 32'd4);
            default:   next_pc = pc + 32'd4;
        endcase
    end

    // ---------------- giá trị ghi về trong S_EXEC ----------------
    reg [31:0] wb_val;
    reg        wb_en;
    always @(*) begin
        wb_en  = 1'b0;
        wb_val = 32'd0;
        case (opc)
            OP_LUI:         begin wb_en = 1'b1; wb_val = imm_u; end
            OP_AUIPC:       begin wb_en = 1'b1; wb_val = pc + imm_u; end
            OP_JAL, OP_JALR:begin wb_en = 1'b1; wb_val = pc + 32'd4; end
            OP_OPIMM:       begin wb_en = 1'b1; wb_val = alu_r; end
            OP_OP:          begin wb_en = 1'b1; wb_val = alu_r; end
            OP_SYSTEM:      begin wb_en = is_csr; wb_val = csr_val; end
            OP_CUSTOM:      begin
                                wb_en  = is_dot4 || is_pmax4;
                                wb_val = is_pmax4 ? pmax4_val : dot4_val;
                            end
                            /* REQ đi qua S_MD, không ghi về ở đây */
            default:        begin wb_en = 1'b0; end
        endcase
    end

    wire acc_data = (opc == OP_LOAD) || (opc == OP_STORE);
    wire mis      = (opc == OP_LOAD) ? ld_mis : st_mis;
    wire bad      = illegal || is_sys0 || (acc_data && mis);

    assign dbg_pc    = pc;
    assign dbg_instr = instr;
    assign dbg_state = state;

    // ---------------- cổng bộ nhớ (tổ hợp) ----------------
    always @(*) begin
      if (FAST_ADDR == 0) begin
        mem_addr  = addr_r;
        mem_wdata = wdata_r;
        mem_wstrb = wstrb_r;
        mem_valid = valid_r && !trap;
      end else begin
        mem_addr  = pc;
        mem_wdata = 32'd0;
        mem_wstrb = 4'b0000;
        mem_valid = 1'b0;
        if (!trap) begin
            case (state)
                S_FETCH: if (DUAL_PORT == 0) begin
                    mem_addr  = pc;
                    mem_valid = 1'b1;
                end
                S_EXEC: begin
                    if (bad) begin
                        mem_valid = 1'b0;                  // sắp trap: không truy cập
                    end else if (acc_data) begin
                        mem_addr  = {d_addr[31:2], 2'b00};
                        mem_wdata = st_data;
                        mem_wstrb = (opc == OP_STORE) ? st_strb : 4'b0000;
                        mem_valid = 1'b1;
                    end else if (!is_muldiv && DUAL_PORT == 0) begin
                        mem_addr  = next_pc;               // nạp lệnh kế NGAY chu kỳ này
                        mem_valid = 1'b1;
                    end
                end
                S_MEM: if (DUAL_PORT == 0) begin
                    mem_addr  = pc_ret;
                    mem_valid = 1'b1;
                end
                S_MD: if (md_cnt == 6'd0 && DUAL_PORT == 0) begin
                    mem_addr  = pc_ret;
                    mem_valid = 1'b1;
                end
                default: ;
            endcase
        end
      end
    end

    // ---------------- cổng LỆNH (tổ hợp, chỉ DUAL_PORT=1) ----------------
    // Điểm then chốt của ứng viên này: ở S_EXEC, kể cả khi lệnh là load/store (cổng dữ
    // liệu đang bị chiếm), cổng lệnh vẫn đặt được địa chỉ lệnh kế -> không mất chu kỳ.
    always @(*) begin
        imem_addr  = pc;
        imem_valid = 1'b0;
        if ((DUAL_PORT != 0) && !trap) begin
            case (state)
                S_FETCH: begin
                    imem_addr  = pc;
                    imem_valid = 1'b1;
                end
                S_EXEC: if (!bad && !is_muldiv) begin
                    // Đúng ở CẢ hai trường hợp: lệnh thường VÀ lệnh load/store.
                    imem_addr  = next_pc;
                    imem_valid = 1'b1;
                end
                S_MD: if (md_cnt == 6'd0) begin
                    imem_addr  = pc_ret;
                    imem_valid = 1'b1;
                end
                default: ;
            endcase
        end
    end

    // ---------------- ghi tệp thanh ghi (tổ hợp) ----------------
    always @(*) begin
        rf_we = 1'b0;
        rf_wa = 5'd0;
        rf_wd = 32'd0;
        case (state)
            S_EXEC: if (!bad && !acc_data && !is_muldiv && wb_en && rd != 5'd0) begin
                rf_we = 1'b1; rf_wa = rd;    rf_wd = wb_val;
            end
            S_MEM: if (ld_is && ld_rd != 5'd0) begin
                rf_we = 1'b1; rf_wa = ld_rd; rf_wd = ld_val;
            end
            S_MD: if (md_cnt == 6'd0 && md_rd != 5'd0) begin
                rf_we = 1'b1; rf_wa = md_rd; rf_wd = md_res;
            end
            default: ;
        endcase
    end

    // ---------------- máy trạng thái ----------------
    always @(posedge clk) begin
        if (!resetn) begin
            state       <= S_FETCH;
            pc          <= RESET_PC;
            trap        <= 1'b0;
            cnt_cycle   <= 64'd0;
            cnt_instret <= 64'd0;
            ld_is       <= 1'b0;
            ld_pend     <= 1'b0;
            md_cnt      <= 6'd0;
            md_is_req   <= 1'b0;
            addr_r      <= RESET_PC;
            wstrb_r     <= 4'b0000;
            wdata_r     <= 32'd0;
            valid_r     <= 1'b1;
        end else if (!trap) begin
            cnt_cycle <= cnt_cycle + 64'd1;

            case (state)
                S_FETCH: begin
                    ld_pend <= 1'b0;
                    state   <= S_EXEC;
                end

                S_EXEC: begin
                    if (bad) begin
                        trap    <= 1'b1;
                        ld_pend <= 1'b0;
                    end else if (acc_data) begin
                        ld_is  <= (opc == OP_LOAD);
                        ld_f3  <= f3;
                        ld_off <= d_addr[1:0];
                        ld_rd  <= rd;
                        pc_ret <= next_pc;
                        if (FAST_ADDR == 0) begin
                            addr_r  <= {d_addr[31:2], 2'b00};
                            wdata_r <= st_data;
                            wstrb_r <= (opc == OP_STORE) ? st_strb : 4'b0000;
                            valid_r <= 1'b1;
                            state   <= S_MEMW;
                        end else if (DUAL_PORT != 0) begin
                            // MỘT chu kỳ: lệnh kế đã được nạp qua cổng lệnh ngay chu kỳ
                            // này, nên không cần S_MEM. Kết quả load ghi về ở chu kỳ sau
                            // qua cổng ghi 2, và chuyển tiếp lo cho lệnh dùng ngay.
                            ld_pend     <= (opc == OP_LOAD);
                            pc          <= next_pc;
                            cnt_instret <= cnt_instret + 64'd1;
                            state       <= S_EXEC;
                        end else begin
                            state   <= S_MEM;
                        end
                    end else if (is_muldiv) begin
                        ld_pend <= 1'b0;
                        md_a   <= is_req ? (rv1[31] ? 32'd0 : rv1) : rv1;  /* ReLU trong REQ */
                        md_b   <= rv2;
                        md_f3  <= f3;
                        md_rd  <= rd;
                        md_is_req <= is_req;
                        md_is_div <= is_req ? 1'b0 : f3[2];
                        req_sh <= f7[4:0];
                        pc_ret <= next_pc;
                        if (!is_req && f3[2]) begin
                            // chia: 32 bước dịch-trừ trên trị tuyệt đối
                            q_neg <= (f3 == 3'b100) && (rv1[31] ^ rv2[31]) && (rv2 != 32'd0);
                            r_neg <= (f3 == 3'b110) && rv1[31];
                            dvs   <= (div_signed_d && rv2[31]) ? (~rv2 + 32'd1) : rv2;
                            quo   <= 32'd0;
                            rmd   <= 32'd0;
                            if (rv2 == 32'd0) begin
                                // Đặc tả RISC-V: chia 0 -> thương toàn 1, dư = số bị chia
                                dvd    <= 32'd0;
                                quo    <= 32'hFFFF_FFFF;
                                rmd    <= (div_signed_d && rv1[31]) ? (~rv1 + 32'd1) : rv1;
                                md_cnt <= 6'd0;
                            end else begin
                                dvd    <= (div_signed_d && rv1[31]) ? (~rv1 + 32'd1) : rv1;
                                md_cnt <= 6'd32;
                            end
                        end else begin
                            md_cnt <= 6'd0;                // nhân / REQ: kết quả có ngay ở S_MD
                        end
                        state <= S_MD;
                    end else begin
                        ld_pend     <= 1'b0;
                        pc          <= next_pc;
                        cnt_instret <= cnt_instret + 64'd1;
                        if (FAST_ADDR == 0) begin
                            addr_r  <= next_pc;
                            wstrb_r <= 4'b0000;
                            valid_r <= 1'b1;
                            state   <= S_FETCH;
                        end else begin
                            state   <= S_EXEC;
                        end
                    end
                end

                // chỉ FAST_ADDR=0: địa chỉ dữ liệu đang ở đầu vào BSRAM
                S_MEMW: begin
                    wstrb_r <= 4'b0000;          // ghi chỉ kéo dài một chu kỳ
                    state   <= S_MEM;
                end

                S_MEM: begin
                    ld_is       <= 1'b0;
                    ld_pend     <= 1'b0;
                    pc          <= pc_ret;
                    cnt_instret <= cnt_instret + 64'd1;
                    if (FAST_ADDR == 0) begin
                        addr_r  <= pc_ret;
                        wstrb_r <= 4'b0000;
                        valid_r <= 1'b1;
                        state   <= S_FETCH;
                    end else begin
                        state   <= S_EXEC;
                    end
                end

                S_MD: begin
                    ld_pend <= 1'b0;
                    if (md_cnt != 6'd0) begin
                        if (md_is_div) begin
                            rmd <= rmd_ge ? rmd_sub[31:0] : rmd_sh[31:0];
                            dvd <= dvd << 1;
                            quo <= {quo[30:0], rmd_ge};
                        end
                        md_cnt <= md_cnt - 6'd1;
                    end else begin
                        pc          <= pc_ret;
                        cnt_instret <= cnt_instret + 64'd1;
                        if (FAST_ADDR == 0) begin
                            addr_r  <= pc_ret;
                            wstrb_r <= 4'b0000;
                            valid_r <= 1'b1;
                            state   <= S_FETCH;
                        end else begin
                            state   <= S_EXEC;
                        end
                    end
                end
                default: state <= S_FETCH;
            endcase
        end
    end

    // Cổng ghi THỨ HAI (chỉ DUAL_PORT=1): kết quả load về ở chu kỳ sau, đúng lúc lệnh
    // kế cũng có thể đang ghi thanh ghi của nó -> cần hai cổng ghi.
    wire        rf2_we = (DUAL_PORT != 0) && ld_pend && (ld_rd != 5'd0);
    wire [4:0]  rf2_wa = ld_rd;
    wire [31:0] rf2_wd = ld_val;

    always @(posedge clk) begin
        if (resetn) begin
            // Cổng 2 ghi TRƯỚC, cổng 1 ghi SAU: nếu hai cổng trùng thanh ghi thì giá trị
            // của cổng 1 (lệnh đang chạy) phải thắng, vì kết quả load là của lệnh CŨ hơn.
            if (rf2_we) regs[rf2_wa] <= rf2_wd;
            if (rf_we)  regs[rf_wa]  <= rf_wd;
        end
    end

endmodule

`default_nettype wire
