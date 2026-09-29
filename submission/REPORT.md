# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Ngô Kỳ Anh
- **MSSV:** 2A202602916
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/glacerjust/K4-L3A-Day13-NgoKyAnh-02916-Monitoring-LLMOps
- **Commit SHA cuối:** d8a05c082ae6b3e6fc05cfcdae2f0ce64cd0842a
- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602916`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đầy đủ required fields, correlation ID, enrichment và che PII |
| `validate_dashboard.py` | 6/6 panel hợp lệ | 6/6 panel hợp lệ | Đạt 6/6 panel theo dashboard contract |
| `pytest` | 22/22 passed | 25/25 passed | Đạt 100% tests (bổ sung test PII CCCD, thẻ, passport) |
| Số traces hợp lệ | 0 | 10+ traces | Trace có root, retrieval span và generation trên Langfuse |
| Số PII leak | 0 | 0 | Không phát hiện rò rỉ PII ở log lẫn trace |
| Latency P95 / TTFT P95 | ~1782ms / Chưa đo | ~163ms / 50ms | Latency phản hồi nhanh và ổn định |
| Retrieval success rate | Chưa đo | 100% | 10/10 request retrieval thành công |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware`, trước mỗi request gọi `clear_contextvars()` để tránh rò rỉ context giữa các request. Nhận `x-request-id` từ client header hoặc sinh mới bằng `req-{uuid4().hex[:8]}`. Dùng `bind_contextvars(correlation_id=correlation_id)` và lưu `request.state.correlation_id` để endpoint `/chat` trả về trong response body và response header.
- **Các metadata được ghi vào structured log:** `ts` (ISO 8601 UTC), `level`, `service`, `event`, `correlation_id`, `env`, `user_id_hash` (băm SHA256 12 hex), `session_id`, `feature`, `model`, `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`, và `payload`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Xây dựng hàm `scrub_event` quét đệ quy chuỗi, dict, list bằng các regex pattern trong `PII_PATTERNS` (email, SĐT VN, CCCD, thẻ ngân hàng, hộ chiếu) và thay thế bằng `[REDACTED_...]`. Đăng ký `scrub_event` vào pipeline structlog ngay trước `JsonlFileProcessor` và `JSONRenderer`.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` kiểm tra schema, rò rỉ PII, số lượng correlation ID và log enrichment, đạt điểm số 100/100. Chạy toàn bộ 25 unit tests qua `python -m pytest -q` pass 100%.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Cấu hình API keys của project cá nhân `day13-k4-l3a-2A202602916` vào file `.env`. Trong UI Langfuse, trace list hiển thị đúng project name này cùng các metadata `correlation_id` khớp với `data/logs.jsonl`.
- **Cấu trúc root/retrieval/generation observations:** Root observation là `lab-agent-run` (type `agent`), chứa 2 child observations: `retrieval` (type `span` đo thời gian và số lượng tài liệu retrieved) và `generation` (type `generation` chứa model name, prompt text, response output, usage chi tiết input/output tokens và cost).
- **Cách nối trace với log:** Gắn cùng một mã `correlation_id` (ví dụ `req-xxxxxxxx`) vào `metadata` của trace/span trên Langfuse và trường `correlation_id` trong mỗi log record của `data/logs.jsonl`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 (label: `baseline`, `production`)
- **Version/label candidate:** Version 2 (label: `candidate`)
- **Trace ID của mỗi version:** Version 1: `c3d3c706eb230cd320b8e848e03259c6` | Version 2: `ac8694063ecf0ea4aca8e4ca8777194d`
- **Cách promote và rollback `production`:** Trên Langfuse UI, mở prompt `day13-chat`, tại mục Versions, chuyển label `production` từ v1 sang v2 (promote), sau đó chuyển ngược lại từ v2 về v1 (rollback).

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** 6 panel được định nghĩa chuẩn trong `config/dashboard.yaml`:
  1. `latency`: P50, P95, P99 latency và TTFT P95 (ngưỡng P95 <= 3000ms).
  2. `traffic`: Tốc độ request mỗi phút (rate_per_minute >= 1).
  3. `errors`: Tỷ lệ lỗi request_failed (%) và tỷ lệ retrieval tool success (%) (ngưỡng error_rate <= 2%).
  4. `cost`: Tổng chi phí tích lũy theo USD (ngưỡng total <= 2.5$).
  5. `tokens`: Tổng lượng input và output tokens (ngưỡng sum <= 50,000 tokens).
  6. `quality`: Điểm đánh giá chất lượng trung bình theo heuristic (ngưỡng mean >= 0.75).
- **SLO và lý do chọn:** Primary SLO `fast_successful_requests` với mục tiêu 99.5% request hoàn thành thành công và có `latency_ms <= 3000ms` trong chu kỳ rolling 28 ngày. Lý do chọn: 3000ms là ngưỡng thời gian tối đa để đảm bảo trải nghiệm tương tác chat không bị gián đoạn, kết hợp đo lường cả tính sẵn sàng lẫn hiệu năng hệ thống.
- **Cách tính error budget:** Error budget = 100% - Target SLO = 100% - 99.5% = 0.5% tổng số requests. Trong chu kỳ 28 ngày với 100,000 requests, ngân sách cho phép tối đa 500 requests bị chậm (> 3000ms) hoặc bị lỗi (HTTP 500 / request_failed).
- **Ba alert và runbook tương ứng:** Cấu hình tại `config/alert_rules.yaml` và runbook tại `docs/alerts.md`:
  1. `high_latency_p95` (Warning, 5m): P95 latency > 3000ms trong 5 phút. Runbook: `docs/alerts.md#alert-1`.
  2. `high_error_rate` (Critical, 5m): Tỷ lệ lỗi > 2.0% trong 5 phút. Runbook: `docs/alerts.md#alert-2`.
  3. `degraded_retrieval_success` (Warning, 5m): Tỷ lệ retrieval thành công < 90% trong 5 phút. Runbook: `docs/alerts.md#alert-3`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-29T15:33:30+07:00 đến 2026-09-29T15:34:05+07:00 (tương ứng 08:33:30Z đến 08:34:05Z UTC)
