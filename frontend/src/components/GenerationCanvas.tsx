import React from 'react';
import { FileText, AudioWaveform, Loader2, Sparkles } from 'lucide-react';

interface GenerationCanvasProps {
  text: string;
  onChangeText: (text: string) => void;
  onConvert: () => void;
  isRendering: boolean;
  maxChars?: number;
}

const SAMPLE_PROMPTS = [
  'Welcome to Kokoro Studio! Ultra-realistic neural voice synthesis powered by Kokoro-82M.',
  'Experience crystal-clear speech generation with studio EQ mastering and instant subtitle export.',
  'Bonjour! Kokoro Studio prend en charge le français, l’anglais, le japonais, le coréen et bien plus encore.',
  '日本語の音声合成も極めて自然で、感情豊かなナレーションが可能です。',
];

export const GenerationCanvas: React.FC<GenerationCanvasProps> = React.memo(({
  text,
  onChangeText,
  onConvert,
  isRendering,
  maxChars = 2000,
}) => {
  const charCount = text.length;
  const isOverLimit = charCount > maxChars;

  return (
    <div className="max-w-4xl mx-auto w-full select-none">
      <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-blue-100 dark:border-slate-700/80 rounded-3xl p-6 sm:p-8 shadow-sm hover:shadow-md transition-all">
        {/* Dedicated Visible Text Input Box */}
        <div className="relative bg-slate-50/90 dark:bg-slate-900/80 border-2 border-slate-200/90 dark:border-slate-700 rounded-2xl p-4 sm:p-5 transition-all focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/15 focus-within:bg-white dark:focus-within:bg-slate-900 shadow-inner mb-4">
          <div className="flex items-center justify-between text-xs text-slate-400 dark:text-slate-500 mb-2.5">
            <div className="flex items-center gap-2 font-semibold text-slate-600 dark:text-slate-300">
              <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span>Type or paste your text below:</span>
            </div>

            <div
              className={`font-mono text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                isOverLimit
                  ? 'bg-rose-500/10 text-rose-500 dark:text-rose-400'
                  : 'bg-slate-200/80 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
              }`}
            >
              {charCount} / {maxChars}
            </div>
          </div>

          <textarea
            value={text}
            onChange={(e) => onChangeText(e.target.value)}
            placeholder="Type or paste your script here to generate speech..."
            rows={5}
            className="w-full bg-transparent text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 text-sm sm:text-base leading-relaxed resize-y min-h-[120px] focus:outline-none border-0 p-0 font-sans"
          />
        </div>

        {/* Sample Prompt Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-4 pb-6 border-t border-slate-100 dark:border-slate-700/60">
          <span className="text-[11px] font-medium text-slate-400 dark:text-slate-500 flex items-center gap-1 mr-1">
            <Sparkles className="w-3 h-3 text-blue-500" />
            Try:
          </span>
          {SAMPLE_PROMPTS.map((sample, idx) => (
            <button
              key={idx}
              onClick={() => onChangeText(sample)}
              className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100/80 dark:bg-slate-900/50 hover:bg-blue-50 dark:hover:bg-blue-950/40 text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 border border-slate-200/60 dark:border-slate-700/60 hover:border-blue-300 transition-all truncate max-w-[200px] sm:max-w-xs cursor-pointer"
            >
              {sample}
            </button>
          ))}
        </div>

        {/* Big Centered "Convert to Audio" Pill Button */}
        <div className="flex justify-center pt-2">
          <button
            onClick={onConvert}
            disabled={isRendering || !text.trim() || isOverLimit}
            className={`px-8 sm:px-12 py-3.5 rounded-full font-semibold text-sm sm:text-base flex items-center gap-3 transition-all shadow-lg select-none cursor-pointer ${
              isRendering || !text.trim() || isOverLimit
                ? 'bg-slate-300 dark:bg-slate-700 text-slate-500 cursor-not-allowed shadow-none'
                : 'bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            {isRendering ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-white" />
                <span>Generating Speech...</span>
              </>
            ) : (
              <>
                <AudioWaveform className="w-5 h-5 text-white animate-pulse" />
                <span>Convert to Audio</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
});
export default GenerationCanvas;
