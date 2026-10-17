#!/usr/bin/env python3
"""So mã máy của từng hàm giữa hai bản firmware (objdump -D).

Dùng để chứng minh: biến thể mới KHÔNG đổi mã của các lớp tính toán, nên số đo của
bản đã kiểm (kit = Verilator, CRC khớp golden) vẫn áp dụng được. So hai mức:

  byte y hệt : chuỗi byte mã máy trùng khít — mạnh nhất, nhưng sẽ khác nếu bố cục
               .bss/.text dịch chỗ (các lệnh lui/addi nạp địa chỉ tuyệt đối).
  lệnh y hệt : trùng mnemonic, thanh ghi và mọi offset THẬT (bước con trỏ), chỉ bỏ
               qua giá trị tức thì mà objdump giải ra được thành địa chỉ ký hiệu.

Giới hạn cần biết: mức thứ hai KHÔNG phát hiện việc một lệnh đổi từ địa chỉ dữ liệu
này sang địa chỉ dữ liệu khác. Nó dùng để trả lời "thuật toán và cách sinh mã có đổi
không", chứ không thay cho phép kiểm CRC trên dữ liệu thật.
"""
import re
import sys

LBL = re.compile(r"^([0-9a-f]+)\s+<([^>]+)>:\s*$")
INS = re.compile(r"^\s*[0-9a-f]+:\s+([0-9a-f ]+?)\s*\t(.*)$")
HEX = re.compile(r"0x[0-9a-f]+")
ADDR = re.compile(r"\b[0-9a-f]{1,8}\s+<")


def norm(text):
    """Bỏ địa chỉ tuyệt đối của dữ liệu/mã, giữ nguyên mnemonic, thanh ghi và các
    offset thật (bước con trỏ). Địa chỉ .bss đổi khi bố cục bộ nhớ đổi — điều đó
    KHÔNG phải thay đổi thuật toán; mọi thứ khác đổi thì phải báo."""
    text = text.strip()
    if "#" in text:
        head, comment = text.split("#", 1)
        if "<" in comment:
            # objdump đã giải giá trị tức thì ra một ký hiệu -> đó là ĐỊA CHỈ.
            # Che giá trị tức thì (cả dạng "...,-1332" và "...,-1332(ra)") rồi BỎ LUÔN
            # phần chú thích: khi giá trị đã bị che, tên ký hiệu objdump đoán ra không
            # còn thông tin nào thêm (cùng một địa chỉ có thể được gán cho ký hiệu
            # khác nếu bố cục .bss đổi).
            head = re.sub(r"-?\d+(?=\(\w+\)\s*$)", "@", head.rstrip())
            head = re.sub(r"-?\d+(?=\s*$)", "@", head.rstrip())
            text = head.rstrip()
        else:
            text = head.rstrip() + " # " + comment.strip()
    text = ADDR.sub("@ <", text)
    return HEX.sub("@", text).strip()


def funcs(path):
    """{tên hàm: (chuỗi byte mã máy, chuỗi disassembly đã chuẩn hoá)}"""
    out, cur = {}, None
    for ln in open(path, errors="replace"):
        m = LBL.match(ln)
        if m:
            cur = m.group(2)
            out[cur] = ([], [])
            continue
        if cur is None:
            continue
        m = INS.match(ln)
        if m:
            out[cur][0].append(m.group(1).replace(" ", ""))
            out[cur][1].append(norm(m.group(2)))
    return {k: ("".join(v[0]), " | ".join(v[1])) for k, v in out.items()}


def main():
    if len(sys.argv) < 4:
        print("dùng: cmp_layers.py A.dis B.dis <tên hàm>...")
        return 2
    a, b = funcs(sys.argv[1]), funcs(sys.argv[2])
    names = sys.argv[3:]
    print(f"{'hàm':<16} {'A byte':>8} {'B byte':>8}  byte y hệt  lệnh y hệt (bỏ địa chỉ)")
    bad = 0
    n_cmp = 0
    for n in names:
        fa, fb = a.get(n), b.get(n)
        if fa is None or fb is None:
            print(f"{n:<16} {'-' if fa is None else len(fa[0])//2:>8} "
                  f"{'-' if fb is None else len(fb[0])//2:>8}  "
                  f"(không có ở một bên — bị nội suy hoặc loại bỏ)")
            continue
        n_cmp += 1
        same_b = fa[0] == fb[0]
        same_n = fa[1] == fb[1]
        if not same_n:
            bad += 1
        print(f"{n:<16} {len(fa[0])//2:>8} {len(fb[0])//2:>8}  "
              f"{'CÓ' if same_b else 'không':>10}  {'CÓ' if same_n else 'KHÁC'}")
    print(f"\n{'CMP_PASS' if bad == 0 else 'CMP_DIFF'} khác={bad}/{n_cmp} hàm so được")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
