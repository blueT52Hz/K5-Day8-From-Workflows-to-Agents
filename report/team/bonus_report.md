# Bonus report: B3

- Topic + nguồn (tên, năm, slide): B3 · Verifier/aggregator chống khuếch đại lỗi. Google Research 2026, *Towards a Science of Scaling Agent Systems* (error amplification). Slide 17 (Evaluator-optimizer), 22 (Reflection), 42.
- CLAIM của nguồn (1 câu): Agent độc lập khuếch đại lỗi tới 17,2×, còn orchestration tập trung (có điểm kiểm soát chung) chỉ khuếch đại 4,4×.
- BOUNDARY (model / dataset / setup): LLM thật, nhiều benchmark agentic tổng quát, đo tỉ lệ lỗi lan truyền qua nhiều agent. Không phải task tiền tệ có ledger, và không có "nguồn sự thật có cấu trúc" để đối chiếu.
- HYPOTHESIS trên LogiX: Thêm một verifier bằng code trước bước ghi, đối chiếu mọi dữ kiện dùng để quote với order row có cấu trúc, sẽ chặn được lỗi swarm mang từ ticket sang. Khi đó swarm_verified đạt pass rate và pass^5 bằng workflow, nhưng cost/success vẫn cao hơn vì phần peer/parse không bị bỏ.
- Biến cố định / biến thay đổi: Cố định claim, seed (11, 22, 33, 44, 55), pricing, MockLLM, evaluator (`lab8.benchmark`), host durability/policy. Biến thay đổi duy nhất: có hay không bước `verify_quote_inputs` (so `swarm` với `swarm_verified`). `workflow` là baseline.
- Lệnh tái lập (copy-paste được, chạy trong `src/`):
  ```
  python -m pytest -q tests/test_bonus_swarm_verified.py
  python -m lab8.benchmark --shapes workflow,swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json
  python -m lab8.benchmark --shapes workflow,swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --cases bonus/cases.jsonl --world bonus/world.json --seeds 11,22,33,44,55 --out reports/bonus_adversarial.json
  python -m bonus.report_interventions --out reports/bonus_verifier.json
  ```
- File report + run id: `src/reports/bonus_benchmark.json` (public, 14 claim), `src/reports/bonus_adversarial.json` (10 claim tự viết B-001..B-010, nhãn viết tay, dữ liệu ở `src/bonus/cases.jsonl` + `src/bonus/world.json`), `src/reports/bonus_verifier.json`. Code: `src/bonus/swarm_verified.py`, test: `src/tests/test_bonus_swarm_verified.py`. Trace minh họa: `R-swarm_verified-C-002-s55`, so với `R-swarm-C-002-s55`.

## Kết quả

Public, 14 claim × 5 seed = 70 trial mỗi shape:

| Shape | Pass | pass^5 | Variance | Seed min-max | Cost/success (VND) | Model call TB | Tool call TB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 0 | 1.000-1.000 | 27.86 | 0.00 | 2.79 |
| swarm | 0.986 | 0.929 | 0.000816 | 0.929-1.000 | 49.57 | 3.00 | 4.66 |
| swarm_verified | 1.000 | 1.000 | 0 | 1.000-1.000 | 49.00 | 3.00 | 4.67 |

Bộ đối kháng tự viết, 10 claim × 5 seed = 50 trial mỗi shape:

| Shape | Pass | pass^5 | Variance | Seed min-max | Cost/success (VND) | Model call TB | Tool call TB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 0 | 1.000-1.000 | 30.00 | 0.00 | 3.00 |
| swarm | 0.900 | 0.500 | 0.040000 | 0.500-1.000 | 59.50 | 3.00 | 5.12 |
| swarm_verified | 1.000 | 1.000 | 0 | 1.000-1.000 | 54.75 | 3.00 | 5.24 |

Swarm fail 5/50, tất cả ở seed 55: B-001, B-004, B-009 (nói quá → trả tiền sai), B-002 (nói thiếu → từ chối oan), B-008 (nói quá + approval hết hạn: host chặn tiền nhưng `proposal_amount` sai). B-003 (nói dối hỏng hàng), B-005, B-007, B-010 không fail, vì swarm không tin ticket ở các field đó.

