import sys
import os
import webbrowser
import threading
import time
import uvicorn
from dotenv import load_dotenv

# Nạp cấu hình từ .env nếu có
load_dotenv()

def open_browser():
    """Tự động mở trình duyệt sau khi máy chủ khởi động thành công."""
    time.sleep(1.5)
    url = "http://localhost:8000"
    print(f"\n[MAS-Diffusion-Lab] Đang mở trình duyệt tại: {url}")
    webbrowser.open(url)

def main():
    print("=" * 70)
    print("  MAS-Diffusion-Lab: Multi-Agent Simulation & Empirical Evaluation")
    print("  Đề tài NCKH 2026: Mô phỏng Lan truyền Thông tin Đa tác tử LLMs")
    print("=" * 70)
    print("✓ Backend API: FastAPI + WebSocket Realtime")
    print("✓ Core Engine: NetworkX Complex Networks (ER, WS, BA, SBM)")
    print("✓ AI Engines: Ollama Local (http://localhost:11434) + Cloud + Mock")
    print("=" * 70)

    # Chạy thread mở trình duyệt
    threading.Thread(target=open_browser, daemon=True).start()

    # Khởi chạy máy chủ Uvicorn
    uvicorn.run(
        "src.api.routes:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
