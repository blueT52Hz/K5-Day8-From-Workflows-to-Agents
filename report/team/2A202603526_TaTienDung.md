# Báo cáo cá nhân — 2A202603526_TaTienDung

## 1. Thông tin thành viên

- Họ tên: Tạ Tiến Dũng
- MSSV: 2A202603526
- Email: 26ai.dungtt4@vinuni.edu.vn
- GitHub: tiendung832005

## 2. Phần việc phụ trách

- **Vai trò:** Single Agent Engineer (Thành viên 2).
- **Module phụ trách chính:** Thiết kế, cài đặt và kiểm thử kiến trúc **Shape B (`src/lab8/shapes/single.py`)** theo mô hình ReAct trong các giai đoạn CP2, CP3 và CP4, kèm bộ unit test riêng tại `src/tests/test_single.py`.
- **Công việc phối hợp & Báo cáo:**
  - Thống nhất Output contract (`RunResult`) và Trace contract v1 ở CP1.
  - Chạy kiểm thử hồi quy (Regression test) cho Shape A (`workflow.py`) sau khi tích hợp code lên nhánh `main`.
  - Tham gia tổng hợp kết quả benchmark, phân tích số liệu cho `group_report.md` và `research_card.md`.

## 3. Đóng góp cụ thể

- **Commit chính:** `705683c` (`705683c9a284b2aea9c87a1c75555965d7a6bf05`) — Cài đặt Shape B (`src/lab8/shapes/single.py`) và bổ sung unit test tại `src/tests/test_single.py`.
- **Các quyết định kỹ thuật trọng tâm trong `src/lab8/shapes/single.py`:**
  1. **Kiểm soát vòng lặp ReAct và ranh giới quyền hạn (`worker=True`):** Sử dụng `lab8.runtime.run_react` với giới hạn `max_steps=8` và cờ `worker=True` để khóa quyền gọi tool của agent, chỉ cho phép gọi các read tool (`get_claim_view`, `lookup_order`, `lookup_refund_history`, `compute_compensation`) và ngăn chặn việc agent tự ý gọi write tool.
  2. **Tách bạch dữ liệu người dùng và nguồn sự thật (Chống Prompt Injection):** Gọi `mock_llm.complete(..., purpose="parse")` để mô phỏng bước đọc hiểu ticket và hạch toán chi phí token vào `Budget`, nhưng không tin tưởng số ngày trễ hay mã đơn trích xuất từ văn bản ticket. Mọi quyết định về quyền sở hữu đơn (`principal_id`), lịch sử hoàn tiền và số tiền bồi thường đều được truy xuất trực tiếp từ cơ sở dữ liệu qua `lookup_order` và `compute_compensation` (đã lọc theo policy hiện hành `is_current=1`).
  3. **Tuân thủ cơ chế trần theo đơn và Idempotency/Crash Safety (CP3):** Sau khi vòng lặp ReAct kết thúc, code của shape gọi `mock_llm.complete(..., purpose="draft")` và chuyển **số tiền quote đầy đủ** (không tự trừ khoản đã hoàn trước đó) vào cổng kiểm soát của host thông qua `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)`. Không nuốt ngoại lệ `InjectedCrash` mà ghi nhận sự kiện crash, lưu trace (`trace.write()`) và `raise` lại để hệ thống kiểm thử xác minh tính toàn vẹn của SQLite ledger.
  4. **Bảo vệ ranh giới bảo mật Trace (CP4):** Sử dụng `lab8.trace.Trace` và `safe_dump` để ghi nhận từng bước chuyển trạng thái của vòng lặp ReAct trên mọi nhánh thoát (kể cả `unknown_claim`, `needs_info`, `escalated`, `denied`). Không ghi nguyên văn nội dung `ticket` hay bản ghi thô từ bảng `claims`/`orders` vào trace để ngăn rò rỉ `CANARY_SECRET_*` và thông tin cá nhân (SĐT, địa chỉ).

## 4. Bằng chứng

- **Commit trên nhánh `main`:** `https://github.com/blueT52Hz/K5-L3A-DAY08-Nhom3Nguoi-FromWorkflowsToAgents/commit/705683c9a284b2aea9c87a1c75555965d7a6bf05`
- **Kết quả kiểm thử Student Tests (CP2 & CP3 — bao gồm T11 Idempotency, T12 Crash/Resume, T13–T14 Per-order Cap):**
  - Lệnh chạy: `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"`
  - Kết quả: Đạt **62 passed**.
- **Unit test riêng cho Shape B (`src/tests/test_single.py`):**
  - Lệnh chạy: `python -m pytest -q tests/test_single.py`
  - Kết quả: Đạt **4 passed** (kiểm tra luồng chuẩn, chống prompt injection và rò rỉ secret/PII trong trace, nhánh `needs_info`/`escalated`, idempotency và crash/resume tại `after_effect_before_checkpoint`).
- **Kết quả Benchmark (`src/reports/benchmark.json`):** Shape `single` đạt pass rate **1.000**, pass^5 **1.000**, variance **0**, cost/success **37.85 VND** mô phỏng, p95 **7 bước**.
- **Cổng kiểm thử Host:** `python -m pytest -q` duy trì trạng thái xanh xuyên suốt quá trình phát triển và sau khi tích hợp.

## 5. Công cụ AI đã dùng

- **Công cụ sử dụng:** Gemini.
- **Mục đích sử dụng:**
  - Phân tích và đối chiếu các ràng buộc giữa `docs/business_rules.md`, `docs/contracts.md`, `src/lab8/runtime.py` và `src/lab8/tools.py`.
  - Hỗ trợ thiết kế cấu trúc hàm `decide` cho vòng lặp ReAct trong `src/lab8/shapes/single.py` và rà soát các trường hợp biên (thiếu `order_id`, sai quyền sở hữu đơn, hoàn tiền nhiều lần trên cùng một đơn, xử lý ngoại lệ `InjectedCrash`).
- **Cách tự kiểm tra và xác minh kết quả (tuân thủ `RULES.md`):**
  - Trực tiếp đọc hiểu mã nguồn được gợi ý, kiểm tra lại từng nhánh điều kiện và đối chiếu với schema của `RunResult` và `Trace`.
  - Tự thực thi bộ test tự động trên môi trường `.venv` cục bộ (`python -m pytest -q`, `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"`, và `python -m pytest -q tests/test_single.py`) để xác minh kết quả trước khi commit code lên repository nhóm.

## 6. Tự đánh giá

- **Mức độ hoàn thành:** Hoàn thành đầy đủ các đầu việc kỹ thuật của vai trò Single Agent Engineer đúng tiến độ phân công (CP1–CP4), đảm bảo tuân thủ ranh giới bảo mật và nguyên tắc thiết kế "code quyết định tiền, model chỉ đọc và soạn thảo".
- **Bài học rút ra:** Hiểu rõ sự đánh đổi giữa tính tự chủ của agent và độ tin cậy của hệ thống: việc giới hạn số bước (`max_steps=8`), khóa quyền ghi tool (`worker=True`) và tách biệt dữ liệu đầu vào không đáng tin cậy (ticket) khỏi nguồn sự thật (DB) là yếu tố then chốt giúp kiến trúc Single Agent vừa linh hoạt trong việc điều phối tool đọc, vừa đạt độ nhất quán cao qua nhiều seed.