Verifier (`src/reports/bonus_verifier.json`): kiểm tra 110/120 run (10 run còn lại là C-004 `needs_info` và C-005 `escalated`, dừng trước bước quote). Can thiệp **7 lần**, đều ở seed 55 và đều trên field `delay_days`. 6/7 lần đổi số tiền: C-002 20.000→0, B-001 30.000→0, B-002 0→25.000, B-004 20.000→0, B-008 40.000→0, B-009 15.000→0. B-006 can thiệp nhưng số tiền giữ nguyên 120.000, vì khoản hỏng hàng lớn hơn phí ship.

Safety counts (cả 2 bộ, 3 shape): approval bypass 0 (ledger mọi trial khớp nhãn, B-008 có approval hết hạn không có dòng refund nào), secret leak 0 (benchmark không có trial `leak_suspect`; quét 120 trace `R-swarm_verified-*` tìm `CANARY_SECRET_`, `CANARY_INTERNAL_`, `parent_secret`, `raw_headers`, SĐT đều 0), crash: test `test_swarm_verified_crash_keeps_one_refund` vẫn đúng 1 refund. `pytest -q` (trong `src/`): 98 passed (54 + 44 test bonus).

Trace minh họa `R-swarm_verified-C-002-s55`: `handoff` → `investigator` (visible) → `model_override` {delay_days: 5} → `verifier` {mismatched: [delay_days]} → `verifier_override` {before 20000, after 0} → `quote` 0 → `decision` denied 0.

## Kết luận

**Ủng hộ** hypothesis, trong phạm vi LogiX. Verifier tập trung đưa swarm từ 0.986 / 0.929 (public) và 0.900 / 0.500 (đối kháng) lên 1.000 / 1.000 trên cả 2 bộ, variance về 0. Đây là ví dụ thu nhỏ của claim nguồn: lỗi sinh ra ở một agent (tin ticket) không được đi tới bước ghi khi có một điểm kiểm soát chung. Tuy vậy, verifier **không** làm swarm rẻ như workflow: cost/success vẫn gấp khoảng 1,76× (49.00 so với 27.86) trên public và 1,83× (54.75 so với 30.00) trên bộ đối kháng. Tổng cost chỉ tăng khoảng 0,3% (public) và 2% (đối kháng) so với swarm, vì mỗi lần can thiệp chỉ tốn 1 tool call. Cost/success của swarm_verified thấp hơn swarm là nhờ số trial pass tăng.

Swarm còn giữ lại giá trị gì khi verifier đã thay phần quyết định? Trên LogiX thì **gần như không còn**. Mọi dữ kiện quyết định tiền đều có nguồn có cấu trúc, nên các lần gọi `peer` / `parse` chỉ tốn cost. Giá trị duy nhất còn lại là phần đọc ticket để soạn câu trả lời cho khách, mà việc này không ảnh hưởng tiền. Vì vậy kết quả bonus củng cố quyết định chọn workflow trong ADR, chứ không thay đổi nó.

Kết luận đảo lại khi: (1) dữ kiện quyết định **không có** nguồn có cấu trúc để đối chiếu (ví dụ hỏng hàng chỉ chứng minh được bằng mô tả hay ảnh), lúc đó verifier bằng code không kiểm được và giá trị của agent đọc hiểu tăng lên; (2) chính order row sai, vì verifier tin tuyệt đối dữ liệu có cấu trúc; (3) lỗi nằm ở field ngoài `VERIFIED_FIELDS` (ví dụ chọn sai policy), verifier hiện tại không thấy.

## Giới hạn

- MockLLM không phải model thật. Lỗi của swarm là **một** chế độ lỗi tất định (seed % 5 == 0 tin số ngày trong ticket), không phải phân bố lỗi của LLM. Vì vậy không so được trực tiếp hệ số 17,2× / 4,4× của nguồn.
- Bộ đối kháng chỉ có 10 claim, nhãn do nhóm tự viết tay theo luật trong README. Chúng phủ các kiểu nói quá, nói thiếu, nói dối hỏng hàng, nhiều con số, đúng ngưỡng, vừa trễ vừa hỏng, status không hợp lệ, approval hết hạn, đã hoàn một phần.
- Latency `unavailable`. Cost là VND mô phỏng theo `config/pricing.yaml`.
- Verifier chỉ kiểm input của quote, không kiểm bản thân policy (đã do `compute_compensation` lấy policy `is_current`).
