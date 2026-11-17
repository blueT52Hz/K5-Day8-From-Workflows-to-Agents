# Báo cáo cá nhân - 2A202603519_NguyenHoaThanhTung

## 1. Thông tin thành viên

- Họ tên: Nguyễn Hoa Thanh Tùng
- MSSV: 2A202603519
- Email: 26ai.tungnht2@vinuni.edu.vn
- GitHub: [@bluet52hz](https://github.com/bluet52hz)

## 2. Phần việc phụ trách

- Shape C - orchestrator + handoff (`src/lab8/shapes/orchestrator.py`).
- Crash suite và rà 3 điều kiện must-pass (approval, secret, crash).
- Benchmark 4 shape trên bộ public, tự kiểm hidden, số liệu cho ADR và research card.
- Bonus B3 - verifier chống khuếch đại lỗi (`src/bonus/`).
- Giao diện demo Streamlit và slide trình bày (`demo_ui/`).
- Tích hợp phần của các thành viên lên `main`, viết báo cáo nhóm.

## 3. Đóng góp cụ thể

**Orchestrator**
- Orchestrator đọc claim view, gọi 1 lần planner (MockLLM, prompt chỉ chứa id), dựng handoff bằng `make_handoff` với `facts={}` và `allowed_tools=["lookup_order"]`. Lý do để `facts` rỗng: trước khi điều tra, nguồn duy nhất về số ngày trễ là ticket, mà ticket là dữ liệu không tin cậy.
- `run_readonly_investigators` chạy `lookup_order` theo principal của claim. Investigator không có registry ghi.
- Orchestrator tự quote từ order view có cấu trúc rồi gọi `durability.issue_refund` với quote đầy đủ, truyền `crash_at`, chỉ bắt `InjectedCrash` để ghi trace rồi ném lại.
- Trace chỉ ghi handoff đã sanitize (`safe_dump`), `investigator` (`order_id`, `visible`, `reason`), `quote`, `issue_refund`, `decision`; không ghi parent context, ticket hay order row.

**Crash, must-pass, benchmark**
- Chạy crash suite 20 kịch bản, rà các nhánh approval hỏng, approval của claim khác, đơn đã hoàn đủ.
- Quét trace public và hidden của 3 shape tìm canary, header, địa chỉ, tên hàng, SĐT.
- Chạy benchmark 4 shape × 14 claim × 5 seed, tự kiểm hidden trên `student_drop/`, điền số liệu ADR và research card (R2 - MAST).

**Bonus B3**
- `swarm_verified`: giữ nguyên swarm (kể cả điểm yếu ở seed 55), thêm `verify_quote_inputs` đối chiếu `delay_days`, `status`, `damage_verified` với order row trước bước ghi. Lệch thì quote lại tối đa 1 vòng và ghi `verifier_override`; vẫn lệch thì `failed`, không ghi tiền.
- Viết 10 claim đối kháng có nhãn tính tay (`src/bonus/cases.jsonl`, `world.json`): nói quá, nói thiếu, nói dối hỏng hàng, nhiều con số, biên 3 ngày, vừa trễ vừa hỏng, status không hợp lệ, approval hết hạn, injection, đã hoàn một phần.
- Script đếm can thiệp `src/bonus/report_interventions.py`.

**Demo và slide**
- Streamlit demo 5 trang: chạy claim, so sánh 4 shape, bảo mật, durability, benchmark. Demo dùng `trial_pass` chính thức để chấm, đọc `src/reports` không sửa.
- Slide trình bày điền số thật từ `src/reports/*.json`.

**Quyết định kỹ thuật**
- Chọn workflow cho ADR: cùng độ đúng với single và orchestrator nhưng rẻ nhất và tất định.
- Investigator chỉ được `lookup_order`, không có `lookup_refund_history`: host đã tự trừ phần đã hoàn trong transaction ghi, nên đưa thêm tool chỉ tốn cost.

## 4. Bằng chứng

- Test thêm: `src/tests/test_bonus_swarm_verified.py` - 44 test (phát hiện field lệch, sửa C-002 seed 55, im lặng khi dữ kiện khớp, 10 claim × 2 shape × 2 seed theo nhãn tay, crash vẫn 1 refund).
- Ma trận student: 248/248; `python -m pytest -q`: 98 passed.
- `src/reports/crash.json`: crash_safety 20/20.
- `src/reports/benchmark.json`: orchestrator 1.000 / 1.000, cost/success 38.03 VND; workflow 1.000 / 1.000, 27.86 VND.
- `src/reports/hidden_selfcheck.json`: 600 trial, 0 error, 0 leak_suspect.
- `src/reports/bonus_benchmark.json`, `bonus_adversarial.json`, `bonus_verifier.json`: swarm 0.986 / 0.929 (public) và 0.900 / 0.500 (đối kháng) lên 1.000 / 1.000; 7 lần `verifier_override`, 6 lần đổi số tiền.
- Run id: `R-orchestrator-C-012-s11` (crash rồi resume, 1 refund), `R-swarm_verified-C-002-s55` so với `R-swarm-C-002-s55`.
- Commit: `b612394` trên `main` (tích hợp orchestrator, bonus B3, `src/reports/*.json`, tài liệu nhóm).

## 5. Công cụ AI đã dùng

- Claude Code: hỗ trợ đọc contract, viết khung code orchestrator và bonus, soạn tài liệu, chạy lệnh test và benchmark.
- Cách tự kiểm tra: mọi số liệu trong báo cáo lấy từ file do `lab8.benchmark`, `lab8.crash_test` sinh ra, không chép tay; chạy lại ma trận student và `check_submission` sau mỗi thay đổi; tự đọc trace để chắc không có secret; nhãn của 10 claim đối kháng tự tính tay theo luật trong `docs/business_rules.md`.

## 6. Tự đánh giá

- Làm tốt: orchestrator qua toàn bộ test, crash 20/20, bonus đo công bằng (chỉ đổi 1 biến) và có giới hạn rõ ràng.
- Hạn chế: bộ đối kháng chỉ 10 claim do tự viết nhãn; lỗi của swarm là 1 chế độ lỗi tất định của MockLLM nên không so trực tiếp được với hệ số khuếch đại lỗi của paper.
- Bài học: thêm tự chủ cho agent không làm tăng độ đúng khi mọi dữ kiện quyết định tiền đều có nguồn có cấu trúc; một điểm kiểm soát chung bằng code đủ chặn lỗi lan từ ticket sang ledger.
