# Danh mục Agent Skills Tuyển chọn từ GitHub Phù hợp cho Dự án NCKH 2026
### Đề tài: "Nghiên cứu, phát triển công cụ mô phỏng và đánh giá thực nghiệm quá trình lan truyền thông tin trong mạng lưới đa tác tử trên các mô hình ngôn ngữ lớn (LLMs)"

> **Mục đích tài liệu:** Tài liệu này tổng hợp và cấu trúc các **AI Agent Skills** chuyên biệt (theo chuẩn Agent Skills Specification `SKILL.md`) được tìm kiếm và tuyển chọn từ các kho lưu trữ GitHub uy tín (Claude Code Ecosystem, Google Antigravity, Awesome Agent Skills). Các skill này hỗ trợ trực tiếp việc làm đẹp giao diện UI/UX, tối ưu hóa thuật toán mạng phức hợp, phân tích thống kê NCKH và viết bài báo quốc tế.

---

## 🎨 NHÓM 1: UI/UX, Trực quan hóa Dữ liệu & Làm đẹp Dự án (Frontend & Visuals)

Đây là nhóm skill giải quyết trực tiếp yêu cầu: *"cần 1 skill UI UX để làm đẹp dự án"*, biến giao diện dashboard của `MAS-Diffusion-Lab` thành sản phẩm đạt chuẩn quốc tế, trực quan và tạo ấn tượng mạnh cho hội đồng đánh giá NCKH.

### 1.1. `ui-ux-pro-max` (Chuyên gia Thiết kế UI/UX & Design System)
- **Nguồn / Tham chiếu:** `github.com/anthropics/claude-code/skills` • `antigravity-ide/skills`
- **Mô tả chức năng:**
  - Cung cấp hệ thống Design Token hoàn chỉnh: bảng màu HSLTailored (Dark theme, Cyberpunk, Scientific Slate), tỷ lệ căn lề 8pt grid, typography hiện đại (Inter, Outfit, JetBrains Mono).
  - Loại bỏ hoàn toàn các màu mặc định đơn điệu (plain red, plain blue), thay bằng dải màu gradient và hiệu ứng kính mờ (Glassmorphism / Backdrop Filter).
  - Tối ưu hóa tính công thái học (Ergonomics): các nút điều khiển mô phỏng, thanh trượt tham số ($N$, $\tau$, Fact-Checker ratio) được bố trí khoa học, dễ thao tác.
- **Ứng dụng vào MAS-Diffusion-Lab:**
  - Làm đẹp thanh điều khiển bên trái (`sidebar-config`).
  - Thiết kế các thẻ thẻ thông điệp (`trace-card`) hiển thị nhận thức của từng AI với màu sắc tương ứng theo từng Persona (Xanh ngọc: Fact-Checker, Đỏ cam: Malicious, Tím: Opinion Leader).

### 1.2. `frontend-design` (Kỹ sư Thiết kế Giao diện Sáng tạo)
- **Nguồn / Tham chiếu:** Agent Skills Standard Framework
- **Mô tả chức năng:**
  - Định hướng phát triển giao diện theo tư duy *Frontend Designer-Engineer*, tránh các bố cục MVP nhàm chán hoặc thô cứng.
  - Tích hợp các hiệu ứng vi chuyển động (Micro-interactions): hover 3D tilt, hiệu ứng chuyển trạng thái mượt mà (smooth transitions), loading states dạng xung nhịp (pulse).
- **Ứng dụng vào MAS-Diffusion-Lab:**
  - Thiết kế hiệu ứng hào quang (glow effect) khi một tác tử bị "lây nhiễm" hoặc khi thông điệp phản biện dập tắt tin giả.
  - Tạo các thẻ HUD Metric số liệu động (counter animation) khi chỉ số $R(t)$ và $Dist_{sem}$ biến thiên.

### 1.3. `claude-d3js-skill` & `animejs-animation` (Đồ thị Động & Hoạt ảnh Tương tác)
- **Nguồn / Tham chiếu:** `github.com/d3/d3` • `github.com/juliangarnier/anime`
- **Mô tả chức năng:**
  - Xử lý trực quan hóa dữ liệu mạng lưới phức hợp ở cấp độ nâng cao (Force-directed layout, Sankey diagrams cho dòng thác thông tin, Chord diagrams cho buồng vang SBM).
  - Xử lý chuyển động mượt mà cho hàng trăm phần tử SVG/Canvas cùng lúc mà không làm giật khung hình (60 FPS).
