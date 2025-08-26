from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.manager import manager

router = APIRouter()

@router.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket, token: str = Query(...)):
    # TODO: валідуй token (JWT) і відхиляй unknown
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # збереження в БД, якщо треба
            await manager.broadcast({"type": "message", **data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
