# BÁO CÁO NGHIỆM THU TIẾN ĐỘ GIAI ĐOẠN ĐẦU (14 NGÀY)
### Đề tài NCKH Sinh viên năm 2026 — Nhóm 1

> **TÊN ĐỀ TÀI:** Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm quá trình lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (Multi-Agent LLMs)  
> **TÊN TIẾNG ANH:** Information Propagation & Consensus in Multi-Agent Large Language Model Networks  
> **Chủ nhiệm đề tài:** Nguyễn Văn An (MSSV: 23010163 — Lớp: CNTT Việt Nhật K17)  
> **Sinh viên thành viên:** Lê Phạm Thành Đạt (MSSV: 23010541 — Lớp: CNTT Việt Nhật 1 K17)  
> **Giảng viên hướng dẫn:** TS. Phạm Ngọc Hưng (Trường Công nghệ Thông tin — Đại học Phenikaa)  
> **Ngày báo cáo:** 23 tháng 09 năm 2026  

---

## 1. TỔNG QUAN TÀI LIỆU VÀ LÀM RÕ BÀI TOÁN KHOA HỌC

### 1.1. Bản chất Hiện tượng Trôi dạt Ngữ nghĩa (Semantic Drift)
Trong các mạng lưới đa tác tử LLM giao tiếp tự chủ qua nhiều bước nhảy (Multi-hop), mỗi tác tử khi tiếp nhận thông tin $M_{t-1}$ sẽ tái tạo và phát sinh thông điệp mới $M_t \sim P_\theta(M_t \mid M_{t-1}, \text{Persona})$. Quá trình này tạo nên **hiệu ứng tam sao thất bản (Telephone Game Effect)**:
- **Suy giảm ngữ nghĩa (Semantic Degradation):** Mất dần các dữ kiện cốt lõi của thông điệp ban đầu.
- **Tích tụ ảo giác (Hallucination Compounding):** Chi tiết hư cấu/thêm thắt (embellishment) ở nút trước được các nút sau tiếp nhận như sự thật khách quan và tiếp tục khuếch đại.

### 1.2. Tổng hợp 04 Bài báo Kinh điển Nền tảng (ref/)
1. **CAMEL (Li et al., NeurIPS 2023):** Thiết lập phương pháp giao tiếp tự chủ giữa hai tác tử đóng vai qua cơ chế *Inception Prompting*. Bài học áp dụng: Ngăn chặn hiện tượng lật vai (*Role-flipping*) và kiểm soát tiêu chí dừng hội thoại.
2. **AutoGen (Wu et al., Microsoft Research 2023):** Cung cấp mô hình lập trình hội thoại mở rộng (*ConversableAgent*), cho phép kết nối mạng lưới dị thể giữa Local LLM (Ollama) và Cloud LLM (DeepSeek, Gemini).
3. **Generative Agents (Park et al., ACM UIST 2023):** Minh chứng thực nghiệm đầu tiên về lan truyền thông tin tự nhiên trong xã hội 25 tác tử. Kế thừa cấu trúc *Memory Buffer* và *Reflection* để duy trì nhận thức tác tử qua từng vòng.
4. **HaluEval (Li et al., EMNLP 2023):** Chỉ ra nghịch lý: LLM sinh ảo giác trung bình 19.5% và rất yếu trong việc tự phát hiện ảo giác khi suy luận đa bước. Cung cấp phương pháp luận đo lường sự đột biến thông tin.

### 1.3. Bộ 04 Chỉ số Đo lường Cốt lõi (Hybrid Metrics)
- **Chỉ số 1 (Cosine Similarity trên Sentence Embeddings):** Đo lường độ tương đồng ngữ nghĩa tổng thể giữa $M_0$ và $M_t$. Khoảng cách trôi dạt: $\text{Dist}_{\text{sem}} = 1 - \text{CosineSim}(e(M_0), e(M_t))$.
- **Chỉ số 2 (BERTScore - F1-BERTScore):** Đo độ trùng khớp ngữ nghĩa từng từ qua ma trận căn chỉnh tham lam (Greedy Alignment), khắc phục nhược điểm của BLEU/ROUGE.
- **Chỉ số 3 (Tỷ lệ Suy diễn Logic - NLI Entailment Ratio):** Phân loại xem thông điệp đầu ra là Hệ quả logic (*Entailment*), Trung lập (*Neutral*) hay Mâu thuẫn (*Contradiction*) với thông điệp gốc.
- **Chỉ số 4 (Tỷ lệ Ảo giác - Hallucination Rate %):** Tỷ lệ thực thể, số liệu mới bị bịa đặt thêm mà không có trong nguồn tin gốc.

---

## 2. KẾT QUẢ THỰC NGHIỆM TRUYỀN TIN SƠ BỘ TRÊN MẠNG VÒNG (RING TOPOLOGY)

