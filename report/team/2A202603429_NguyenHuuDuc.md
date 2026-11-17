# Báo cáo cá nhân - 2A202603429_NguyenHuuDuc

## 1. Thông tin thành viên

- Họ tên: Nguyễn Hữu Đức
- MSSV: 2A202603429
- Email: 26ai.ducnh3@vinuni.edu.vn
- GitHub: [@ducnguyen2112](https://github.com/ducnguyen2112)

## 2. Phần việc phụ trách

Triển khai workflow (shape được nhóm chọn trong ADR); thêm test nghiệp vụ, approval, retry/crash; kiểm host gate và crash suite; soạn ADR bản đầu để nhóm hoàn thiện sau khi benchmark đủ 4 shape.

## 3. Đóng góp cụ thể

- Commit: `0ef1f64` (triển khai `src/lab8/shapes/workflow.py`), `f909084` (thêm `src/tests/test_workflow.py`).
- `src/lab8/shapes/workflow.py`: các bước cố định đọc claim → kiểm order thuộc principal → tính quote → gọi host → trả `RunResult` bằng `finish()`.
- Dùng `compute_compensation` qua `dispatch`, không lấy số ngày hay chỉ dẫn từ ticket để quyết định tiền. Workflow không gọi model.
- Quote dương luôn chuyển đầy đủ cho `durability.issue_refund`; host kiểm approval và trừ tiền đã hoàn trước đó. Quote bằng 0 không gọi ghi refund.
- Phân biệt `denied` khi host từ chối và `failed` khi retry có amount conflict. Không bắt `InjectedCrash`; connection luôn đóng trong `finally`.
- Trace chỉ ghi metadata và dữ liệu qua allowlist; không ghi ticket hoặc claim/order row thô.
- `src/tests/test_workflow.py`: 21 trường hợp mới, gồm nhánh trả sớm, approval hỏng, trạng thái đơn không hợp lệ, policy tương lai, nhiều claim trên cùng đơn, conflict, ba điểm crash cho refund thường và top-up, cùng kiểm tra rò dữ liệu qua ticket.

## 4. Bằng chứng

Mọi lệnh sau chạy trong `src/`:

```powershell
python -m pytest -q
python -m pytest -q tests/test_workflow.py
python -m pytest -q -m student -o addopts= -k workflow
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
```

- Smoke: `lab8.smoke pass`. Host gate `python -m pytest -q` của cả nhóm: 123 passed.
- `tests/test_workflow.py`: 21 passed.
- Ma trận student của workflow: 62 passed, gồm T11 retry và T12 crash/resume.
- Crash suite: 20/20 (`src/reports/crash.json`). Suite này kiểm host và swarm; workflow được kiểm riêng trong test mới ở cả `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`.
- Benchmark public (`src/reports/benchmark.json`): workflow 70/70 trial đúng, pass rate 1.000, pass^5 1.000, variance 0, cost/success 27.86 VND mô phỏng (thấp nhất trong 4 shape). Swarm cùng điều kiện 0.986 / 0.929, 49.57 VND; C-002 seed 55 là trial sai của swarm.
- Run id minh họa: `R-workflow-C-001-s11`, `R-workflow-C-002-s55`, `R-workflow-C-014-s55`.
- Các report JSON là output của CLI, không sửa tay.

## 5. Công cụ AI đã dùng

- Công cụ: Codex.
- Mục đích: đọc repo và contract (`docs/business_rules.md`, `docs/contracts.md`), gợi ý khung các bước workflow, gợi ý danh sách trường hợp biên cho test hồi quy, hỗ trợ đọc trace.
- Cách tự kiểm tra:
  - Tự đọc lại từng nhánh trong `workflow.py`, đối chiếu với luật trong `docs/business_rules.md` (nguồn sự thật là order row và policy `is_current`, host là bên ghi duy nhất).
  - Tự chạy `python -m pytest -q`, `tests/test_workflow.py`, ma trận student `-k workflow` và crash suite trên `.venv` cục bộ; số liệu trong báo cáo lấy từ output CLI và `src/reports/*.json`, không chép tay.
  - Mở trace `traces/R-workflow-*.json` để chắc không có ticket, SĐT, địa chỉ, tên hàng hay canary.

## 6. Tự đánh giá

- Làm tốt: workflow qua toàn bộ test student, 21 test hồi quy riêng, là shape rẻ nhất và tất định nên được nhóm chọn trong ADR.
- Hạn chế: lúc đầu làm benchmark riêng workflow so với swarm; số liệu cuối dùng `src/reports/benchmark.json` đủ 4 shape do nhóm chạy sau khi tích hợp.
- Không suy kết quả MockLLM thành độ đúng hay latency của model sản xuất.
