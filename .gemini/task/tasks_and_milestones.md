# Quản lý Nhiệm vụ & Các Mốc Kiểm thử (Tasks & Milestones)
### Đề tài NCKH 2026: MAS-Diffusion-Lab

> **Trạng thái tổng thể dự án:** 🟢 **ĐÃ HOÀN THÀNH PHÁT TRIỂN LÕI & KIỂM THỬ THỰC TẾ TRÊN GPU CỤC BỘ**  
> **Cập nhật lần cuối:** 21/09/2026

---

## 📋 1. Danh mục Nhiệm vụ Đã Hoàn thành (Completed Tasks)

### 1.1. Xây dựng Hồ sơ Lý thuyết NCKH Chuẩn mực
- [x] **TASK-01:** Soạn thảo Chương 1: Cơ sở lý thuyết mạng phức hợp, mô hình lan truyền cổ điển ($SIR, ICM, LTM$) và nhận thức BDI (`.gemini/docs/01_co_so_ly_thuyet.md`).
- [x] **TASK-02:** Soạn thảo Chương 2: Mô hình Tứ giác Pasteur và định vị "Use-Inspired Basic Research" (`.gemini/docs/02_tu_giac_pasteur_va_dinh_vi_nghien_cuu.md`).
- [x] **TASK-03:** Soạn thảo Chương 3: Hệ thống phân loại toàn diện 4 chiều Taxonomy (`.gemini/docs/03_he_thong_phan_loai_taxonomy.md`).
- [x] **TASK-04:** Soạn thảo Chương 4: Phương pháp luận thực nghiệm và bộ công thức toán học (`.gemini/docs/04_phuong_phap_luan_va_thiet_ke_thuc_nghiem.md`).
- [x] **TASK-05:** Soạn thảo Chương 5: Quy trình 5 bước NCKH, các câu hỏi nghiên cứu (RQs) và giả thuyết (H1-H4) (`.gemini/docs/05_quy_trinh_5_buoc_nckh.md`).
- [x] **TASK-06:** Soạn thảo Chương 6: Kiến trúc công cụ phần mềm và kế hoạch kỹ thuật (`.gemini/docs/06_kien_truc_cong_cu_va_ke_hoach_ky_thuat.md`).
- [x] **TASK-07:** Soạn thảo Chương 7: Liêm chính học thuật, đạo đức AI và chuẩn trích dẫn (`.gemini/docs/07_liem_chinh_hoc_thuat_va_dao_duc_ai.md`).
- [x] **TASK-08:** Tổng quan hồ sơ tài liệu khoa học (`.gemini/docs/README.md`).

### 1.2. Phát triển Ứng dụng & Lõi Mô phỏng (Core Software Engine)
- [x] **TASK-09:** Triển khai module sinh đồ thị 4 mô hình Topo (`ER`, `WS`, `BA`, `SBM`) và tính các chỉ số Centrality (`src/core/network.py`).
- [x] **TASK-10:** Triển khai mô hình nhận thức tác tử BDI với 6 Persona xã hội, quản lý điểm niềm tin $b_i \in [-1, 1]$ (`src/core/agent.py`).
- [x] **TASK-11:** Triển khai bộ tính toán toán học: Độ tương đồng Cosine, Semantic Drift Distance, Độ phủ $R(t)$, Phân cực $PI(t)$ và Hệ số lây nhiễm $R_t$ (`src/core/metrics.py`).
- [x] **TASK-12:** Triển khai lõi điều phối mô phỏng theo từng bước nhảy (Hop-by-Hop Simulation Engine) (`src/core/engine.py`).
- [x] **TASK-13:** Xây dựng hệ thống Model Adapters hỗ trợ kết nối Ollama cục bộ, Cloud APIs và Mock Mode có cơ chế fallback an toàn (`src/adapters/`).
- [x] **TASK-14:** Triển khai hệ thống lưu vết thực nghiệm (Telemetry Manager) xuất dữ liệu JSON và CSV (`src/storage/telemetry.py`).
- [x] **TASK-15:** Xây dựng dịch vụ FastAPI REST endpoints và WebSocket truyền phát thời gian thực (`src/api/routes.py`, `src/api/websocket.py`).
- [x] **TASK-16:** Thiết kế giao diện Web Dashboard phong cách Dark theme khoa học với Vis.js và Chart.js (`src/web/`).
- [x] **TASK-17:** Tạo điểm khởi động nhanh chỉ với một lệnh `python run.py`.

