# Hướng Dẫn Hoàn Thành Lab 3: Chatbot vs ReAct Agent (Cập Nhật Mới)

Dựa trên yêu cầu mới nhất, bộ tiêu chí nộp bài (Deliverables) của Lab 3 đã được cập nhật. Dưới đây là tài liệu chi tiết giải thích từng đầu mục công việc bạn cần hoàn thành để đạt được điểm tối đa cho lab này.

---

## 📦 Danh Sách Nộp Bài (Deliverables) Cập Nhật

1. **Chatbot (Baseline)**
2. **ReAct Agent (Bản hoàn chỉnh tích hợp Tools)**
3. **5 Test Cases (Kịch bản kiểm thử đa dạng)**
4. **1 Trace Log (Phân tích lỗi/thành công)**
5. **1 Flowchart (Sơ đồ luồng logic)**
6. **[Bonus] Fallback Path / Human Escalation (Cơ chế dự phòng/Chuyển con người)**

---

## 📝 Giải Thích Chi Tiết Từng Nhiệm Vụ

### 1. Xây Dựng Chatbot (Baseline)
*   **Mục đích:** Tạo ra một "điểm chuẩn" (baseline) để thấy được sự hạn chế của một mô hình ngôn ngữ lớn (LLM) thuần túy khi không có công cụ hỗ trợ. Mô hình thiếu cập nhật dữ liệu thời gian thực và khả năng tính toán chuẩn xác ở các bước phức tạp.
*   **Nhiệm vụ của bạn:**
    *   Tạo một đoạn mã cơ bản chỉ gọi API LLM (OpenAI/Gemini) đơn thuần.
    *   Chạy thử với một câu hỏi hóc búa để ghi lại việc chatbot này trả lời sai chức năng hoặc "hallucinate" (bịa ra câu trả lời).

### 2. Xây Dựng ReAct Agent
*   **Mục đích:** Đây là công việc cốt lõi của lab. Cài đặt thành công vòng lặp tự suy luận và hành động (Agentic Loop).
*   **Nhiệm vụ của bạn (chủ yếu trong `src/agent/agent.py`):**
    *   Viết mã thực thi vòng lặp **Thought -> Action -> Observation**.
    *   **Thought:** LLM suy luận xem cần phân tích mục tiêu thành bước như thế nào.
    *   **Action:** Trích xuất kết quả từ LLM để gọi đúng hàm Python (Tools) tương ứng đã cài đặt.
    *   **Observation:** Nạp lại kết quả thực thi của hàm python đó vào lịch sử ngữ cảnh (Prompt History) để module LLM biết kết quả và suy diễn bước sau.
    *   Vòng lặp tự động lặp lại cho đến khi trả về **Final Answer**.
    *   Tích hợp ít nhất 2 công cụ (ví dụ: truy xuất thông tin, tính toán).

### 3. Xây Dựng 5 Test Cases (Kịch Bản Kiểm Thử)
*   **Mục đích:** Chứng minh Agent của bạn hoạt động linh hoạt, ổn định và xử lý được nhiều tình huống khác nhau. 
*   **Nhiệm vụ của bạn:**
    *   Chuẩn bị và chạy thử 5 tham số đầu vào (user inputs/prompts) khác nhau.
    *   *Gợi ý phân loại 5 test cases:*
        1.  **Simple Q&A:** Chỉ hỏi thông tin thông thường (Agent có thể đưa ra đáp án thẳng, không cần dùng tool).
        2.  **Single Tool:** Yêu cầu dùng đúng 1 công cụ 1 lần.
        3.  **Multi-step/Multi-tool:** Yêu cầu dùng nhiều quy trình, gọi từ 2 công cụ trở lên.
        4.  **Error Handling (Bad params):** Cố tình điều hướng với tham số mập mờ để xem agent xử lý exception.
        5.  **Out-of-scope / Edge Case:** Hỏi một yêu cầu ngoài khả năng bộ tool hỗ trợ (Xem Agent từ chối hoặc fallback ra sao).

### 4. Thu Thập & Phân Tích 1 Trace (Nhật Ký Chạy)
*   **Mục đích:** Thể hiện hiểu biết sâu sắc về "Observability" qua việc đọc cấu trúc log, nắm vững tư duy kỹ thuật hệ thống.
*   **Nhiệm vụ của bạn:**
    *   Truy cập thư mục `logs/` và lấy ra 1 file JSON ghi lại quá trình xử lý ấn tượng (có thể ở dạng lỗi hoặc thực thi tốt).
    *   **Báo cáo giải trình cần ghi:** Bạn phải dịch/diễn giải từng bước trong trace JSON đó. Tại sao Agent chọn action đó? Parse JSON có bị crash không? Nguyên nhân sinh ra ảo giác tới từ Prompt viết chưa đúng hay khai báo Tool Description lỏng lẻo?

### 5. Vẽ 1 Flowchart (Sơ Đồ Luồng)
*   **Mục đích:** Thiết kế trực quan cách mã nguồn ReAct Loop vận hành thực tế.
*   **Nhiệm vụ của bạn:**
    *   Dùng các công cụ (Draw.io, Mermaid,...) để vẽ luồng tương tác.
    *   **Mô tả:** Luồng chảy vòng lặp bắt đầu từ `User Input` qua Agent để sinh `Thought`, qua `LLM API`, phân tích (`Parse Action`), chạy hàm (`Execute Tool`), nhận lại `Observation` và cách thức bắt được `Final Answer` để hoàn thành.

### 6. Cài Đặt Bonus (Điểm Thưởng): Fallback Path / Human Escalation
*   **Mục đích:** Xây dựng tính năng chuẩn Production-ready. Trong tình huống hệ thống sập hoặc vượt quyền truy cập, cần có cơ chế "bảo vệ".
*   **Nhiệm vụ (Chọn triển khai một trong hai, hoặc cả hai):**
    *   **Fallback Path (Cơ chế dự phòng):** Xây dựng cơ chế try-except. Nếu quá trình trích xuất JSON lỗi hoặc API Tool bị chết (Timeout) sau N lần retry, Agent không được crash toàn bộ chương trình mà phải tự động ngắt và trả về thông báo lỗi thân thiện với người dùng.
    *   **Human Escalation (Chuyển tiếp con người):** Tạo một Tool mới chỉ định ví dụ như `escalate_to_human`. Điều chỉnh system prompt: *"Nếu người dùng yêu cầu thao tác phức tạp, hoặc hệ thống không thể đáp ứng công cụ sẵn có, hãy dùng tool này"*. Khi tool chạy, in ra nội dung chuyển hướng tới hỗ trợ viên con người.
