# Team

## Thông tin nhóm

- Tên nhóm: Nhom3Nguoi
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-Nhom3Nguoi-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/blueT52Hz/K5-L3A-DAY08-Nhom3Nguoi-FromWorkflowsToAgents · `main` · xem dòng `Commit hash` trong `report/team/decision_adr.md`

## Thành viên

| STT | Họ tên           | MSSV        | Email                     | GitHub                                                                                                                                           | Vai trò                                       |
| --: | ------------------ | ----------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
|   1 | Nguyễn Hữu Đức | 2A202603429 | 26ai.ducnh3@vinuni.edu.vn | [@ducnguyen2112](https://github.com/ducnguyen2112) | Workflow, test retry/crash, tích hợp và ADR |
|   2 | Tạ Tiến Dũng | 2A202603526 | | [@tiendung832005](https://github.com/tiendung832005) | Single agent (ReAct) |
|   3 | Nguyễn Hoa Thanh Tùng | 2A202603519 | 26ai.tungnht2@vinuni.edu.vn | [@bluet52hz](https://github.com/bluet52hz) | Orchestrator + handoff, crash suite, benchmark, bonus B3, demo/slide |

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người            | Vai                                                          | Commit                                    | Test đã thêm hoặc sửa                    |
| ------------------ | ------------------------------------------------------------ | ----------------------------------------- | --------------------------------------------- |
| Nguyễn Hữu Đức | Workflow, test hồi quy, kiểm host/crash và ADR bản nháp | `0ef1f6435cfc295f56e87e7e10485a684a21b2bb` (workflow; test và report chưa commit) | `src/tests/test_workflow.py` (21 trường hợp) |
| Tạ Tiến Dũng | Single agent (ReAct): `run_react` tối đa 8 bước, chỉ tool đọc, host ghi tiền | `705683c` (Implement Shape B) | (chưa có test riêng; single qua 62 test student) |
| Nguyễn Hoa Thanh Tùng | Orchestrator + handoff allowlist, crash suite, benchmark 4 shape, hidden self-check, bonus B3, demo/slide | `b612394` (tích hợp orchestrator, bonus B3, reports, docs) | `src/tests/test_bonus_swarm_verified.py` (44 test) |

## Cá nhân

Báo cáo đầy đủ của từng thành viên:

- `report/team/2A202603429_NguyenHuuDuc.md`
- `report/team/2A202603526_TaTienDung.md`
- `report/team/2A202603519_NguyenHoaThanhTung.md`

## 2A202603429_NguyenHuuDuc

### Phần việc phụ trách

- Triển khai kiến trúc A — workflow trong `src/lab8/shapes/workflow.py`.
- Bổ sung test nghiệp vụ, approval, retry, crash/resume và trace an toàn.
- Kiểm tra host gate, chạy crash suite và tạo benchmark baseline workflow so với swarm.
- Chuẩn bị ADR bản nháp; phụ trách tích hợp và cập nhật ADR cùng nhóm khi single và orchestrator hoàn thành.

### Đóng góp cụ thể

- Xây dựng luồng cố định: đọc claim → kiểm quyền truy cập đơn → tính quote bằng `compute_compensation` → gọi host → trả `RunResult` bằng `finish()`.
- Dùng dữ liệu đơn hàng làm nguồn sự thật; không lấy số ngày hoặc chỉ dẫn trong ticket để quyết định số tiền. Workflow không gọi model.
- Truyền quote đầy đủ vào `durability.issue_refund` để host kiểm approval và trừ khoản đã hoàn theo đơn; không tự trừ trước. Phân biệt kết quả bị từ chối (`denied`) với xung đột số tiền khi retry (`failed`).
- Truyền `crash_at` cho host, để `InjectedCrash` truyền ra runner và luôn đóng connection trong `finally`; xác minh resume/retry chỉ giữ một refund và một audit committed.
- Chỉ ghi metadata và dữ liệu đã lọc vào trace; không ghi ticket, secret, header, SĐT, địa chỉ, tên hàng hoặc ghi chú nội bộ.
- Thêm 21 trường hợp trong `src/tests/test_workflow.py`: nhánh trả sớm, approval sai/thiếu/hết hạn, policy tương lai, đơn không hợp lệ, trần hoàn tiền giữa các claim, amount conflict, ba điểm crash cho refund thường và top-up, cùng kiểm tra rò dữ liệu.
- Sinh report bằng CLI và điền `report/team/decision_adr.md` ở trạng thái bản nháp dựa trên số liệu thực tế.

### Bằng chứng

- Commit triển khai workflow: `0ef1f6435cfc295f56e87e7e10485a684a21b2bb` (`update workflow.py`). Test bổ sung và report hiện chưa commit; cần bổ sung hash chứa các file này trước khi nộp.
- Môi trường đã kiểm tra: Windows AMD64, Python 3.12.7, pytest 8.4.2, PyYAML 6.0.3.
- `python -m pytest -q`: **75 passed, 248 deselected**.
- `python -m pytest -q -m student -o addopts= -k workflow`: **62 passed**, gồm T11 retry và T12 crash/resume.
- [Crash report](src/reports/crash.json): **20/20** cho suite host/swarm. Test workflow bổ sung kiểm riêng cả `before_effect`, `after_effect_before_checkpoint` và `after_checkpoint`.
- [Benchmark baseline](src/reports/workflow_baseline.json): workflow đúng **70/70 trial** trên 14 claim × 5 seed; pass rate = **1.0**, pass^5 = **1.0**, variance = **0**, cost/success ≈ **27.86 VND mô phỏng**. Swarm cùng điều kiện đúng 69/70 trial, cost/success ≈ 49.57 VND mô phỏng.
- Run id minh họa: `R-workflow-C-001-s11`, `R-workflow-C-002-s55`, `R-workflow-C-014-s55`.
- [Báo cáo cá nhân](report/team/2A202603429_NguyenHuuDuc.md) và [ADR bản nháp](report/team/decision_adr.md). Chưa có kết quả hidden; quyết định kiến trúc cuối cùng cần benchmark đủ bốn shape sau khi tích hợp.

## 2A202603526_TaTienDung

### Phần việc phụ trách

- Triển khai kiến trúc B - single agent ReAct trong `src/lab8/shapes/single.py`.

### Đóng góp cụ thể

- Dùng `lab8.runtime.run_react` với `max_steps=8` và `worker=True`: agent chỉ được gọi tool đọc (`get_claim_view`, `lookup_order`, `lookup_refund_history`, `compute_compensation`), không có tool ghi.
- Quote lấy từ kết quả `compute_compensation` trên order row, không lấy số trong ticket; ticket chỉ là dữ liệu không tin cậy.
- Host gọi `durability.issue_refund` với quote đầy đủ sau vòng lặp, truyền `crash_at`, chỉ bắt `InjectedCrash` để ghi trace rồi ném lại.
- Trace ghi `react_step`, `observation` (visible, reason, số tiền đã hoàn), `quote`; không ghi ticket hay row thô.

### Bằng chứng

- Commit: `705683c` (Implement Shape B (Single Agent ReAct)).
- `python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"`: 62 passed.
- `src/reports/benchmark.json`: single 1.000 / 1.000, cost/success 37.85 VND, p95 7 bước.
- Báo cáo cá nhân: `report/team/2A202603526_TaTienDung.md`.

## 2A202603519_NguyenHoaThanhTung

### Phần việc phụ trách

- Kiến trúc C - orchestrator + handoff (`src/lab8/shapes/orchestrator.py`).
- Crash suite, rà must-pass, benchmark 4 shape, tự kiểm hidden.
- Bonus B3 (`src/bonus/`), demo Streamlit và slide (`demo_ui/`), tích hợp lên `main`, báo cáo nhóm.

### Đóng góp cụ thể

- Orchestrator dựng handoff bằng `make_handoff` với `facts={}` và `allowed_tools=["lookup_order"]`; investigator chỉ đọc; orchestrator tự quote từ order view và gọi `issue_refund` với quote đầy đủ và `crash_at`.
- Bonus B3: `swarm_verified` thêm `verify_quote_inputs` đối chiếu `delay_days`, `status`, `damage_verified` với order row trước bước ghi; 10 claim đối kháng nhãn tính tay.
- Chạy crash suite, benchmark, hidden self-check; điền ADR, research card (R2 - MAST), báo cáo nhóm, bonus report.

### Bằng chứng

- Commit: `b612394` (tích hợp orchestrator, bonus B3, reports, docs).
- Test: `src/tests/test_bonus_swarm_verified.py` (44 test); ma trận student 248/248.
- `src/reports/crash.json` 20/20; `src/reports/benchmark.json` orchestrator 1.000 / 1.000, 38.03 VND; `src/reports/hidden_selfcheck.json` 600 trial, 0 error, 0 leak.
- Báo cáo cá nhân: `report/team/2A202603519_NguyenHoaThanhTung.md`.
