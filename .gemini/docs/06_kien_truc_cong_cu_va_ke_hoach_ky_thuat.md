# KIẾN TRÚC CÔNG CỤ VÀ KẾ HOẠCH TRIỂN KHAI KỸ THUẬT

> **Chương 6:** Thiết kế kiến trúc phần mềm, cơ chế tích hợp mô hình cục bộ Ollama và Cloud AI, quy trình điều phối bất đồng bộ và kế hoạch phát triển công cụ `MAS-Diffusion-Lab`.

---

## 1. Kiến trúc Hệ thống Tổng thể (System Architecture)

Công cụ mô phỏng được thiết kế theo kiến trúc **5 tầng hướng module (Modular 5-Layer Architecture)**, đảm bảo tính mở rộng cao, khả năng cắm/rút linh hoạt giữa các nhà cung cấp LLM, và khả năng tái lập thực nghiệm dễ dàng:

```mermaid
flowchart TD
    subgraph UI_Layer [Tầng Giao diện & Trực quan hóa - UI Layer]
        WebUI[Web Dashboard - React/Vite hoặc Streamlit]
        GraphVis[Trực quan hóa Đồ thị Động - PyVis / D3.js / Vis.js]
        Charts[Biểu đồ Thống kê Realtime - ECharts / Plotly]
    end

    subgraph API_Layer [Tầng Dịch vụ & Điều khiển - API & Controller]
        FastAPI_App[FastAPI REST API Server]
        WSEngine[WebSocket Event Broadcaster]
        ExpManager[Trình Quản lý Kịch bản Thí nghiệm - Experiment Config]
    end

    subgraph Core_Engine [Tầng Lõi Mô phỏng - Simulation Core Engine]
        GraphManager[Quản lý Đồ thị Mạng - NetworkX]
        Scheduler[Bộ Điều phối Chu kỳ - Tick/Event Scheduler]
        AgentRuntime[Runtime Quản lý Vòng đời Tác tử - Agent Lifecycle]
        MemoryManager[Quản lý Bộ nhớ & Ngữ cảnh - Epistemic Buffer]
    end

    subgraph Model_Adapters [Tầng Kết nối Mô hình Dị thể - Heterogeneous Model Layer]
        Router[Bộ Điều phối Tải & Phân loại Node - Model Router]
        OllamaAdapter[Ollama Local Adapter: Llama3, Qwen2.5, DeepSeek]
        CloudAdapter[Cloud Adapter: OpenAI GPT-4o, Gemini 2.0, Claude 3.5]
        RateLimiter[Bộ Quản lý Luồng & Hàng đợi VRAM Semaphore]
    end

    subgraph Analytics_Storage [Tầng Phân tích & Lưu trữ - Analytics & Persistence]
        Embeddings[Vector Embedding Engine: Sentence-Transformers / Ollama]
        MetricsEngine[Bộ Tính toán Chỉ số: Cosine Drift, Diffusion, Polarization]
        TelemetryDB[(Cơ sở dữ liệu Trace: SQLite / DuckDB / JSONL)]
    end

    UI_Layer <--> API_Layer
    API_Layer <--> Core_Engine
    Core_Engine <--> Model_Adapters
    Core_Engine --> Analytics_Storage
    Analytics_Storage --> API_Layer
```

---

## 2. Chi tiết Tích hợp Mô hình Cục bộ (Ollama) và Mô hình Đám mây (Cloud)

### 2.1. Cấu hình Cụm Mô hình Cục bộ (Ollama Local Edge)
- **Địa chỉ kết nối:** `http://localhost:11434/api/generate` hoặc qua thư viện `ollama-python`.
- **Danh sách mô hình khuyến nghị trên môi trường cục bộ:**
  1. `llama3:8b-instruct-q4_K_M`: Đại diện cho mô hình tổng quát mạnh mẽ, cân bằng nhận thức tốt.
  2. `qwen2.5:7b-instruct`: Khả năng suy luận logic và tuân thủ định dạng JSON/structured prompt rất cao.
  3. `deepseek-r1:8b`: Mô hình chuyên sâu về tư duy phản biện (reasoning/chain-of-thought), lý tưởng cho vai trò **Fact-Checker**.
  4. `mistral:7b-instruct-v0.3`: Xử lý sắc thái ngữ nghĩa linh hoạt.
- **Cơ chế Điều tiết Tài nguyên Phần cứng (VRAM / Concurrency Guard):**
  Do máy trạm thực nghiệm có giới hạn về VRAM card đồ họa (GPU), hệ thống triển khai bộ điều khiển `asyncio.Semaphore(concurrency_limit)` (ví dụ: tối đa 2-4 tác tử gọi mô hình cục bộ song song) để tránh lỗi tràn bộ nhớ (CUDA Out-of-Memory).

### 2.2. Tích hợp Mô hình Đám mây (Cloud Tier)
- **Mô hình mục tiêu:**
  - `gpt-4o-mini` / `gpt-4o` (OpenAI SDK)
  - `gemini-1.5-flash` / `gemini-2.0-flash` (Google GenAI SDK)
  - `claude-3-5-sonnet` (Anthropic SDK)
- **Vai trò trong mạng lưới:**
  - Được gán cho các nút có bậc liên kết cao (Hubs), nút cầu nối (Bridges) hoặc nút thẩm định độc lập (LLM-as-a-Judge).
  - Đóng vai trò làm mốc đối chứng chất lượng cao để đánh giá sự khác biệt hành vi giữa các mô hình mở quy mô 7B-8B và các mô hình thương mại hàng đầu thế giới.

---

## 3. Luồng Thực thi của Một Bước Mô phỏng (Hop Cycle Sequence)

