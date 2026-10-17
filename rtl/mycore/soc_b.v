// soc_b — SoC cho lõi tự viết (nhánh B).
//
// Bản đồ bộ nhớ GIỐNG HỆT feasibility/F5_soc/soc.v để chạy được CHÍNH các file
// firmware.hex của nhánh A, không biên dịch lại:
//   0x0000_0000 .. 0x0000_FFFF  RAM 64 KB (BSRAM, nạp bằng $readmemh)
//   0x1000_0000                 UART data   (ghi = gửi byte; đọc = byte nhận, xoá rx_valid)
//   0x1000_0004                 UART status (bit0 = tx_busy, bit1 = rx_valid)
//   0x1000_0010                 bộ đếm phần cứng: ghi 1 = xoá và chạy, ghi 0 = dừng
//   0x1000_0014                 giá trị bộ đếm (chỉ đọc)
//   0x1000_0020                 LED (6 bit thấp; phần cứng đảo cho LED tích cực mức thấp)
//
// KHÁC soc.v ở ĐÚNG MỘT ĐIỂM, và đó là điểm chính của nhánh B:
//   soc.v   — bus 2 chu kỳ mỗi truy cập (S_IDLE -> S_WAIT), kể cả nạp lệnh.
//   soc_b.v — 1 chu kỳ: địa chỉ trình ra ở chu kỳ n, dữ liệu có ở chu kỳ n+1.
// Nhờ vậy khi so B-V0 với A-V0 trên CÙNG file hex, chênh lệch là thuần vi kiến trúc.

