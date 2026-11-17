# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 · Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST), NeurIPS 2025, https://arxiv.org/abs/2503.13657. Loại bằng chứng: phân tích định tính có gắn nhãn trên trace của nhiều framework multi-agent mã nguồn mở, kèm đo độ đồng thuận giữa người gắn nhãn |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lỗi của hệ multi-agent gom được vào 3 nhóm: (1) đặc tả và thiết kế hệ thống, (2) lệch phối hợp giữa các agent, (3) kiểm chứng và kết thúc nhiệm vụ. Nhiều lỗi đến từ thiết kế hệ thống và thiếu bước kiểm chứng, không chỉ do năng lực của model |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | LLM thật, task tổng quát (lập trình, toán, hỏi đáp) trên các framework như ChatDev, MetaGPT, AG2. Không có ledger tiền tệ, không có nguồn sự thật có cấu trúc để đối chiếu. Lab dùng MockLLM với một chế độ lỗi tất định, nên chỉ kiểm được việc phân loại, không kiểm được tỉ lệ giữa các nhóm |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Các trial fail của swarm ở seed 55 đều thuộc nhóm (3), lỗi kiểm chứng: quote dùng số ngày trễ trong ticket mà không đối chiếu với order row (FM-3.3 *incorrect verification*; phụ là FM-2.5 *ignored other agent's input*, vì investigator đã trả order row đúng). Nếu đúng vậy, bật một verifier bằng code trước bước ghi sẽ sửa **toàn bộ** các trial fail đó: pass^5 của swarm từ 0.929 lên 1.000 trên public, variance về 0, cost/success tăng không quá 5% |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định: MockLLM, tool manifest 1.1, seed 11,22,33,44,55, corpus 14 claim public, `config/pricing.yaml`, evaluator `lab8.benchmark`, host durability/policy, toàn bộ code swarm (kể cả `REFERENCE_WEAKNESS`). Biến duy nhất được thay đổi: có hay không bước `verify_quote_inputs` (`swarm` so với `swarm_verified`, `src/bonus/swarm_verified.py`) |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: swarm trả tiền cho claim lẽ ra bị từ chối (C-002, seed 55). Đo bằng pass rate, pass^5, variance, cost/success từ `src/reports/bonus_benchmark.json`, số lần can thiệp từ `src/reports/bonus_verifier.json`. Kiểm thêm leak và bypass phải giữ 0 |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn, trong `src/`): `python -m lab8.benchmark --shapes workflow,swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json` rồi `python -m bonus.report_interventions --out reports/bonus_verifier.json`
- Run id / file report: `src/reports/bonus_benchmark.json`, `src/reports/bonus_verifier.json`. Trial fail duy nhất của swarm trên public: `R-swarm-C-002-s55` (`resolved` thay vì `denied`, trả 20.000). Sau verifier: `R-swarm_verified-C-002-s55` có event `verifier_override` {fields: [delay_days], before_vnd: 20000, after_vnd: 0} và ra `denied`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng.** Lỗi duy nhất của swarm trên public là lỗi kiểm chứng (FM-3.3): dữ kiện `delay_days` lấy từ ticket không được đối chiếu với order row. Bật verifier: pass 0.986 → 1.000, pass^5 0.929 → 1.000, variance 0.000816 → 0. Cost/success 49.57 → 49.00 (tổng cost tăng khoảng 0,3%, cost/success giảm vì số trial pass tăng). Trên bộ đối kháng 10 claim tự viết, cả 5 trial fail của swarm (B-001, B-002, B-004, B-008, B-009, đều seed 55) cũng cùng một loại lỗi và đều được verifier sửa: pass^5 0.500 → 1.000. Không có lỗi nào thuộc nhóm (1) đặc tả hay lỗi giao việc khác thuộc nhóm (2).
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Lỗi của swarm là một chế độ lỗi tất định (seed % 5 == 0 tin ticket), nên chỉ có 1 failure mode xuất hiện; không so được phân bố giữa 3 nhóm của MAST. Bộ đối kháng do nhóm tự viết nhãn.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
