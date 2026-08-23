import React from 'react';
import {
  X,
  Gauge,
  Music,
  Sliders,
  FileAudio,
  BarChart2,
} from 'lucide-react';

interface MasterInspectorProps {
  isOpen: boolean;
  onClose: () => void;
  selectedPreset: string;
  onSelectPreset: (preset: string) => void;
  presets: string[];
  speed: number;
  onChangeSpeed: (speed: number) => void;
  outputFormat: 'wav' | 'mp3';
  onChangeOutputFormat: (fmt: 'wav' | 'mp3') => void;
  pausePunctuationMs: number;
  onChangePausePunctuationMs: (ms: number) => void;
  pauseParagraphMs: number;
  onChangePauseParagraphMs: (ms: number) => void;
}

export const MasterInspector: React.FC<MasterInspectorProps> = ({
  isOpen,
  onClose,
  selectedPreset,
  onSelectPreset,
  presets,
  speed,
  onChangeSpeed,
  outputFormat,
  onChangeOutputFormat,
  pausePunctuationMs,
  onChangePausePunctuationMs,
  pauseParagraphMs,
  onChangePauseParagraphMs,
}) => {
  if (!isOpen) return null;

  const speedTicks = [0.8, 1.0, 1.2, 1.5];

  const presetDescriptions: Record<string, string> = {
    'Clean Studio (Default)': 'Pristine 24kHz clarity with balanced dynamic response',
    'Warm Podcast Host (+Bass)': 'Gentle +3dB low-end boost with broadcast warmth',
    'Deep Cinematic Trailer': 'Rich sub-harmonics and expanded presence',
    'Radio Broadcast (Punchy)': 'Aggressive multi-band compression & punch',
    'Crisp Air (Commercial)': 'High-frequency air boost (+4dB @ 8kHz)',
    'Vintage Tube Warmth': 'Analog saturation with gentle high roll-off',
    'Bassy Narration': 'Focused proximity effect for audiobook depth',
    'Flat / Raw (Unprocessed)': 'Pure uncolored raw neural audio stream',
  };

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
      />

      {/* Slide-over Drawer */}
      <div className="fixed top-0 right-0 h-full w-96 bg-studio-bg border-l border-white/[0.08] shadow-2xl z-50 flex flex-col select-none overflow-hidden animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-5 border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-brand-primary" />
            <h2 className="font-semibold text-sm text-white">Audio Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/[0.06] transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Settings Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* 1. Acoustic Mastering EQ Preset */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-white flex items-center gap-2">
                <Music className="w-3.5 h-3.5 text-brand-accent" /> Acoustic EQ Preset
              </label>
              <span className="text-[10px] text-brand-accent font-medium">DSP Master</span>
            </div>

            <select
              value={selectedPreset}
              onChange={(e) => onSelectPreset(e.target.value)}
              className="w-full bg-studio-surface border border-white/[0.08] rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-brand-primary transition-all"
            >
              {presets.map((preset) => (
                <option key={preset} value={preset} className="bg-[#151824] text-white">
                  {preset}
                </option>
              ))}
            </select>

            <p className="text-xs text-gray-400 bg-white/[0.03] p-3 rounded-xl border border-white/[0.06] leading-relaxed">
              {presetDescriptions[selectedPreset] || 'Standard studio mastering curve'}
            </p>
          </div>

          {/* 2. Speed Rate Multiplier */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-white flex items-center gap-2">
                <Gauge className="w-3.5 h-3.5 text-brand-secondary" /> Voice Speed Multiplier
              </label>
              <span className="text-xs font-mono font-bold text-white bg-white/[0.08] px-2 py-0.5 rounded-lg">
                {speed.toFixed(2)}x
              </span>
            </div>

            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.05"
              value={speed}
              onChange={(e) => onChangeSpeed(Number(e.target.value))}
              className="w-full h-1.5 bg-white/[0.08] rounded-lg cursor-pointer"
            />

            <div className="grid grid-cols-4 gap-1.5">
              {speedTicks.map((tick) => (
                <button
                  key={tick}
                  onClick={() => onChangeSpeed(tick)}
                  className={`py-1.5 rounded-lg text-xs font-mono transition-all ${
                    Math.abs(speed - tick) < 0.01
                      ? 'bg-white text-black font-semibold shadow-sm'
                      : 'bg-white/[0.04] text-gray-400 hover:text-white hover:bg-white/[0.08]'
                  }`}
                >
                  {tick.toFixed(1)}x
                </button>
              ))}
            </div>
          </div>

          {/* 3. Output Format Selector */}
          <div className="space-y-2.5">
            <label className="text-xs font-semibold text-white flex items-center gap-2">
              <FileAudio className="w-3.5 h-3.5 text-brand-primary" /> Audio Container Format
            </label>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => onChangeOutputFormat('wav')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  outputFormat === 'wav'
                    ? 'bg-brand-primary/10 border-brand-primary text-white shadow-glow-primary'
                    : 'bg-white/[0.03] border-white/[0.06] text-gray-400 hover:text-white'
                }`}
              >
                <div className="font-semibold text-xs text-white">WAV</div>
                <div className="text-[10px] text-gray-500">24kHz 16-bit Lossless</div>
              </button>

              <button
                onClick={() => onChangeOutputFormat('mp3')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  outputFormat === 'mp3'
                    ? 'bg-brand-primary/10 border-brand-primary text-white shadow-glow-primary'
                    : 'bg-white/[0.03] border-white/[0.06] text-gray-400 hover:text-white'
                }`}
              >
                <div className="font-semibold text-xs text-white">MP3</div>
                <div className="text-[10px] text-gray-500">320kbps Compressed</div>
              </button>
            </div>
          </div>

          {/* 4. Cadence & Pause Controls */}
          <div className="space-y-4 pt-2 border-t border-white/[0.06]">
            <div className="text-xs font-semibold text-white">
              Cadence & Pause Durations
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Punctuation Pause</span>
                <span className="font-mono text-white">{pausePunctuationMs}ms</span>
              </div>
              <input
                type="range"
                min="50"
                max="500"
                step="25"
                value={pausePunctuationMs}
                onChange={(e) => onChangePausePunctuationMs(Number(e.target.value))}
                className="w-full h-1.5 bg-white/[0.08] rounded-lg cursor-pointer"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Paragraph Pause</span>
                <span className="font-mono text-white">{pauseParagraphMs}ms</span>
              </div>
              <input
                type="range"
                min="100"
                max="1200"
                step="50"
                value={pauseParagraphMs}
                onChange={(e) => onChangePauseParagraphMs(Number(e.target.value))}
                className="w-full h-1.5 bg-white/[0.08] rounded-lg cursor-pointer"
              />
            </div>
          </div>

          {/* 5. VU Spectrum Preview */}
          <div className="bg-white/[0.03] p-3.5 rounded-xl border border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-gray-400 flex items-center gap-1.5">
                <BarChart2 className="w-3.5 h-3.5 text-brand-primary" /> Target Loudness
              </span>
              <span className="font-mono text-[11px] text-emerald-400">-14.0 LUFS</span>
            </div>

            <div className="h-8 flex items-end gap-1 px-1 bg-black/40 rounded-lg py-1">
              {[35, 55, 75, 90, 70, 50, 40, 35, 50, 70, 60, 45, 30, 20].map((h, i) => (
                <div
                  key={i}
                  style={{ height: `${h}%` }}
                  className="flex-1 bg-gradient-to-t from-brand-primary to-brand-accent rounded-t-sm opacity-80"
                />
              ))}
            </div>
          </div>
        </div>

        {/* Footer Done Button */}
        <div className="p-4 border-t border-white/[0.06]">
          <button
            onClick={onClose}
            className="w-full py-2.5 rounded-xl bg-white hover:bg-gray-100 text-black font-semibold text-xs transition-all shadow-md active:scale-98"
          >
            Apply Settings
          </button>
        </div>
      </div>
    </>
  );
};
