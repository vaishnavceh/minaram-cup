"""
Automated test suite for YouTube URL validation, live stream configuration,
public endpoint privacy enforcement, and administrative security.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth import create_access_token
from app.database import Database
from app.live_stream_service import (
    extract_youtube_video_id,
    build_embed_url,
    build_chat_url,
    LiveStreamService,
)

client = TestClient(app)


def test_youtube_url_parsing_valid_formats():
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&feature=share", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ?t=100", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/live/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/live/dQw4w9WgXcQ?si=abc123xyz", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://music.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("http://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("1234567890A", "1234567890A"),
    ]
    for url, expected_id in test_cases:
        extracted = extract_youtube_video_id(url)
        assert extracted == expected_id, f"Failed for {url}: expected {expected_id}, got {extracted}"


def test_youtube_url_parsing_invalid_and_malicious():
    invalid_cases = [
        "",
        "   ",
        None,
        "https://vimeo.com/12345678",
        "https://evil.com/watch?v=dQw4w9WgXcQ",
        "javascript:alert('xss')",
        "<script>alert(1)</script>",
        "https://www.youtube.com/watch?v=too_short",
        "https://www.youtube.com/watch?v=way_too_long_to_be_a_youtube_id_123456",
        "https://www.youtube.com/watch?v=invalid!char",
        "https://www.youtube.com/user/channelname",
    ]
    for invalid in invalid_cases:
        assert extract_youtube_video_id(invalid) is None, f"Expected None for {invalid}"


def test_build_embed_and_chat_urls():
    vid = "dQw4w9WgXcQ"
    embed_url = build_embed_url(vid)
    assert embed_url == f"https://www.youtube.com/embed/{vid}?playsinline=1&rel=0&modestbranding=1"

    # Chat url
    chat_url = build_chat_url(vid, "minaramcup.com")
    assert chat_url == f"https://www.youtube.com/live_chat?v={vid}&embed_domain=minaramcup.com"

    # Chat with port or http prefix
    chat_url2 = build_chat_url(vid, "http://localhost:5173")
    assert chat_url2 == f"https://www.youtube.com/live_chat?v={vid}&embed_domain=localhost"


def test_public_endpoint_privacy_when_hidden_or_unpublished():
    db = Database()
    svc = LiveStreamService(db)

    # Save a stream with a real YouTube ID, but hidden/unpublished
    svc.save_config(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Secret Internal Test Broadcast",
        stage="Round of 8",
        status="Hidden",
        announcement="Private test",
        is_published=False,
        broadcast_update=False
    )

    resp = client.get("/api/public/live-stream")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_active"] is False
    assert data["status"] in ("Hidden", "None")
    # Must NEVER leak the video ID or embed URL
    assert data["video_id"] is None
    assert data["embed_url"] is None
    assert data["chat_url"] is None
    assert data["watch_url"] is None


def test_public_endpoint_when_published_and_live():
    db = Database()
    svc = LiveStreamService(db)

    svc.publish(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="MINARAM CUP 2026 — GRAND FINAL",
        stage="GRAND FINAL",
        status="Live",
        announcement="Welcome to the grand final broadcast!",
        scheduled_start_time="2026-10-22T20:00:00"
    )

    resp = client.get("/api/public/live-stream")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_active"] is True
    assert data["status"] == "Live"
    assert data["title"] == "MINARAM CUP 2026 — GRAND FINAL"
    assert data["stage"] == "GRAND FINAL"
    assert data["announcement"] == "Welcome to the grand final broadcast!"
    assert data["video_id"] == "dQw4w9WgXcQ"
    assert "https://www.youtube.com/embed/dQw4w9WgXcQ" in data["embed_url"]
    assert "https://www.youtube.com/watch?v=dQw4w9WgXcQ" in data["watch_url"]


def test_admin_endpoints_require_authentication():
    # Unauthenticated GET
    resp = client.get("/api/admin/live-stream")
    assert resp.status_code == 401

    # Unauthenticated PUT
    resp = client.put("/api/admin/live-stream", json={
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Unauthorized update",
        "status": "Live"
    })
    assert resp.status_code == 401

    # Unauthenticated POST publish
    resp = client.post("/api/admin/live-stream/publish", json={})
    assert resp.status_code == 401

    # Unauthenticated POST end
    resp = client.post("/api/admin/live-stream/end")
    assert resp.status_code == 401

    # Unauthenticated POST hide
    resp = client.post("/api/admin/live-stream/hide")
    assert resp.status_code == 401


def test_admin_authenticated_operations():
    token = create_access_token("admin")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Preview
    prev_resp = client.post("/api/admin/live-stream/preview", json={
        "youtube_url": "https://youtu.be/dQw4w9WgXcQ?t=10"
    }, headers=headers)
    assert prev_resp.status_code == 200
    assert prev_resp.json()["valid"] is True
    assert prev_resp.json()["video_id"] == "dQw4w9WgXcQ"

    # Preview invalid
    prev_bad = client.post("/api/admin/live-stream/preview", json={
        "youtube_url": "https://example.com/not-youtube"
    }, headers=headers)
    assert prev_bad.status_code == 400

    # 2. Update/Save
    save_resp = client.put("/api/admin/live-stream", json={
        "youtube_url": "https://www.youtube.com/live/dQw4w9WgXcQ",
        "title": "MINARAM CUP — SEMI FINALS",
        "stage": "SEMI FINALS",
        "status": "Scheduled",
        "announcement": "Broadcast begins shortly.",
        "scheduled_start_time": "2026-10-22T18:00:00",
        "is_published": False
    }, headers=headers)
    assert save_resp.status_code == 200
    cfg = save_resp.json()
    assert cfg["video_id"] == "dQw4w9WgXcQ"
    assert cfg["title"] == "MINARAM CUP — SEMI FINALS"
    assert cfg["status"] == "Scheduled"

    # 3. Publish
    pub_resp = client.post("/api/admin/live-stream/publish", json={
        "status": "Live"
    }, headers=headers)
    assert pub_resp.status_code == 200
    assert pub_resp.json()["status"] == "Live"
    assert pub_resp.json()["is_published"] is True

    # 4. End
    end_resp = client.post("/api/admin/live-stream/end", headers=headers)
    assert end_resp.status_code == 200
    assert end_resp.json()["status"] == "Ended"

    # 5. Hide
    hide_resp = client.post("/api/admin/live-stream/hide", headers=headers)
    assert hide_resp.status_code == 200
    assert hide_resp.json()["status"] == "Hidden"
    assert hide_resp.json()["is_published"] is False


def test_persistence_across_restarts():
    """Verify stream configuration persists across fresh database / service connections."""
    db1 = Database()
    svc1 = LiveStreamService(db1)
    svc1.save_config(
        youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="PERSISTENCE CHECK STREAM",
        stage="ROUND OF 8",
        status="Live",
        announcement="Will survive restart",
        scheduled_start_time="2026-10-22T21:00:00",
        is_published=True,
        admin_username="admin"
    )

    # Simulate fresh startup / restart
    db2 = Database()
    svc2 = LiveStreamService(db2)
    cfg = svc2.get_admin_config()
    assert cfg["title"] == "PERSISTENCE CHECK STREAM"
    assert cfg["stage"] == "ROUND OF 8"
    assert cfg["status"] == "Live"
    assert cfg["video_id"] == "dQw4w9WgXcQ"
    assert cfg["is_published"] is True


def test_desktop_live_stream_view_instantiation():
    import customtkinter as ctk
    from app.ui.live_stream import LiveStreamView
    root = ctk.CTk()
    root.withdraw()
    view = LiveStreamView(root, Database())
    view.refresh()
    root.destroy()


def test_spa_live_page_serving():
    """Verify FastAPI backend serves the SPA index.html for /live route."""
    resp = client.get("/live")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "<div id=\"root\">" in resp.text or "<!DOCTYPE html>" in resp.text



