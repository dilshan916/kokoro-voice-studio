import React from 'react';
import { ArrowLeft, Cpu, ShieldCheck, Heart, Sparkles, Globe2, Music, Award } from 'lucide-react';

interface AboutPageProps {
  onBackToStudio: () => void;
  onNavigate: (route: string) => void;
}

export const AboutPage: React.FC<AboutPageProps> = ({ onBackToStudio, onNavigate }) => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Top Navigation */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-6">
          <button
            onClick={onBackToStudio}
            className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Voice Studio</span>
          </button>
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <button onClick={() => onNavigate('guide')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Guide</button>
            <span>•</span>
            <button onClick={() => onNavigate('voices')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Voices</button>
            <span>•</span>
            <button onClick={() => onNavigate('contact')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Contact</button>
          </div>
        </div>

        {/* Hero Section */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-semibold border border-blue-200 dark:border-blue-800">
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            <span>Open Neural Speech Architecture</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight">
            About Kokoro Voice Studio
          </h1>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Democratizing natural, broadcast-quality speech synthesis through state-of-the-art open weights, lightweight CPU inference, and creator-first audio mastering.
          </p>
        </div>

        {/* Mission & Story Card */}
        <div className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Heart className="w-6 h-6 text-rose-500" />
            <span>Our Mission &amp; Purpose</span>
          </h2>
          <div className="prose dark:prose-invert max-w-none text-sm text-slate-600 dark:text-slate-300 leading-relaxed space-y-4">
            <p>
              Kokoro Voice Studio was founded with a singular conviction: ultra-realistic, studio-grade speech synthesis should not be locked behind expensive corporate paywalls or restrictive subscription subscriptions. Creators, educators, indie game developers, and accessibility advocates deserve unhindered access to natural AI voice technology.
            </p>
            <p>
              By combining the breakthrough <strong>Kokoro-82M</strong> neural model developed by hexgrad with enterprise-grade ONNX Runtime inference and automated audio post-production engineering, Kokoro Voice Studio delivers real-time voice synthesis that matches or exceeds the naturalness of traditional multi-gigabyte models while running efficiently on cost-effective CPU infrastructure.
            </p>
          </div>
        </div>

        {/* Pillars / Technical Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-900 dark:text-white">82M Parameter Model</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Trained on high-fidelity multi-speaker datasets. Compact architecture allows ultra-fast inference speeds without requiring dedicated GPU server farms.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-900 dark:text-white">Zero-Login Privacy</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              No mandatory registration or personal data harvesting. Anonymous client device quotas allow immediate synthesis without tracking cookies.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 dark:text-amber-400">
              <Music className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-900 dark:text-white">Acoustic EQ Mastering</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Integrated audio engineering pipeline applying high-pass filtering, parametric EQ, and -14 LUFS loudness normalization ready for broadcast.
            </p>
          </div>
        </div>

        {/* Open-Source Attribution & Tech Stack */}
        <div className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Award className="w-6 h-6 text-indigo-500" />
            <span>Open-Source Attributions &amp; Technology Stack</span>
          </h2>
          <div className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed space-y-4">
            <p>
              Kokoro Voice Studio proudly stands on the shoulders of the open-source artificial intelligence and web development communities:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1.5">
                <span className="font-bold text-slate-900 dark:text-white text-sm">Kokoro-82M by hexgrad</span>
                <p className="text-xs text-slate-500 dark:text-slate-400">The foundational neural acoustic model trained on English and international multilingual speech datasets with StyleTTS2 architecture roots.</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1.5">
                <span className="font-bold text-slate-900 dark:text-white text-sm">ONNX Runtime</span>
                <p className="text-xs text-slate-500 dark:text-slate-400">High-performance cross-platform inference engine developed by Microsoft, powering optimized CPU tensor computation with sub-second latency.</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1.5">
                <span className="font-bold text-slate-900 dark:text-white text-sm">FastAPI &amp; Python 3.12</span>
                <p className="text-xs text-slate-500 dark:text-slate-400">High-throughput asynchronous backend server with dual-worker process pooling for concurrent audio batch rendering.</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1.5">
                <span className="font-bold text-slate-900 dark:text-white text-sm">React 18 &amp; Tailwind CSS</span>
                <p className="text-xs text-slate-500 dark:text-slate-400">Modern, reactive audio workstation user interface with real-time waveform visualization powered by WaveSurfer.js.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Global Impact & Languages */}
        <div className="p-8 rounded-3xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-lg space-y-4">
          <div className="flex items-center gap-3">
            <Globe2 className="w-7 h-7 text-blue-200" />
            <h2 className="text-2xl font-bold tracking-tight">Worldwide Multilingual Reach</h2>
          </div>
          <p className="text-sm text-blue-100 leading-relaxed max-w-2xl">
            Kokoro Voice Studio natively synthesizes human-grade voiceovers across 9 international language families: American English, British English, Japanese, French, Korean, Mandarin Chinese, Spanish, Hindi, Italian, and Brazilian Portuguese.
          </p>
          <div className="pt-2">
            <button
              onClick={() => onNavigate('voices')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-blue-700 font-semibold text-xs shadow hover:bg-blue-50 transition-colors"
            >
              <span>Explore All 60 Voices &amp; Accents</span>
              <ArrowLeft className="w-3.5 h-3.5 rotate-180" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
