# Câu lệnh dán vào Claude Code (chạy trong thư mục tinyml-riscv-tn20k)

## Phiên đầu tiên
```
Đọc CLAUDE.md, docs/FEASIBILITY_PLAN.md và docs/FEASIBILITY_REPORT.md. Mục tiêu phiên này là kiểm chứng
tính khả thi trên phần cứng thật, bắt đầu từ cổng F0. Làm đúng từng cổng theo thứ tự, tuân thủ các quy tắc
trong CLAUDE.md: không sang cổng sau khi cổng trước chưa ĐẠT, tối đa 3 hướng sửa rồi dừng hỏi tôi, không bịa
số, chỉ nạp SRAM, hỏi tôi khi cần xác nhận vật lý (LED, cắm kit). Trước khi bắt đầu, liệt kê ngắn những
gì bạn sẽ làm ở F0 và những gì cần tôi làm. Sau mỗi cổng: cập nhật FEASIBILITY_REPORT.md và LOG.md, commit git,
rồi báo tôi kết quả trước khi sang cổng tiếp theo.
```

## Các phiên sau
```
Đọc CLAUDE.md, docs/LOG.md (mục mới nhất) và docs/FEASIBILITY_REPORT.md. Tiếp tục từ cổng chưa ĐẠT đầu tiên
theo docs/FEASIBILITY_PLAN.md, giữ nguyên các quy tắc trong CLAUDE.md.
```

## Khi bị kẹt
```
Dừng sửa. Tóm tắt trong LOG.md: triệu chứng, 3 hướng đã thử, log lỗi đầy đủ, và các phương án dự phòng trong
FEASIBILITY_PLAN.md cho cổng này. Đề xuất phương án nên thử tiếp và lý do.
```

## Giai đoạn đồng thiết kế (sau thí nghiệm M1-S)
```
Đọc CLAUDE.md, docs/KET_QUA_M1S.md và docs/CODESIGN_PLAN.md. Bắt đầu giai đoạn đồng thiết kế từ P0, làm đúng
thứ tự P0 → P4, giữ mọi quy tắc trong CLAUDE.md. Không sửa hay xoá các thư mục feasibility/ và experiment/m1s/
đã có. Ở P3, luôn ghi dự báo của mô hình P2 TRƯỚC khi hiện thực ứng viên, rồi so với số đo. Sau mỗi bước:
cập nhật LOG.md, commit, báo tôi kết quả trước khi sang bước sau.
```

## (Cũ) Giai đoạn pipeline CDP — dùng bộ câu lệnh chính thức ở cuối file
```
Đọc CLAUDE.md, docs/KET_QUA_TONG_HOP.md, docs/PIPELINE_SPEC.md và docs/PIPELINE_PLAN.md. Dựng pipeline CDP theo
đúng thứ tự S0 → S8, giữ mọi quy tắc trong CLAUDE.md và các nguyên tắc ở mục 0 của PIPELINE_SPEC (AI chỉ đề xuất,
mọi số từ công cụ; đúng từng bit; ghi dự báo trước khi đo; tái lập; chế độ mù ở S4–S5 bằng subagent chỉ được đọc
sandbox; một kit tuần tự qua kit.lock; bọc script có sẵn, không sửa thư mục kết quả cũ). Dùng lại các file đã soạn
sẵn trong pipeline/ (catalog, schema, prompt, spec mẫu). Trước khi bắt đầu, tóm tắt kế hoạch S0–S1 và những gì
cần tôi làm. Sau mỗi bước: cập nhật LOG.md, commit, báo kết quả rồi chờ tôi đồng ý mới sang bước sau.
```


---

# BỘ CÂU LỆNH CHÍNH THỨC — PIPELINE CDP (2026-10-18)

B1 (tối ưu phần mềm) đã làm thủ công: firmware A-V1. Các phiên dưới đây làm B2 theo `docs/PIPELINE_PLAN.md`.
Dùng từng câu lệnh theo thứ tự; mỗi câu lệnh kết thúc bằng một điểm dừng để bạn duyệt.

