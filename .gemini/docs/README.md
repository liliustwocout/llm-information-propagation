# TỔNG QUAN HỆ THỐNG TÀI LIỆU NGHIÊN CỨU KHOA HỌC (NCKH 2026)

> **Tên đề tài:** Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm quá trình lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (LLMs)  
> **Lĩnh vực:** Khoa học máy tính / Trí tuệ nhân tạo / Khoa học mạng phức hợp (Network Science & AI)  
> **Hướng nghiên cứu:** Multi-Agent Systems (MAS), Generative Agents, Information Diffusion, LLM Epistemology, AI Safety  
> **Môi trường thực nghiệm:** Tích hợp mô hình cục bộ (Local LLMs qua Ollama) kết hợp các mô hình đám mây (Cloud LLMs: OpenAI, Google Gemini, Anthropic)

---

## 1. Tóm tắt Đề tài (Abstract)

Sự bùng nổ của các Mô hình Ngôn ngữ Lớn (Large Language Models - LLMs) đã mở ra kỷ nguyên mới cho Hệ đa tác tử (Multi-Agent Systems - MAS), nơi các tác tử nhân tạo (Generative Agents) có khả năng tự suy luận, ghi nhớ, giao tiếp bằng ngôn ngữ tự nhiên và hình thành các cấu trúc xã hội số phức tạp. Tuy nhiên, tính chất ngẫu nhiên (stochasticity), thiên kiến nội tại và nguy cơ sinh ảo giác (hallucination) của LLMs đặt ra những câu hỏi chưa có lời giải về quy luật lan truyền thông tin, cơ chế biến dạng ngữ nghĩa (semantic drift), cũng như động học hình thành buồng vang thông tin (echo chambers) khi hàng chục đến hàng trăm tác tử tương tác với nhau trên các cấu trúc mạng phức hợp (complex network topologies).

Đề tài tập trung **nghiên cứu cơ sở lý thuyết, phát triển bộ công cụ phần mềm mô phỏng mã nguồn mở và tiến hành đánh giá thực nghiệm** quá trình lan truyền thông tin trong mạng lưới đa tác tử LLM dị thể (heterogeneous multi-agent networks), kết hợp giữa các mô hình AI mã nguồn mở chạy cục bộ (thông qua Ollama) và các mô hình thương mại trên đám mây. Đề tài định lượng hóa mức độ biến dạng thông tin, tốc độ lan truyền, và hiệu quả của các cơ chế can thiệp phản biện (fact-checking inoculation), đóng góp cả về mặt lý thuyết nền tảng lẫn công cụ thực tiễn cho cộng đồng nghiên cứu AI an toàn và khoa học xã hội tính toán (Computational Social Science).

---

## 2. Mục tiêu Nghiên cứu

### 2.1. Mục tiêu Tổng quát
Xây dựng khung lý thuyết liên ngành và phát triển một nền tảng công cụ thực nghiệm mạnh mẽ, trực quan, cho phép mô phỏng, đo lường và đánh giá định lượng các quy luật lan truyền thông tin (thông tin đúng, tin đồn, tin sai lệch) trong mạng lưới các tác tử AI sử dụng LLMs.

### 2.2. Mục tiêu Cụ thể
1. **Hệ thống hóa cơ sở lý thuyết:** Kết hợp lý thuyết mạng phức hợp, mô hình lan truyền dịch tễ học, hệ đa tác tử nhận thức và động học ngữ nghĩa LLM.
2. **Thiết kế hệ thống phân loại (Taxonomy):** Chuẩn hóa cấu trúc mạng, vai trò nhận thức của tác tử (personas), bản chất thông tin và các kịch bản thực nghiệm.
3. **Phát triển công cụ mô phỏng dị thể (Simulation Platform):** Thiết kế kiến trúc module linh hoạt, hỗ trợ plug-and-play các mô hình cục bộ thông qua Ollama (Llama 3, Qwen 2.5, DeepSeek, Mistral) và API mô hình Cloud (GPT-4o, Gemini 2.0/1.5, Claude 3.5).
4. **Xây dựng bộ chỉ số đánh giá thực nghiệm (Evaluation Metrics):** Định lượng hóa tốc độ khuếch tán, độ sâu phân tầng, độ lệch khoảng cách ngữ nghĩa (Embedding Semantic Drift), chỉ số phân cực và tỷ lệ đồng thuận.
5. **Thực nghiệm & Kiểm định giả thuyết:** Thực thi các kịch bản kiểm thử quy mô đa dạng, phân tích so sánh giữa mạng đồng thể (homogeneous) và dị thể (heterogeneous), đánh giá các chiến lược dập tắt tin giả.
6. **Đảm bảo tính tái lập và liêm chính học thuật:** Toàn bộ mã nguồn, cấu hình prompt, trace thực nghiệm và bộ dữ liệu đều tuân thủ nguyên tắc Open Science và quy chuẩn đạo đức AI.