`default_nettype none

module soc_b #(
    parameter integer DIV     = 234,              // 27e6/115200
    parameter         HEXFILE = "firmware.hex",
    parameter integer FAST_ADDR = 1,
    // BEACON=1: SoC tự phát trạng thái lõi qua UART mỗi ~0,3 s, ĐỘC LẬP với lõi.
    // Dùng để chẩn đoán "kit không phát byte nào": nếu thấy đèn hiệu thì xung nhịp,
    // UART và bitstream đều tốt, và vấn đề nằm ở lõi; nếu không thấy gì thì ngược lại.
    // Khung: 'S' <state> <'T' nếu trap, '.' nếu không> <8 hex PC> '\n'
    parameter integer BEACON    = 0,
    parameter         WITH_DOT4 = 0
) (
    input  wire        clk,
    input  wire        resetn,
    output wire        uart_tx,
    input  wire        uart_rx,
    output wire [5:0]  led,
    output reg         dbg_tx_valid,
    output reg  [7:0]  dbg_tx_byte,
    output wire        dbg_trap
);
    function [7:0] hexc;
        input [3:0] n;
        hexc = (n < 4'd10) ? (8'd48 + {4'd0, n}) : (8'd87 + {4'd0, n});
    endfunction

    // ---------------- lõi ----------------
    wire [31:0] mem_addr, mem_wdata;
    wire [3:0]  mem_wstrb;
    wire        mem_valid;
    reg  [31:0] mem_rdata;

    mycore #(
        .RESET_PC(32'h0000_0000),
        .WITH_MULDIV(1),
        .FAST_ADDR(FAST_ADDR),
        .WITH_DOT4(WITH_DOT4)
    ) u_core (
        .clk(clk), .resetn(resetn),
        .mem_addr(mem_addr), .mem_wdata(mem_wdata), .mem_wstrb(mem_wstrb),
        .mem_valid(mem_valid), .mem_rdata(mem_rdata),
        .trap(dbg_trap), .dbg_pc(core_pc), .dbg_instr(), .dbg_state(core_state)
    );
    wire [31:0] core_pc;
    wire [2:0]  core_state;

    wire sel_ram = (mem_addr[31:28] == 4'h0);
    wire sel_per = (mem_addr[31:28] == 4'h1);
    wire is_write = (mem_wstrb != 4'b0000);

    // ---------------- RAM 64 KB ----------------
    reg [31:0] ram [0:16383];
    wire [13:0] ram_addr = mem_addr[15:2];
    reg  [31:0] ram_q;
    initial $readmemh(HEXFILE, ram);

    // ---------------- UART ----------------
    reg  [7:0] tx_byte;
    reg        tx_start;
    wire       tx_busy;
    uart_tx #(.DIV(DIV)) u_tx (
        .clk(clk), .data(tx_byte), .start(tx_start), .busy(tx_busy), .tx(uart_tx)
    );

    wire [7:0] rx_data;
    wire       rx_valid;
    wire [7:0] rx_err;
    uart_rx #(.DIV(DIV)) u_rx (
        .clk(clk), .rx(uart_rx), .data(rx_data), .valid(rx_valid), .err_cnt(rx_err)
    );
    reg [7:0] rx_hold = 8'd0;
    reg       rx_full = 1'b0;

    // ---------------- đèn hiệu chẩn đoán ----------------
    reg [22:0] bcn_div = 23'd0;
    reg [3:0]  bcn_i   = 4'd0;
    reg        bcn_run = 1'b0;
    reg [7:0]  bcn_ch;
    always @(*) begin
        case (bcn_i)
            4'd0:  bcn_ch = "S";
            4'd1:  bcn_ch = 8'd48 + {5'd0, core_state};
            4'd2:  bcn_ch = dbg_trap ? "T" : ".";
            4'd3:  bcn_ch = hexc(core_pc[31:28]);
            4'd4:  bcn_ch = hexc(core_pc[27:24]);
            4'd5:  bcn_ch = hexc(core_pc[23:20]);
            4'd6:  bcn_ch = hexc(core_pc[19:16]);
            4'd7:  bcn_ch = hexc(core_pc[15:12]);
            4'd8:  bcn_ch = hexc(core_pc[11:8]);
            4'd9:  bcn_ch = hexc(core_pc[7:4]);
            4'd10: bcn_ch = hexc(core_pc[3:0]);
            4'd11: bcn_ch = 8'h0A;
            default: bcn_ch = "?";
        endcase
    end

    // ---------------- bộ đếm phần cứng, LED ----------------
    reg [31:0] hw_cnt = 32'd0;
    reg        hw_run = 1'b0;
    reg [5:0]  led_r  = 6'd0;
    assign led = ~led_r;

    // ---------------- đọc ngoại vi (tổ hợp) ----------------
    reg [31:0] per_rdata;
    always @(*) begin
        case (mem_addr[7:0])
            8'h00:   per_rdata = {24'd0, rx_hold};
            8'h04:   per_rdata = {30'd0, rx_full, tx_busy};
            8'h14:   per_rdata = hw_cnt;
            8'h20:   per_rdata = {26'd0, led_r};
            default: per_rdata = 32'd0;
        endcase
    end

    reg        sel_ram_q;
    reg [31:0] per_q;
    always @(*) mem_rdata = sel_ram_q ? ram_q : per_q;

    // ---------------- một chu kỳ mỗi truy cập ----------------
    always @(posedge clk) begin
        // đọc đồng bộ: địa chỉ ở chu kỳ n -> dữ liệu ở chu kỳ n+1
        ram_q     <= ram[ram_addr];
        per_q     <= per_rdata;
        sel_ram_q <= sel_ram;

        // ghi RAM theo byte
        if (mem_valid && sel_ram && is_write) begin
            if (mem_wstrb[0]) ram[ram_addr][ 7: 0] <= mem_wdata[ 7: 0];
            if (mem_wstrb[1]) ram[ram_addr][15: 8] <= mem_wdata[15: 8];
            if (mem_wstrb[2]) ram[ram_addr][23:16] <= mem_wdata[23:16];
            if (mem_wstrb[3]) ram[ram_addr][31:24] <= mem_wdata[31:24];
        end

        // UART thu
        if (rx_valid) begin
            rx_hold <= rx_data;
            rx_full <= 1'b1;
        end

        if (hw_run) hw_cnt <= hw_cnt + 32'd1;

        tx_start     <= 1'b0;
        dbg_tx_valid <= 1'b0;
        if (mem_valid && sel_per && is_write) begin
            case (mem_addr[7:0])
                8'h00: begin
                    tx_byte      <= mem_wdata[7:0];
                    tx_start     <= 1'b1;
                    dbg_tx_byte  <= mem_wdata[7:0];
                    dbg_tx_valid <= 1'b1;
                end
                8'h10: begin
                    hw_run <= mem_wdata[0];
                    if (mem_wdata[0]) hw_cnt <= 32'd0;
                end
                8'h20: led_r <= mem_wdata[5:0];
                default: ;
            endcase
        end

        // đèn hiệu: chỉ phát khi lõi không đang gửi và UART rỗi
        if (BEACON != 0) begin
            bcn_div <= bcn_div + 23'd1;
            if (bcn_div == 23'd0 && !bcn_run) begin
                bcn_run <= 1'b1;
                bcn_i   <= 4'd0;
            end else if (bcn_run && !tx_busy && !tx_start
                         && !(mem_valid && sel_per && is_write)) begin
                tx_byte  <= bcn_ch;
                tx_start <= 1'b1;
                if (bcn_i == 4'd11) bcn_run <= 1'b0;
                else                bcn_i   <= bcn_i + 4'd1;
            end
        end

        // đọc UART data thì xoá rx_valid
        if (mem_valid && sel_per && !is_write && (mem_addr[7:0] == 8'h00))
            rx_full <= 1'b0;

        if (!resetn) begin
            hw_run    <= 1'b0;
            hw_cnt    <= 32'd0;
            rx_full   <= 1'b0;
            led_r     <= 6'd0;
            sel_ram_q <= 1'b1;
        end
    end
endmodule

`default_nettype wire
