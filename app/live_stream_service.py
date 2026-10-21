"""
MINARAM CUP — Live Stream Management Service
Handles YouTube URL validation, video ID extraction, stream configuration,
database persistence, and real-time live event broadcasting.
"""

from __future__ import annotations

import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from app.database import Database
from app.events import broadcaster

logger = logging.getLogger("minaram_cup.live_stream")

# Standard YouTube 11-character alphanumeric, underscore, hyphen ID regex
YOUTUBE_VIDEO_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{11}$")

ALLOWED_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}

VALID_STREAM_STATUSES = {"Scheduled", "Live", "Ended", "Hidden"}


def extract_youtube_video_id(raw_url: str) -> Optional[str]:
    """
    Safely extract and validate an 11-character YouTube video ID using urllib.parse.
    Supports:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - https://www.youtube.com/live/VIDEO_ID
      - https://www.youtube.com/embed/VIDEO_ID
      - m.youtube.com and music.youtube.com variants
      - Raw 11-character video IDs
    Rejects:
      - Non-YouTube domains
      - Malformed IDs
      - Script/HTML injection attempts
      - Empty or whitespace-only inputs
    """
    if not raw_url or not isinstance(raw_url, str):
        return None

    cleaned = raw_url.strip()
    if not cleaned:
        return None

    # Direct 11-character ID match
    if YOUTUBE_VIDEO_ID_REGEX.match(cleaned):
        return cleaned

    # Prepend scheme if missing (e.g., youtube.com/watch?v=...)
    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned

    try:
        parsed = urlparse(cleaned)
    except Exception:
        return None

    # Verify domain
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None

    # Check hostname matches or ends with allowed domains
    is_allowed = False
    for allowed in ALLOWED_YOUTUBE_HOSTS:
        if hostname == allowed or hostname.endswith("." + allowed):
            is_allowed = True
            break

    if not is_allowed:
        return None

    candidate_id: Optional[str] = None
    path_segments = [seg for seg in parsed.path.split("/") if seg]

    if "youtu.be" in hostname:
        # Format: youtu.be/VIDEO_ID
        if path_segments:
            candidate_id = path_segments[0]
    else:
        # Format: youtube.com/watch?v=VIDEO_ID
        if parsed.path.rstrip("/") == "/watch":
            qs = parse_qs(parsed.query)
            v_list = qs.get("v")
            if v_list and len(v_list[0]) > 0:
                candidate_id = v_list[0]
        # Format: youtube.com/live/VIDEO_ID
        elif len(path_segments) >= 2 and path_segments[0] == "live":
            candidate_id = path_segments[1]
        # Format: youtube.com/embed/VIDEO_ID
        elif len(path_segments) >= 2 and path_segments[0] == "embed":
            candidate_id = path_segments[1]
        # Format: youtube.com/v/VIDEO_ID or youtube.com/shorts/VIDEO_ID
        elif len(path_segments) >= 2 and path_segments[0] in ("v", "shorts"):
            candidate_id = path_segments[1]

    if candidate_id and YOUTUBE_VIDEO_ID_REGEX.match(candidate_id):
        return candidate_id

    return None


def build_embed_url(video_id: str) -> str:
    """Construct a clean, secure HTTPS YouTube iframe embed URL."""
    if not video_id or not YOUTUBE_VIDEO_ID_REGEX.match(video_id):
        return ""
    return f"https://www.youtube.com/embed/{video_id}?playsinline=1&rel=0&modestbranding=1"


def build_chat_url(video_id: str, embed_domain: str) -> str:
    """
    Construct a YouTube live chat iframe URL for the matching public hostname.
    Cleans domain of any port or scheme.
    """
    if not video_id or not YOUTUBE_VIDEO_ID_REGEX.match(video_id):
        return ""
    clean_domain = re.sub(r"^https?://", "", embed_domain or "").split(":")[0].strip()
    if not clean_domain:
        clean_domain = "localhost"
    return f"https://www.youtube.com/live_chat?v={video_id}&embed_domain={clean_domain}"


