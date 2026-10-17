// F8 — module bọc: SoC của F5 với WITH_DOT4 = 1 (bật PCPI ngoài + khối pcpi_dot4).
// Dùng cho cả Verilator (top-module soc_f8) và cho bitstream (qua top_f8.v).
module soc_f8 #(
    parameter integer DIV       = 234,
    parameter integer WITH_REQ  = 0,
    parameter         HEXFILE   = "firmware.hex"
) (
    input  wire        clk,
    input  wire        resetn,
    output wire        uart_tx,
    input  wire        uart_rx,
    output wire [5:0]  led,
    output wire        dbg_tx_valid,
    output wire [7:0]  dbg_tx_byte,
    output wire        dbg_trap
);
    soc #(.DIV(DIV), .HEXFILE(HEXFILE), .WITH_DOT4(1), .WITH_REQ(WITH_REQ)) u_soc (
        .clk(clk), .resetn(resetn),
        .uart_tx(uart_tx), .uart_rx(uart_rx), .led(led),
        .dbg_tx_valid(dbg_tx_valid), .dbg_tx_byte(dbg_tx_byte), .dbg_trap(dbg_trap)
    );
endmodule
