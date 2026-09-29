# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: high_latency_p95
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack (#llmops-alerts)
- SLI/SLO liên quan: `fast_successful_requests` (latency_ms <= 3000ms đạt 99.5%)
- Điều kiện và thời gian duy trì: `p95_latency_ms > 3000` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng cảm nhận hệ thống phản hồi chậm chạp, trải nghiệm chat bị gián đoạn, nguy cơ time out ở client app.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel `Latency percentiles and TTFT`, kiểm tra xem latency tăng ở pha nào (TTFT do model hay pha retrieval vector search).
  2. Lọc log trong `data/logs.jsonl` tìm các request có `latency_ms > 3000`, lấy `correlation_id` của request bị ảnh hưởng.
  3. Mở Langfuse trace theo `correlation_id` đó, kiểm tra waterfall span tree để xác định span chậm (`retrieval` hay `generation`).
- Mitigation tạm thời: Bật cache cho RAG query, scale up instance hoặc hạ timeout retrieval xuống fallback answer nhanh.
- Owner: oncall-llmops

## Alert 2

- Tên: high_error_rate
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack (#llmops-incidents)
- SLI/SLO liên quan: Guardrail `error_rate_pct_max` <= 2%
- Điều kiện và thời gian duy trì: `error_rate_pct > 2.0` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận mã lỗi HTTP 500 hoặc thông báo lỗi hệ thống không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel `Error rate and retrieval success` trên dashboard để xem loại lỗi phổ biến (`error_type`).
  2. Tra cứu trong log line các event `request_failed` gần nhất kèm correlation_id và payload `detail`.
  3. Kiểm tra health check `/health` và endpoint upstream LLM/Vector store xem có incident downtime diện rộng hay không.
- Mitigation tạm thời: Chuyển hướng traffic sang model/cluster dự phòng (fallback provider), kích hoạt circuit breaker để tránh cascade failure.
- Owner: oncall-llmops

## Alert 3

- Tên: degraded_retrieval_success
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack (#llmops-alerts)
- SLI/SLO liên quan: Guardrail `retrieval_success_rate_pct_min` >= 90%
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90.0` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Chatbot trả lời chung chung (fallback answer) do không tìm thấy tài liệu ngữ cảnh, giảm chất lượng câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Xem tỷ lệ retrieval success trên dashboard panel `Error rate and retrieval success`.
  2. Lọc log có `tool_name == "retrieval"` và `tool_success == false` hoặc kiểm tra incident `tool_fail`.
  3. Mở trace trên Langfuse kiểm tra span `retrieval` để xem error log từ vector database connection.
- Mitigation tạm thời: Reset kết nối vector database client, kiểm tra quota cluster vector search hoặc chuyển sang dùng BM25/keyword fallback.
- Owner: oncall-llmops

