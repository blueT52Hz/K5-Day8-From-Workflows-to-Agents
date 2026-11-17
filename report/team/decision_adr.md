# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: b612394 (nhánh main; 3 shape, bonus và `src/reports/*.json` đều nằm trong commit này)
- Run id dẫn chứng: R-workflow-C-002-s55 (đúng `denied`, so với R-swarm-C-002-s55 sai `resolved`), R-workflow-C-007-s11 (approval hết hạn → `denied`), R-workflow-C-012-s11 (crash / resume, 1 refund)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000-1.000 / 0.000000 (src/reports/benchmark.json, 14 claim public × seed 11,22,33,44,55)
- Cost per success (mô phỏng, VND): 27.86 (single 37.85, orchestrator 38.03, swarm 49.57)
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 (quét 860 trace public + hidden của 3 shape, không có `print` trong shape; C-007, C-013 ra `denied`, không có dòng refund)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Trên cùng corpus (14 claim public) và cùng 5 seed (70 trial mỗi shape), workflow, single và orchestrator đều đạt pass 1.000, pass^5 1.000, variance 0. Swarm đạt 0.986 / 0.929 vì ở seed 55 nó tin số ngày trễ ghi trong ticket (C-002: ticket nói 5 ngày, đơn ghi 2 ngày) và trả 20.000 cho một claim lẽ ra phải từ chối. Khi độ đúng ngang nhau, nhóm chọn shape ít tự chủ nhất và rẻ nhất. Workflow có cost/success thấp nhất (27.86 VND), 0 model call, mean steps 4.43 (p95 5). Mọi quyết định tiền đều do code tính từ order row và policy `is_current`, nên kết quả không phụ thuộc seed.

## Có đáng đổi lấy multi-agent không

Không. Trên public, orchestrator không đúng hơn workflow (cùng 1.000) nhưng đắt hơn 36% (38.03 so với 27.86 VND), vì tốn thêm 1.79 model call và gần 1 tool call mỗi trial (investigator đọc lại claim). Swarm vừa đắt hơn 78% vừa sai ở seed 55. Single đắt hơn 36% (37.85 VND, 2 model call và 3.64 tool call mỗi trial) và dùng nhiều bước hơn (6.36 so với 4.43) mà không đổi kết quả. Kể cả khi một shape nhiều agent đúng hơn chút ít, nhóm vẫn giữ workflow nếu phần đúng thêm đó đi kèm variance khác 0 hoặc cost tăng hơn khoảng 30%: một hệ thống xử lý tiền cần kết quả lặp lại được. Quyết định sẽ đảo lại nếu: (1) bộ hidden có dạng claim mà luật cố định không biểu diễn được (ví dụ cần đọc hiểu bằng chứng dạng văn bản tự do) khiến workflow rớt dưới 0.75, trong khi shape agentic vượt ngưỡng với pass^5 ổn định; hoặc (2) số loại claim tăng tới mức bảo trì nhánh if/else đắt hơn chi phí model. Bonus B3 (`report/team/bonus_report.md`) củng cố thêm: thêm verifier bằng code đưa swarm lên 1.000 / 1.000 nhưng cost/success vẫn gấp khoảng 1,8 lần workflow.

## Trace và bằng chứng

Cả 3 shape ghi `traces/<run_id>.json` (`{run_id, steps, events}`) trên mọi nhánh return. Workflow ghi `claim` (`claim_id`, `found`), `lookup_order` (view đã allowlist do tool trả về), `quote`, `refund` (`ok`, `reason`, `conflict`), `decision`. Single ghi `react_step` (bước, tool), `observation` (`visible`, `reason`, số lần và số tiền đã hoàn), `quote`, và `crash` (`at`) khi crash. Orchestrator ghi `handoff` qua `safe_dump`, `investigator` (`order_id`, `visible`, `reason`), `quote`, `issue_refund`, `decision`, `crash`. Field cố ý **không** ghi: ticket, claim row, order row, SĐT, địa chỉ, tên hàng, internal note, `parent_secret`, raw headers. Ticket là dữ liệu người dùng không tin cậy và có thể chứa PII. Các row thô chứa secret và PII mà quyết định không cần. Bằng chứng không lộ secret không chỉ dựa vào scanner: (1) dữ liệu được allowlist ngay tại nguồn, vì `get_claim_view` và `lookup_order` chỉ trả các cột cho phép, nên kể cả khi workflow ghi nguyên view của `lookup_order` thì view đó cũng không có SĐT, địa chỉ, tên hàng, internal note; (2) `make_handoff` / `sanitize` từ chối payload chứa canary hoặc tool ghi; (3) workflow không gọi model; orchestrator chỉ gửi id cho MockLLM; single có gửi ticket cho MockLLM để parse nhưng kết quả không dùng cho quyết định tiền và MockLLM không ghi prompt ra đâu cả; (4) không có `print` trong shape; (5) nhóm đã quét lại 860 trace public và hidden của 3 shape tìm `CANARY_SECRET_`, `CANARY_INTERNAL_`, địa chỉ, tên hàng, `parent_secret`, `raw_headers`, `Bearer` và mẫu SĐT, kết quả 0 match.

## Giới hạn

MockLLM không phải model sản xuất: text của nó không ảnh hưởng quyết định, nên số model call chỉ phản ánh cost, không phản ánh độ đúng của một LLM thật. Latency để `unavailable`. Cost là VND mô phỏng theo `src/config/pricing.yaml`, không phải hóa đơn API. Pass rate đo trên 14 claim public. Tự kiểm hidden (`src/reports/hidden_selfcheck.json`, `student_drop/` không nhãn): 40 claim × 5 seed × 3 shape = 600 trial, 0 trial `error`, 0 `leak_suspect`, trace đúng contract; pass rate hidden chính thức do grader của giảng viên chấm. Không sửa JSON cho đủ 0.75.
