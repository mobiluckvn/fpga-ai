// F8 — harness Verilator cho SoC có DOT4 (WITH_DOT4 = 1 qua top_f8.v).
// Giống ../F5_soc/sim_main.cpp nhưng instantiate module bọc có WITH_DOT4=1.
#include "Vsoc_f8.h"
#include "verilated.h"
#include <cstdio>
#include <cstring>
#include <string>

int main(int argc, char **argv)
{
    Verilated::commandArgs(argc, argv);

    long max_cycles = 400000000L;
    std::string stop_on = "F8,done";
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--max-cycles") && i + 1 < argc)
            max_cycles = atol(argv[++i]);
        else if (!strcmp(argv[i], "--stop-on") && i + 1 < argc)
            stop_on = argv[++i];
    }

    Vsoc_f8 *dut = new Vsoc_f8;
    dut->clk = 0;
    dut->resetn = 0;
    dut->uart_rx = 1;

    std::string line;
    long cycle = 0;
    bool done = false;

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
                if (line.rfind(stop_on, 0) == 0)
                    done = true;
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