- **Triệu chứng từ metrics:** P95 / Tail latency tăng đột biến từ ~160ms lên 2654ms (thời gian xử lý tại server) và lên tới 10,644ms – 13,305ms (roundtrip time client đo được khi chạy 5 request đồng thời). Vi phạm nghiêm trọng SLO P95 <= 3000ms và vượt ngưỡng `latency_threshold_ms: 2000ms` của challenge.
- **Log line và correlation ID liên quan:**
  - Correlation ID: `req-9766e8d4` (feature: `monitoring`, session: `k4-l3a-challenge-s04`)
  - Log line (trích từ `data/logs.jsonl`):
    `{"service": "api", "latency_ms": 2653, "ttft_ms": 50, "tokens_in": 45, "tokens_out": 111, "cost_usd": 0.0018, "quality_score": 0.9, "tool_name": "retrieval", "tool_success": true, "payload": {"answer_preview": "Starter answer. You should improve this output logic and add better quality chec..."}, "event": "response_sent", "correlation_id": "req-9766e8d4", "session_id": "k4-l3a-challenge-s04", "feature": "monitoring", "model": "claude-sonnet-4-5", "user_id_hash": "4570299f37e2", "env": "dev", "level": "info", "ts": "2026-09-29T08:33:49.611573Z"}`
- **Trace ID và span gây ảnh hưởng:**
  - Correlation ID: `req-9766e8d4`
  - Span gây ảnh hưởng: Span con **`retrieval`** bị chậm bất thường, tiêu tốn tới 2.50s (~94% tổng latency của trace), trong khi span `generation` chỉ mất 0.15s (150ms).
