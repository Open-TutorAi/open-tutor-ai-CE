"""Socket.IO ASGI sub-application mounted at /realtime.

The client connects to TUTOR_BASE_URL with path='/realtime/socket.io'.
Authentication is via JWT token passed as `token` query parameter or
Authorization header.
"""

import logging
import time
from typing import Any

import socketio

from gateway.http.dependencies import decode_jwt_token

log = logging.getLogger(__name__)

# Session pool: sid -> {user_id, email, last_seen_at}
SESSION_POOL: dict[str, dict[str, Any]] = {}

# Usage pool: model_id -> {sid: {updated_at}}
USAGE_POOL: dict[str, dict[str, dict[str, Any]]] = {}

# Minimal CORS — accepts all origins (same policy as the FastAPI CORS middleware)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    transports=["websocket", "polling"],
    always_connect=False,
)

# Wrap in ASGI app — this is what gets mounted.
# socketio_path must be the full path as FastAPI does not strip the mount prefix
# from scope['path'] before passing to sub-apps.
socket_app = socketio.ASGIApp(sio, socketio_path="/realtime/socket.io")


async def _broadcast_user_list():
    """Broadcast the list of active user IDs to all connected clients."""
    user_ids = list(
        set(
            session.get("user_id")
            for session in SESSION_POOL.values()
            if session.get("user_id")
        )
    )
    await sio.emit("user-list", {"user_ids": user_ids})
    log.debug("Broadcast user-list: %s", user_ids)


async def _broadcast_usage():
    """Broadcast current usage pool to all connected clients."""
    models = {}
    for model_id, connections in USAGE_POOL.items():
        if connections:
            models[model_id] = len(connections)
    await sio.emit("usage", {"models": models})
    log.debug("Broadcast usage: %s", models)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None):
    """Authenticate on connect. Disconnect immediately if no valid token."""
    token = None

    # 1. Try auth dict (from Socket.IO client auth option)
    if auth and isinstance(auth, dict):
        token = auth.get("token")

    # 2. Fall back to query string: ?token=<jwt>
    if not token:
        qs = environ.get("QUERY_STRING", "")
        for part in qs.split("&"):
            if part.startswith("token="):
                token = part[len("token=") :]
                break

    if not token:
        log.warning("Socket.IO connect rejected: no token (sid=%s)", sid)
        return False  # reject connection

    user = decode_jwt_token(token)
    if not user:
        log.warning("Socket.IO connect rejected: invalid token (sid=%s)", sid)
        return False

    user_id = user.get("sub")
    email = user.get("email")

    # Store in session pool
    SESSION_POOL[sid] = {
        "user_id": user_id,
        "email": email,
        "last_seen_at": int(time.time()),
    }

    # Join user-specific room for targeted messaging
    await sio.enter_room(sid, f"user:{user_id}")

    log.info("Socket.IO connected: sid=%s user=%s", sid, user_id)
    await sio.save_session(sid, {"user_id": user_id, "email": email})

    # Broadcast updated user list
    await _broadcast_user_list()

    return True


@sio.event
async def disconnect(sid: str):
    """Handle client disconnection. Remove from session pool and broadcast."""
    user = SESSION_POOL.pop(sid, None)
    log.info(
        "Socket.IO disconnected: sid=%s user=%s",
        sid,
        user.get("user_id") if user else None,
    )

    # Broadcast updated user list
    await _broadcast_user_list()


@sio.on("user-join")
async def user_join(sid: str, data: dict):
    """Handle user-join event. Track user in session pool and join user room."""
    auth = data.get("auth")
    if not auth or "token" not in auth:
        return

    token_data = decode_jwt_token(auth["token"])
    if token_data is None:
        return

    user_id = token_data.get("sub")
    email = token_data.get("email")

    if not user_id:
        return

    # Store in session pool
    SESSION_POOL[sid] = {
        "user_id": user_id,
        "email": email,
        "last_seen_at": int(time.time()),
    }

    # Join user-specific room
    await sio.enter_room(sid, f"user:{user_id}")

    # Broadcast updated user list
    await _broadcast_user_list()

    log.info("Socket.IO user-join: sid=%s user=%s", sid, user_id)
    return {"id": user_id, "email": email}


@sio.on("usage")
async def usage(sid: str, data: dict):
    """Handle usage event. Track model usage in USAGE_POOL."""
    if sid not in SESSION_POOL:
        return

    model_id = data.get("model")
    if not model_id:
        return

    current_time = int(time.time())

    # Store usage data
    USAGE_POOL[model_id] = {
        **(USAGE_POOL.get(model_id) or {}),
        sid: {"updated_at": current_time},
    }

    # Broadcast usage update
    await _broadcast_usage()


@sio.on("heartbeat")
async def heartbeat(sid: str, data: dict):
    """Handle heartbeat event. Keep session alive and update last_seen_at."""
    user = SESSION_POOL.get(sid)
    if user:
        SESSION_POOL[sid] = {**user, "last_seen_at": int(time.time())}


def get_active_user_ids() -> list[str]:
    """Return list of unique user IDs with active sessions."""
    return list(
        set(
            session.get("user_id")
            for session in SESSION_POOL.values()
            if session.get("user_id")
        )
    )


async def emit_chat_event(user_id: str, data: dict) -> None:
    """Emit chat-events to the user's room (server → client)."""
    await sio.emit("chat-events", data, room=f"user:{user_id}")


async def emit_channel_event(channel_id: str, data: dict) -> None:
    """Emit channel-events to the channel's room (server → client)."""
    await sio.emit("channel-events", data, room=f"channel:{channel_id}")


@sio.on("events:chat")
async def chat_events(sid: str, data: dict):
    """Handle chat events, such as last_read_at."""
    user = SESSION_POOL.get(sid)
    if not user:
        return

    event_data = data.get("data", {})
    event_type = event_data.get("type")

    # Currently just log - can be extended to update chat state in DB
    log.debug(
        "Chat event: type=%s chat_id=%s user=%s",
        event_type,
        data.get("chat_id"),
        user.get("user_id"),
    )


@sio.on("events:channel")
async def channel_events(sid: str, data: dict):
    """Handle channel events, such as typing and last_read_at."""
    user = SESSION_POOL.get(sid)
    if not user:
        return

    room = f"channel:{data.get('channel_id')}"
    participants = sio.manager.get_participants(namespace="/", room=room)

    sids = [s for s, _ in participants]
    if sid not in sids:
        return

    event_data = data.get("data", {})
    event_type = event_data.get("type")

    if event_type == "typing":
        # Broadcast typing event to channel participants
        await sio.emit(
            "events:channel",
            {
                "channel_id": data.get("channel_id"),
                "message_id": data.get("message_id"),
                "data": event_data,
                "user": {
                    "id": user.get("user_id"),
                    "name": user.get("email", "").split("@")[0],
                },
            },
            room=room,
        )
    elif event_type == "last_read_at":
        # Could update channel member last_read_at in DB
        log.debug(
            "Channel last_read_at: channel=%s user=%s",
            data.get("channel_id"),
            user.get("user_id"),
        )
