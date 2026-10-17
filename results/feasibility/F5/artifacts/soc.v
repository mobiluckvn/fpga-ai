// F5 — SoC PicoRV32 + RAM 64 KB (BSRAM) + UART + bộ đếm phần cứng + LED.
//
// Bản đồ bộ nhớ (theo docs/FEASIBILITY_PLAN.md):
//   0x0000_0000 .. 0x0000_FFFF  RAM 64 KB, nạp firmware bằng $readmemh
//   0x1000_0000                 UART data   (ghi = gửi byte; đọc = byte nhận, xoá rx_valid)
//   0x1000_0004                 UART status (bit0 = tx_busy, bit1 = rx_valid)
//   0x1000_0010                 bộ đếm phần cứng: ghi 1 = xoá và chạy, ghi 0 = dừng
//   0x1000_0014                 giá trị bộ đếm (chỉ đọc)
//   0x1000_0020                 LED (6 bit thấp; 1 = sáng, phần cứng đảo cho LED tích cực mức thấp)
//
// Mỗi truy cập bộ nhớ mất ĐÚNG 2 chu kỳ (1 chu kỳ chờ) cho cả RAM và ngoại vi,
// nên số chu kỳ là tất định và giống nhau giữa Verilator và kit.
//
// dbg_tx_valid/dbg_tx_byte: chỉ dùng cho Verilator (in UART ra stdout ngay), không
// ảnh hưởng tới phần cứng và KHÔNG thay đổi số chu kỳ: khối uart_tx thật vẫn được
// dùng ở cả hai môi trường nên tx_busy diễn ra y như nhau.

