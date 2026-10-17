// Harness Verilator cho soc_b (lõi tự viết). Giống F5/F8 nhưng sửa một điểm đã
// phát hiện ở cổng B0: XẢ phần dòng còn dở khi kết thúc. riscv-tests in tên bài
// KHÔNG kèm '\n', nên một bài trap giữa đường sẽ cho log rỗng hoàn toàn nếu
// không xả — rất dễ nhầm là "mất output".
#include "Vsoc_b.h"
#include "verilated.h"
#include <cstdio>
#include <cstring>
#include <string>

int main(int argc, char **argv)
{
    Verilated::commandArgs(argc, argv);

    long max_cycles = 400000000L;
    std::string stop_on = "DONE";
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--max-cycles") && i + 1 < argc)
            max_cycles = atol(argv[++i]);
        else if (!strcmp(argv[i], "--stop-on") && i + 1 < argc)
            stop_on = argv[++i];
    }

    Vsoc_b *dut = new Vsoc_b;
    dut->clk = 0;
    dut->resetn = 0;
    dut->uart_rx = 1;

    std::string line;
    long cycle = 0;
    bool done = false;
    int rc = 0;

    for (; cycle < max_cycles && !done; cycle++) {
        if (cycle == 1024) dut->resetn = 1;
        dut->clk = 0; dut->eval();
        dut->clk = 1; dut->eval();

        if (dut->dbg_tx_valid) {
            char c = (char)dut->dbg_tx_byte;
            if (c == '\n') {
                printf("%s\n", line.c_str());
                fflush(stdout);
                if (line.rfind(stop_on, 0) == 0) done = true;
                line.clear();
            } else if (c != '\r') {
                line.push_back(c);
            }
        }
        if (dut->dbg_trap) {
            fprintf(stderr, "SIM_TRAP: loi o chu ky %ld\n", cycle);
            rc = 2;
            break;
        }
    }

    if (!line.empty()) {                 // xả phần dở (bài kiểm chưa in '\n')
        printf("%s\n", line.c_str());
        fflush(stdout);
    }
    if (rc == 0 && !done) {
        fprintf(stderr, "SIM_TIMEOUT: khong thay %s sau %ld chu ky\n", stop_on.c_str(), cycle);
        rc = 1;
    }
    if (rc == 0) fprintf(stderr, "SIM_OK: xong sau %ld chu ky\n", cycle);
    delete dut;
    return rc;
}
