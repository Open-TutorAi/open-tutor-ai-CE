"""Contract tests — /api/v1/audio/* and /api/v1/images/* match UI clients."""

from unittest.mock import AsyncMock, MagicMock, patch


def _admin_auth(client):
    """First signup → admin."""
    client.post(
        "/auths/signup",
        json={"email": "admin@media.com", "name": "Admin", "password": "pass1234!"},
    )
    r = client.post(
        "/api/v1/auths/signin",
        json={"email": "admin@media.com", "password": "pass1234!"},
    )
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _user_auth(client):
    """Second signup → regular user."""
    client.post(
        "/auths/signup",
        json={"email": "user@media.com", "name": "User", "password": "pass1234!"},
    )
    r = client.post(
        "/api/v1/auths/signin",
        json={"email": "user@media.com", "password": "pass1234!"},
    )
    return {"Authorization": f"Bearer {r.json()['token']}"}


class TestAudioApiV1:
    def test_get_config_admin(self, client):
        h = _admin_auth(client)
        assert client.get("/api/v1/audio/config", headers=h).status_code == 200

    def test_get_config_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        assert client.get("/api/v1/audio/config", headers=h).status_code == 403

    def test_update_config_flat(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/audio/config/update",
            json={
                "url": "https://api.openai.com",
                "key": "sk-test",
                "model": "tts-1",
                "speaker": "nova",
            },
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["speaker"] == "nova"

    def test_update_config_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.post(
            "/api/v1/audio/config/update", json={"model": "tts-1"}, headers=h
        )
        assert r.status_code == 403

    def test_get_models(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        assert client.get("/api/v1/audio/models", headers=h).status_code == 200

    def test_get_voices(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.get("/api/v1/audio/voices", headers=h)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_speech_endpoint(self, client):
        h_admin = _admin_auth(client)
        # Configure audio URL so the proxy has a target
        client.post(
            "/api/v1/audio/config/update",
            json={"url": "https://api.openai.com", "key": "sk-test"},
            headers=h_admin,
        )
        h = _user_auth(client)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"audio bytes"
        mock_resp.headers = MagicMock()
        mock_resp.headers.get = MagicMock(return_value="audio/mpeg")

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_resp)

        with patch("gateway.http.routers.audio.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
            r = client.post(
                "/api/v1/audio/speech",
                json={"input": "hello", "voice": "alloy"},
                headers=h,
            )
        assert r.status_code == 200

    def test_transcriptions_local_fallback_when_no_url(self, client):
        """With no external STT URL, transcription falls back to local whisper."""
        import io
        import ai.media.whisper_stt as w

        h = _user_auth(client)  # no URL configured by default
        with (
            patch.object(w, "WHISPER_AVAILABLE", True),
            patch.object(w, "transcribe_bytes", return_value="local transcription"),
        ):
            r = client.post(
                "/api/v1/audio/transcriptions",
                files={"file": ("a.wav", io.BytesIO(b"x"), "audio/wav")},
                headers=h,
            )
        assert r.status_code == 200
        assert r.json()["text"] == "local transcription"

    def test_transcriptions_endpoint(self, client):
        import io

        h_admin = _admin_auth(client)
        # Configure audio URL so the proxy has a target
        client.post(
            "/api/v1/audio/config/update",
            json={"url": "https://api.openai.com", "key": "sk-test"},
            headers=h_admin,
        )
        h = _user_auth(client)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"text": "hello world"})

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_resp)

        fake_audio = io.BytesIO(b"fake audio data")
        with patch("gateway.http.routers.audio.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
            r = client.post(
                "/api/v1/audio/transcriptions",
                files={"file": ("audio.mp3", fake_audio, "audio/mpeg")},
                headers=h,
            )
        assert r.status_code == 200
        assert "text" in r.json()


class TestImagesApiV1:
    def test_get_config_admin(self, client):
        h = _admin_auth(client)
        assert client.get("/api/v1/images/config", headers=h).status_code == 200

    def test_get_config_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        assert client.get("/api/v1/images/config", headers=h).status_code == 403

    def test_update_config(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/images/config/update", json={"engine": "openai"}, headers=h
        )
        assert r.status_code == 200
        assert r.json()["engine"] == "openai"

    def test_verify_config_url_is_get_admin(self, client):
        h = _admin_auth(client)
        r = client.get("/api/v1/images/config/url/verify", headers=h)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_verify_config_url_user_forbidden(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        assert (
            client.get("/api/v1/images/config/url/verify", headers=h).status_code == 403
        )

    def test_image_config_admin(self, client):
        h = _admin_auth(client)
        assert client.get("/api/v1/images/image/config", headers=h).status_code == 200

    def test_update_image_config(self, client):
        h = _admin_auth(client)
        r = client.post(
            "/api/v1/images/image/config/update",
            json={"model": "dall-e-2", "size": "512x512"},
            headers=h,
        )
        assert r.status_code == 200
        assert r.json()["model"] == "dall-e-2"

    def test_get_models_admin(self, client):
        h = _admin_auth(client)
        r = client.get("/api/v1/images/models", headers=h)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_generations_returns_list(self, client):
        """generations must return a list directly for UI's res.map((image) => image.url)."""
        _admin_auth(client)
        h = _user_auth(client)
        r = client.post(
            "/api/v1/images/generations", json={"prompt": "a cat"}, headers=h
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_generations_user_allowed(self, client):
        _admin_auth(client)
        h = _user_auth(client)
        r = client.post(
            "/api/v1/images/generations", json={"prompt": "test"}, headers=h
        )
        assert r.status_code == 200
