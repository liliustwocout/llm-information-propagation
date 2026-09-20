import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import asyncio

from src.core.network import TopologyType
from src.core.engine import SimulationEngine
from src.adapters.router import ModelRouter
from src.storage.telemetry import TelemetryManager
from src.api.websocket import ws_manager

app = FastAPI(
    title="MAS-Diffusion-Lab",
    description="Công cụ mô phỏng & đánh giá lan truyền thông tin mạng lưới đa tác tử trên LLMs (NCKH 2026)",
    version="1.0.0"
)

# Kích hoạt CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo Singletons
router = ModelRouter()
engine = SimulationEngine(router=router)
telemetry = TelemetryManager(output_dir="experiments")

async def progress_broadcast(event: str, data: Dict[str, Any]):
    await ws_manager.broadcast({
        "event": event,
        "data": data
    })

engine.progress_callback = progress_broadcast

# Pydantic Schemas cho API
class InitSimulationRequest(BaseModel):
    topology: str = Field("BA_SCALE_FREE", description="ER_RANDOM, WS_SMALL_WORLD, BA_SCALE_FREE, SBM_COMMUNITY")
    num_nodes: int = Field(30, ge=5, le=200)
    seed_message: str = Field(
        "Tổ chức Y tế khuyến nghị người dân nên duy trì thói quen uống đủ 2 lít nước mỗi ngày và vận động thể thao để tăng cường miễn dịch.",
        description="Nội dung thông điệp tiêm vào nút nguồn"
    )
    local_model: str = Field("qwen2.5:3b", description="Mô hình Ollama: qwen2.5:3b, llama3:8b, ...")
    fact_checker_ratio: float = Field(0.1, ge=0.0, le=0.5)
    fact_checker_placement: str = Field("HUB_DEGREE", description="RANDOM, HUB_DEGREE, BRIDGE_BETWEENNESS")
    cloud_ratio: float = Field(0.0, ge=0.0, le=1.0)
    temperature: float = Field(0.7, ge=0.0, le=1.5)
    max_hops: int = Field(10, ge=1, le=50)
    seed: int = Field(42)

# ==================== ENDPOINTS ====================

@app.get("/api/system/status")
async def get_system_status():
    """
    Kiểm tra trạng thái máy chủ Ollama, Cloud APIs và Mock Mode.
    """
    status = await router.check_all_providers()
    return status

@app.post("/api/simulation/init")
async def init_simulation(req: InitSimulationRequest):
    """
    Khởi tạo mạng lưới và các tác tử cho một đợt mô phỏng mới.
    """
    try:
        topo_enum = TopologyType(req.topology.upper())
    except ValueError:
        topo_enum = TopologyType.BA_SCALE_FREE

    res = engine.initialize_simulation(
        topology=topo_enum,
        num_nodes=req.num_nodes,
        seed_message=req.seed_message,
        local_model=req.local_model,
        fact_checker_ratio=req.fact_checker_ratio,
        fact_checker_placement=req.fact_checker_placement,
        cloud_ratio=req.cloud_ratio,
        temperature=req.temperature,
        max_hops=req.max_hops,
        seed=req.seed
    )

    # Phát thông báo qua WebSocket
    await ws_manager.broadcast({
        "event": "SIMULATION_INITIALIZED",
        "data": {
            "simulation_id": engine.simulation_id,
            "total_nodes": req.num_nodes,
            "topology": req.topology,
            "seed_message": req.seed_message
        }
    })

    return res

@app.post("/api/simulation/step")
async def step_simulation():
    """
    Chạy duy nhất 1 bước nhảy (1 Hop) của mô phỏng.
    """
    if not engine.graph:
        raise HTTPException(status_code=400, detail="Mô phỏng chưa được khởi tạo. Hãy gọi /api/simulation/init trước.")

    step_result = await engine.step()

    # Truyền phát sự kiện qua WebSocket
    await ws_manager.broadcast({
        "event": "HOP_COMPLETED",
        "data": step_result
    })

    return step_result

@app.post("/api/simulation/run_all")
async def run_all_simulation(background_tasks: BackgroundTasks):
    """
    Chạy tự động toàn bộ các bước nhảy cho đến khi hoàn tất.
    """
    if not engine.graph:
        raise HTTPException(status_code=400, detail="Mô phỏng chưa được khởi tạo.")

    async def _runner():
        engine.is_running = True
        while not engine.is_finished and engine.is_running:
            res = await engine.step()
            await ws_manager.broadcast({
                "event": "HOP_COMPLETED",
                "data": res
            })
            if res.get("finished"):
                break
            await asyncio.sleep(0.5) # Khoảng nghỉ ngắn để quan sát hiệu ứng trực quan
        engine.is_running = False

    asyncio.create_task(_runner())
    return {"status": "started", "simulation_id": engine.simulation_id}

@app.post("/api/simulation/stop")
async def stop_simulation():
    """
    Dừng khẩn cấp quá trình mô phỏng đang chạy tự động.
    """
    engine.is_running = False
    return {"status": "stopped"}

@app.get("/api/simulation/current")
async def get_current_state():
    """
    Lấy thông tin trạng thái hiện tại của mô phỏng.
    """
    return {
        "simulation_id": engine.simulation_id,
        "current_hop": engine.current_hop,
        "max_hops": engine.max_hops,
        "is_running": engine.is_running,
        "is_finished": engine.is_finished,
        "informed_count": len(engine.informed_nodes),
        "total_nodes": len(engine.agents),
        "pending_messages": len(engine.message_queue),
        "hop_metrics": engine.hop_metrics_history
    }

@app.post("/api/simulation/export")
async def export_data():
    """
    Xuất toàn bộ dữ liệu thực nghiệm ra tệp CSV & JSON để phân tích NCKH.
    """
    if not engine.simulation_id:
        raise HTTPException(status_code=400, detail="Chưa có dữ liệu mô phỏng để xuất.")

    files = telemetry.save_experiment_run(
        simulation_id=engine.simulation_id,
        config=engine.config,
        hop_metrics=engine.hop_metrics_history,
        all_traces=engine.all_traces
    )
    return {
        "message": "Xuất dữ liệu thành công",
        "files": files
    }

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Lắng nghe ping/pong hoặc tin nhắn từ client
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# ==================== STATIC & FRONTEND ====================

web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(web_dir, "index.html"))
