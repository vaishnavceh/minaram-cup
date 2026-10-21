import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { AdminLiveStreamConfig, LiveStreamStatus } from '../types';
import {
  Tv,
  ExternalLink,
  Save,
  Radio,
  Clock,
  Eye,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  EyeOff,
  StopCircle,
  Sparkles,
  Info
} from 'lucide-react';

interface AdminLiveStreamManagerProps {
  token: string;
}

export const AdminLiveStreamManager: React.FC<AdminLiveStreamManagerProps> = ({ token }) => {
  const [config, setConfig] = useState<AdminLiveStreamConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  // Form Fields
  const [youtubeUrl, setYoutubeUrl] = useState<string>('');
  const [title, setTitle] = useState<string>('');
  const [stage, setStage] = useState<string>('');
  const [status, setStatus] = useState<LiveStreamStatus>('Scheduled');
  const [announcement, setAnnouncement] = useState<string>('');
  const [scheduledStartTime, setScheduledStartTime] = useState<string>('');

  // Preview State
  const [previewActive, setPreviewActive] = useState<boolean>(false);
  const [previewVideoId, setPreviewVideoId] = useState<string>('');
  const [previewEmbedUrl, setPreviewEmbedUrl] = useState<string>('');

  const loadConfig = async () => {
    try {
      setLoading(true);
      setErrorMessage('');
      const data = await api.adminGetLiveStream(token);
      setConfig(data);
      setYoutubeUrl(data.youtube_url || '');
      setTitle(data.title || 'MINARAM CUP — LIVE BROADCAST');
      setStage(data.stage || '');
      setStatus(data.status || 'Scheduled');
      setAnnouncement(data.announcement || '');
      setScheduledStartTime(data.scheduled_start_time || '');
      if (data.video_id) {
        setPreviewVideoId(data.video_id);
        setPreviewEmbedUrl(data.embed_url || `https://www.youtube.com/embed/${data.video_id}?playsinline=1&rel=0`);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load livestream settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, [token]);

  const showNotification = (msg: string, isError: boolean = false) => {
    if (isError) {
      setErrorMessage(msg);
      setSuccessMessage('');
    } else {
      setSuccessMessage(msg);
      setErrorMessage('');
      setTimeout(() => setSuccessMessage(''), 6000);
    }
  };

  // 1. Preview Stream
  const handlePreview = async () => {
    if (!youtubeUrl.trim()) {
      showNotification('Please enter a YouTube livestream URL to preview.', true);
      return;
    }
    try {
      setErrorMessage('');
      const res = await api.adminPreviewLiveStream(youtubeUrl.trim(), token);
      setPreviewVideoId(res.video_id);
      setPreviewEmbedUrl(res.embed_url);
      setPreviewActive(true);
      showNotification(`Valid YouTube video detected (ID: ${res.video_id}). Preview active below.`);
    } catch (err: any) {
      showNotification(err.message || 'Invalid YouTube URL.', true);
    }
  };

  // 2. Save Stream (persists without forcing publish)
  const handleSave = async () => {
    try {
      setSaving(true);
      setErrorMessage('');
      const updated = await api.adminUpdateLiveStream(
        {
          youtube_url: youtubeUrl.trim(),
          title: title.trim(),
          stage: stage.trim(),
          status: status,
          announcement: announcement.trim(),
          scheduled_start_time: scheduledStartTime.trim(),
        },
        token
      );
      setConfig(updated);
      showNotification('Stream configuration saved successfully to authoritative database.');
    } catch (err: any) {
      showNotification(err.message || 'Failed to save stream configuration.', true);
    } finally {
      setSaving(false);
    }
  };

  // 3. Publish to Website
  const handlePublish = async () => {
    if (!youtubeUrl.trim()) {
      showNotification('Please enter a YouTube livestream URL before publishing.', true);
      return;
    }
    try {
      setSaving(true);
      setErrorMessage('');
      const updated = await api.adminPublishLiveStream(
        {
          youtube_url: youtubeUrl.trim(),
          title: title.trim(),
          stage: stage.trim(),
          status: status === 'Hidden' ? 'Live' : status,
          announcement: announcement.trim(),
          scheduled_start_time: scheduledStartTime.trim(),
        },
        token
      );
      setConfig(updated);
      setStatus(updated.status);
      showNotification(`Livestream successfully published to /live with status "${updated.status}"! Connected visitors updated in real time.`);
    } catch (err: any) {
      showNotification(err.message || 'Failed to publish stream to website.', true);
    } finally {
      setSaving(false);
    }
  };

  // 4. End Broadcast
  const handleEnd = async () => {
    if (!window.confirm('Are you sure you want to end this live broadcast?')) return;
    try {
      setSaving(true);
      setErrorMessage('');
      const updated = await api.adminEndLiveStream(token);
      setConfig(updated);
      setStatus('Ended');
      showNotification('Broadcast ended. Public page updated to show ended status with replay available.');
    } catch (err: any) {
      showNotification(err.message || 'Failed to end broadcast.', true);
    } finally {
      setSaving(false);
    }
  };

  // 5. Hide Live Page
  const handleHide = async () => {
    if (!window.confirm('Are you sure you want to hide the live stream from public visitors?')) return;
    try {
      setSaving(true);
      setErrorMessage('');
      const updated = await api.adminHideLiveStream(token);
      setConfig(updated);
      setStatus('Hidden');
      showNotification('Live broadcast hidden from public website. URL and details are completely concealed.');
    } catch (err: any) {
      showNotification(err.message || 'Failed to hide live stream.', true);
    } finally {
      setSaving(false);
    }
  };

  const stagePresets = [
    'Group Stage',
    'Round of 16',
    'Round of 8',
    'Quarter Finals',
    'Semi Finals',
    'Third Place Playoff',
    'Grand Final'
  ];

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center">
        <RefreshCw className="w-8 h-8 text-brand-red animate-spin mb-3" />
        <span className="font-mono text-xs text-[#9A9A9A] tracking-wider uppercase">
          Loading Live Stream Settings...
        </span>
      </div>
    );
  }

  const isPublished = config?.is_published;
  const currentStatus = config?.status || 'Scheduled';

  return (
    <div className="space-y-6">
      {/* Notifications */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800 text-xs font-mono text-emerald-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-xs font-mono text-red-300 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-brand-red" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Active Broadcast Overview Banner */}
      <div className="bg-[#111111] border border-[#222222] rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-black/60 border border-neutral-800 flex items-center justify-center text-brand-red shadow-lg">
            <Tv className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="font-mono text-xs text-[#9A9A9A] uppercase tracking-wider">
                CURRENT PUBLIC STATE:
              </span>
              {!isPublished ? (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-neutral-800 text-neutral-300 border border-neutral-700 uppercase">
                  UNPUBLISHED DRAFT
                </span>
              ) : currentStatus === 'Live' ? (
                <span className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-brand-red text-white text-[11px] font-mono font-bold tracking-widest uppercase shadow-glow-red animate-pulse">
                  <span className="w-1.5 h-1.5 rounded-full bg-white inline-block animate-ping" />
                  <span>● LIVE NOW</span>
                </span>
              ) : currentStatus === 'Scheduled' ? (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-blue-900/40 text-blue-300 border border-blue-700/50 uppercase">
                  SCHEDULED / UPCOMING
                </span>
              ) : currentStatus === 'Ended' ? (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-900/40 text-amber-300 border border-amber-700/50 uppercase">
                  BROADCAST ENDED
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-neutral-900 text-neutral-400 border border-neutral-800 uppercase">
                  HIDDEN
                </span>
              )}
            </div>
            <div className="text-xs font-mono text-neutral-400">
              Video ID: <span className="text-white font-bold">{config?.video_id || 'None'}</span> • Title: <span className="text-neutral-200">{config?.title || 'MINARAM CUP — LIVE BROADCAST'}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href="/live"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-xs font-mono text-neutral-200 hover:text-white transition-colors"
          >
            <span>VIEW PUBLIC PAGE (/live)</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Main Configuration Card */}
      <div className="bg-[#111111] border border-[#222222] rounded-xl p-6 space-y-6">
        <div className="border-b border-[#222222] pb-4">
          <h2 className="font-display text-xl text-white tracking-wider uppercase">
            LIVE STREAM SETTINGS
          </h2>
          <p className="text-xs text-[#9A9A9A] font-sans mt-1">
            Configure the official YouTube livestream URL, tournament stage, and live broadcast parameters.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Field 1: YouTube Live URL */}
          <div className="md:col-span-2 space-y-1.5">
            <label className="block text-xs font-mono font-bold uppercase tracking-wider text-neutral-300">
              1. YouTube Live URL <span className="text-brand-red">*</span>
            </label>
            <p className="text-[11px] text-neutral-500">
              Accepts watch?v=, youtu.be/, /live/, /embed/, or raw 11-char ID. Example: https://www.youtube.com/watch?v=YOUR_VIDEO_ID
            </p>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="flex-1 px-4 py-2.5 rounded-lg bg-[#181818] border border-[#2a2a2a] text-white text-sm font-mono placeholder-neutral-600 focus:outline-none focus:border-brand-red"
              />
              <button
                type="button"
                onClick={handlePreview}
                className="px-4 py-2.5 rounded-lg bg-[#222222] hover:bg-[#2c2c2c] border border-neutral-700 text-white font-mono text-xs font-bold tracking-wider uppercase flex items-center space-x-1.5 transition-colors whitespace-nowrap"
              >
                <Eye className="w-3.5 h-3.5 text-brand-gold" />
                <span>PREVIEW STREAM</span>
              </button>
            </div>
          </div>

          {/* Field 2: Stream Title */}
          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-bold uppercase tracking-wider text-neutral-300">
              2. Stream Title <span className="text-brand-red">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="MINARAM CUP 2026 — ROUND OF 8"
              className="w-full px-4 py-2.5 rounded-lg bg-[#181818] border border-[#2a2a2a] text-white text-sm font-sans placeholder-neutral-600 focus:outline-none focus:border-brand-red"
            />
          </div>

          {/* Field 3: Tournament Stage or Round */}
          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-bold uppercase tracking-wider text-neutral-300">
              3. Tournament Stage or Round
            </label>
            <input
              type="text"
              value={stage}
              onChange={(e) => setStage(e.target.value)}
              placeholder="ROUND OF 8"
              className="w-full px-4 py-2.5 rounded-lg bg-[#181818] border border-[#2a2a2a] text-white text-sm font-sans placeholder-neutral-600 focus:outline-none focus:border-brand-red"
            />
            {/* Quick preset chips */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {stagePresets.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setStage(preset)}
                  className={`text-[10px] font-mono px-2 py-0.5 rounded transition-colors ${
                    stage === preset
                      ? 'bg-brand-red text-white'
                      : 'bg-[#181818] text-neutral-400 hover:text-white border border-neutral-800'
                  }`}
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>

          {/* Field 4: Stream Status */}
          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-bold uppercase tracking-wider text-neutral-300">
              4. Stream Status <span className="text-brand-red">*</span>
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as LiveStreamStatus)}
              className="w-full px-4 py-2.5 rounded-lg bg-[#181818] border border-[#2a2a2a] text-white text-sm font-mono focus:outline-none focus:border-brand-red"
            >
              <option value="Scheduled">Scheduled — Upcoming broadcast with start time</option>
              <option value="Live">Live — Player active with LIVE NOW badge</option>
              <option value="Ended">Ended — Broadcast concluded, replay available</option>
              <option value="Hidden">Hidden — Concealed from public website</option>
            </select>
          </div>

          {/* Field 6: Scheduled Start Time */}
          <div className="space-y-1.5">
            <label className="block text-xs font-mono font-bold uppercase tracking-wider text-neutral-300">
              6. Scheduled Start Time (Optional)
            </label>
            <input
              type="text"
              value={scheduledStartTime}
              onChange={(e) => setScheduledStartTime(e.target.value)}
              placeholder="e.g. 2026-10-22 20:00 (UTC/IST)"
              className="w-full px-4 py-2.5 rounded-lg bg-[#181818] border border-[#2a2a2a] text-white text-sm font-mono placeholder-neutral-600 focus:outline-none focus:border-brand-red"
            />
          </div>

          {/* Field 5: Optional Short Announcement */}
          <div className="md:col-span-2 space-y-1.5">
            <label className="block text-xs font-mono font-bold uppercase tracking-wider text-neutral-300">
              5. Short Public Announcement (Optional)
            </label>
            <textarea
              value={announcement}
              onChange={(e) => setAnnouncement(e.target.value)}
              rows={2}
              placeholder="e.g. Welcome to the MINARAM CUP quarterfinals broadcast! Use YouTube live chat to support your campus squad."
              className="w-full px-4 py-2.5 rounded-lg bg-[#181818] border border-[#2a2a2a] text-white text-sm font-sans placeholder-neutral-600 focus:outline-none focus:border-brand-red"
            />
          </div>
        </div>

        {/* Action Buttons Toolbar */}
        <div className="pt-4 border-t border-[#222222] flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-[#222222] hover:bg-[#2c2c2c] border border-neutral-700 text-white font-mono text-xs font-bold tracking-wider uppercase transition-colors"
          >
            <Save className="w-4 h-4 text-emerald-400" />
            <span>SAVE STREAM</span>
          </button>

          <button
            type="button"
            onClick={handlePublish}
            disabled={saving}
            className="flex items-center space-x-2 px-6 py-2.5 rounded-lg bg-brand-red hover:bg-[#8e0e15] text-white font-mono text-xs font-bold tracking-wider uppercase transition-colors shadow-glow-red"
          >
            <Radio className="w-4 h-4 animate-pulse" />
            <span>PUBLISH TO WEBSITE</span>
          </button>

          <button
            type="button"
            onClick={handleEnd}
            disabled={saving}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-amber-900/40 hover:bg-amber-900/60 border border-amber-700/60 text-amber-200 font-mono text-xs font-bold tracking-wider uppercase transition-colors"
          >
            <StopCircle className="w-4 h-4 text-amber-400" />
            <span>END BROADCAST</span>
          </button>

          <button
            type="button"
            onClick={handleHide}
            disabled={saving}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-red-950/40 hover:bg-red-950/70 border border-red-900/60 text-red-300 font-mono text-xs font-bold tracking-wider uppercase transition-colors"
          >
            <EyeOff className="w-4 h-4 text-brand-red" />
            <span>HIDE LIVE PAGE</span>
          </button>
        </div>
      </div>

      {/* Interactive Embed Preview Box */}
      {(previewActive || previewVideoId) && (
        <div className="bg-[#111111] border border-[#222222] rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#222222] pb-3">
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-brand-gold" />
              <h3 className="font-display text-lg text-white tracking-wider uppercase">
                EMBED VERIFICATION PREVIEW
              </h3>
            </div>
            <span className="text-xs font-mono text-emerald-400">
              Validated YouTube Video ID: {previewVideoId}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 aspect-video bg-black rounded-lg overflow-hidden border border-neutral-800">
              {previewEmbedUrl ? (
                <iframe
                  src={previewEmbedUrl}
                  title="Stream Preview"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="w-full h-full border-0"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-xs font-mono text-neutral-500">
                  No preview available
                </div>
              )}
            </div>

            <div className="bg-[#161616] border border-neutral-800 rounded-lg p-4 flex flex-col justify-between text-xs font-mono space-y-3">
              <div>
                <span className="text-neutral-400 uppercase tracking-wider block mb-2 font-bold">
                  Preview Diagnostics:
                </span>
                <p className="text-neutral-300 mb-1">
                  • Embed URL: <span className="text-neutral-500 break-all">{previewEmbedUrl}</span>
                </p>
                <p className="text-neutral-300 mb-1">
                  • Watch Link: <a href={`https://www.youtube.com/watch?v=${previewVideoId}`} target="_blank" rel="noopener noreferrer" className="text-brand-red underline">Open on YouTube</a>
                </p>
                <p className="text-neutral-300">
                  • Target Public Page: <a href="/live" target="_blank" rel="noopener noreferrer" className="text-emerald-400 underline">/live</a>
                </p>
              </div>

              <div className="p-2.5 rounded bg-neutral-900 border border-neutral-800 text-[11px] text-neutral-400 leading-relaxed font-sans">
                💡 Clicking <strong>PUBLISH TO WEBSITE</strong> will instantly push this stream to all active visitors without refreshing or rebuilding.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
