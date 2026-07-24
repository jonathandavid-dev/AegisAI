import structlog
from fastapi import WebSocket
from typing import List

logger = structlog.get_logger("aegis.websocket")

class WebSocketManager:
    """Manages active WebSocket connections for real-time bi-directional messaging."""
    
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", client=str(websocket.client))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("websocket_disconnected")

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error("websocket_broadcast_failed", error=str(e))

websocket_manager = WebSocketManager()
