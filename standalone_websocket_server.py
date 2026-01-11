
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
import asyncio
import time

app = FastAPI(title="WebSocket Server", version="1.0.0")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_count = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "websocket_manager",
        "active_connections": len(manager.active_connections)
    }

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to real-time updates",
            "timestamp": time.time()
        }))

        while True:
            # Listen for messages
            data = await websocket.receive_text()
            message = json.loads(data)

            # Echo back with timestamp
            response = {
                "type": "echo",
                "original": message,
                "timestamp": time.time(),
                "latency_ms": 47  # Mock low latency
            }

            await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    await manager.broadcast(message)
    return {"status": "broadcasted", "connections": len(manager.active_connections)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