---

## 3. Cấu trúc Hệ thống Tài liệu Nghiên cứu

Hệ thống tài liệu được chuẩn hóa theo chuẩn hồ sơ nghiên cứu khoa học hàn lâm, lưu trữ tại thư mục `g:\Project\NCKH_2026\.gemini\docs`:

| STT | Tên tài liệu | Nội dung chính |
|:---:|:---|:---|
| 01 | [`01_co_so_ly_thuyet.md`](file:///g:/Project/NCKH_2026/.gemini/docs/01_co_so_ly_thuyet.md) | Lý thuyết mạng phức hợp, mô hình lan truyền cổ điển & hiện đại, Hệ đa tác tử BDI, Động học nhận thức & Biến dạng ngữ nghĩa LLM |
| 02 | [`02_tu_giac_pasteur_va_dinh_vi_nghien_cuu.md`](file:///g:/Project/NCKH_2026/.gemini/docs/02_tu_giac_pasteur_va_dinh_vi_nghien_cuu.md) | Mô hình Tứ giác Pasteur (Donald Stokes), định vị nghiên cứu trong góc "Use-Inspired Basic Research", giá trị khoa học & ứng dụng |
| 03 | [`03_he_thong_phan_loai_taxonomy.md`](file:///g:/Project/NCKH_2026/.gemini/docs/03_he_thong_phan_loai_taxonomy.md) | Phân loại topo mạng, vai trò nhận thức tác tử, kiểu thông tin lan truyền và các kịch bản mô phỏng |
| 04 | [`04_phuong_phap_luan_va_thiet_ke_thuc_nghiem.md`](file:///g:/Project/NCKH_2026/.gemini/docs/04_phuong_phap_luan_va_thiet_ke_thuc_nghiem.md) | Phương pháp luận thực nghiệm tính toán, biến số độc lập/kiểm soát/phụ thuộc, công thức các chỉ số đo lường (Metrics) |
| 05 | [`05_quy_trinh_5_buoc_nckh.md`](file:///g:/Project/NCKH_2026/.gemini/docs/05_quy_trinh_5_buoc_nckh.md) | Quy trình chuẩn 5 bước NCKH: Ý tưởng/Câu hỏi, Tổng quan tài liệu, Thiết kế phương pháp, Thu thập & Phân tích, Công bố |
| 06 | [`06_kien_truc_cong_cu_va_ke_hoach_ky_thuat.md`](file:///g:/Project/NCKH_2026/.gemini/docs/06_kien_truc_cong_cu_va_ke_hoach_ky_thuat.md) | Kiến trúc phần mềm, kết nối Ollama/Cloud, Engine điều phối (Orchestrator), UI/Dashboard trực quan và Roadmap kỹ thuật |
| 07 | [`07_liem_chinh_hoc_thuat_va_dao_duc_ai.md`](file:///g:/Project/NCKH_2026/.gemini/docs/07_liem_chinh_hoc_thuat_va_dao_duc_ai.md) | Nguyên tắc minh bạch số liệu, tính tái lập (Reproducibility), quản lý rủi ro tin giả tổng hợp, đạo đức học thuật & quy chuẩn trích dẫn |
| 08 | [`08_tong_quan_tai_lieu_4_bai_bao_kinh_dien.md`](file:///g:/Project/NCKH_2026/.gemini/docs/08_tong_quan_tai_lieu_4_bai_bao_kinh_dien.md) | Tổng quan chuyên sâu 04 bài báo kinh điển (CAMEL, AutoGen, Generative Agents, HaluEval), phương pháp tra cứu học thuật & ma trận tổng hợp |

---

## 4. Bảng Ký hiệu & Thuật ngữ Viết tắt

- **MAS**: Multi-Agent Systems (Hệ đa tác tử)
- **ABM**: Agent-Based Modeling (Mô hình hóa dựa trên tác tử)
- **LLM**: Large Language Model (Mô hình ngôn ngữ lớn)
- **ICM**: Independent Cascade Model (Mô hình thác độc lập)
- **LTM**: Linear Threshold Model (Mô hình ngưỡng tuyến tính)
- **SIR / SIS / SEIR**: Susceptible - Infectious - Recovered (Mô hình dịch tễ học lan truyền)
- **BDI**: Belief - Desire - Intention (Mô hình tác tử Niềm tin - Mong muốn - Ý định)
- **RAG**: Retrieval-Augmented Generation (Tạo sinh có tăng cường truy xuất)
- **Semantic Drift**: Sự biến dạng/trôi dạt ngữ nghĩa của thông tin qua các nút trung gian
- **Ollama**: Nền tảng thực thi mô hình ngôn ngữ lớn cục bộ (Local Model Runner)