## Lệnh 1 — Khởi động: S0 → S3 (hạ tầng, tái lập, ISS, phân tích)
```
Bối cảnh: dự án đã xong giai đoạn khả thi, nhánh A, nhánh B (14 cấu hình, 332,9 → 13,6 ms, xem
docs/KET_QUA_TONG_HOP.md). Bước tối ưu phần mềm (B1) đã làm thủ công, kết quả là firmware A-V1. Giờ ta dựng
pipeline đồng thiết kế có AI hỗ trợ (CDP) để làm B2: phân tích firmware và đề xuất tối ưu từ tầng lệnh đến
vi kiến trúc, rồi đo thật.

Đọc theo thứ tự: CLAUDE.md, docs/KET_QUA_TONG_HOP.md, docs/PIPELINE_SPEC.md, docs/PIPELINE_PLAN.md, và các
file soạn sẵn trong pipeline/ (catalog, schema, prompt, spec mẫu). Đọc thêm rtl/mycore/mycore.v,
rtl/mycore/Makefile, experiment/m1s/Makefile và scripts/branch_b_measure.sh để bọc đúng luồng có sẵn.

Phiên này làm S0, S1, S2, S3 — lần lượt, mỗi bước một commit, không gộp bước:
- S0: khung gói pipeline/cdp, CLI python -m cdp, sổ cái SQLite, khoá kit, kiểm đặc tả YAML.
- S1: bọc build/sim/kit/synth bằng Makefile và script có sẵn; tái tạo A-V0, B-V1, B-V3 qua cdp. Phải BẰNG
  TUYỆT ĐỐI 8.987.660 / 1.459.993 / 365.992 chu kỳ, CRC và SRC_HASH khớp. Cần kit: hỏi tôi trước khi nạp.
- S2: ISS RV32IM + plugin dot4/req (ngữ nghĩa lấy đúng từ RTL) + mô hình chu kỳ mycore và picorv32; kiểm trên
  cả 14 cấu hình. mycore phải khớp Verilator tuyệt đối từng lớp; picorv32 sai số ≤ 2 %. Ghi số thật kể cả
  khi không đạt.
- S3: profile 3 tầng + analyze (ILP, DLP, byte/MAC, roofline) cho A-V0, A-V1, B-V1, B-V1+DOT4+C1, B-V3;
  summary.md giải thích bằng số từ profile các hệ số đã đo (1,45×; 2,31×; 1,29×; 1,33×).

Quy tắc bắt buộc (ngoài CLAUDE.md):
1. Mọi con số phải từ ISS/Verilator/nextpnr/kit, kèm đường dẫn log. Không ước đoán thành kết quả.
2. Không sửa hay xoá feasibility/, experiment/m1s/, rtl/mycore/ hiện có, results/ cũ. Biến thể mới chỉ thêm
   qua tham số mới (mặc định giữ hành vi cũ) hoặc thư mục mới.
3. Mỗi lệnh cdp ghi pipeline/runs/<id>/meta.json (git commit, phiên bản công cụ, tham số, SRC_HASH).
4. Kit chỉ qua kit.lock, tuần tự, có đối chứng như branch_b_measure.sh.
5. Một bước thử tối đa 3 hướng sửa; vẫn hỏng thì dừng, ghi LOG.md và hỏi tôi.

Trước khi viết mã: trình bày ngắn (≤ 15 dòng) cấu trúc gói cdp bạn định dựng, các script có sẵn sẽ bọc, và
những gì cần tôi làm. Chờ tôi đồng ý. Sau MỖI bước S0–S3: cập nhật docs/LOG.md, kết quả vào results/pipeline/S<n>/,
commit "S<n>: ...", báo tôi bảng kết quả + tiêu chí ĐẠT/KHÔNG, rồi DỪNG chờ tôi trước khi sang bước sau.
```

## Lệnh 2 — S5: sinh ứng viên mù (AI và theo luật)
```
Đọc docs/LOG.md (mục mới nhất), docs/PIPELINE_PLAN.md mục S5 và PIPELINE_SPEC mục 4. Làm S5.

1. Chạy cdp profile + analyze cho firmware A-V1 trên mycore cấu hình gốc (B-V1: FAST_ADDR=1, WITH_DOT4=0,
   WITH_REQ=0). Tạo budget.json từ tài nguyên thật còn lại của B-V1.
2. Dựng sandbox mù theo SPEC 4.6: chỉ chứa analysis.json, budget.json, candidate.schema.json, prompts/propose.md
   và (chế độ blind_catalog) catalog/optimizations.yaml. Ghi danh sách file đã cấp vào meta.json.
3. Với MỖI lần chạy, khởi một subagent MỚI (Task tool), làm việc chỉ trong sandbox, không được đọc file nào ngoài
   sandbox; giao cho nó nội dung prompts/propose.md. Chạy 3 lần blind_open + 3 lần blind_catalog. Lưu nguyên văn
   input/prompt/output/meta (model, thời gian, hash). Kiểm output bằng schema; output sai schema thì cho
   subagent đó sửa tối đa 1 lần, sau đó ghi là lỗi.
4. Chạy cdp propose --rules trên cùng analysis.json.
5. Chấm tái khám phá bằng bảng: với mỗi đáp án đã biết (DOT4 – SIMD nhân-cộng 4×int8; bố cục 4 pha – đổi bố cục
   để SIMD dùng được ở lớp Cin=1; REQ – requantize một lệnh; bộ nhớ/lõi nhanh – L3), lần chạy nào đề xuất ra,
   ở thứ hạng nào, với spec có hiện thực được không. Người chấm là bạn, nhưng tiêu chí "tương đương" phải viết
   ra TRƯỚC khi mở các file output.
6. Ghi mọi ứng viên vào sổ cái (status=proposed). Chưa hiện thực gì.

Kết thúc: results/pipeline/S5/ (6 file AI + 1 file luật + bảng tái khám phá + summary.md), LOG.md, commit
"S5: ...". Báo tôi bảng tái khám phá và số ứng viên theo tầng, rồi DỪNG.
```