```mermaid
sequenceDiagram
    autonumber
    participant S as Scheduler
    participant G as Network Graph
    participant A1 as Agent i (Sender)
    participant MR as Model Router
    participant L as Ollama / Cloud
    participant M as Metrics Engine
    participant DB as Telemetry Log

    S->>G: Lấy danh sách thông điệp cần chuyển ở bước t
    G->>A1: Kích hoạt Agent i với tin nhắn nhận được từ hàng xóm
    A1->>A1: Tổng hợp ngữ cảnh, đối chiếu Persona & Niềm tin
    A1->>MR: Gửi yêu cầu suy luận kèm Prompt
    MR->>L: Thực thi sinh văn bản (Ollama Local hoặc Cloud API)
    L-->>MR: Trả về câu trả lời, mức độ tin cậy và quyết định
    MR-->>A1: Cập nhật trạng thái nhận thức
    A1->>G: Nếu quyết định lan truyền -> Gửi tin đi các nút đích
    A1->>M: Gửi bản ghi (M_0, M_t, Sender, Receiver)
    M->>M: Tính Embedding, Cosine Drift, Độ dài ký tự
    M->>DB: Lưu vĩnh viễn Trace vào SQLite / JSONL
    DB-->>S: Xác nhận hoàn tất vòng lặp
```

---

## 4. Đặc tả Cấu trúc Dữ liệu Thông điệp (Message Envelope Schema)

Mỗi thông điệp lưu thông trong mạng lưới được chuẩn hóa theo định dạng JSON có cấu trúc:

```json
{
  "simulation_id": "SIM_2026_EXP04_RUN01",
  "hop_count": 3,
  "timestamp": 1774108800.125,
  "origin_message": {
    "claim_id": "CLAIM_MED_01",
    "text": "Tổ chức Y tế khẳng định rằng việc tập thể dục 30 phút mỗi ngày giúp giảm 40% nguy cơ bệnh tim mạch.",
    "veracity": "GROUND_TRUTH"
  },
  "current_message": {
    "sender_id": "agent_07",
    "sender_persona": "GULLIBLE_SPREADER",
    "sender_model": "ollama:llama3:8b",
    "receiver_id": "agent_12",
    "text": "Nghe nói các chuyên gia bảo chỉ cần chạy bộ là hết sạch nguy cơ đột quỵ luôn, mọi người nên chia sẻ ngay!",
    "sentiment": "EXCITED",
    "subjective_confidence": 0.95
  },
  "metrics": {
    "semantic_cosine_distance": 0.284,
    "distortion_detected": true,
    "hallucinated_entities": ["hết sạch nguy cơ đột quỵ"]
  }
}
```

---

## 5. Kế hoạch Triển khai Kỹ thuật & Lộ trình Thời gian (Development Roadmap)

Dự án được phân chia thành 4 giai đoạn kỹ thuật (Sprints) rõ ràng:

```mermaid
gantt
    title Lộ trình Kỹ thuật Phát triển Nền tảng MAS-Diffusion-Lab
    dateFormat  YYYY-MM-DD
    section Giai đoạn 1: Khung lõi
    Thiết kế CSDL & Schema JSON           :done, 2026-09-21, 7d
    Xây dựng NetworkX Graph Engine         :done, 2026-09-28, 7d
    Lập trình Ollama & Cloud Adapters      :active, 2026-10-05, 10d
    section Giai đoạn 2: Engine mô phỏng
    Phát triển Scheduler & Agent Runtime   :2026-10-15, 14d
    Tích hợp Bộ nhớ & Semantic Cache      :2026-10-29, 10d
    section Giai đoạn 3: Phân tích & UI
    Module tính Semantic Drift & Cosine    :2026-11-08, 10d
    Xây dựng Web Dashboard & PyVis         :2026-11-18, 14d
    section Giai đoạn 4: Thực nghiệm & Tối ưu
    Thực thi 45+ kịch bản đối chứng        :2026-12-02, 14d
    Kiểm định thống kê & Đóng gói Repo     :2026-12-16, 10d
```

### 5.1. Phân kỳ Công việc Chi tiết

1. **Sprint 1: Xây dựng Nền tảng và Adapter Kết nối (Tuần 1 - 3)**
   - Khởi tạo cấu trúc dự án Python hiện đại sử dụng `poetry` hoặc `pip`.
   - Viết các adapter bất đồng bộ kết nối Ollama (`/api/generate`) và Cloud APIs (OpenAI, Google Gemini, Anthropic).
   - Viết test suite kiểm tra độ trễ mạng và xử lý lỗi rớt mạng/rate limit.
2. **Sprint 2: Lõi Mô phỏng và Đồ thị Mạng (Tuần 4 - 6)**
   - Hiện thực hóa module sinh đồ thị `topology_generator.py` với các thuật toán ER, WS, BA, SBM.
   - Xây dựng Agent State Machine (Perceive -> Deliberate -> Act).
   - Tích hợp bộ đệm Context Window và chống tràn bộ nhớ.
3. **Sprint 3: Engine Đo lường và Giao diện Trực quan (Tuần 7 - 9)**
   - Tích hợp mô hình Text Embedding tính khoảng cách Cosine theo thời gian thực.
   - Xây dựng Web Dashboard tương tác (hiển thị đồ thị mạng với các node đổi màu theo trạng thái tin tưởng/hoài nghi).
   - Xuất dữ liệu telemetry ra các định dạng chuẩn (CSV, JSONL, SQLite).
4. **Sprint 4: Chạy Thực nghiệm Kiểm định & Tinh chỉnh (Tuần 10 - 12)**
   - Tiến hành chạy tự động hóa toàn bộ 45 phiên thực nghiệm đối chứng.
   - Xuất các biểu đồ thống kê, tính $p$-value và biên soạn báo cáo kỹ thuật.
