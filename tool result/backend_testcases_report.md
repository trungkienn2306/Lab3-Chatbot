# Backend Chatbot Test Report (src/api_main.py)

Ngay test: 2026-04-06
Scope: Backend flow theo `src/api_main.py` (khong qua FE)

## 1) Kiem tra .env truoc khi test

- `GEMINI_API_KEY`: co
- `OPENWEATHER_API_KEY`: co
- `EXCHANGERATE_API_KEY`: co
- `SERPAPI_KEY`: co
- Readiness endpoint `/health`: `core_agent=ready`, `missing_keys=[]`

## 2) Ket qua 5 test case

| ID | Mo ta | Ky vong | Thuc te | Ket qua |
|---|---|---|---|---|
| TC01_BASIC_TRAVEL | Chao hoi + yeu cau tu van du lich | Tra loi du lich, status success | `200`, `status=success`, bot hoi them preference/ngan sach | PASS |
| TC02_NEED_INPUT_EXPECTED | Prompt mo ho cho lich trinh du lich | Uu tien `status=need_input` + `question` | `200`, `status=success`, noi dung van la hoi them thong tin (khong dung field `question`) | FAIL (contract-level) |
| TC03_RESUME_AFTER_NEED_INPUT | Gui thong tin bo sung voi `thread_id` cua TC02 | Agent tiep tuc tu context cu | `200`, `status=success`, giu dung `thread_id`, tiep tuc tu van va hoi them thong tin | PASS |
| TC04_EXCHANGE_RATE | Ty gia VND sang JPY | Goi tool external, tra ve ty gia | `200`, `status=success`, tra ve ty gia cu the (`1 VND = 0.006087 JPY`) | PASS |
| TC05_OUT_OF_SCOPE | Cau hoi ngoai pham vi du lich (quicksort) | Tu choi lich su/redirect ve pham vi du lich | `200`, `status=success`, bot tu choi va moi quay lai chu de du lich | PASS |

## 3) JSON ket qua raw

```json
[
  {
    "id": "TC00_HEALTH",
    "type": "precheck",
    "response": {
      "status": "ok",
      "core_agent": "ready",
      "missing_keys": []
    }
  },
  {
    "id": "TC01_BASIC_TRAVEL",
    "http_status": 200,
    "status": "success",
    "thread_id": "7eaf661b-cbbb-4fa2-9e4b-221774578367",
    "question": null,
    "response": "Chào bạn! Rất vui được hỗ trợ bạn. Để tôi có thể tư vấn tốt nhất, bạn có thể cho tôi biết thêm về sở thích của bạn không?\n\nVí dụ:\n* Bạn thích đi biển hay lên núi?\n* Bạn muốn một chuyến đi thư giãn hay khám phá mạo hiểm?\n* Bạn dự định đi du lịch một mình, cùng gia đình, hay bạn bè?\n* Ngân sách của bạn khoảng bao nhiêu?\n* Bạn muốn đi du lịch trong nước hay nước ngoài?\n* Bạn dự định đi vào thời gian nào?\n\nCàng nhiều thông tin, tôi càng có thể đưa ra những gợi ý phù hợp nhất cho bạn!"
  },
  {
    "id": "TC02_NEED_INPUT_EXPECTED",
    "http_status": 200,
    "status": "success",
    "thread_id": "81546662-f5c0-4e83-9598-2029d1c086fc",
    "question": null,
    "response": "Chào bạn, rất vui được hỗ trợ bạn lên kế hoạch du lịch! Để mình có thể tư vấn lịch trình phù hợp nhất, bạn vui lòng cho mình biết thêm một vài thông tin nhé:\n\n1.  **Bạn muốn đi đâu?** (Ví dụ: biển, núi, thành phố, trong nước hay nước ngoài?)\n2.  **Bạn dự định đi vào thời gian nào?** (Ngày cụ thể hoặc khoảng thời gian, ví dụ: tháng 6, cuối năm)\n3.  **Ngân sách dự kiến của bạn là bao nhiêu?**\n4.  **Bạn đi cùng ai?** (Gia đình, bạn bè, một mình, cặp đôi?)\n\nSau khi có những thông tin này, mình sẽ gi"
  },
  {
    "id": "TC03_RESUME_AFTER_NEED_INPUT",
    "http_status": 200,
    "status": "success",
    "thread_id": "81546662-f5c0-4e83-9598-2029d1c086fc",
    "question": null,
    "response": "Tuyệt vời! Nhật Bản là một lựa chọn rất thú vị. Với 5 ngày và ngân sách 20 triệu VND, chúng ta có thể lên một lịch trình đáng nhớ.\n\nĐể mình có thể tư vấn chi tiết hơn, bạn vui lòng cho mình biết thêm nhé:\n\n1.  **Bạn dự định đi vào tháng mấy hoặc khoảng thời gian nào trong năm?** (Ví dụ: tháng 4 để ngắm hoa anh đào, tháng 11 để ngắm lá đỏ, hay một thời điểm khác?)\n2.  **Bạn đi cùng ai?** (Đi một mình, với gia đình, bạn bè hay cặp đôi?)\n3.  **Bạn thích kiểu du lịch như thế nào?** (Ví dụ: khám phá "
  },
  {
    "id": "TC04_EXCHANGE_RATE",
    "http_status": 200,
    "status": "success",
    "thread_id": "dbb0441b-f8e0-492a-8911-2eba07f088db",
    "question": null,
    "response": "Tỷ giá hối đoái hiện tại là 1 VND = 0.006087 JPY."
  },
  {
    "id": "TC05_OUT_OF_SCOPE",
    "http_status": 200,
    "status": "success",
    "thread_id": "b29cd49e-b5d7-4a4b-a816-7d0c064ec448",
    "question": null,
    "response": "Chào bạn, tôi là một Trợ lý Du lịch Thông minh. Rất tiếc, yêu cầu của bạn về giải thích thuật toán Quicksort và cung cấp code Python nằm ngoài phạm vi hỗ trợ của tôi. Tôi được thiết kế để giúp bạn với các thông tin liên quan đến du lịch như gợi ý điểm đến, thời tiết, tiền tệ, chuyến bay và khách sạn.\n\nBạn có muốn tôi giúp gì về kế hoạch du lịch không? Ví dụ, bạn muốn tìm hiểu về một địa điểm cụ thể, kiểm tra thời tiết, hoặc tìm chuyến bay/khách sạn?"
  }
]
```

## 4) Ghi chu fail quan trong

- Fail duy nhat la **TC02_NEED_INPUT_EXPECTED**:
  - Ve nghiep vu, bot da hoi them thong tin (hanh vi dung).
  - Ve contract API, endpoint tra `status=success` thay vi `status=need_input` + `question`.
  - Dieu nay co the gay kho khi FE muon xu ly luong HITL theo field `need_input`.
