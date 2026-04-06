# Plan 02 — External API integration (nâng cấp sau khi mock ổn định)

**Mục tiêu:** Sau khi Plan 01 đã ổn định, tích hợp API ngoài theo từng tool để tăng tính thực tế, nhưng vẫn đảm bảo demo an toàn bằng cơ chế fallback.

**Điều kiện tiên quyết (bắt buộc):**

- [ ] Hoàn thành toàn bộ quality gate trong [PLAN-01-MOCK-FIRST-IMPLEMENTATION.md](PLAN-01-MOCK-FIRST-IMPLEMENTATION.md)
- [ ] Có baseline metric của mock phase để so sánh trước/sau tích hợp live API

**Nhà cung cấp đã chốt:**

- **Exchange rate:** `ExchangeRate.host`
- **Weather:** `Open-Meteo`
- **Places:** `Foursquare Places`

---

## 1. Tracking board cho AI agent

| ID | Task | Owner | Status | Evidence |
|----|------|-------|--------|----------|
| P2-T01 | Thêm config provider mode cho từng tool (`mock/live/auto`) | AI | todo | Settings + README |
| P2-T02 | Tích hợp live cho `get_exchange_rate` (ExchangeRate.host) | AI | todo | Response mapping + tests |
| P2-T03 | Tích hợp live weather tool (Open-Meteo) | AI | todo | Response mapping + tests |
| P2-T04 | Tích hợp live places cho `search_destination_tips` (Foursquare) | AI | todo | Response mapping + tests |
| P2-T05 | Implement timeout/retry/fallback policy | AI | todo | Error path logs |
| P2-T06 | Ghi metric phân tách `source=mock/live/fallback` | AI | todo | SQL/log sample |
| P2-T07 | Chạy regression 5 test case + so sánh với mock phase | AI | todo | Bảng before/after |
| P2-T08 | Cập nhật trace RCA cho lỗi external API | AI | todo | 1 trace integration failure |
| P2-T09 | Chốt demo script có phương án internet lỗi | AI | todo | Demo checklist |

---

## 2. Thiết kế tích hợp theo từng tool

### 2.1 `get_exchange_rate` -> ExchangeRate.host

- Input nội bộ: `from_currency`, `to_currency`, `amount`
- Output nội bộ giữ nguyên như mock phase.
- Mapping:
  - Nếu API trả rate hợp lệ -> `source=live`
  - Nếu API lỗi/timeout -> fallback mock -> `source=fallback_mock`
- Ghi metric:
  - `event_type=tool_call`, `metadata.provider=exchangerate_host`

### 2.2 Weather tool -> Open-Meteo

- Tool mới hoặc mở rộng từ `search_destination_tips`.
- Bước gọi:
  - geocoding (tọa độ từ city)
  - weather endpoint (theo lat/lon)
- Chuẩn hóa output về text ngắn gọn cho agent.
- Nếu lỗi: fallback dữ liệu thời tiết mock theo city.

### 2.3 `search_destination_tips` -> Foursquare Places

- Query places theo city/query.
- Chuẩn hóa tối đa 5 kết quả:
  - name
  - category
  - area/distance (nếu có)
- Nếu quota/rate limit/lỗi mạng: fallback tips mock.

---

## 3. Chính sách vận hành an toàn (bắt buộc)

Mỗi tool external áp dụng 3 mode:

- `mock`: chỉ dùng dữ liệu nội bộ.
- `live`: chỉ gọi API ngoài.
- `auto`: gọi live, lỗi thì fallback mock.

Khuyến nghị demo:

- Bình thường chạy `auto`.
- Trước demo có thể ép `mock` nếu mạng không ổn định.

Policy kỹ thuật:

- Timeout: 2–5s mỗi request.
- Retry: tối đa 1–2 lần.
- Circuit-like behavior đơn giản:
  - nếu fail liên tiếp nhiều lần thì tự chuyển `fallback_mock` trong phiên hiện tại.

---

## 4. Biến môi trường đề xuất

| Biến | Mô tả |
|------|--------|
| `EXCHANGE_RATE_PROVIDER` | `mock` / `live` / `auto` |
| `WEATHER_PROVIDER` | `mock` / `live` / `auto` |
| `PLACES_PROVIDER` | `mock` / `live` / `auto` |
| `FOURSQUARE_API_KEY` | API key cho Foursquare Places |
| `EXTERNAL_API_TIMEOUT_MS` | Timeout mặc định cho HTTP client |

Ghi chú:

- `ExchangeRate.host` và `Open-Meteo` có thể dùng không key ở mức cơ bản.
- `Foursquare Places` cần key.

---

## 5. Đo lường và chứng minh ở phase external

Giữ nguyên các metric cũ, bổ sung:

- Tỷ lệ `source=live` vs `source=fallback_mock`
- Tỷ lệ lỗi theo từng provider
- Độ trễ theo từng provider

Nguồn dữ liệu:

- `lab_metric_log.metadata`:
  - `provider`
  - `source`
  - `http_status`
  - `duration_ms`
- `tool_invocation` (nếu bật):
  - `tool_name`, `result_ok`, `error_code`, `duration_ms`

---

## 6. Regression test bắt buộc

Chạy lại đúng 5 case từ Plan 01 trong 2 cấu hình:

1. `mock`
2. `auto` (live + fallback)

Kết quả cần có:

- Bảng so sánh trước/sau:
  - success rate
  - avg latency
  - avg steps
  - external error rate

---

## 7. Cổng chất lượng hoàn tất Plan 02

- [ ] Tất cả case pass trong `mock`.
- [ ] Tất cả case pass trong `auto` (cho phép fallback).
- [ ] Không có crash khi provider ngoài lỗi.
- [ ] Có bảng metric trước/sau rõ ràng.
- [ ] Có 1 trace lỗi external API + phân tích RCA + cách fallback xử lý.

---

## 8. Kết quả bàn giao của Plan 02

- Hệ thống chạy được theo cả mock và live/fallback.
- Tool external tích hợp theo nhà cung cấp đã chốt.
- Đủ dữ liệu để thuyết trình:
  - chứng minh ổn định (mock-first),
  - chứng minh nâng cấp (external-ready),
  - chứng minh kiểm soát rủi ro (fallback).