## Lệnh 3 — S6: phễu đánh giá, hiện thực, đo kit, vòng mở
```
Đọc docs/LOG.md (mục mới nhất) và docs/PIPELINE_PLAN.md mục S6. Làm S6 theo hai phần, dừng giữa hai phần.

Phần A — vòng tái khám phá:
1. cdp estimate cho TẤT CẢ ứng viên S5 (gộp trùng lặp, ghi rõ gộp cái nào). L1/L2 qua plugin ISS + biến thể
   firmware; L3 qua sửa file timing; L4/L5 giải tích. Ghi dự báo vào sổ cái TRƯỚC khi hiện thực bất cứ thứ gì,
   và commit sổ cái ở trạng thái này (đây là bằng chứng "dự báo trước").
2. Chọn top-K (K ≤ 4) theo dự báo tăng tốc/chi phí ước lượng; nêu lý do chọn. Hiện thực trên mycore bằng tham số
   mới mặc định tắt. Qua đủ cdp verify: kiểm ngẫu nhiên ≥ 1 triệu vector so với plugin ISS, riscv-tests 48/48,
   đúng bit M1-S, ISS = Verilator tuyệt đối, SRC_HASH.
3. Đo kit 10 ảnh; cdp synth khối riêng để lấy chi phí (KHÔNG dùng hiệu hai lần tổng hợp toàn SoC — xem cạm bẫy 5
   trong KET_QUA_TONG_HOP); Fmax từ tổng hợp toàn SoC.
4. Bảng dự báo-vs-đo + sai số theo tầng. Báo tôi rồi DỪNG.

Phần B — vòng mở (chỉ làm khi tôi đồng ý):
5. Điểm xuất phát B-V3 (13,6 ms), chế độ open (được xem history.csv). Lặp S3 → S5 (1 lần AI open + luật) → phần A.
6. Cấu hình nhanh nhất mới (nếu có) phải đúng bit trên kit cả 10 ảnh và 10.000 ảnh.

Kết thúc mỗi phần: results/pipeline/S6/, LOG.md, commit, báo cáo, DỪNG.
```

## Lệnh 4 — S7 + S8: mô hình giữ lại và báo cáo
```
Đọc docs/LOG.md và PIPELINE_PLAN mục S7, S8.
S7: thêm mô hình giữ lại M1-L (gấp đôi kênh: conv 16 và 32 kênh) — huấn luyện, lượng tử hoá, golden Python,
firmware C bản A-V1 (áp cùng các biến đổi phần mềm, không tối ưu riêng). Kiểm vừa 64 KB trước; không vừa thì báo
tôi. Áp các cấu hình phần cứng đã chọn ở S6 KHÔNG chọn lại; đo ISS + kit; đúng bit.
S8: viết docs/KET_QUA_PIPELINE.md trả lời PQ1–PQ6 bằng số, kèm biểu đồ trong report/pipeline/ (dự báo-vs-đo,
Pareto chu kỳ–LUT, roofline trước/sau, bảng tái khám phá, chi phí AI). Mỗi khẳng định ghi mức tin cậy như mục 4
của KET_QUA_TONG_HOP (đo / suy ra / không kết luận được). Commit, báo tôi, DỪNG.
```

## Lệnh rà soát độc lập — dùng sau MỖI bước, trước khi cho sang bước tiếp
```
Khởi một subagent mới làm người rà soát độc lập, KHÔNG có ngữ cảnh phiên này. Giao cho nó: docs/PIPELINE_PLAN.md
mục của bước vừa xong, results/pipeline/S<n>/, phần LOG.md của bước đó và sổ cái. Yêu cầu nó: (1) đối chiếu từng
con số trong báo cáo với log gốc, (2) kiểm từng tiêu chí ĐẠT có bằng chứng, (3) chỉ ra khẳng định nào vượt quá dữ
liệu, (4) kiểm có vi phạm chế độ mù hay "dự báo trước" không. Trả lại danh sách vấn đề. Sửa các vấn đề có thật,
ghi vào LOG.md những gì đã sửa và những gì bác bỏ (kèm lý do), rồi báo tôi.
```

## Lệnh tiếp tục (phiên mới)
```
Đọc CLAUDE.md, docs/LOG.md (mục mới nhất), docs/PIPELINE_PLAN.md. Xác định bước pipeline đang dở, tóm tắt trạng
thái trong 5 dòng và việc tiếp theo, rồi chờ tôi đồng ý.
```

## Lệnh khi kẹt
```
Dừng sửa. Trước tiên chạy đối chứng bằng một cấu hình ĐÃ BIẾT CHẠY (ví dụ B-V1) để loại trừ hạ tầng đo hỏng.
Sau đó ghi vào LOG.md: triệu chứng, 3 hướng đã thử, log lỗi, kết quả đối chứng, và đề xuất bước tiếp theo kèm lý do.
```
