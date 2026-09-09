import React from 'react';
import { User, Sliders, Gauge, AudioWaveform, ChevronDown } from 'lucide-react';
import { Voice } from '../types';
import { CountryFlag } from './CountryFlag';

interface ControlCardsProps {
  selectedVoice: Voice;
  onOpenVoiceModal: () => void;
  speed: number;
  onChangeSpeed: (speed: number) => void;
  selectedPreset: string;
  onChangePreset: (preset: string) => void;
  presets: string[];
}

export const ControlCards: React.FC<ControlCardsProps> = React.memo(({
  selectedVoice,
  onOpenVoiceModal,
  speed,
  onChangeSpeed,
  selectedPreset,
  onChangePreset,
  presets,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 max-w-4xl mx-auto w-full select-none">
      {/* Card 1: SELECT VOICE */}
      <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-blue-100 dark:border-slate-700/80 rounded-3xl p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Select Voice
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Choose from a variety of realistic voices
            </p>
          </div>
        </div>

        {/* Selected Voice Card (Clickable to open Voice Modal) */}
        <button
          onClick={onOpenVoiceModal}
          className="w-full bg-slate-50/80 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-900 border border-slate-200/80 dark:border-slate-700/80 hover:border-blue-400 dark:hover:border-blue-500 rounded-2xl p-3.5 flex items-center justify-between transition-all group text-left cursor-pointer"
        >
          <div className="flex items-center gap-3.5">
            {/* Flag Badge */}
            <div className="w-10 h-10 rounded-full overflow-hidden shadow-sm border border-slate-200/60 dark:border-slate-700 flex items-center justify-center shrink-0 bg-slate-100 dark:bg-slate-800">
              <CountryFlag lang={selectedVoice.lang} className="w-full h-full object-cover" />
            </div>

            {/* Voice Info */}
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm sm:text-base text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {selectedVoice.name}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-700 dark:text-blue-300 font-mono font-medium">
                  {selectedVoice.id}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {selectedVoice.gender} • {selectedVoice.lang_name}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {/* Voice Avatar Thumbnail */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow-sm">
              {selectedVoice.name.slice(0, 1).toUpperCase()}
            </div>
            <ChevronDown className="w-4 h-4 transition-transform group-hover:translate-y-0.5" />
          </div>
        </button>
      </div>

      {/* Card 2: AUDIO OPTIONS */}
      <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-blue-100 dark:border-slate-700/80 rounded-3xl p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Audio Options
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Adjust the speed and acoustic mastering
            </p>
          </div>
        </div>

        {/* Side-by-Side Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {/* Speed Slider Control */}
          <div className="bg-slate-50/80 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-700/80 rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">
              <label htmlFor="speech-speed-slider" className="flex items-center gap-1.5 cursor-pointer">
                <Gauge className="w-3.5 h-3.5 text-blue-500" />
                Speed
              </label>
              <span className="font-mono text-blue-700 dark:text-blue-300 font-bold bg-blue-500/10 px-1.5 py-0.5 rounded">
                {speed.toFixed(1)}x
              </span>
            </div>
            <input
              id="speech-speed-slider"
              aria-label="Speech Speed Multiplier"
              type="range"
              min={0.5}
              max={2.0}
              step={0.05}
              value={speed}
              onChange={(e) => onChangeSpeed(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          {/* Mastering EQ Preset Selector */}
          <div className="bg-slate-50/80 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-700/80 rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              <label htmlFor="mastering-eq-select" className="flex items-center gap-1.5 cursor-pointer">
                <AudioWaveform className="w-3.5 h-3.5 text-blue-500" />
                Mastering EQ
              </label>
            </div>
            <select
              id="mastering-eq-select"
              aria-label="Acoustic Mastering Equalizer Preset"
              value={selectedPreset}
              onChange={(e) => onChangePreset(e.target.value)}
              className="w-full bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-xl px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:border-blue-500 cursor-pointer"
            >
              {presets.map((preset) => (
                <option key={preset} value={preset}>
                  {preset}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
});
export default ControlCards;
