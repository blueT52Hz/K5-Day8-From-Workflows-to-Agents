# Báo cáo nhóm - Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: Nhom3Nguoi
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): xem dòng `Commit hash` trong ADR

## 2. Mục tiêu và cách tiếp cận

Bài toán: xử lý claim hoàn phí ship của LogiX-VN trên 4 kiến trúc (workflow, single ReAct, orchestrator, swarm), rồi chọn kiến trúc **ít tự chủ nhất mà vẫn đúng** bằng số đo trên cùng claim, cùng seed, cùng bảng giá. Nguyên tắc nhóm thống nhất trước khi code: order row và policy `is_current` là nguồn sự thật, chữ trong ticket là dữ liệu người dùng không tin cậy, tiền do `compute_compensation` tính, host là bên ghi duy nhất.

Thứ tự làm theo checkpoint:
1. CP1: cài môi trường, đọc `docs/business_rules.md`, `docs/contracts.md`, `swarm_reference.py`. Smoke pass, ma trận student 186 failed / 62 passed (đúng trạng thái stub).
2. CP2: viết workflow trước (ít thành phần nhất, làm baseline), sau đó single (vòng ReAct) và orchestrator (handoff cho investigator chỉ đọc). Cả 3 trả kết quả qua `finish()`.
3. CP3: truyền `crash_at` vào `issue_refund`, bắt `InjectedCrash` chỉ để ghi trace rồi ném lại.
4. CP4: crash suite 20/20, rà nhánh approval và quét trace.
5. CP5: benchmark 4 shape × 5 seed, ADR, research card, bonus B3.

## 3. Giải pháp

Cả 3 shape mở connection, chạy các bước và luôn đóng connection trong `finally` (tránh khóa file `.sqlite` trên Windows). Mọi nhánh return đều đi qua `finish()`, nên trace luôn được ghi kể cả ở `needs_info`, `escalated`, `failed`.

| Shape | Đọc gì | Ai quyết định | Gọi host |
| --- | --- | --- | --- |
| A workflow | `get_claim_view` → `lookup_order` theo principal → `compute_compensation`, gọi qua `runtime.dispatch` | Code, các bước cố định, 0 model call | Quote > 0 thì `issue_refund(full quote, crash_at)` |
| B single | `run_react` tối đa 8 bước, `decide()` giữ trạng thái trong dict `state`: `get_claim_view` → `lookup_order` → `lookup_refund_history` → `compute_compensation` | Agent chọn tool đọc; quote lấy từ kết quả `compute_compensation`, không lấy từ ticket | Host gọi `issue_refund` sau vòng lặp, agent không có tool ghi |
| C orchestrator | Claim view, rồi giao `lookup_order` cho investigator chỉ đọc qua handoff | Orchestrator tự quote từ order view của investigator | Orchestrator gọi `issue_refund` |

Ranh giới code / model (xem [docs/architecture.md](../../docs/architecture.md)): model không chọn số tiền và không ghi refund. Workflow không gọi model; orchestrator chỉ gửi id cho MockLLM; single gửi ticket cho MockLLM để parse nhưng không dùng kết quả cho tiền (ticket là dữ liệu không tin cậy).

Handoff (orchestrator): `make_handoff` với `facts={}` (trước khi điều tra, nguồn duy nhất về số ngày trễ là ticket, không tin được) và `allowed_tools=["lookup_order"]`. `make_handoff` tự bỏ field ngoài allowlist và từ chối canary hoặc tool ghi. Trace ghi handoff qua `safe_dump`, không ghi parent context.

Trace ghi: workflow `claim`, `lookup_order` (view đã allowlist), `quote`, `refund`, `decision`; single `react_step`, `observation`, `quote`, `crash`; orchestrator `handoff`, `investigator`, `quote`, `issue_refund`, `decision`, `crash`. Không bao giờ ghi ticket, claim row hay order row thô.

## 4. Kết quả

Bộ public, 14 claim × 5 seed = 70 trial mỗi shape (`src/reports/benchmark.json`):