- **Ứng dụng vào MAS-Diffusion-Lab:**
  - Hoạt ảnh hạt phát sáng (particle packet) di chuyển dọc theo các cạnh đồ thị Vis.js từ nút gửi ($sender$) sang nút nhận ($receiver$) trong từng Hop.
  - Biểu đồ nhiệt (Heatmap) thể hiện phân cực niềm tin theo thời gian thực.

### 1.4. `ui-visual-validator` (Kiểm định Thẩm mỹ & Khả năng Tiếp cận)
- **Nguồn / Tham chiếu:** `wcag-audit-patterns` • `ui-visual-validator`
- **Mô tả chức năng:**
  - Tự động rà soát giao diện web qua headless browser (Playwright / Puppeteer).
  - Phát hiện lỗi tràn viền (overflow), chồng lấn văn bản, độ tương phản màu sắc không đạt chuẩn WCAG 2.2, kiểm tra hiển thị đồng đều trên các độ phân giải màn hình khác nhau (Laptop 1080p, Màn hình rời 2K/4K).

---

## 🔬 NHÓM 2: Nghiên cứu Khoa học, Khoa học Mạng & Đánh giá LLMs

Nhóm skill củng cố chiều sâu học thuật, tính toán các chỉ số lý thuyết mạng phức hợp và đo lường định lượng cho đề tài.

### 2.1. `networkx` & `complex-networks` (Thuật toán Mạng Phức hợp)
- **Nguồn / Tham chiếu:** `networkx.org` • `github.com/networkx/networkx`
- **Mô tả chức năng:**
  - Thuật toán sinh đồ thị chuẩn hóa: Barabási–Albert (Scale-free preferential attachment), Watts–Strogatz (Small-world rewiring), Stochastic Block Model (Community detection).
  - Tính toán các chỉ số trọng yếu: Bậc trung tâm (Degree Centrality), Độ trung gian (Betweenness Centrality), Hệ số gom cụm (Clustering Coefficient), Độ dài đường đi trung bình (Average Shortest Path Length).
- **Ứng dụng vào MAS-Diffusion-Lab:**
  - Tự động xác định các nút Trục (Hubs) và nút Cầu nối (Bridges) trong đồ thị để phục vụ chiến lược can thiệp Fact-Checker có chủ đích.

### 2.2. `data-storytelling` & `matplotlib` (Kể chuyện qua Dữ liệu & Đồ thị Báo chí)
- **Nguồn / Tham chiếu:** `matplotlib.org` • Python Scientific Stack
- **Mô tả chức năng:**
  - Chuyển đổi các bảng số liệu khô khan thành các biểu đồ khoa học đạt chuẩn xuất bản (Publication-ready figures với độ phân giải cao 300-600 DPI).
  - Lựa chọn biểu đồ tối ưu: Biểu đồ đường phân tầng (Multi-line curves) cho $R(t)$, Biểu đồ hộp (Boxplot) cho phân bố niềm tin, Biểu đồ tán xạ (Scatter plot) cho tương quan giữa Centrality và tốc độ lây nhiễm.
- **Ứng dụng vào MAS-Diffusion-Lab:**
  - Sinh tự động các hình ảnh đồ thị minh họa cho bài báo NCKH từ các tệp `experiments/*.csv`.

### 2.3. `llm-evaluation` (Phương pháp Đánh giá Định lượng LLM)
- **Nguồn / Tham chiếu:** `github.com/huggingface/lighteval` • `llm-evaluation`
- **Mô tả chức năng:**
  - Phương pháp luận đo lường mức độ tin cậy, phân tích ảo giác (hallucination audit) và khoảng cách vector nhúng (Cosine Semantic Drift).
  - Thiết kế các rubric đánh giá phản hồi tác tử theo thang đo Likert hoặc nhị phân chuẩn khoa học.

---

## ⚙️ NHÓM 3: Tối ưu Hóa Hệ thống, GPU/CUDA & Local LLMs trên Windows

Nhóm skill hỗ trợ khai thác triệt để phần cứng máy tính của bạn (NVIDIA GeForce RTX 3050 Ti Laptop GPU 4GB VRAM, 16GB RAM, ổ đĩa G:).

