# Kế hoạch Nghiên cứu Chi tiết & Lộ trình Thực hiện NCKH 2026
### Đề tài: "Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm quá trình lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (LLMs)"

> **Mã số đề tài dự kiến:** NCKH-2026-MAS-LLM  
> **Thời gian thực hiện:** 12 tháng (01/2026 – 12/2026)  
> **Mục tiêu đầu ra:** 01 Bộ công cụ phần mềm mã nguồn mở hoàn chỉnh (`MAS-Diffusion-Lab`), 01 Bộ dữ liệu thực nghiệm chuẩn hóa, 01 Báo cáo tổng kết NCKH, và 01–02 Bài báo khoa học đăng ký nộp tại Hội nghị/Tạp chí chuyên ngành.

---

## 📅 1. Lộ trình Phân kỳ 5 Giai đoạn (Gantt Chart & Milestones)

```
Giai đoạn 1: Tổng quan & Khung lý thuyết  [Tháng 1 - Tháng 2] ━━━
Giai đoạn 2: Thiết kế Kiến trúc & Adapter  [Tháng 3 - Tháng 4]     ━━━
Giai đoạn 3: Phát triển Công cụ & UI Lab   [Tháng 5 - Tháng 6]         ━━━
Giai đoạn 4: Thu thập Dữ liệu & Phân tích  [Tháng 7 - Tháng 9]             ━━━━━
Giai đoạn 5: Viết Báo cáo & Công bố        [Tháng 10 - Tháng 12]                 ━━━━━
```

---

## 🎯 2. Nội dung Chi tiết Từng Giai đoạn

### Giai đoạn 1: Cơ sở Lý thuyết & Khung Phân loại (Tháng 1 – Tháng 2)
- **Mục tiêu:** Xây dựng nền tảng học thuật vững chắc, xác định rõ câu hỏi nghiên cứu (RQs) và giả thuyết khoa học (H1–H4).
- **Công việc cụ thể:**
  1. Tổng hợp tài liệu liên ngành: Complex Networks (Albert & Barabási, Watts & Strogatz), Classical Epidemic Diffusion ($SIR/ICM/LTM$), Generative Agents (Park et al., 2023), và Semantic Drift trong LLMs.
  2. Định vị nghiên cứu trong **Tứ giác Pasteur** (Góc Nghiên cứu Cơ bản Hướng Ứng dụng - Use-Inspired Basic Research).
  3. Hoàn thiện hệ thống phân loại 4 chiều (Taxonomy): Topo mạng, Persona nhận thức BDI, Phân loại thông tin, Ma trận kịch bản can thiệp.
- **Sản phẩm đầu ra:** Các chương tài liệu hoàn thiện: `01_co_so_ly_thuyet.md`, `02_tu_giac_pasteur_va_dinh_vi_nghien_cuu.md`, `03_he_thong_phan_loai_taxonomy.md`.

---

### Giai đoạn 2: Thiết kế Phương pháp luận & Bộ Chỉ số (Tháng 3 – Tháng 4)
- **Mục tiêu:** Chuẩn hóa các biến số thực nghiệm và công thức toán học đo lường.
- **Công việc cụ thể:**
  1. Xác định biến độc lập (Topology $G$, Tỷ lệ Fact-Checker $\alpha$, Vị trí $Hub/Bridge$, Mô hình LLM), biến kiểm soát ($N$, Temperature $\tau$, Seed), biến phụ thuộc ($R(t)$, $Dist_{sem}$, $PI(t)$, $R_t$).
  2. Thiết kế thuật toán tính toán Semantic Drift qua Cosine Distance dựa trên vector nhúng 768 chiều (`nomic-embed-text`).
  3. Xây dựng ma trận thực nghiệm giai thừa (Factorial Experimental Matrix: 4 Topologies x 3 Tỷ lệ can thiệp x 3 Chủng loại mô hình = 36 kịch bản).
- **Sản phẩm đầu ra:** Tài liệu `04_phuong_phap_luan_va_thiet_ke_thuc_nghiem.md` và mã nguồn module toán học `src/core/metrics.py`.

---

