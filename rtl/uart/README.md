# Khối UART dùng chung

`uart_tx.v`, `uart_rx.v` là **bản đã kiểm chứng ở cổng F2** (10.240 byte echo không sai byte nào
trên kit thật, bộ đếm trong FPGA xác nhận dr=0 er=0 ov=0).

Nguồn gốc: `feasibility/F2_uart/uart_tx.v` và `uart_rx.v`, sao sang đây **không sửa gì** để các cổng
sau (F3, F5–F8) dùng lại cùng một khối, tránh phân nhánh. `feasibility/F2_uart/` giữ nguyên bản của nó
làm hồ sơ của cổng F2 (quy tắc "mỗi cổng một thư mục tự chứa" trong CLAUDE.md).

Kiểm tra hai bản còn giống nhau:

    shasum -a 256 rtl/uart/uart_tx.v feasibility/F2_uart/uart_tx.v
    shasum -a 256 rtl/uart/uart_rx.v feasibility/F2_uart/uart_rx.v
