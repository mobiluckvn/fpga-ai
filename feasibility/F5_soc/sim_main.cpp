// F5 — harness Verilator cho SoC.
//
// Nạp cùng firmware.hex mà kit dùng, chạy tới khi thấy dòng "F5,done" (hoặc hết
// giới hạn chu kỳ), in mọi byte UART ra stdout theo tín hiệu dbg_tx_valid.
//
// Vì khối uart_tx THẬT vẫn được dùng, tx_busy diễn ra y như trên kit, nên số chu kỳ
// mà firmware đo được (rdcycle, bộ đếm phần cứng) giống hệt phần cứng.
//
// Dùng: Vsoc [--max-cycles N] [--stop-on "F5,done"]
#include "Vsoc.h"
#include "verilated.h"
#include <cstdio>
#include <cstring>
#include <string>

int main(int argc, char **argv)
{
    Verilated::commandArgs(argc, argv);

    long max_cycles = 200000000L;
    std::string stop_on = "F5,done";
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--max-cycles") && i + 1 < argc)
            max_cycles = atol(argv[++i]);
        else if (!strcmp(argv[i], "--stop-on") && i + 1 < argc)
            stop_on = argv[++i];
    }

    Vsoc *dut = new Vsoc;
    dut->clk = 0;
    dut->resetn = 0;
    dut->uart_rx = 1;

    std::string line;
    long cycle = 0;
    bool done = false;
    int done_seen = 0;

    for (; cycle < max_cycles && !done; cycle++) {
        if (cycle == 1024)
            dut->resetn = 1;

        dut->clk = 0;
        dut->eval();
        dut->clk = 1;
        dut->eval();

        if (dut->dbg_tx_valid) {
            char c = (char)dut->dbg_tx_byte;
            if (c == '\n') {
                printf("%s\n", line.c_str());
                fflush(stdout);
                if (line.rfind(stop_on, 0) == 0) {
                    if (++done_seen >= 1)
                        done = true;
                }
                line.clear();
            } else if (c != '\r') {
                line.push_back(c);
            }
        }

        if (dut->dbg_trap) {
            fprintf(stderr, "SIM_TRAP: loi o chu ky %ld\n", cycle);
            delete dut;
            return 2;
        }
    }

    if (!done) {
        fprintf(stderr, "SIM_TIMEOUT: khong thay %s sau %ld chu ky\n", stop_on.c_str(), cycle);
        delete dut;
        return 1;
    }
    fprintf(stderr, "SIM_OK: xong sau %ld chu ky\n", cycle);
    delete dut;
    return 0;
}