class LiveStreamService:
    def __init__(self, db: Database):
        self.db = db

    def get_admin_config(self) -> Dict[str, Any]:
        """Retrieve authoritative stream configuration for administrators."""
        row = self.db.execute_one("SELECT * FROM live_stream_config WHERE id = 1;")
        if not row:
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute_non_query("""
                INSERT OR IGNORE INTO live_stream_config (
                    id, youtube_url, video_id, title, stage, status, announcement, scheduled_start_time, is_published, created_at, updated_at, updated_by
                ) VALUES (
                    1, '', '', 'MINARAM CUP — LIVE BROADCAST', '', 'Scheduled', '', '', 0, ?, ?, 'admin'
                );
            """, (now_ts, now_ts))
            row = self.db.execute_one("SELECT * FROM live_stream_config WHERE id = 1;")

        res = dict(row)
        res["is_published"] = bool(res.get("is_published", 0))
        video_id = res.get("video_id") or ""
        res["embed_url"] = build_embed_url(video_id) if video_id else ""
        res["watch_url"] = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        return res

    def get_public_config(self, host_domain: str = "") -> Dict[str, Any]:
        """
        Retrieve sanitized public stream state for visitors.
        Strict privacy: If unpublished or status is 'Hidden', suppresses the video ID
        and YouTube URL so private/draft broadcasts are never exposed.
        """
        row = self.db.execute_one("SELECT * FROM live_stream_config WHERE id = 1;")
        if not row:
            return {
                "is_active": False,
                "status": "Hidden",
                "title": "MINARAM CUP — LIVE BROADCAST",
                "stage": "",
                "announcement": "",
                "scheduled_start_time": "",
                "video_id": None,
                "embed_url": None,
                "chat_url": None,
                "watch_url": None,
            }

        cfg = dict(row)
        is_published = bool(cfg.get("is_published", 0))
        status = cfg.get("status", "Scheduled")

        # If hidden or not published, do not expose video details to public visitors
        if not is_published or status == "Hidden":
            return {
                "is_active": False,
                "status": "Hidden" if status == "Hidden" else "None",
                "title": cfg.get("title") or "MINARAM CUP — LIVE BROADCAST",
                "stage": cfg.get("stage") or "",
                "announcement": cfg.get("announcement") or "",
                "scheduled_start_time": cfg.get("scheduled_start_time") or "",
                "video_id": None,
                "embed_url": None,
                "chat_url": None,
                "watch_url": None,
            }

        video_id = cfg.get("video_id") or ""
        return {
            "is_active": status == "Live",
            "status": status,
            "title": cfg.get("title") or "MINARAM CUP — LIVE BROADCAST",
            "stage": cfg.get("stage") or "",
            "announcement": cfg.get("announcement") or "",
            "scheduled_start_time": cfg.get("scheduled_start_time") or "",
            "video_id": video_id or None,
            "embed_url": build_embed_url(video_id) if video_id else None,
            "chat_url": build_chat_url(video_id, host_domain) if video_id else None,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
        }

    def save_config(
        self,
        youtube_url: str,
        title: str,
        stage: str = "",
        status: str = "Scheduled",
        announcement: str = "",
        scheduled_start_time: str = "",
        is_published: Optional[bool] = None,
        admin_username: str = "admin",
        broadcast_update: bool = True
    ) -> Dict[str, Any]:
        """Validate and persist the stream configuration."""
        clean_url = (youtube_url or "").strip()
        video_id = ""
        if clean_url:
            extracted = extract_youtube_video_id(clean_url)
            if not extracted:
                raise ValueError("Invalid YouTube URL. Please provide a valid youtube.com or youtu.be livestream link.")
            video_id = extracted

        # Validate status
        if status not in VALID_STREAM_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STREAM_STATUSES)}")

        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        current = self.get_admin_config()
        new_published = current["is_published"] if is_published is None else (1 if is_published else 0)

        self.db.execute_non_query("""
            UPDATE live_stream_config SET
                youtube_url = ?,
                video_id = ?,
                title = ?,
                stage = ?,
                status = ?,
                announcement = ?,
                scheduled_start_time = ?,
                is_published = ?,
                updated_at = ?,
                updated_by = ?
            WHERE id = 1;
        """, (
            clean_url,
            video_id,
            title.strip(),
            stage.strip(),
            status,
            announcement.strip(),
            scheduled_start_time.strip(),
            new_published,
            now_ts,
            admin_username
        ))

        updated_config = self.get_admin_config()

        if broadcast_update:
            self._broadcast_change(updated_config)

        return updated_config

    def publish(
        self,
        youtube_url: Optional[str] = None,
        title: Optional[str] = None,
        stage: Optional[str] = None,
        status: str = "Live",
        announcement: Optional[str] = None,
        scheduled_start_time: Optional[str] = None,
        admin_username: str = "admin"
    ) -> Dict[str, Any]:
        """Publish the stream configuration to the public live website."""
        current = self.get_admin_config()

        url_to_save = youtube_url if youtube_url is not None else current["youtube_url"]
        title_to_save = title if title is not None else current["title"]
        stage_to_save = stage if stage is not None else current["stage"]
        announcement_to_save = announcement if announcement is not None else current["announcement"]
        scheduled_to_save = scheduled_start_time if scheduled_start_time is not None else current["scheduled_start_time"]

        return self.save_config(
            youtube_url=url_to_save,
            title=title_to_save,
            stage=stage_to_save,
            status=status,
            announcement=announcement_to_save,
            scheduled_start_time=scheduled_to_save,
            is_published=True,
            admin_username=admin_username,
            broadcast_update=True
        )

    def end_broadcast(self, admin_username: str = "admin") -> Dict[str, Any]:
        """Mark the active stream as Ended and broadcast update."""
        current = self.get_admin_config()
        return self.save_config(
            youtube_url=current["youtube_url"],
            title=current["title"],
            stage=current["stage"],
            status="Ended",
            announcement=current["announcement"],
            scheduled_start_time=current["scheduled_start_time"],
            is_published=True,
            admin_username=admin_username,
            broadcast_update=True
        )

    def hide_broadcast(self, admin_username: str = "admin") -> Dict[str, Any]:
        """Hide the stream from public view and broadcast update."""
        current = self.get_admin_config()
        return self.save_config(
            youtube_url=current["youtube_url"],
            title=current["title"],
            stage=current["stage"],
            status="Hidden",
            announcement=current["announcement"],
            scheduled_start_time=current["scheduled_start_time"],
            is_published=False,
            admin_username=admin_username,
            broadcast_update=True
        )

    def _broadcast_change(self, config: Dict[str, Any]) -> None:
        """Broadcast live stream state change to all connected SSE clients."""
        public_state = self.get_public_config()
        payload = {
            "type": "live_stream_updated",
            "event": "live_stream_updated",
            "data": public_state,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            broadcaster.broadcast_from_thread("live_stream_updated", None, public_state)
        except Exception as e:
            logger.warning(f"Could not broadcast live stream change: {e}")