| Shape | Pass | pass^5 | Seed min-max | Variance | Cost/success (VND) | Steps mean / p95 | Model call TB | Tool call TB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 1.000-1.000 | 0 | **27.86** | 4.43 / 5 | 0.00 | 2.79 |
| single | 1.000 | 1.000 | 1.000-1.000 | 0 | 37.85 | 6.36 / 7 | 2.00 | 3.64 |
| orchestrator | 1.000 | 1.000 | 1.000-1.000 | 0 | 38.03 | 4.36 / 5 | 1.79 | 3.71 |
| swarm | 0.986 | 0.929 | 0.929-1.000 | 0.000816 | 49.57 | 2.80 / 3 | 3.00 | 4.66 |

- Không có trial `error` hay `leak_suspect`. Trial fail duy nhất: `R-swarm-C-002-s55` (swarm tin "trễ 5 ngày" trong ticket, order ghi 2 ngày).
- Crash safety: **20/20** (`src/reports/crash.json`), gồm crash trước effect, sau effect trước checkpoint, sau checkpoint, đổi số tiền khi retry, retry không approval.
- Must-pass: approval bypass 0, secret leak 0 (quét 860 trace public và hidden của 3 shape), crash 20/20.
- Tự kiểm hidden (`src/reports/hidden_selfcheck.json`): 40 claim × 5 seed, cả 3 shape chạy hết 600 trial, 0 trial `error`, 0 `leak_suspect`, trace đúng contract. Phân bố status của workflow: denied 95, resolved 90, escalated 10, needs_info 5; single và orchestrator ra cùng phân bố. Không có nhãn nên pass rate hidden do grader giảng viên chấm.
- Bonus B3: verifier bằng code đưa swarm lên 1.000 / 1.000 trên cả public và bộ đối kháng 10 claim, nhưng cost/success vẫn gấp khoảng 1,8 lần workflow (`report/team/bonus_report.md`).

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md` (chọn **workflow**). Phiếu nghiên cứu và ablation: xem `report/team/research_card.md` (R2, MAST).

## 5. Khó khăn và cách xử lý

- **`-k single` chọn nhầm cả 4 shape.** Lệnh `pytest -m student -k single` ra 60 failed vì tên hàm `test_public_single_run_cases` chứa chữ "single". Xử lý: dùng `-k "single and not workflow and not orchestrator and not swarm"` → 62 passed.
- **T12 fail "crash did not fire" ở CP2.** Đúng dự kiến khi chưa truyền `crash_at`. CP3 truyền `crash_at` và không nuốt `InjectedCrash` → 248/248 student pass.
- **Hiểu vì sao checkpoint đơn lẻ không đủ.** `python -m lab8.demo.buggy_workflow` in `unsafe refund rows: 2`. Nhóm dựa vào idempotency key `refund:{claim_id}` của ledger, replay trả lại effect cũ trước khi tới điểm crash.
- **Trừ tiền hai lần (T14).** Không tự trừ phần đã hoàn mà truyền **quote đầy đủ**, host tự trừ và cap.
- **Đề đổi layout giữa buổi** (code dời vào `src/`, docs dời vào `report/team/`). Nhóm làm lại trên nhánh mới theo đúng checkpoint, số đo khớp hoàn toàn với lần trước.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

- MockLLM không phải model sản xuất; latency là `unavailable`; cost là VND mô phỏng. Text của MockLLM không ảnh hưởng quyết định, nên số model call chỉ phản ánh cost.
- Pass rate mới đo trên 14 claim public và 10 claim đối kháng tự viết. Bộ hidden 40 claim chỉ tự kiểm được format, lỗi và leak (không có nhãn).
- Kết luận chọn workflow đảo lại nếu bộ hidden có dạng claim luật cố định không biểu diễn được (bằng chứng dạng văn bản tự do, ảnh), làm workflow rớt dưới 0.75 trong khi shape agentic vượt ngưỡng với pass^5 ổn định; hoặc khi số loại claim tăng tới mức bảo trì if/else đắt hơn chi phí model.

## 8. Tài liệu tham khảo

- Lab 8 README, `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md`, `docs/bonus_topics.md`.
- Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST), NeurIPS 2025, https://arxiv.org/abs/2503.13657.
- Google Research 2026, *Towards a Science of Scaling Agent Systems* (error amplification, dùng cho bonus B3).
