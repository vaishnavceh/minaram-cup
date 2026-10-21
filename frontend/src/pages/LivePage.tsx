import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { PublicLiveStream } from '../types';
import { useLiveUpdates } from '../hooks/useLiveUpdates';
import {
  Radio,
  ExternalLink,
  MessageSquare,
  Calendar,
  BarChart3,
  Trophy,
  AlertCircle,
  Clock,
  Share2,
  RefreshCw,
  Info,
  Tv
} from 'lucide-react';

export const LivePage: React.FC = () => {
  const [stream, setStream] = useState<PublicLiveStream | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [playerError, setPlayerError] = useState<boolean>(false);
  const [chatFallback, setChatFallback] = useState<boolean>(false);
  const [copiedLink, setCopiedLink] = useState<boolean>(false);

  const fetchStream = async () => {
    try {
      setError(null);
      const data = await api.getLiveStream();
      setStream(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load live stream configuration.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStream();
  }, []);

  // Listen to real-time live stream updates via SSE
  useLiveUpdates((evt) => {
    const evType = evt.event || (evt as any).type;
    if (evType === 'live_stream_updated') {
      const data = evt.data || {};
      setStream(data);
      setPlayerError(false);
    }
  });

  const handleShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 3000);
    }
  };

  // Determine current hostname for YouTube chat embedding
  const currentHostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const isLocalhost = currentHostname === 'localhost' || currentHostname === '127.0.0.1';

  // Construct chat URL
  const videoId = stream?.video_id;
  const youtubeChatUrl = videoId
    ? `https://www.youtube.com/live_chat?v=${encodeURIComponent(videoId)}&embed_domain=${encodeURIComponent(currentHostname)}`
    : null;
  const watchUrl = stream?.watch_url || (videoId ? `https://www.youtube.com/watch?v=${videoId}` : null);
  const directChatUrl = videoId ? `https://www.youtube.com/live_chat?v=${encodeURIComponent(videoId)}` : null;

  // Render Loading State
  if (loading) {
    return (
      <div className="min-h-[75vh] flex flex-col items-center justify-center px-4 bg-[#080808]">
        <div className="w-12 h-12 rounded-full border-2 border-brand-red border-t-transparent animate-spin mb-4" />
        <span className="font-mono text-sm tracking-widest text-[#9A9A9A] uppercase">
          CONNECTING TO LIVE BROADCAST...
        </span>
      </div>
    );
  }

  // Render API Error State
  if (error) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center px-4 bg-[#080808]">
        <div className="max-w-md w-full bg-[#111111] border border-[#222222] rounded-xl p-8 text-center shadow-2xl">
          <AlertCircle className="w-12 h-12 text-brand-red mx-auto mb-4" />
          <h2 className="font-display text-2xl text-white tracking-wider mb-2">BROADCAST FEED ERROR</h2>
          <p className="text-sm text-[#9A9A9A] font-sans mb-6">{error}</p>
          <button
            onClick={() => {
              setLoading(true);
              fetchStream();
            }}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-brand-red hover:bg-[#8e0e15] text-white font-mono text-xs uppercase tracking-wider transition-colors shadow-glow-red"
          >
            <RefreshCw className="w-4 h-4" />
            <span>RETRY CONNECTION</span>
          </button>
        </div>
      </div>
    );
  }

  const status = stream?.status || 'None';
  const isLive = stream?.is_active && status === 'Live';
  const isScheduled = status === 'Scheduled';
  const isEnded = status === 'Ended';
  const isHidden = status === 'Hidden' || status === 'None' || !stream?.video_id;

  // Format scheduled time if present
  let formattedScheduledTime: string | null = null;
  if (stream?.scheduled_start_time) {
    try {
      const dt = new Date(stream.scheduled_start_time);
      if (!isNaN(dt.getTime())) {
        formattedScheduledTime = dt.toLocaleString('en-US', {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          timeZoneName: 'short',
        });
      } else {
        formattedScheduledTime = stream.scheduled_start_time;
      }
    } catch {
      formattedScheduledTime = stream.scheduled_start_time;
    }
  }

  return (
    <div className="min-h-screen bg-[#080808] text-[#F5F5F5] pb-16">
      {/* Editorial Broadcast Header */}
      <section className="relative border-b border-[#222222] bg-[#0c0c0c]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            {/* Titles & Badge */}
            <div className="flex items-start space-x-4">
              <div className="w-14 h-14 sm:w-16 sm:h-16 flex-shrink-0 p-1.5 rounded-full bg-black/80 border border-neutral-800 shadow-xl flex items-center justify-center">
                <img
                  src="/assets/logos/transparent/minaram_logo_white.png"
                  alt="Minaram Cup Official Crest"
                  className="w-full h-full object-contain drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]"
                />
              </div>

              <div>
                <div className="flex items-center space-x-2.5 mb-1.5 flex-wrap gap-y-1">
                  <span className="font-mono text-xs font-bold tracking-widest text-brand-red uppercase">
                    MINARAM CUP
                  </span>
                  <span className="text-neutral-600">•</span>
                  <span className="font-mono text-xs tracking-widest text-[#9A9A9A] uppercase">
                    LIVE BROADCAST
                  </span>

                  {/* Status Badges */}
                  {isLive && (
                    <span className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-brand-red text-white font-mono text-[11px] font-bold tracking-widest uppercase shadow-glow-red animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-white inline-block animate-ping" />
                      <span>LIVE NOW</span>
                    </span>
                  )}

                  {isScheduled && (
                    <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-blue-600/20 border border-blue-500/50 text-blue-400 font-mono text-[11px] font-bold tracking-widest uppercase">
                      <Clock className="w-3 h-3" />
                      <span>UPCOMING BROADCAST</span>
                    </span>
                  )}

                  {isEnded && (
                    <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/50 text-amber-400 font-mono text-[11px] font-bold tracking-widest uppercase">
                      <span>BROADCAST ENDED</span>
                    </span>
                  )}
                </div>

                <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl tracking-wider text-white uppercase leading-tight">
                  {stream?.title || 'MINARAM CUP — OFFICIAL STREAM'}
                </h1>

                {stream?.stage && (
                  <div className="mt-1 flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-xs font-mono tracking-wider text-neutral-300">
                      🏆 {stream.stage}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Header Right Action Tools */}
            <div className="flex items-center space-x-2 self-start md:self-end">
              <button
                onClick={handleShare}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-[#161616] hover:bg-[#222222] border border-[#2a2a2a] text-xs font-mono text-neutral-300 hover:text-white transition-colors"
                title="Share stream link"
              >
                <Share2 className="w-3.5 h-3.5" />
                <span>{copiedLink ? 'LINK COPIED!' : 'SHARE'}</span>
              </button>

              {watchUrl && (
                <a
                  href={watchUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-md bg-brand-red hover:bg-[#8e0e15] text-white text-xs font-mono font-bold tracking-wider uppercase transition-colors shadow-glow-red"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>YOUTUBE</span>
                </a>
              )}
            </div>
          </div>

          {/* Announcement Banner (if configured) */}
          {stream?.announcement && (
            <div className="mt-4 px-4 py-2.5 rounded-lg bg-neutral-950/80 border border-neutral-800/80 flex items-start space-x-3 text-xs sm:text-sm text-neutral-300">
              <Info className="w-4 h-4 text-brand-red flex-shrink-0 mt-0.5" />
              <div className="flex-1 font-sans">{stream.announcement}</div>
            </div>
          )}
        </div>
      </section>

      {/* Main Stream Workspace */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-8">
        {/* STATE 1: HIDDEN OR NO STREAM CONFIGURED */}
        {isHidden ? (
          <div className="py-20 px-4 text-center">
            <div className="max-w-xl mx-auto bg-[#111111] border border-[#222222] rounded-2xl p-10 shadow-2xl">
              <div className="w-16 h-16 rounded-full bg-neutral-900 border border-neutral-800 flex items-center justify-center mx-auto mb-6">
                <Tv className="w-8 h-8 text-neutral-500" />
              </div>
              <h2 className="font-display text-3xl sm:text-4xl tracking-wider text-white mb-3 uppercase">
                NO LIVE BROADCAST
              </h2>
              <p className="text-[#9A9A9A] text-base font-sans mb-8 leading-relaxed max-w-md mx-auto">
                The next MINARAM CUP broadcast will appear here. Check the tournament schedule or results while waiting for matchday coverage.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <Link
                  to="/fixtures"
                  className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-sm font-mono tracking-wider text-white transition-colors"
                >
                  <Calendar className="w-4 h-4 text-brand-red" />
                  <span>VIEW FIXTURES</span>
                </Link>
                <Link
                  to="/standings"
                  className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-sm font-mono tracking-wider text-white transition-colors"
                >
                  <BarChart3 className="w-4 h-4 text-brand-red" />
                  <span>VIEW STANDINGS</span>
                </Link>
              </div>
            </div>
          </div>
        ) : (
          /* STATE 2, 3, 4: SCHEDULED, LIVE, OR ENDED */
          <div className="space-y-6">
            {/* Scheduled Notice Card (when scheduled) */}
            {isScheduled && formattedScheduledTime && (
              <div className="bg-gradient-to-r from-blue-950/40 via-neutral-900/60 to-blue-950/40 border border-blue-900/40 rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center space-x-3 text-center sm:text-left">
                  <div className="w-10 h-10 rounded-full bg-blue-900/40 border border-blue-700/50 flex items-center justify-center text-blue-400 flex-shrink-0">
                    <Clock className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-display text-lg text-white tracking-wide">BROADCAST SCHEDULED</h3>
                    <p className="text-xs font-mono text-blue-200">
                      Live coverage starts on <span className="font-bold text-white">{formattedScheduledTime}</span>
                    </p>
                  </div>
                </div>
                {watchUrl && (
                  <a
                    href={watchUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-bold tracking-wider uppercase transition-colors whitespace-nowrap shadow-[0_0_15px_rgba(37,99,235,0.4)]"
                  >
                    SET REMINDER ON YOUTUBE
                  </a>
                )}
              </div>
            )}

            {/* Ended Notice Card (when ended) */}
            {isEnded && (
              <div className="bg-amber-950/20 border border-amber-900/40 rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-amber-900/30 border border-amber-700/50 flex items-center justify-center text-amber-400 flex-shrink-0">
                    <Trophy className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-display text-lg text-white tracking-wide">MATCH BROADCAST CONCLUDED</h3>
                    <p className="text-xs text-neutral-300">
                      The official replay is available in the player below. Browse latest standings and upcoming fixtures.
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Link
                    to="/results"
                    className="px-3.5 py-1.5 rounded-lg bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-xs font-mono text-white transition-colors"
                  >
                    MATCH RESULTS
                  </Link>
                </div>
              </div>
            )}

            {/* Two-Column Desktop Layout / Stacked Mobile Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: Responsive 16:9 Official YouTube Player */}
              <div className="lg:col-span-8 flex flex-col">
                <div className="relative w-full aspect-video bg-[#000000] rounded-xl overflow-hidden border border-[#222222] shadow-[0_12px_40px_rgba(0,0,0,0.8)]">
                  {playerError ? (
                    /* Error State if embedding fails or video unavailable */
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-[#111111]">
                      <AlertCircle className="w-12 h-12 text-brand-red mb-3" />
                      <h3 className="font-display text-xl text-white tracking-wider mb-2">
                        VIDEO PLAYER UNAVAILABLE
                      </h3>
                      <p className="text-xs text-[#9A9A9A] max-w-md font-sans mb-5 leading-relaxed">
                        The broadcast may be restricted by YouTube embedding settings, marked private, or not yet streaming.
                        You can watch directly on YouTube.
                      </p>
                      {watchUrl && (
                        <a
                          href={watchUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-brand-red hover:bg-[#8e0e15] text-white font-mono text-xs font-bold tracking-wider uppercase transition-colors shadow-glow-red"
                        >
                          <ExternalLink className="w-4 h-4" />
                          <span>WATCH DIRECTLY ON YOUTUBE</span>
                        </a>
                      )}
                    </div>
                  ) : (
                    /* Official YouTube Embedded Player */
                    <iframe
                      src={stream?.embed_url || `https://www.youtube.com/embed/${videoId}?playsinline=1&rel=0&modestbranding=1`}
                      title={stream?.title || 'MINARAM CUP Live Stream'}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                      allowFullScreen
                      onError={() => setPlayerError(true)}
                      className="absolute inset-0 w-full h-full border-0"
                    />
                  )}
                </div>

                {/* Under Player Information Row */}
                <div className="mt-4 bg-[#111111] border border-[#222222] rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-display text-lg sm:text-xl text-white tracking-wide">
                        {stream?.title}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3 text-xs font-mono text-[#9A9A9A] flex-wrap gap-y-1">
                      {stream?.stage && (
                        <span className="text-neutral-300 font-bold">Stage: {stream.stage}</span>
                      )}
                      <span>•</span>
                      <span>Official MINARAM CUP Feed</span>
                      {videoId && (
                        <>
                          <span>•</span>
                          <span className="text-neutral-500">ID: {videoId}</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Fast Navigation Links */}
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <Link
                      to="/fixtures"
                      className="px-3 py-1.5 rounded-md bg-[#181818] hover:bg-[#222222] border border-[#2a2a2a] text-xs font-mono text-neutral-300 hover:text-white transition-colors"
                    >
                      FIXTURES
                    </Link>
                    <Link
                      to="/standings"
                      className="px-3 py-1.5 rounded-md bg-[#181818] hover:bg-[#222222] border border-[#2a2a2a] text-xs font-mono text-neutral-300 hover:text-white transition-colors"
                    >
                      STANDINGS
                    </Link>
                  </div>
                </div>
              </div>

              {/* Right Column: Embedded YouTube Live Chat */}
              <div className="lg:col-span-4 flex flex-col">
                <div className="bg-[#111111] border border-[#222222] rounded-xl overflow-hidden flex flex-col h-[520px] sm:h-[580px] lg:h-[calc(100vh-280px)] min-h-[460px] shadow-xl">
                  {/* Chat Section Header */}
                  <div className="px-4 py-3 bg-[#161616] border-b border-[#222222] flex items-center justify-between flex-shrink-0">
                    <div className="flex items-center space-x-2">
                      <MessageSquare className="w-4 h-4 text-brand-red" />
                      <span className="font-display text-base tracking-wider text-white">LIVE CHAT</span>
                    </div>
                    {directChatUrl && (
                      <a
                        href={directChatUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[11px] font-mono text-[#9A9A9A] hover:text-white flex items-center space-x-1 transition-colors"
                        title="Open popout chat in YouTube"
                      >
                        <span>POPOUT</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  {/* Chat Content / Fallback */}
                  <div className="flex-1 relative bg-[#0a0a0a]">
                    {chatFallback || !youtubeChatUrl ? (
                      /* Chat Fallback Card */
                      <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
                        <MessageSquare className="w-10 h-10 text-neutral-600 mb-3" />
                        <h4 className="font-display text-lg text-neutral-300 tracking-wider mb-2 uppercase">
                          CHAT UNAVAILABLE
                        </h4>
                        <p className="text-xs text-[#9A9A9A] max-w-xs font-sans mb-5 leading-relaxed">
                          {isLocalhost
                            ? 'YouTube requires production domain cookies to embed interactive chat.'
                            : 'Live chat embedding may be disabled or restricted by YouTube security policies.'}
                        </p>
                        {directChatUrl && (
                          <a
                            href={directChatUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-[#222222] hover:bg-[#2e2e2e] text-white font-mono text-xs tracking-wider uppercase transition-colors border border-[#333333]"
                          >
                            <ExternalLink className="w-3.5 h-3.5 text-brand-red" />
                            <span>OPEN CHAT ON YOUTUBE</span>
                          </a>
                        )}
                        <button
                          onClick={() => setChatFallback(false)}
                          className="mt-3 text-[11px] font-mono text-neutral-500 hover:text-neutral-400 underline"
                        >
                          Try Reloading Chat Frame
                        </button>
                      </div>
                    ) : (
                      /* YouTube Official Live Chat Frame */
                      <iframe
                        src={youtubeChatUrl}
                        title="YouTube Live Chat"
                        className="w-full h-full border-0"
                        onError={() => setChatFallback(true)}
                      />
                    )}
                  </div>

                  {/* Chat Footer note */}
                  <div className="px-3.5 py-2 bg-[#0e0e0e] border-t border-[#1a1a1a] flex items-center justify-between text-[10px] font-mono text-neutral-500">
                    <span>Powered by YouTube Live</span>
                    {directChatUrl && (
                      <a
                        href={directChatUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-neutral-300 underline"
                      >
                        Open YouTube
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LivePage;
