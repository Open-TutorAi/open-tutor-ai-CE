"""Tests for the Socket.IO ASGI sub-mount at /realtime.

Reference: open-webui/backend/open_webui/socket/main.py
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from gateway.http.app import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def _admin_token(client):
    r = client.post(
        "/auths/signup",
        json={"email": "rt@t.com", "name": "RT", "password": "pass1234!"},
    )
    return r.json()["token"]


def test_socket_io_endpoint_exists(client):
    """GET /realtime/socket.io/?EIO=4&transport=polling must return a valid response."""
    r = client.get("/realtime/socket.io/?EIO=4&transport=polling")
    # Socket.IO responds with 200 on polling handshake
    assert r.status_code == 200


def test_socket_io_not_mounted_at_old_path(client):
    """Legacy /ws/socket.io path must not exist."""
    r = client.get("/ws/socket.io/?EIO=4&transport=polling")
    # Should return 404 (not mounted) or redirect — but NOT 200 from a real sio server
    assert r.status_code != 200


async def test_connect_rejects_missing_token():
    """connect() must return False when no token is provided."""
    from gateway.realtime.socket import SESSION_POOL, connect

    SESSION_POOL.clear()
    result = await connect("sid_no_token", {"QUERY_STRING": ""}, auth=None)
    assert result is False
    assert "sid_no_token" not in SESSION_POOL


async def test_connect_rejects_invalid_token():
    """connect() must return False when the token is invalid."""
    from gateway.realtime.socket import SESSION_POOL, connect

    SESSION_POOL.clear()
    with patch("gateway.realtime.socket.decode_jwt_token", return_value=None):
        result = await connect(
            "sid_bad_token", {"QUERY_STRING": "token=bad"}, auth=None
        )
    assert result is False
    assert "sid_bad_token" not in SESSION_POOL


async def test_connect_accepts_valid_token():
    """connect() must return True and populate SESSION_POOL for a valid token."""
    from gateway.realtime.socket import SESSION_POOL, connect, sio

    SESSION_POOL.clear()
    with patch(
        "gateway.realtime.socket.decode_jwt_token",
        return_value={"sub": "u1", "email": "a@b.com"},
    ):
        with patch.object(sio, "enter_room", new_callable=AsyncMock):
            with patch.object(sio, "save_session", new_callable=AsyncMock):
                with patch(
                    "gateway.realtime.socket._broadcast_user_list",
                    new_callable=AsyncMock,
                ):
                    result = await connect(
                        "sid_valid", {"QUERY_STRING": "token=good"}, auth=None
                    )
    assert result is True
    assert SESSION_POOL["sid_valid"]["user_id"] == "u1"


# ── Socket.IO event handler tests ───────────────────────────────────────────────


async def test_user_join_adds_to_session_pool():
    """When user-join is emitted, user should be added to SESSION_POOL."""
    from gateway.realtime import socket as socket_module
    from gateway.realtime.socket import SESSION_POOL, sio

    # Clear session pool
    SESSION_POOL.clear()

    # Mock the broadcast function and sio.enter_room
    with patch(
        "gateway.realtime.socket._broadcast_user_list", new_callable=AsyncMock
    ) as mock_broadcast:
        with patch.object(sio, "enter_room", new_callable=AsyncMock):
            # Create a mock sid
            sid = "test_sid_user_join"

            # Mock decode_jwt_token to return a valid user
            with patch("gateway.realtime.socket.decode_jwt_token") as mock_decode:
                mock_decode.return_value = {
                    "sub": "user123",
                    "email": "test@example.com",
                }

                # Call the user_join handler directly
                await socket_module.user_join(sid, {"auth": {"token": "fake_token"}})

                # Verify user was added to session pool
                assert sid in SESSION_POOL
                assert SESSION_POOL[sid]["user_id"] == "user123"
                assert SESSION_POOL[sid]["email"] == "test@example.com"

                # Verify broadcast was called
                mock_broadcast.assert_called_once()


async def test_disconnect_removes_from_session_pool_and_broadcasts():
    """When user disconnects, user should be removed and user-list broadcasted."""
    from gateway.realtime import socket as socket_module
    from gateway.realtime.socket import SESSION_POOL

    # Pre-populate session pool
    sid = "test_sid_disconnect"
    SESSION_POOL[sid] = {
        "user_id": "user123",
        "email": "test@example.com",
        "last_seen_at": 123456,
    }

    with patch(
        "gateway.realtime.socket._broadcast_user_list", new_callable=AsyncMock
    ) as mock_broadcast:
        # Call disconnect handler directly
        await socket_module.disconnect(sid)

        # Verify user was removed
        assert sid not in SESSION_POOL

        # Verify broadcast was called
        mock_broadcast.assert_called_once()


async def test_usage_updates_usage_pool():
    """When usage event is emitted, USAGE_POOL should be updated."""
    from gateway.realtime import socket as socket_module
    from gateway.realtime.socket import SESSION_POOL, USAGE_POOL

    # Pre-populate session pool (required by usage handler)
    sid = "test_sid_usage"
    SESSION_POOL[sid] = {
        "user_id": "user123",
        "email": "test@example.com",
        "last_seen_at": 123456,
    }

    # Clear usage pool
    USAGE_POOL.clear()

    with patch(
        "gateway.realtime.socket._broadcast_usage", new_callable=AsyncMock
    ) as mock_broadcast:
        # Call usage handler directly
        await socket_module.usage(sid, {"model": "llama3"})

        # Verify usage was recorded
        assert "llama3" in USAGE_POOL
        assert sid in USAGE_POOL["llama3"]

        # Verify broadcast was called
        mock_broadcast.assert_called_once()


async def test_heartbeat_updates_last_seen():
    """When heartbeat is emitted, last_seen_at should be updated."""

    from gateway.realtime import socket as socket_module
    from gateway.realtime.socket import SESSION_POOL

    # Pre-populate session pool
    sid = "test_sid_heartbeat"
    original_time = 123456
    SESSION_POOL[sid] = {
        "user_id": "user123",
        "email": "test@example.com",
        "last_seen_at": original_time,
    }

    # Call heartbeat handler directly
    await socket_module.heartbeat(sid, {})

    # Verify last_seen_at was updated (should be >= original_time)
    assert SESSION_POOL[sid]["last_seen_at"] >= original_time


async def test_chat_events_handler():
    """events:chat handler should not raise and should log the event."""
    from gateway.realtime import socket as socket_module
    from gateway.realtime.socket import SESSION_POOL

    # Pre-populate session pool
    sid = "test_sid_chat"
    SESSION_POOL[sid] = {
        "user_id": "user123",
        "email": "test@example.com",
        "last_seen_at": 123456,
    }

    # Call chat events handler - should not raise
    await socket_module.chat_events(
        sid, {"chat_id": "chat123", "data": {"type": "last_read_at"}}
    )

    # No exception means test passes


async def test_channel_events_typing_broadcasts():
    """events:channel with typing should broadcast to channel room."""
    from gateway.realtime import socket as socket_module
    from gateway.realtime.socket import SESSION_POOL, sio

    # Pre-populate session pool
    sid = "test_sid_channel"
    SESSION_POOL[sid] = {
        "user_id": "user123",
        "email": "test@example.com",
        "last_seen_at": 123456,
    }

    # Mock sio.manager.get_participants to return our sid
    mock_participants = [(sid, None)]

    with patch.object(sio.manager, "get_participants", return_value=mock_participants):
        with patch.object(sio, "emit", new_callable=AsyncMock) as mock_emit:
            # Call channel events handler
            await socket_module.channel_events(
                sid,
                {
                    "channel_id": "channel123",
                    "data": {"type": "typing", "content": "hello"},
                },
            )

            # Verify emit was called with events:channel
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == "events:channel"


async def test_emit_chat_event_targets_user_room():
    """emit_chat_event must emit chat-events to user:{user_id} room."""
    from gateway.realtime.socket import emit_chat_event, sio

    with patch.object(sio, "emit", new_callable=AsyncMock) as mock_emit:
        await emit_chat_event("user42", {"type": "chat:completion", "chat_id": "c1"})

    mock_emit.assert_called_once_with(
        "chat-events",
        {"type": "chat:completion", "chat_id": "c1"},
        room="user:user42",
    )


async def test_emit_channel_event_targets_channel_room():
    """emit_channel_event must emit channel-events to channel:{channel_id} room."""
    from gateway.realtime.socket import emit_channel_event, sio

    with patch.object(sio, "emit", new_callable=AsyncMock) as mock_emit:
        await emit_channel_event("ch99", {"type": "message", "content": "hi"})

    mock_emit.assert_called_once_with(
        "channel-events",
        {"type": "message", "content": "hi"},
        room="channel:ch99",
    )


def test_get_active_user_ids_deduplicates():
    """get_active_user_ids must return unique user IDs from SESSION_POOL."""
    from gateway.realtime.socket import SESSION_POOL, get_active_user_ids

    SESSION_POOL.clear()
    SESSION_POOL["s1"] = {"user_id": "u1", "email": "a@b.com", "last_seen_at": 1}
    SESSION_POOL["s2"] = {
        "user_id": "u1",
        "email": "a@b.com",
        "last_seen_at": 2,
    }  # same user, two sids
    SESSION_POOL["s3"] = {"user_id": "u2", "email": "c@d.com", "last_seen_at": 3}

    ids = get_active_user_ids()
    assert sorted(ids) == ["u1", "u2"]
    SESSION_POOL.clear()


# Run async tests with anyio
pytestmark = pytest.mark.anyio
