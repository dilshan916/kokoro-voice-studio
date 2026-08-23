import React, { useRef, useState, useEffect, useCallback } from 'react';
import WaveSurfer from 'wavesurfer.js';
import {
  Play,
  Pause,
  RotateCcw,
  RotateCw,
  Volume2,
  VolumeX,
  Repeat,
  Download,
  Music,
  FileText,
  Copy,
  Check,
  X,
  Sparkles,
} from 'lucide-react';
import { AudioTrack } from '../types';

interface AudioPlayerBarProps {
  currentTrack: AudioTrack | null;
}

export const AudioPlayerBar: React.FC<AudioPlayerBarProps> = ({ currentTrack }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.85);
  const [isMuted, setIsMuted] = useState(false);
  const [isLooping, setIsLooping] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [showSrtModal, setShowSrtModal] = useState(false);
  const [copiedSrt, setCopiedSrt] = useState(false);

  // Initialize or re-create WaveSurfer instance on track change
  useEffect(() => {
    if (!containerRef.current || !currentTrack) return;

    let isMounted = true;
    let blobUrl: string | null = null;

    // Destroy existing instance
    if (wavesurferRef.current) {
      wavesurferRef.current.destroy();
      wavesurferRef.current = null;
    }

    setIsReady(false);
    setIsPlaying(false);
    setCurrentTime(0);

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: 'rgba(255, 255, 255, 0.2)',
      progressColor: '#6366f1',
      cursorColor: '#ffffff',
      cursorWidth: 2,
      barWidth: 2,
      barGap: 3,
      barRadius: 2,
      height: 36,
      normalize: true,
    });

    ws.on('ready', () => {
      if (!isMounted) return;
      setIsReady(true);
      setDuration(ws.getDuration());
      ws.setVolume(isMuted ? 0 : volume);
      // Auto-play when ready
      ws.play().then(() => {
        if (isMounted) setIsPlaying(true);
      }).catch((e) => {
        console.warn('Auto-play blocked or aborted:', e);
      });
    });

    ws.on('play', () => setIsPlaying(true));
    ws.on('pause', () => setIsPlaying(false));

    ws.on('timeupdate', (currTime) => {
      setCurrentTime(currTime);
    });

    ws.on('finish', () => {
      if (isLooping) {
        ws.play();
      } else {
        setIsPlaying(false);
      }
    });

    wavesurferRef.current = ws;

    if (currentTrack.audio_url.startsWith('blob:')) {
      // In-memory Blob URL from App.tsx: 100% immune to IDM / download managers, instant zero-latency load!
      ws.load(currentTrack.audio_url);
    } else {
      // HTTP URL fallback: fetch as Blob in JS to bypass external download managers
      fetch(currentTrack.audio_url)
        .then((res) => res.blob())
        .then((blob) => {
          if (!isMounted) return;
          blobUrl = URL.createObjectURL(blob);
          ws.load(blobUrl);
        })
        .catch((err) => {
          console.error('Failed to load audio blob into WaveSurfer:', err);
          if (isMounted) {
            ws.load(currentTrack.audio_url);
          }
        });
    }

    return () => {
      isMounted = false;
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
      ws.destroy();
      wavesurferRef.current = null;
    };
  }, [currentTrack]);

  // Handle Play/Pause toggle
  const togglePlay = useCallback(() => {
    if (!wavesurferRef.current || !isReady) return;
    wavesurferRef.current.playPause();
  }, [isReady]);

  // Skip seconds
  const skipSeconds = useCallback(
    (seconds: number) => {
      if (!wavesurferRef.current || !isReady) return;
      const current = wavesurferRef.current.getCurrentTime();
      const total = wavesurferRef.current.getDuration() || 1;
      const targetTime = Math.min(Math.max(0, current + seconds), total);
      wavesurferRef.current.setTime(targetTime);
    },
    [isReady]
  );

  // Volume change
  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setVolume(val);
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(val);
    }
    if (val > 0 && isMuted) {
      setIsMuted(false);
    }
  };

  const toggleMute = () => {
    if (!wavesurferRef.current) return;
    if (isMuted) {
      wavesurferRef.current.setVolume(volume);
      setIsMuted(false);
    } else {
      wavesurferRef.current.setVolume(0);
      setIsMuted(true);
    }
  };

  const toggleLoop = () => {
    setIsLooping(!isLooping);
  };
  // Download .srt subtitle file for CapCut / Premiere Pro
  const downloadSrt = useCallback(() => {
    if (!currentTrack?.srt_content) return;
    const blob = new Blob([currentTrack.srt_content], {
      type: 'text/plain;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentTrack.srt_filename || `${currentTrack.id}.srt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [currentTrack]);

  // Copy raw SRT subtitles to clipboard
  const copySrtToClipboard = useCallback(() => {
    if (!currentTrack?.srt_content) return;
    navigator.clipboard.writeText(currentTrack.srt_content);
    setCopiedSrt(true);
    setTimeout(() => setCopiedSrt(false), 2000);
  }, [currentTrack]);

  // Format seconds to mm:ss
  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs < 0) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <>
      <footer className="h-16 border-t border-white/[0.06] bg-studio-surface/80 backdrop-blur-xl px-6 flex items-center justify-between select-none z-30">
        {/* Left: Track Info */}
        <div className="w-1/4 min-w-[200px] flex items-center space-x-3 overflow-hidden">
          {currentTrack ? (
            <>
              <div className="w-9 h-9 rounded-xl bg-white/[0.06] flex items-center justify-center text-lg shrink-0 shadow-sm">
                {currentTrack.voice_flag || '🎙️'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-white truncate">
                  {currentTrack.title}
                </p>
                <div className="flex items-center space-x-1.5 text-[10px] text-gray-400">
                  <span className="font-medium text-gray-300">
                    {currentTrack.voice_name}
                  </span>
                  <span>•</span>
                  <span className="text-brand-primary truncate">
                    {currentTrack.eq_preset}
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <Music className="w-4 h-4 opacity-40" />
              <span>Ready to generate speech</span>
            </div>
          )}
        </div>

        {/* Center: Transport Controls & Waveform Peaks */}
        <div className="flex-1 max-w-2xl px-6 flex flex-col items-center justify-center space-y-1">
          {/* Transport Buttons */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => skipSeconds(-5)}
              disabled={!currentTrack || !isReady}
              className="text-gray-500 hover:text-white disabled:opacity-30 transition-colors"
              title="Rewind 5s"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={togglePlay}
              disabled={!currentTrack || !isReady}
              className="w-8 h-8 rounded-full bg-white text-black hover:bg-gray-200 disabled:bg-white/20 disabled:text-gray-500 flex items-center justify-center shadow-lg transition-all active:scale-95"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <Pause className="w-4 h-4 fill-black" />
              ) : (
                <Play className="w-4 h-4 fill-black ml-0.5" />
              )}
            </button>

            <button
              onClick={() => skipSeconds(5)}
              disabled={!currentTrack || !isReady}
              className="text-gray-500 hover:text-white disabled:opacity-30 transition-colors"
              title="Forward 5s"
            >
              <RotateCw className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={toggleLoop}
              disabled={!currentTrack}
              className={`p-1 transition-colors ${
                isLooping ? 'text-brand-primary' : 'text-gray-500 hover:text-white'
              }`}
              title="Loop"
            >
              <Repeat className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* WaveSurfer Audio Waveform Peaks Canvas & Timecode */}
          <div className="w-full flex items-center space-x-3">
            <span className="w-9 text-right text-[10px] font-mono text-gray-400">
              {formatTime(currentTime)}
            </span>

            <div className="flex-1 relative flex items-center">
              {/* WaveSurfer rendering container */}
              <div
                ref={containerRef}
                className={`w-full h-9 cursor-pointer transition-opacity ${
                  isReady ? 'opacity-100' : 'opacity-20'
                }`}
              />
              {!isReady && currentTrack && (
                <div className="absolute inset-0 flex items-center justify-center text-[11px] font-mono text-gray-500">
                  Loading waveform peaks...
                </div>
              )}
            </div>

            <span className="w-9 text-[10px] font-mono text-gray-400">
              {formatTime(duration || (currentTrack?.duration ?? 0))}
            </span>
          </div>
        </div>

        {/* Right: Volume & Export Suite */}
        <div className="w-1/4 min-w-[240px] flex items-center justify-end space-x-3">
          <div className="flex items-center space-x-1.5">
            <button
              onClick={toggleMute}
              className="text-gray-400 hover:text-white transition-colors"
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="w-4 h-4 text-rose-400" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-14 h-1 bg-white/[0.08] rounded-lg cursor-pointer"
            />
          </div>

          {currentTrack && (
            <div className="flex items-center space-x-1.5">
              {/* Subtitles (SRT) for CapCut / Premiere */}
              {currentTrack.srt_content && (
                <button
                  onClick={() => setShowSrtModal(true)}
                  className="px-3 py-1.5 rounded-full bg-brand-primary/10 hover:bg-brand-primary/20 text-brand-primary border border-brand-primary/25 hover:border-brand-primary/40 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                  title="View & Export CapCut Subtitles (.srt)"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>SRT</span>
                </button>
              )}

              {/* Audio Export Download */}
              <a
                href={currentTrack.audio_url}
                download={currentTrack.filename}
                className="px-3.5 py-1.5 rounded-full bg-white/[0.06] hover:bg-white/[0.12] text-xs text-white font-medium flex items-center gap-1.5 transition-all shadow-sm"
                title="Download Mastered Audio"
              >
                <Download className="w-3.5 h-3.5 text-white" />
                <span>Audio</span>
              </a>
            </div>
          )}
        </div>
      </footer>

      {/* Subtitles & CapCut Export Modal */}
      {showSrtModal && currentTrack?.srt_content && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-150"
          onClick={() => setShowSrtModal(false)}
        >
          <div
            className="w-full max-w-xl bg-studio-surface border border-white/[0.12] rounded-3xl p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-brand-primary/20 text-brand-primary flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    Synchronized Subtitles (.srt)
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-brand-success/20 text-brand-success font-mono font-normal">
                      CapCut Ready
                    </span>
                  </h3>
                  <p className="text-[11px] text-gray-400 font-mono">
                    {currentTrack.srt_filename || `${currentTrack.id}.srt`}
                  </p>
                </div>
              </div>

              <button
                onClick={() => setShowSrtModal(false)}
                className="p-1.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/[0.06] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Quick CapCut Tip Banner */}
            <div className="p-3.5 rounded-2xl bg-white/[0.03] border border-white/[0.06] text-xs text-gray-300 flex items-start gap-3 leading-relaxed">
              <Sparkles className="w-4 h-4 text-brand-primary shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-white">How to import into CapCut / Premiere:</span>
                <p className="text-[11px] text-gray-400 mt-1">
                  1. Click <b>"Download .SRT"</b> below.<br />
                  2. In CapCut: Go to <b>Text → Local captions / Import</b> and select your downloaded <code className="text-brand-primary font-mono font-semibold">.srt</code> file.
                </p>
              </div>
            </div>

            {/* SRT Preview Box */}
            <div className="max-h-56 overflow-y-auto p-3.5 bg-black/40 rounded-2xl border border-white/[0.06]">
              <pre className="text-xs font-mono text-gray-200 whitespace-pre-wrap leading-relaxed select-text">
                {currentTrack.srt_content}
              </pre>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-2">
              <button
                onClick={copySrtToClipboard}
                className="px-4 py-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-xs font-semibold text-white flex items-center gap-2 transition-all"
              >
                {copiedSrt ? (
                  <Check className="w-3.5 h-3.5 text-brand-success" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                <span>{copiedSrt ? 'Copied to Clipboard!' : 'Copy SRT Text'}</span>
              </button>

              <button
                onClick={downloadSrt}
                className="px-5 py-2 rounded-xl bg-brand-primary hover:bg-brand-primary/90 text-xs font-bold text-white flex items-center gap-2 shadow-lg shadow-brand-primary/25 transition-all"
              >
                <Download className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Download .SRT File</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
