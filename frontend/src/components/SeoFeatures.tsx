import React from 'react';
import { Mic2, Sliders, Zap, Subtitles, Sparkles, ShieldCheck } from 'lucide-react';

const FEATURES = [
  {
    icon: <Mic2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />,
    title: '60 International Neural AI Voices',
    description:
      'Expressive speech synthesis across 9+ global languages including English (US & UK), Japanese, French, Korean, Mandarin, Spanish, Hindi, Italian, and Brazilian Portuguese.',
  },
  {
    icon: <Sliders className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />,
    title: 'Acoustic Studio Mastering EQ',
    description:
      'Master voice tracks with 8 professional acoustic EQ presets including Warm Podcast Host, Deep Cinematic Trailer, Radio Broadcast, and Crisp Commercial Air.',
  },
  {
    icon: <Zap className="w-5 h-5 text-amber-500" />,
    title: 'Ultra-Fast 24kHz Audio Fidelity',
    description:
      'Powered by Kokoro-82M ONNX neural weights with process isolation for instantaneous, crystal-clear speech rendering with zero lag.',
  },
  {
    icon: <Subtitles className="w-5 h-5 text-purple-600 dark:text-purple-400" />,
    title: 'Synchronized Subtitles (.SRT)',
    description:
      'Export timed SubRip (.srt) subtitle files with intelligent clause chunking, 100% compatible with CapCut, Premiere Pro, DaVinci Resolve, and TikTok.',
  },
  {
    icon: <Sparkles className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />,
    title: 'Neural Voice Blender',
    description:
      'Mathematically interpolate between any two voice embeddings to craft custom, one-of-a-kind vocal identities tailored for your brand.',
  },
  {
    icon: <ShieldCheck className="w-5 h-5 text-emerald-500" />,
    title: '100% Private & No Install Required',
    description:
      'Runs directly in your desktop or mobile browser with zero login friction. Anonymous monthly quotas protect your privacy while granting instant access.',
  },
];

export const SeoFeatures: React.FC = React.memo(() => {
  return (
    <section className="max-w-4xl mx-auto w-full py-10 px-2 select-none">
      <div className="text-center mb-8">
        <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-2">
          Everything You Need For Studio-Grade AI Audio
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-xl mx-auto">
          The ultimate cloud-powered neural audio workstation designed for content creators, podcasters, video editors, and game developers.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {FEATURES.map((feat, idx) => (
          <div
            key={idx}
            className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-md border border-blue-100 dark:border-slate-700/80 rounded-2xl p-4 sm:p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center mb-3">
                {feat.icon}
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1.5">
                {feat.title}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                {feat.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
});
export default SeoFeatures;
