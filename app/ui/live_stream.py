"""
MINARAM CUP — Live Stream Management Desktop View
Administrator control panel for configuring, previewing, saving, publishing,
ending, and hiding the active YouTube livestream on the public /live watch page.
"""

import webbrowser
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from app.ui import theme
from app.database import Database
from app.live_stream_service import (
    LiveStreamService,
    extract_youtube_video_id,
    build_embed_url,
    build_chat_url,
)


class LiveStreamView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db: Database):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.service = LiveStreamService(db)

        self.status_var = ctk.StringVar(value="Scheduled")
        self.stage_var = ctk.StringVar(value="Round of 8")

        self.build_ui()
        self.refresh()

    def refresh(self):
        """Reload configuration from database into interface fields."""
        cfg = self.service.get_admin_config()

        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, cfg.get("youtube_url", ""))

        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, cfg.get("title", ""))

        self.stage_entry.delete(0, "end")
        self.stage_entry.insert(0, cfg.get("stage", ""))

        self.status_seg.set(cfg.get("status", "Scheduled"))

        self.announcement_box.delete("1.0", "end")
        self.announcement_box.insert("1.0", cfg.get("announcement", ""))

        self.scheduled_entry.delete(0, "end")
        self.scheduled_entry.insert(0, cfg.get("scheduled_start_time", ""))

        self.update_status_display(cfg)

    def build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 12))

        title_box = ctk.CTkFrame(hdr, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="LIVE STREAM SETTINGS",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Configure active YouTube broadcast, preview player & chat, and publish directly to /live",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED
        ).pack(anchor="w")

        # Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=16, pady=(0, 20))

        # 1. Active Status Overview Card
        self.status_card = ctk.CTkFrame(
            self.container,
            fg_color=theme.BG_CARD,
            corner_radius=10,
            border_color=theme.BORDER_COLOR,
            border_width=1
        )
        self.status_card.pack(fill="x", pady=(0, 16))

        sc_hdr = ctk.CTkFrame(self.status_card, fg_color="transparent")
        sc_hdr.pack(fill="x", padx=16, pady=(14, 10))

        ctk.CTkLabel(
            sc_hdr,
            text="CURRENT BROADCAST STATUS",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(side="left")

        self.active_pill = ctk.CTkLabel(
            sc_hdr,
            text="CHECKING...",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#333333",
            text_color="#FFFFFF",
            corner_radius=6,
            padx=10,
            pady=3
        )
        self.active_pill.pack(side="right")

        self.status_details_lbl = ctk.CTkLabel(
            self.status_card,
            text="No stream loaded",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
            justify="left"
        )
        self.status_details_lbl.pack(fill="x", padx=16, pady=(0, 14))

        # 2. Main Configuration Card
        cfg_card = ctk.CTkFrame(
            self.container,
            fg_color=theme.BG_CARD,
            corner_radius=10,
            border_color=theme.BORDER_COLOR,
            border_width=1
        )
        cfg_card.pack(fill="x", pady=(0, 16))

        c_hdr = ctk.CTkFrame(cfg_card, fg_color="transparent")
        c_hdr.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(
            c_hdr,
            text="BROADCAST CONFIGURATION",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(side="left")

        # Field 1: YouTube Live URL
        f1 = ctk.CTkFrame(cfg_card, fg_color="transparent")
        f1.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(f1, text="1. YouTube Live URL:", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            f1,
            text="Supports standard watch?v=, youtu.be/, /live/, or /embed/ formats. Validates 11-char video ID.",
            font=ctk.CTkFont(size=10),
            text_color=theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 4))
        self.url_entry = ctk.CTkEntry(
            f1,
            placeholder_text="https://www.youtube.com/watch?v=YOUR_VIDEO_ID",
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            height=34
        )
        self.url_entry.pack(fill="x")

        # Field 2 & 3: Title and Stage (2-column layout)
        f_row = ctk.CTkFrame(cfg_card, fg_color="transparent")
        f_row.pack(fill="x", padx=16, pady=(0, 10))
        f_row.columnconfigure(0, weight=3)
        f_row.columnconfigure(1, weight=2)

        # Field 2: Stream Title
        f2 = ctk.CTkFrame(f_row, fg_color="transparent")
        f2.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(f2, text="2. Stream Title:", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        self.title_entry = ctk.CTkEntry(
            f2,
            placeholder_text="e.g. MINARAM CUP 2026 — ROUND OF 8",
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            height=34
        )
        self.title_entry.pack(fill="x", pady=(4, 0))

        # Field 3: Tournament Stage or Round
        f3 = ctk.CTkFrame(f_row, fg_color="transparent")
        f3.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        ctk.CTkLabel(f3, text="3. Tournament Stage or Round:", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        self.stage_entry = ctk.CTkEntry(
            f3,
            placeholder_text="e.g. ROUND OF 8 / QUARTER FINALS",
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            height=34
        )
        self.stage_entry.pack(fill="x", pady=(4, 0))

        # Field 4: Stream Status
        f4 = ctk.CTkFrame(cfg_card, fg_color="transparent")
        f4.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(f4, text="4. Stream Status:", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        self.status_seg = ctk.CTkSegmentedButton(
            f4,
            values=["Scheduled", "Live", "Ended", "Hidden"],
            variable=self.status_var,
            selected_color=theme.ACCENT_GREEN,
            selected_hover_color=theme.ACCENT_GREEN_HOVER,
            unselected_color=theme.BG_INPUT,
            unselected_hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            height=32
        )
        self.status_seg.pack(fill="x", pady=(4, 0))

        # Field 5: Optional Short Announcement
        f5 = ctk.CTkFrame(cfg_card, fg_color="transparent")
        f5.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(f5, text="5. Optional Short Announcement:", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        self.announcement_box = ctk.CTkTextbox(
            f5,
            height=60,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            border_width=1
        )
        self.announcement_box.pack(fill="x", pady=(4, 0))

        # Field 6: Optional Scheduled Start Time
        f6 = ctk.CTkFrame(cfg_card, fg_color="transparent")
        f6.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(f6, text="6. Optional Scheduled Start Time:", font=ctk.CTkFont(size=12, weight="bold"), text_color=theme.TEXT_PRIMARY).pack(anchor="w")
        self.scheduled_entry = ctk.CTkEntry(
            f6,
            placeholder_text="e.g. 2026-10-22 20:00 (UTC/IST)",
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            height=34
        )
        self.scheduled_entry.pack(fill="x", pady=(4, 0))

        # 3. Action Buttons Card
        btn_card = ctk.CTkFrame(
            self.container,
            fg_color=theme.BG_CARD,
            corner_radius=10,
            border_color=theme.BORDER_COLOR,
            border_width=1
        )
        btn_card.pack(fill="x", pady=(0, 16))

        b_hdr = ctk.CTkFrame(btn_card, fg_color="transparent")
        b_hdr.pack(fill="x", padx=16, pady=(14, 10))
        ctk.CTkLabel(
            b_hdr,
            text="CONTROL ACTIONS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=theme.TEXT_PRIMARY
        ).pack(side="left")

        actions_frame = ctk.CTkFrame(btn_card, fg_color="transparent")
        actions_frame.pack(fill="x", padx=16, pady=(0, 14))

        # 5 Buttons required:
        # PREVIEW STREAM, SAVE STREAM, PUBLISH TO WEBSITE, END BROADCAST, HIDE LIVE PAGE
        self.btn_preview = ctk.CTkButton(
            actions_frame,
            text="👁️  PREVIEW STREAM",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            height=36,
            command=self.handle_preview
        )
        self.btn_preview.pack(side="left", padx=(0, 8), fill="x", expand=True)

        self.btn_save = ctk.CTkButton(
            actions_frame,
            text="💾  SAVE STREAM",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            height=36,
            command=self.handle_save
        )
        self.btn_save.pack(side="left", padx=(0, 8), fill="x", expand=True)

        self.btn_publish = ctk.CTkButton(
            actions_frame,
            text="🚀  PUBLISH TO WEBSITE",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=theme.ACCENT_GREEN,
            hover_color=theme.ACCENT_GREEN_HOVER,
            text_color=theme.TEXT_DARK,
            height=36,
            command=self.handle_publish
        )
        self.btn_publish.pack(side="left", padx=(0, 8), fill="x", expand=True)

        self.btn_end = ctk.CTkButton(
            actions_frame,
            text="⏹️  END BROADCAST",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#D97706",
            hover_color="#B45309",
            text_color="#FFFFFF",
            height=36,
            command=self.handle_end
        )
        self.btn_end.pack(side="left", padx=(0, 8), fill="x", expand=True)

        self.btn_hide = ctk.CTkButton(
            actions_frame,
            text="🔒  HIDE LIVE PAGE",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#B91C1C",
            hover_color="#991B1B",
            text_color="#FFFFFF",
            height=36,
            command=self.handle_hide
        )
        self.btn_hide.pack(side="left", fill="x", expand=True)

        # Quick Links Bar
        links_box = ctk.CTkFrame(btn_card, fg_color="transparent")
        links_box.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            links_box,
            text="🌐 Open Public Live Page (/live)",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=theme.ACCENT_GREEN_TEXT,
            hover_color=theme.BG_INPUT,
            anchor="w",
            command=lambda: webbrowser.open("http://localhost:8000/live")
        ).pack(side="left")

    def update_status_display(self, cfg):
        st = cfg.get("status", "Scheduled")
        is_pub = cfg.get("is_published", False)
        vid = cfg.get("video_id") or "None"
        title = cfg.get("title") or "MINARAM CUP — LIVE BROADCAST"
        stage = cfg.get("stage") or "Not configured"
        up_at = cfg.get("updated_at") or "Unknown"

        if not is_pub:
            self.active_pill.configure(text="NOT PUBLISHED", fg_color="#4B5563", text_color="#FFFFFF")
        elif st == "Live":
            self.active_pill.configure(text="● LIVE NOW", fg_color="#DC2626", text_color="#FFFFFF")
        elif st == "Scheduled":
            self.active_pill.configure(text="UPCOMING / SCHEDULED", fg_color="#2563EB", text_color="#FFFFFF")
        elif st == "Ended":
            self.active_pill.configure(text="BROADCAST ENDED", fg_color="#D97706", text_color="#FFFFFF")
        elif st == "Hidden":
            self.active_pill.configure(text="HIDDEN FROM PUBLIC", fg_color="#7F1D1D", text_color="#FFFFFF")

        self.status_details_lbl.configure(
            text=f"Title: {title}  •  Stage: {stage}  •  Video ID: {vid}  •  Published: {'Yes' if is_pub else 'No'}  •  Last updated: {up_at}"
        )

    def handle_preview(self):
        raw_url = self.url_entry.get().strip()
        if not raw_url:
            messagebox.showwarning("Preview Stream", "Please enter a YouTube livestream URL first.")
            return

        vid = extract_youtube_video_id(raw_url)
        if not vid:
            messagebox.showerror(
                "Invalid YouTube URL",
                "The entered URL could not be parsed as a valid YouTube video.\n\n"
                "Please provide a link matching youtube.com or youtu.be with a valid 11-character video ID."
            )
            return

        embed_url = build_embed_url(vid)
        watch_url = f"https://www.youtube.com/watch?v={vid}"

        msg = (
            f"Valid YouTube Video Detected!\n\n"
            f"Video ID: {vid}\n"
            f"Embed URL: {embed_url}\n"
            f"Watch URL: {watch_url}\n\n"
            f"Would you like to open the video in your default browser to test playback?"
        )
        if messagebox.askyesno("Preview Stream", msg):
            webbrowser.open(watch_url)

    def handle_save(self):
        raw_url = self.url_entry.get().strip()
        title = self.title_entry.get().strip() or "MINARAM CUP — LIVE BROADCAST"
        stage = self.stage_entry.get().strip()
        status = self.status_var.get()
        announcement = self.announcement_box.get("1.0", "end").strip()
        scheduled = self.scheduled_entry.get().strip()

        if raw_url:
            vid = extract_youtube_video_id(raw_url)
            if not vid:
                messagebox.showerror(
                    "Validation Error",
                    "Invalid YouTube URL format. Please enter a valid YouTube link before saving."
                )
                return

        try:
            cfg = self.service.save_config(
                youtube_url=raw_url,
                title=title,
                stage=stage,
                status=status,
                announcement=announcement,
                scheduled_start_time=scheduled,
                admin_username="desktop_admin",
                broadcast_update=True
            )
            self.update_status_display(cfg)
            messagebox.showinfo("Stream Saved", "Stream configuration saved successfully to authoritative database.")
        except Exception as e:
            messagebox.showerror("Error Saving Stream", f"Failed to save stream configuration: {e}")

    def handle_publish(self):
        raw_url = self.url_entry.get().strip()
        if not raw_url:
            messagebox.showwarning("Publish Stream", "Please provide a YouTube livestream URL before publishing.")
            return

        vid = extract_youtube_video_id(raw_url)
        if not vid:
            messagebox.showerror(
                "Validation Error",
                "Cannot publish invalid YouTube URL. Please verify the URL before publishing."
            )
            return

        title = self.title_entry.get().strip() or "MINARAM CUP — LIVE BROADCAST"
        stage = self.stage_entry.get().strip()
        announcement = self.announcement_box.get("1.0", "end").strip()
        scheduled = self.scheduled_entry.get().strip()
        status = self.status_var.get()
        if status not in ("Live", "Scheduled"):
            status = "Live"
            self.status_var.set("Live")

        try:
            cfg = self.service.publish(
                youtube_url=raw_url,
                title=title,
                stage=stage,
                status=status,
                announcement=announcement,
                scheduled_start_time=scheduled,
                admin_username="desktop_admin"
            )
            self.update_status_display(cfg)
            messagebox.showinfo(
                "Published to Website",
                f"Livestream published to /live successfully!\n\n"
                f"Status: {status}\n"
                f"Video ID: {cfg.get('video_id')}\n"
                f"Real-time update broadcasted to all connected visitors."
            )
        except Exception as e:
            messagebox.showerror("Publish Error", f"Failed to publish stream: {e}")

    def handle_end(self):
        if not messagebox.askyesno("End Broadcast", "Are you sure you want to mark this broadcast as Ended?"):
            return
        try:
            cfg = self.service.end_broadcast(admin_username="desktop_admin")
            self.status_var.set("Ended")
            self.update_status_display(cfg)
            messagebox.showinfo("Broadcast Ended", "Broadcast status updated to 'Ended' and published to website.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to end broadcast: {e}")

    def handle_hide(self):
        if not messagebox.askyesno("Hide Live Page", "Are you sure you want to hide the live stream from public visitors?"):
            return
        try:
            cfg = self.service.hide_broadcast(admin_username="desktop_admin")
            self.status_var.set("Hidden")
            self.update_status_display(cfg)
            messagebox.showinfo("Live Page Hidden", "Live broadcast has been hidden from public visitors.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to hide live page: {e}")