module soc #(
    parameter integer DIV        = 234,              // 27e6/115200
    parameter integer RAM_WORDS  = 16384,            // 64 KB
    parameter         HEXFILE    = "firmware.hex"
) (
    input  wire        clk,
    input  wire        resetn,
    output wire        uart_tx,
    input  wire        uart_rx,
    output wire [5:0]  led,
    // chỉ cho mô phỏng
    output reg         dbg_tx_valid,
    output reg  [7:0]  dbg_tx_byte,
    output wire        dbg_trap
);
    localparam integer AW = $clog2(RAM_WORDS);

    // ---------------- lõi ----------------
    wire        mem_valid;
    wire        mem_instr;
    reg         mem_ready;
    wire [31:0] mem_addr;
    wire [31:0] mem_wdata;
    wire [3:0]  mem_wstrb;
    reg  [31:0] mem_rdata;
    wire        trap;

    assign dbg_trap = trap;

    picorv32 #(
        .ENABLE_COUNTERS   (1),
        .ENABLE_COUNTERS64 (1),
        .ENABLE_REGS_16_31 (1),
        .ENABLE_REGS_DUALPORT (1),
        .BARREL_SHIFTER    (1),
        .COMPRESSED_ISA    (0),
        .ENABLE_MUL        (0),
        .ENABLE_FAST_MUL   (1),
        .ENABLE_DIV        (1),
        .ENABLE_IRQ        (0),
        .ENABLE_PCPI       (0),     // F8 mới bật
        .PROGADDR_RESET    (32'h0000_0000),
        .STACKADDR         (32'h0001_0000)   // đỉnh RAM; start.S cũng đặt lại sp
    ) cpu (
        .clk       (clk),
        .resetn    (resetn),
        .trap      (trap),
        .mem_valid (mem_valid),
        .mem_instr (mem_instr),
        .mem_ready (mem_ready),
        .mem_addr  (mem_addr),
        .mem_wdata (mem_wdata),
        .mem_wstrb (mem_wstrb),
        .mem_rdata (mem_rdata),
        .mem_la_read (), .mem_la_write (), .mem_la_addr (),
        .mem_la_wdata (), .mem_la_wstrb (),
        .pcpi_valid(), .pcpi_insn(), .pcpi_rs1(), .pcpi_rs2(),
        .pcpi_wr(1'b0), .pcpi_rd(32'd0), .pcpi_wait(1'b0), .pcpi_ready(1'b0),
        .irq(32'd0), .eoi(),
        .trace_valid(), .trace_data()
    );

    // ---------------- giải mã ----------------
    wire sel_ram = (mem_addr[31:28] == 4'h0);
    wire sel_per = (mem_addr[31:28] == 4'h1);

    // ---------------- RAM 64 KB ----------------
    reg [31:0]    ram [0:RAM_WORDS-1];
    reg [31:0]    ram_q = 32'd0;
    wire [AW-1:0] ram_addr = mem_addr[AW+1:2];

    initial begin
        $readmemh(HEXFILE, ram);
    end

    // ---------------- UART ----------------
    reg  [7:0] tx_byte  = 8'd0;
    reg        tx_start = 1'b0;
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

    reg [7:0] rx_hold   = 8'd0;
    reg       rx_full   = 1'b0;

    // ---------------- bộ đếm phần cứng ----------------
    reg [31:0] hw_cnt = 32'd0;
    reg        hw_run = 1'b0;

    // ---------------- LED ----------------
    reg [5:0] led_r = 6'd0;
    assign led = ~led_r;          // tích cực mức thấp

    // ---------------- dữ liệu đọc từ ngoại vi ----------------
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

    // ---------------- bus: 2 chu kỳ mỗi truy cập ----------------
    localparam [0:0] S_IDLE = 1'b0, S_WAIT = 1'b1;
    reg state = S_IDLE;

    wire acc_start = (state == S_IDLE) && mem_valid && !mem_ready;
    wire is_write  = (mem_wstrb != 4'b0000);
    wire ram_we    = acc_start && sel_ram && is_write;
    wire per_we    = acc_start && sel_per && is_write;

    always @(posedge clk) begin
        // --- RAM: ghi theo byte, đọc đồng bộ ---
        if (ram_we) begin
            if (mem_wstrb[0]) ram[ram_addr][ 7: 0] <= mem_wdata[ 7: 0];
            if (mem_wstrb[1]) ram[ram_addr][15: 8] <= mem_wdata[15: 8];
            if (mem_wstrb[2]) ram[ram_addr][23:16] <= mem_wdata[23:16];
            if (mem_wstrb[3]) ram[ram_addr][31:24] <= mem_wdata[31:24];
        end
        ram_q <= ram[ram_addr];

        // --- UART thu ---
        if (rx_valid) begin
            rx_hold <= rx_data;
            rx_full <= 1'b1;
        end

        // --- bộ đếm phần cứng ---
        if (hw_run) hw_cnt <= hw_cnt + 32'd1;

        // --- ngoại vi: ghi ---
        tx_start     <= 1'b0;
        dbg_tx_valid <= 1'b0;
        if (per_we) begin
            case (mem_addr[7:0])
                8'h00: begin
                    tx_byte      <= mem_wdata[7:0];
                    tx_start     <= 1'b1;
                    dbg_tx_byte  <= mem_wdata[7:0];
                    dbg_tx_valid <= 1'b1;
                end
                8'h10: begin
                    hw_run <= mem_wdata[0];
                    if (mem_wdata[0]) hw_cnt <= 32'd0;   // ghi 1 = xoá và chạy
                end
                8'h20: led_r <= mem_wdata[5:0];
                default: ;
            endcase
        end
        // --- ngoại vi: đọc UART data thì xoá rx_valid ---
        if (acc_start && sel_per && !is_write && (mem_addr[7:0] == 8'h00))
            rx_full <= 1'b0;

        // --- máy trạng thái bus ---
        mem_ready <= 1'b0;
        case (state)
            S_IDLE: if (mem_valid && !mem_ready) state <= S_WAIT;
            S_WAIT: begin
                mem_rdata <= sel_ram ? ram_q : per_rdata;
                mem_ready <= 1'b1;
                state     <= S_IDLE;
            end
        endcase

        if (!resetn) begin
            state     <= S_IDLE;
            mem_ready <= 1'b0;
            hw_run    <= 1'b0;
            hw_cnt    <= 32'd0;
            rx_full   <= 1'b0;
            led_r     <= 6'd0;
            tx_start  <= 1'b0;
            dbg_tx_valid <= 1'b0;
        end
    end

    initial begin
        dbg_tx_valid = 1'b0;
        dbg_tx_byte  = 8'd0;
    end
endmodule
