# Báo cáo cá nhân — 2A202603429_NguyenHuuDuc

## 1. Thông tin thành viên

- Họ tên: Nguyễn Hữu Đức
- MSSV: 2A202603429
- Email: 26ai.ducnh3@vinuni.edu.vn
- GitHub: [github.com/blueT52Hz/K5-L3A-DAY08-Nhom3Nguoi-FromWorkflowsToAgents](https://github.com/blueT52Hz/K5-L3A-DAY08-Nhom3Nguoi-FromWorkflowsToAgents)

## 2. Phần việc phụ trách

Triển khai workflow; thêm test nghiệp vụ, approval, retry/crash; kiểm host gate và crash suite; chuẩn bị baseline cùng ADR để nhóm tích hợp sau.

## 3. Đóng góp cụ thể

- `src/lab8/shapes/workflow.py`: các bước cố định đọc claim → kiểm order thuộc principal → tính quote → gọi host → trả `RunResult` bằng `finish()`.
- Dùng `compute_compensation` qua `dispatch`, không lấy số ngày hay chỉ dẫn từ ticket để quyết định tiền. Workflow không gọi model.
- Quote dương luôn chuyển đầy đủ cho `durability.issue_refund`; host kiểm approval và trừ tiền đã hoàn trước đó. Quote bằng 0 không gọi ghi refund.
- Phân biệt `denied` khi host từ chối và `failed` khi retry có amount conflict. Không bắt `InjectedCrash`; connection luôn đóng trong `finally`.
- Trace chỉ ghi metadata và dữ liệu qua allowlist; không ghi ticket hoặc claim/order row thô.
- `src/tests/test_workflow.py`: 21 trường hợp mới, gồm nhánh trả sớm, approval hỏng, trạng thái đơn không hợp lệ, policy tương lai, nhiều claim trên cùng đơn, conflict, ba điểm crash cho refund thường và top-up, cùng kiểm tra rò dữ liệu qua ticket.
- Sinh `src/reports/crash.json`, `src/reports/workflow_baseline.json` bằng CLI và điền `decision_adr.md` ở trạng thái bản nháp.
- Commit chính: chưa tạo commit; bổ sung hash thật sau khi rà thay đổi và commit.

## 4. Bằng chứng

Mọi lệnh sau chạy trong `src/`, với Python của môi trường đã cài `requirements.txt`:

Đã kiểm chứng trên Windows AMD64, Python 3.12.7, pytest 8.4.2 và PyYAML 6.0.3. Môi trường cục bộ ở `src/.venv/`; có thể gọi trực tiếp `.\.venv\Scripts\python.exe` thay cho `python` nếu chưa activate.

```powershell
python -m pytest -q
python -m pytest -q -m student -o addopts= -k workflow
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.benchmark --shapes workflow,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/workflow_baseline.json
```

- Smoke: `lab8.smoke pass`. Host gate mặc định sau khi thêm test: 75 passed, 248 deselected.
- Ma trận student của workflow: 62 passed, gồm T11 retry và T12 crash/resume.
- Test workflow bổ sung: 21 trường hợp, nằm trong host gate mặc định.
- Crash suite: 20/20. Suite này kiểm host và swarm; workflow được kiểm riêng trong test mới ở cả `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`.
- Workflow public benchmark: 70/70 trial đúng, pass rate = 1.0, pass^5 = 1.0, variance = 0, cost/success = 27.857142857142858 VND mô phỏng.
- Swarm cùng điều kiện: 69/70 trial đúng, cost/success = 49.56695652173913 VND mô phỏng. C-002 seed 55 là trial sai của swarm.
- Run id minh họa: `R-workflow-C-001-s11`, `R-workflow-C-002-s55`, `R-workflow-C-014-s55`.
- Các report JSON là output của CLI, không sửa tay. Trace và SQLite không commit.

Sau khi hai thành viên còn lại hoàn thiện shape, người tích hợp cần chạy:

```powershell
python -m pytest -q
python -m pytest -q -m student -o addopts=
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.check_submission
```

Nhóm dùng số liệu benchmark đủ bốn shape để chốt ADR, điền hash commit, research card và báo cáo chung. Chưa có kết quả hidden.

Kiểm tra bài nộp ở thời điểm bàn giao phần 1: `check_submission` xác nhận workflow pass 12/12 claim một lần chạy ở seed 11 và crash report 20/20. Toàn repo còn `4 FAIL, 1 WARN`: single và orchestrator còn stub, thiếu benchmark đủ bốn shape, research card trống và thay đổi chưa commit. Những mục này cần hoàn tất khi tích hợp phần của hai thành viên còn lại; bài nhóm chưa sẵn sàng nộp.

## 5. Công cụ AI đã dùng

Codex được dùng để đọc repo, triển khai workflow, viết test hồi quy, chạy kiểm tra và đọc trace.

## 6. Tự đánh giá

Phần workflow đã có code, test và bằng chứng public/crash. ADR vẫn là bản nháp vì chưa tích hợp single/orchestrator và chưa có hidden grader. Không suy kết quả MockLLM thành độ đúng hay latency của model sản xuất. Thông tin liên hệ và commit thật cần bổ sung trước khi nộp.