### 3.1. `powershell-windows` & `windows-shell-reliability`
- **Nguồn / Tham chiếu:** `antigravity-ide/skills/powershell-windows`
- **Mô tả chức năng:**
  - Xử lý các đặc thù của Windows: biến môi trường (`OLLAMA_MODELS`), liên kết mềm/cứng NTFS Junction (`mklink /J`), mã hóa ký tự UTF-8 Tiếng Việt trên Windows Terminal.
  - Quản lý tiến trình nền (Background Services), kiểm soát an toàn không làm treo GPU hoặc tràn bộ nhớ ổ C.

### 3.2. `local-llm-expert` & `performance-profiling`
- **Nguồn / Tham chiếu:** `ollama.ai` • `llama.cpp` performance guidelines
- **Mô tả chức năng:**
  - Tối ưu hóa tham số nạp mô hình: phân bổ số layer giữa GPU và RAM (`ngl`), kiểm soát số lượng ngữ cảnh (`num_ctx = 2048/4096`), kiểm soát số luồng song song (`OLLAMA_NUM_PARALLEL`) và cơ chế Semaphore.
  - Giảm độ trễ chuyển tiếp giữa các tác tử xuống dưới 1.5 giây/bước nhảy.

---

## 📝 NHÓM 4: Viết Báo cáo NCKH, LaTeX & Liêm chính Học thuật

Nhóm skill biến các kết quả thực nghiệm thành bài báo khoa học hoàn chỉnh sẵn sàng nộp các hội nghị/tạp chí uy tín (VNU, IEEE, Scopus).

### 4.1. `scientific-writing` (Kỹ năng Viết Báo cáo Khoa học Hàn lâm)
- **Nguồn / Tham chiếu:** Academic Writing Guidelines for CS & AI
- **Mô tả chức năng:**
  - Cấu trúc bài báo theo chuẩn quốc tế IMRAD: *Introduction (Giới thiệu) - Related Work (Tổng quan) - Methodology (Phương pháp luận) - Experiments & Results (Thực nghiệm) - Discussion & Conclusion (Thảo luận & Kết luận)*.
  - Viết phần Tóm tắt (Abstract) súc tích, làm nổi bật câu hỏi nghiên cứu (RQs) và đóng góp mới.

### 4.2. `avoid-ai-writing` (Rà soát & Chuẩn hóa Văn phong Khoa học)
- **Nguồn / Tham chiếu:** `antigravity-ide/skills/avoid-ai-writing`
- **Mô tả chức năng:**
  - Rà soát toàn bộ bài viết, loại bỏ 21 mô thức viết sáo rỗng thường gặp của AI (ví dụ: lạm dụng từ "bức tranh toàn cảnh", "minh chứng rõ nét", "điều đáng lưu tâm").
  - Đưa văn phong về đúng chuẩn mực khách quan, trung tính, chặt chẽ của các nhà khoa học máy tính.

### 4.3. `latex-paper-conversion` & `citation-management`
- **Nguồn / Tham chiếu:** IEEEtran / ACM Master Article Template
- **Mô tả chức năng:**
  - Tự động chuyển đổi các tài liệu Markdown trong `.gemini/docs/` sang định dạng $\text{\LaTeX}$ (Overleaf compatible).
  - Tự động quản lý danh mục tài liệu tham khảo qua tệp `references.bib` với định dạng trích dẫn chuẩn IEEE hoặc APA 7th.

---

## 🚀 Hướng dẫn Kích hoạt & Tích hợp Skills vào Dự án

1. **Khám phá và xem nội dung skill:** Khi cần thực hiện tác vụ nào (ví dụ: làm đẹp giao diện), bạn chỉ cần yêu cầu:
   > *"Hãy dùng skill `ui-ux-pro-max` và `frontend-design` để nâng cấp giao diện Web Dashboard của MAS-Diffusion-Lab."*
2. **Hệ thống tự động nạp chỉ dẫn:** Trợ lý AI sẽ tự động đọc tệp chỉ dẫn tương ứng trong kho `skills/` và áp dụng trực tiếp các tiêu chuẩn thiết kế cao cấp nhất vào mã nguồn CSS, HTML và JavaScript của dự án.
3. **Mở rộng thêm Skills mới:** Mọi skill mới tìm thấy từ GitHub có thể được sao chép vào thư mục `C:\Users\acern\.gemini\config\skills\<ten-skill>\SKILL.md` hoặc `.agents/skills/` để sử dụng vĩnh viễn.
