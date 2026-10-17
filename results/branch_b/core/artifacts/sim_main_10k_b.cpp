// Bản cho lõi nhánh B (soc_b). Chép từ experiment/m1s/sim_main_10k.cpp.
// Harness Verilator cho chế độ STREAM_10K: ngoài việc đọc UART phát ra, nó còn
// BƠM ảnh vào chân uart_rx bằng cách tạo dạng sóng 8N1 ở đúng DIV=234 như kit thật.
// Nhờ vậy giao thức (byte đồng bộ 0xA5 + 784 byte) được kiểm trong mô phỏng trước
// khi tổng hợp bitstream, và CRC ảnh do kit báo đối chiếu được ngay.
//
// Dùng: ./Vsoc_10k --imgs imgs.bin --n 3 [--max-cycles N]
#include "Vsoc_b.h"
#include "verilated.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

static const int DIVB = 234;        // chu kỳ mỗi bit (27e6/115200)
static const int IMG_BYTES = 784;
static const unsigned char SYNC = 0xA5;

int main(int argc, char **argv)
{
    Verilated::commandArgs(argc, argv);

    long max_cycles = 2000000000L;
    const char *imgs_path = "imgs.bin";
    int n_want = 3;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--max-cycles") && i + 1 < argc) max_cycles = atol(argv[++i]);
        else if (!strcmp(argv[i], "--imgs") && i + 1 < argc)  imgs_path = argv[++i];
        else if (!strcmp(argv[i], "--n") && i + 1 < argc)     n_want = atoi(argv[++i]);
    }

    FILE *f = fopen(imgs_path, "rb");
    if (!f) { fprintf(stderr, "SIM_LOI: khong mo duoc %s\n", imgs_path); return 2; }
    std::vector<unsigned char> imgs;
    imgs.resize((size_t)IMG_BYTES * (size_t)n_want);
    size_t got = fread(imgs.data(), 1, imgs.size(), f);
    fclose(f);
    if (got != imgs.size()) {
        fprintf(stderr, "SIM_LOI: %s chi co %zu byte, can %zu\n", imgs_path, got, imgs.size());
        return 2;
    }

    Vsoc_b *dut = new Vsoc_b;
    dut->clk = 0;
    dut->resetn = 0;
    dut->uart_rx = 1;

    std::string line;
    long cycle = 0;
    int n_sent = 0, n_resp = 0;
    // Chỉ được gửi khi kit đang CHỜ. Lúc mới reset kit còn đang phát dòng hello;
    // thanh ghi thu chỉ giữ ĐƯỢC MỘT byte (không có FIFO) nên byte nào đến trong lúc
    // đó cũng bị byte sau ghi đè -> mất. Vì vậy chờ hết một dòng đã phát ra thì mới gửi.
    bool kit_ready = false;

    // trạng thái bơm một khung: -1 = chưa gửi gì / đợi phản hồi
    int frame_byte = -1;          // chỉ số byte trong khung (0 = SYNC, 1..784 = pixel)
    int bit_idx = 0, bit_cnt = 0; // bit đang phát và số chu kỳ còn lại của bit đó
    unsigned char cur = 0;
    bool sending = false;

    for (; cycle < max_cycles; cycle++) {
        if (cycle == 1024) dut->resetn = 1;

        // ---- bơm uart_rx ----
        if (sending) {
            if (bit_cnt == 0) {
                if (bit_idx == 0)       dut->uart_rx = 0;                  // start
                else if (bit_idx <= 8)  dut->uart_rx = (cur >> (bit_idx - 1)) & 1; // LSB first
                else                    dut->uart_rx = 1;                  // stop
                bit_cnt = DIVB;
            }
            bit_cnt--;
            if (bit_cnt == 0) {
                bit_idx++;
                if (bit_idx > 9) {      // xong 1 byte
                    bit_idx = 0;
                    frame_byte++;
                    if (frame_byte > IMG_BYTES) {   // xong cả khung
                        sending = false;
                        n_sent++;
                    } else {
                        cur = imgs[(size_t)(n_sent) * IMG_BYTES + (size_t)(frame_byte - 1)];
                    }
                }
            }
        } else if (kit_ready && n_sent == n_resp && n_sent < n_want) {
            // bắt đầu khung mới: byte đồng bộ trước
            sending = true;
            frame_byte = 0;
            bit_idx = 0;
            bit_cnt = 0;
            cur = SYNC;
        }

        dut->clk = 0; dut->eval();
        dut->clk = 1; dut->eval();

        if ((cycle % 1000000) == 0 && cycle > 0)
            fprintf(stderr, "  [sim] %ld M chu ky · da gui %d khung · da nhan %d phan hoi\n",
                    cycle / 1000000, n_sent, n_resp);

        if (dut->dbg_tx_valid) {
            char c = (char)dut->dbg_tx_byte;
            if (c == '\n') {
                printf("%s\n", line.c_str());
                fflush(stdout);
                kit_ready = true;
                if (line.rfind("M1S10K,", 0) == 0 && line.rfind("M1S10K,hello", 0) != 0)
                    n_resp++;
                line.clear();
                if (n_resp == n_want) { delete dut; fprintf(stderr, "SIM_OK: %d anh sau %ld chu ky\n", n_resp, cycle); return 0; }
            } else if (c != '\r') {
                line.push_back(c);
            }
        }
        if (dut->dbg_trap) {
            fprintf(stderr, "SIM_TRAP: loi o chu ky %ld\n", cycle);
            delete dut; return 2;
        }
    }
    fprintf(stderr, "SIM_TIMEOUT: chi nhan %d/%d phan hoi sau %ld chu ky\n", n_resp, n_want, cycle);
    delete dut;
    return 1;
}
