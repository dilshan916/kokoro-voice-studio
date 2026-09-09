import React, { useState } from 'react';
import { Clock, Play, Pause, Download, Trash2, Subtitles, ChevronUp, ChevronDown, Check } from 'lucide-react';
import { GenerationHistoryItem } from '../types';
import { CountryFlag } from './CountryFlag';

interface LastRegenerationsProps {
  history: GenerationHistoryItem[];
  onClearHistory: () => void;
  activeTrackId: string | null;
  onPlayTrack: (item: GenerationHistoryItem) => void;
  onPauseTrack: () => void;
  isPlaying: boolean;
  playbackProgress: number; // 0.0 to 1.0
}

export const LastRegenerations: React.FC<LastRegenerationsProps> = ({
  history,
  onClearHistory,
  activeTrackId,
  onPlayTrack,
  onPauseTrack,
  isPlaying,
  playbackProgress,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [downloadedId, setDownloadedId] = useState<string | null>(null);

  if (history.length === 0) {
    return null;
  }

  const handleDownload = (item: GenerationHistoryItem, e: React.MouseEvent) => {
    e.stopPropagation();
    setDownloadedId(item.id);
    setTimeout(() => setDownloadedId(null), 2000);

    const a = document.createElement('a');
    a.href = item.audio_url;
    a.download = item.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownloadSrt = (item: GenerationHistoryItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!item.srt_content) return;

    const blob = new Blob([item.srt_content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = item.srt_filename || `${item.filename.replace(/\.[^/.]+$/, '')}.srt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed bottom-4 right-4 z-40 w-80 sm:w-96 select-none shadow-2xl transition-all">
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-2xl border border-blue-100 dark:border-slate-700/80 rounded-3xl p-4 shadow-xl shadow-slate-900/10 dark:shadow-black/40">
        {/* Widget Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-700/60">
          <div className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
            <Clock className="w-4 h-4 text-blue-500" />
            <span className="text-xs font-bold uppercase tracking-wider">
              Last Regenerations
            </span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold">
              {history.length}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={onClearHistory}
              className="text-[11px] font-medium text-slate-400 hover:text-rose-500 dark:hover:text-rose-400 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              title="Clear History"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
              title={isCollapsed ? 'Expand' : 'Collapse'}
            >
              {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* List of Recent Generations */}
        {!isCollapsed && (
          <div className="mt-3 space-y-2.5 max-h-64 overflow-y-auto pr-1">
            {history.map((item) => {
              const isThisPlaying = activeTrackId === item.id && isPlaying;
              const isThisActive = activeTrackId === item.id;

              return (
                <div
                  key={item.id}
                  onClick={() => (isThisPlaying ? onPauseTrack() : onPlayTrack(item))}
                  className={`p-2.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                    isThisActive
                      ? 'bg-blue-50/80 dark:bg-blue-950/40 border-blue-300 dark:border-blue-700 shadow-sm'
                      : 'bg-slate-50/60 dark:bg-slate-900/40 hover:bg-slate-100/80 dark:hover:bg-slate-900/80 border-slate-200/60 dark:border-slate-700/60'
                  }`}
                >
                  {/* Play / Pause Round Button */}
                  <div className="relative shrink-0">
                    <button
                      className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${
                        isThisPlaying
                          ? 'bg-blue-600 text-white shadow-md shadow-blue-500/40 scale-105'
                          : 'bg-blue-500/15 hover:bg-blue-600 text-blue-600 hover:text-white dark:bg-blue-500/20 dark:text-blue-400 dark:hover:text-white'
                      }`}
                    >
                      {isThisPlaying ? (
                        <Pause className="w-4 h-4 fill-current" />
                      ) : (
                        <Play className="w-4 h-4 fill-current ml-0.5" />
                      )}
                    </button>
                  </div>

                  {/* Title & Metadata */}
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate">
                      {item.title}
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                      <CountryFlag lang={item.voice_flag} className="w-3.5 h-3.5 rounded-full object-cover shrink-0" />
                      <span>{item.voice_name}</span>
                      <span>•</span>
                      <span>{item.duration.toFixed(1)}s</span>
                      <span>•</span>
                      <span>{item.formatted_time}</span>
                    </div>

                    {/* Mini Progress Bar if Active */}
                    {isThisActive && (
                      <div className="w-full bg-slate-200 dark:bg-slate-700 h-1 rounded-full mt-2 overflow-hidden">
                        <div
                          className="bg-blue-600 h-full rounded-full transition-all duration-100"
                          style={{ width: `${Math.round(playbackProgress * 100)}%` }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Action Buttons: Audio Download & Subtitle Download */}
                  <div className="flex items-center gap-1 shrink-0">
                    {item.srt_content && (
                      <button
                        onClick={(e) => handleDownloadSrt(item, e)}
                        className="p-1.5 rounded-xl text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-white dark:hover:bg-slate-800 transition-colors"
                        title="Download Subtitles (.srt)"
                      >
                        <Subtitles className="w-3.5 h-3.5" />
                      </button>
                    )}

                    <button
                      onClick={(e) => handleDownload(item, e)}
                      className="p-1.5 rounded-xl text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-white dark:hover:bg-slate-800 transition-colors"
                      title="Download Audio File"
                    >
                      {downloadedId === item.id ? (
                        <Check className="w-3.5 h-3.5 text-emerald-500" />
                      ) : (
                        <Download className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
export default LastRegenerations;