### Giai đoạn 3: Phát triển Nền tảng Phần mềm `MAS-Diffusion-Lab` (Tháng 5 – Tháng 6)
- **Mục tiêu:** Xây dựng hoàn chỉnh công cụ phần mềm phục vụ mô phỏng trực quan và thực thi lô lớn (Batch Processing).
- **Công việc cụ thể:**
  1. **Core Engine:** Triển khai `src/core/network.py`, `src/core/agent.py`, `src/core/engine.py`.
  2. **Model Adapters:** Xây dựng `OllamaAdapter` (chạy cục bộ với cơ chế Semaphore kiểm soát VRAM trên GPU RTX 3050 Ti), `CloudAdapter` (OpenAI/Gemini), `MockLLMAdapter` (chạy kiểm thử offline không tốn tài nguyên), và `ModelRouter` (tự động fallback an toàn).
  3. **Giao diện Web:** Xây dựng Dashboard phong cách Dark theme khoa học với Vis.js (đồ thị tương tác) và Chart.js (biểu đồ động học thời gian thực).
  4. **Kiểm thử tự động:** Viết bộ unit tests và API tests đạt độ bao phủ 100% (`tests/test_core.py`, `tests/test_api.py`).
- **Sản phẩm đầu ra:** Kho mã nguồn hoàn chỉnh có thể khởi chạy bằng 1 lệnh `python run.py`.

---

### Giai đoạn 4: Thu thập Dữ liệu & Đánh giá Thực nghiệm (Tháng 7 – Tháng 9)
- **Mục tiêu:** Chạy tự động hóa các đợt mô phỏng đa kịch bản, thu thập dữ liệu sạch và phân tích thống kê.
- **Công việc cụ thể:**
  1. Chạy lặp lại mỗi kịch bản $K = 10$ lần (với các seeds ngẫu nhiên khác nhau từ 42 đến 51) để đảm bảo ý nghĩa thống kê ($p < 0.05$).
  2. Xuất toàn bộ dữ liệu ra định dạng `.csv` và `.json` chuẩn trong thư mục `experiments/`.
  3. Phân tích phương sai đa biến (Two-way ANOVA) để đánh giá tương quan giữa vị trí can thiệp ($Hub$ vs $Bridge$) và tốc độ dập tắt tin giả.
  4. Kiểm định giả thuyết H1, H2, H3, H4 đã đặt ra ở Chương 5.
- **Sản phẩm đầu ra:** Bộ dữ liệu thực nghiệm đầy đủ (`experiments/`) và các bảng biểu phân tích thống kê SPSS/Python Pandas.

---

### Giai đoạn 5: Tổng kết Báo cáo, Viết Bài báo & Nghiệm thu (Tháng 10 – Tháng 12)
- **Mục tiêu:** Hoàn thiện báo cáo toàn văn, xuất bản bài báo khoa học và bảo vệ đề tài trước hội đồng.
- **Công việc cụ thể:**
  1. Soạn thảo Báo cáo Tổng kết Đề tài NCKH theo đúng biểu mẫu của Nhà trường / Đơn vị chủ trì.
  2. Chuyển đổi báo cáo sang định dạng bài báo khoa học $\text{\LaTeX}$ (sử dụng template IEEE Conference hoặc Elsevier Journal).
  3. Rà soát liêm chính học thuật: Kiểm tra trùng lặp đạo văn (< 15%), loại bỏ các cấu trúc sáo rỗng qua kỹ năng `avoid-ai-writing`, xác thực danh mục trích dẫn chuẩn BibTeX.
  4. Chuẩn bị slide thuyết trình trực quan, video demo mô phỏng từ `MAS-Diffusion-Lab`.
- **Sản phẩm đầu ra:** Báo cáo tổng kết NCKH hoàn chỉnh, bản thảo bài báo gửi hội nghị/tạp chí và Slide bảo vệ đề tài.

---

## 🏛️ 3. Phân bổ Nguồn lực & Phần cứng

| Thành phần | Cấu hình / Thông số | Mục đích sử dụng |
|:---|:---|:---|
| **Máy trạm thực nghiệm** | Laptop Intel Core i5-12500H, 16GB RAM | Chạy dịch vụ FastAPI, điều phối mạng lưới và phân tích dữ liệu. |
| **Bộ xử lý Đồ họa (GPU)** | NVIDIA GeForce RTX 3050 Ti (4.0 GB VRAM) | Chạy mô hình suy luận cục bộ `Qwen 2.5 3B` (100% VRAM) và `Llama 3 8B` (Hybrid). |
| **Ổ cứng Lưu trữ Models** | Phân vùng ổ đĩa `G:\Ollama_Models` ($\ge 20\text{ GB}$) | Lưu trữ các tệp trọng số AI (GGUF blobs), bảo vệ an toàn phân vùng hệ điều hành C:. |
| **Mô hình AI Cục bộ** | `qwen2.5:3b`, `llama3:8b`, `nomic-embed-text` | Thực thi suy luận nhận thức của các tác tử và tính toán khoảng cách vector ngữ nghĩa. |
| **Môi trường Phát triển** | VS Code / Antigravity IDE, Python 3.11, Git | Quản lý phiên bản mã nguồn, tài liệu và môi trường lập trình. |