Nhóm đã lập trình và thực thi thành công kịch bản thử nghiệm tại [`experiments/demo_ring_propagation.py`](file:///g:/Project/NCKH_2026/experiments/demo_ring_propagation.py) với cấu hình:
- **Cấu trúc mạng:** Mạng vòng $N = 5$ tác tử ($0 \to 1 \to 2 \to 3 \to 4$).
- **Thông điệp hạt giống ($M_0$):** *"Tổ chức Y tế Thế giới (WHO) khuyến cáo tiêm chủng đầy đủ để phòng ngừa các biến thể cúm mùa trong năm 2026."*

### 2.1. Bảng Số liệu Đo đạc Thực nghiệm Độc lập

| Bước nhảy (Hop) | Nút gửi $\to$ Nút nhận | Persona nhận | Quyết định | Cosine Sim | Semantic Drift | BERTScore F1 | Trạng thái NLI | Tỷ lệ Ảo giác (%) |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Hop 0** | Nguồn $\to$ Agent 0 | `OPINION_LEADER` | Khởi tạo | 1.0000 | 0.0000 | 1.0000 | `ENTAILMENT` | 0.0% |
| **Hop 1** | Agent 0 $\to$ Agent 1 | `GULLIBLE_SPREADER`| `IGNORE` | 1.0000 | 0.0000 | 1.0000 | `ENTAILMENT` | 0.0% |
| **Hop 2** | Agent 1 $\to$ Agent 2 | `DOGMATIC_PARTISAN`| `IGNORE` | 1.0000 | 0.0000 | 1.0000 | `ENTAILMENT` | 0.0% |
| **Hop 3** | Agent 2 $\to$ Agent 3 | `NEUTRAL_OBSERVER` | `FORWARD`| 0.9739 | 0.0261 | 0.9583 | `ENTAILMENT` | 14.3% |
| **Hop 4** | Agent 3 $\to$ Agent 4 | `FACT_CHECKER`     | `IGNORE` | 0.9739 | 0.0261 | 0.9583 | `ENTAILMENT` | 14.3% |

### 2.2. Nhận xét & Phát hiện Khoa học Sơ bộ
1. **Sự xuất hiện của Trôi dạt Ngữ nghĩa:** Tại Hop 3, tác tử thêm tiền tố *"Ghi nhận:..."*, khiến Cosine Similarity giảm từ 1.00 xuống 0.9739, F1-BERTScore giảm xuống 0.9583, tỷ lệ từ ngữ mới (Hallucination Rate) đạt 14.29%.
2. **Khả năng Bảo toàn Logic NLI:** Trạng thái suy diễn vẫn duy trì `ENTAILMENT` (độ tin cậy > 95%), cho thấy thông điệp cốt lõi của WHO chưa bị đảo ngược hay bóp méo thành tin giả độc hại.
3. **Sản phẩm xuất ra hoàn chỉnh:** 
   - Tệp log hội thoại chi tiết: [`experiments/ring_propagation_log.txt`](file:///g:/Project/NCKH_2026/experiments/ring_propagation_log.txt)
   - Tệp số liệu định lượng: [`experiments/ring_propagation_metrics.csv`](file:///g:/Project/NCKH_2026/experiments/ring_propagation_metrics.csv)
   - Biểu đồ suy giảm ngữ nghĩa: [`experiments/semantic_degradation_chart.png`](file:///g:/Project/NCKH_2026/experiments/semantic_degradation_chart.png)

---

## 3. PHÂN CÔNG TRÁCH NHIỆM & KẾ HOẠCH BƯỚC TIẾP THEO

- **Nguyễn Văn An (Chủ nhiệm đề tài):** Đã hoàn thành cấu trúc lớp `LLMAgent`, hệ thống System Prompting, tích hợp DeepSeek/Gemini API, và module logic NLI.
- **Lê Phạm Thành Đạt:** Đã xây dựng hoàn thiện đồ thị mạng lưới bằng NetworkX (Ring, ER, WS, BA, SBM), trích xuất Embeddings và thiết kế giao diện trực quan hóa [`streamlit_app.py`](file:///g:/Project/NCKH_2026/streamlit_app.py).
- **Kế hoạch Giai đoạn 2 (Tháng 2 - Tháng 3/2026):**
  1. Triển khai cơ chế Tự phản tư (*Self-reflection*) vào vòng lặp của tác tử để đánh giá mức độ giảm ảo giác.
  2. Mở rộng thử nghiệm lên quy mô $N = 20 \dots 50$ tác tử trên mạng Watts-Strogatz (Small-World) và Barabási-Albert (Scale-Free).
  3. Duy trì báo cáo định kỳ thứ Sáu hàng tuần cho TS. Phạm Ngọc Hưng.
