// top_b — vỏ cho kit Tang Nano 20K, lõi tự viết (nhánh B).
//
// CLKDIV: chia xung nhịp thạch anh 27 MHz. Lý do tồn tại tham số này là một phát
// hiện ở cổng B3: nextpnr-himbaechel KHÔNG ràng buộc đường tới đầu vào BSRAM —
// `grep -c "Sink u_soc.ram\."` trong nextpnr.log cho **0** ở cả nhánh A và B. Nhánh A
// không bị ảnh hưởng vì mem_addr của PicoRV32 là THANH GHI, nên đường vào địa chỉ
// BSRAM chỉ là ff -> BSRAM. Lõi này đặt cả giải mã + đọc tệp thanh ghi + ALU lên
// đường đó (đó chính là cách đạt 1 chu kỳ/lệnh), nên con số Fmax mà nextpnr báo
// KHÔNG nói gì về đường tới hạn thật.
//   CLKDIV=1 -> 27,00 MHz, DIV_UART=234
//   CLKDIV=2 -> 13,50 MHz, DIV_UART=117
//   CLKDIV=4 ->  6,75 MHz, DIV_UART=59
// Số chu kỳ KHÔNG đổi theo CLKDIV (lõi chỉ thấy xung nhịp của nó), nên phép so
// "kit = Verilator" vẫn đúng từng chu kỳ; chỉ thời gian theo ms đổi.
module top #(
    parameter integer DIV_UART  = 234,
    parameter         HEXFILE   = "firmware.hex",
    parameter integer FAST_ADDR = 1,
    parameter integer WITH_DOT4 = 0,
    parameter integer WITH_REQ  = 0,
    parameter integer WITH_PMAX4 = 0,
    parameter integer BEACON    = 0
) (
    input  wire       clk,
    output wire       uart_tx,
    input  wire       uart_rx,
    output wire [5:0] led
);
    // KHÔNG đặt net trung gian cho xung nhịp. Bài học ở cổng B3: khi viết
    // `wire clk_sys = clk;` thì yosys đổi tên net xung nhịp, IBUF thành
    // `clk_sys_IBUF_O` thay vì mang tên cổng `clk`, nên ràng buộc IO_LOC "clk" 4 và
    // CLOCK_LOC "clk" BUFG trong file .cst KHÔNG khớp cell nào -> xung nhịp bị gán
    // vào chân bất kỳ và cả thiết kế im lặng hoàn toàn. Nối cổng clk TRỰC TIẾP.

    reg [10:0] rst_c  = 11'd0;
    reg        resetn = 1'b0;
    always @(posedge clk) begin
        if (rst_c == 11'd1023) resetn <= 1'b1;
        else                   rst_c  <= rst_c + 11'd1;
    end

    soc_b #(.DIV(DIV_UART), .HEXFILE(HEXFILE), .FAST_ADDR(FAST_ADDR), .WITH_DOT4(WITH_DOT4), .WITH_REQ(WITH_REQ), .WITH_PMAX4(WITH_PMAX4), .BEACON(BEACON)) u_soc (
        .clk(clk), .resetn(resetn),
        .uart_tx(uart_tx), .uart_rx(uart_rx), .led(led),
        .dbg_tx_valid(), .dbg_tx_byte(), .dbg_trap()
    );
endmodule
