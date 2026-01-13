import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, WebSocketException

from app.services.stream_service import stream_service
from app.config import get_settings

router = APIRouter(tags=["Stream"])


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    api_key: str | None = Query(default=None),
):
    """
    WebSocket endpoint for real-time log streaming.
    
    Connect with: ws://localhost:3000/stream?api_key=your-key
    
    Client messages:
    - {"type": "subscribe", "subscription_id": "...", "filters": {...}}
    - {"type": "unsubscribe", "subscription_id": "..."}
    - {"type": "pause", "subscription_id": "..."}
    - {"type": "resume", "subscription_id": "..."}
    - {"type": "pong", "timestamp": "..."}
    
    Server messages:
    - {"type": "connected", "session_id": "...", "server_time": "..."}
    - {"type": "subscribed", "subscription_id": "...", "filters": {...}}
    - {"type": "unsubscribed", "subscription_id": "..."}
    - {"type": "log", "subscription_id": "...", "data": {...}}
    - {"type": "error", "code": "...", "message": "..."}
    - {"type": "ping", "timestamp": "..."}
    """
    # Verify API key
    settings = get_settings()
    if not api_key or api_key != settings.api_key:
        await websocket.close(code=4001, reason="Invalid or missing API key")
        return
    
    session_id = str(uuid.uuid4())
    
    await stream_service.connect(websocket, session_id)
    
    # Send connected message
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "server_time": datetime.now(timezone.utc).isoformat(),
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "subscribe":
                subscription_id = data.get("subscription_id", str(uuid.uuid4()))
                filters = data.get("filters", {})
                
                await stream_service.subscribe(session_id, subscription_id, filters)
                
                await websocket.send_json({
                    "type": "subscribed",
                    "subscription_id": subscription_id,
                    "filters": filters,
                })
            
            elif msg_type == "unsubscribe":
                subscription_id = data.get("subscription_id")
                if subscription_id:
                    await stream_service.unsubscribe(session_id, subscription_id)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "subscription_id": subscription_id,
                    })
            
            elif msg_type == "pause":
                subscription_id = data.get("subscription_id")
                # TODO: Implement pause
                await websocket.send_json({
                    "type": "paused",
                    "subscription_id": subscription_id,
                })
            
            elif msg_type == "resume":
                subscription_id = data.get("subscription_id")
                # TODO: Implement resume
                await websocket.send_json({
                    "type": "resumed",
                    "subscription_id": subscription_id,
                })
            
            elif msg_type == "pong":
                # Client responded to ping
                pass
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "code": "UNKNOWN_MESSAGE_TYPE",
                    "message": f"Unknown message type: {msg_type}",
                })
    
    except WebSocketDisconnect:
        await stream_service.disconnect(session_id)
    except Exception as e:
        await stream_service.disconnect(session_id)
        raise