### 1.3. Hạ tầng Phần cứng & Tích hợp Ollama Cục bộ
- [x] **TASK-18:** Giải quyết triệt để sự cố dung lượng ổ C: Dọn sạch rác bộ nhớ đệm, cấu hình biến môi trường `OLLAMA_MODELS = G:\Ollama_Models` và tạo liên kết NTFS Junction an toàn sang ổ G.
- [x] **TASK-19:** Tải về và kiểm tra thành công các mô hình Ollama trên ổ G: `qwen2.5:3b` (1.9 GB), `llama3:8b` (4.7 GB), `nomic-embed-text` (274 MB).
- [x] **TASK-20:** Thêm tùy chọn chọn mô hình cục bộ linh hoạt (`qwen2.5:3b` vs `llama3:8b`) trên cả backend API và giao diện Web Dashboard.
- [x] **TASK-21:** Đồng bộ hóa vector nhúng ngữ nghĩa: Sử dụng `nomic-embed-text` (768 chiều) tính toán chính xác Semantic Drift tức thời.

### 1.4. Kiểm thử Tự động Hóa & Xác thực Thực tế
- [x] **TASK-22:** Chạy và vượt qua 100% bài kiểm thử đơn vị toán học, mạng phức hợp và tác tử (`python tests/test_core.py`).
- [x] **TASK-23:** Chạy và vượt qua 100% bài kiểm thử tích hợp 5 REST API endpoints (`python tests/test_api.py`).
- [x] **TASK-24:** Thực thi thành công mô phỏng trực quan với mô hình thật `qwen2.5:3b` trên browser subagent với GPU RTX 3050 Ti Laptop (tốc độ ~60 tokens/s).
- [x] **TASK-25:** Xây dựng script tự động chạy ma trận thực nghiệm hàng loạt cho NCKH (`run_experiments.py`).
- [x] **TASK-26:** Hoàn thiện tài liệu tổng quan toàn bộ dự án tại gốc (`README.md`).
- [x] **TASK-27:** Biên soạn danh mục AI Agent Skills tuyển chọn từ GitHub phục vụ làm đẹp UI/UX và nghiên cứu (`.gemini/SKILL.md`).

---

### 1.5. Nâng cấp Giao diện Web Dashboard Chuẩn Quốc tế
- [x] **TASK-28 (Trước đây là TASK-30):** Nâng cấp toàn diện giao diện Web Dashboard theo 4 skills: `ui-ux-pro-max`, `frontend-design`, `claude-d3js-skill & animejs-animation`, và `ui-visual-validator`.
  - Tích hợp **Agent Profile Inspector Drawer** hiển thị hồ sơ tác tử, thước đo niềm tin và lập luận BDI.
  - Xây dựng **Packet Wave Engine** mô phỏng xung sóng photon di chuyển trên các cạnh đồ thị mạng lưới với hiệu ứng sóng lan tỏa tại nút nhận.
  - Cải tiến Anime.js HUD stats counter mượt mà và kiểm định tương phản đạt chuẩn **WCAG 2.2 AA**.

---

## 🎯 2. Các Nhiệm vụ Tiếp theo (Next Steps / Roadmap)

- [ ] **TASK-29:** Tiến hành chạy hàng loạt ma trận thực nghiệm đầy đủ (28 kịch bản × 10 seeds = 280 phiên) qua lệnh `python run_experiments.py --mode full --model qwen2.5:3b --nodes 15 --hops 4 --seeds 42 43 44 45 46 47 48 49 50 51`. Script đã được nâng cấp hỗ trợ 3 mode: `quick` (2 đợt), `matrix` (7 đợt), `full` (28 kịch bản × K seeds). File tổng hợp `SUMMARY_*.csv` được xuất tự động.
- [ ] **TASK-30:** Chạy script phân tích thống kê `python analyze_experiments.py` để kiểm định 4 giả thuyết H1-H4 bằng Two-way ANOVA (statsmodels), T-test, và Tukey HSD post-hoc. Script xuất 5 biểu đồ khoa học (box-plot, heatmap, bar-chart) vào `experiments/analysis/`.
- [ ] **TASK-31:** Soạn thảo bản thảo bài báo khoa học định dạng $\text{\LaTeX}$ (IEEEtran) để gửi hội nghị NCKH hoặc tạp chí khoa học.

