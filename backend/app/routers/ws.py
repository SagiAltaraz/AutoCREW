import asyncio
import json
from collections import defaultdict
from typing import DefaultDict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.redis_client import get_redis

router = APIRouter(tags=["websocket"])


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: DefaultDict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        await websocket.accept()
        self._connections[task_id].append(websocket)

    def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        connections = self._connections.get(task_id, [])
        if websocket in connections:
            connections.remove(websocket)

    async def broadcast(self, task_id: str, message: dict) -> None:
        dead = []
        for ws in list(self._connections.get(task_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, task_id)


manager = WebSocketManager()


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str) -> None:
    await manager.connect(websocket, task_id)
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"task:{task_id}")

    async def listen() -> None:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast(task_id, data)
                    if data.get("type") == "task_complete":
                        break
                except Exception:
                    continue

    listener = asyncio.create_task(listen())

    try:
        while True:
            await asyncio.wait_for(websocket.receive_text(), timeout=60)
    except (WebSocketDisconnect, asyncio.TimeoutError, Exception):
        pass
    finally:
        listener.cancel()
        await pubsub.unsubscribe(f"task:{task_id}")
        manager.disconnect(websocket, task_id)
