from fastapi import WebSocket
from typing import List, Dict, Any
import json

class ConnectionManager:
    """
    Quản lý các kết nối WebSocket trực tiếp phục vụ truyền phát sự kiện mô phỏng realtime.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Gửi dữ liệu sự kiện (Event Stream) tới tất cả các client đang mở giao diện web.
        """
        data_text = json.dumps(message, ensure_ascii=False)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data_text)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

ws_manager = ConnectionManager()