- **Root cause:** Sự cố `rag_slow` được kích hoạt trên hệ thống khiến component RAG retrieval bị nghẽn (mô phỏng bởi lệnh `time.sleep(2.5)` trong hàm `retrieve()`). Khi nhiều request đồng thời gửi tới tính năng `monitoring`, các request bị dồn ứ hàng đợi dẫn đến latency tăng vọt từ 2.6s lên tới hơn 13s ở phía client.
- **Fix action:**
  - Vô hiệu hóa sự cố bằng endpoint `/incidents/rag_slow/disable` để khôi phục tốc độ xử lý bình thường.
  - Trên môi trường production thực tế: Tối ưu vector database query (thêm index HNSW/IVF), scale up số lượng node/replica cho vector store, và bổ sung cache tầng ứng dụng (semantic cache).
- **Preventive measure:**
  - Kích hoạt alert `high_latency_p95` (duration 5m) gửi thông báo về Slack ngay khi P95 vượt 3000ms.
  - Bổ sung cơ chế timeout (ví dụ: `timeout=1500ms`) và circuit breaker cho bước retrieval: nếu vector DB không phản hồi trong 1.5s thì tự động fallback trả về context mặc định hoặc thông báo bận, ngăn chặn hiện tượng nghẽn luồng domino trên toàn bộ server.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Đặt processor `scrub_event` vào pipeline structlog ngay trước `JsonlFileProcessor` và `JSONRenderer`. Lý do: Đảm bảo dữ liệu nhạy cảm PII luôn được che chắn ở tầng pipeline xử lý tập trung trước khi serialize thành chuỗi và lưu vào đĩa cứng hoặc stream ra ngoài, tránh việc bỏ sót PII nếu lập trình viên quên gọi hàm scrub ở từng log riêng lẻ.
- **Một lỗi/blocker đã gặp:** Gặp lỗi `[WinError 10061]` khi chạy `load_test.py` lần đầu do server FastAPI/uvicorn chưa được bật; và lỗi fallback prompt `LangfuseFallback` khi chưa tạo prompt `day13-chat` trên Langfuse Cloud.
- **Cách tìm nguyên nhân và xử lý:** Đọc log traceback và đối chiếu hướng dẫn trong README.md để khởi động server trên terminal riêng; truy cập Langfuse Cloud tạo prompt `day13-chat` với các label `baseline` và `production` để app fetch prompt thành công.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  1. *Metrics:* Phát hiện triệu chứng bất thường tổng thể (ví dụ: P95 latency tăng vọt, error rate vượt ngưỡng 2%) và xác định khung thời gian xảy ra sự cố.
  2. *Logs:* Lọc log trong khoảng thời gian xảy ra sự cố để tìm chính xác các request bị ảnh hưởng (dựa trên `status_code`, `request_failed`, `event`), từ đó lấy được mã `correlation_id` duy nhất của request lỗi.
  3. *Traces:* Dùng `correlation_id` để tra cứu trace chi tiết trên Langfuse, mở waterfall span tree để khoanh vùng chính xác span con nào (retrieval chậm, vector store timeout, hay LLM generate bị loop) là nguyên nhân gốc rễ (root cause).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - *Prompt version & rollback:* Cho phép quản trị prompt như code, có thể triển khai prompt candidate và rollback về baseline ngay lập tức khi phát hiện hallucination hoặc suy giảm chất lượng mà không cần deploy lại ứng dụng.
  - *Token/cost:* Giúp theo dõi chi phí tiêu hao của từng phiên bản prompt/model, phát hiện sớm các hiện tượng prompt injection hoặc loop sinh token bất thường (cost spike).
  - *SLO & Error Budget:* Cung cấp hợp đồng cam kết chất lượng dịch vụ cho người dùng, là cơ sở để quyết định tốc độ release tính năng mới so với việc ưu tiên ổn định hệ thống.
- **Điều quan trọng nhất đã học:** Hiểu sâu sắc quy trình quan sát toàn diện (Observability) cho hệ thống AI/LLM kết hợp giữa structured logging (truyền correlation context), telemetry metrics, và distributed tracing (span tree cha-con).
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Không có; đã hoàn thành đầy đủ các yêu cầu từ CP0 đến CP4, điều tra và tái hiện thành công sự cố challenge `day13-k4-l3a-monitoring-llmops-v1`.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
