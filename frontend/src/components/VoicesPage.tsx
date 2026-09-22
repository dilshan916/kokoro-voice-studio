import React from 'react';
import { ArrowLeft, Mic, Compass } from 'lucide-react';
import { VoiceCatalog } from './VoiceCatalog';
import { Voice } from '../types';

interface VoicesPageProps {
  voices: Voice[];
  selectedVoiceId: string;
  onSelectVoice: (voice: Voice) => void;
  onBackToStudio: () => void;
  onNavigate: (route: string) => void;
}

export const VoicesPage: React.FC<VoicesPageProps> = ({
  voices,
  selectedVoiceId,
  onSelectVoice,
  onBackToStudio,
  onNavigate,
}) => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-12">
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
            <button onClick={() => onNavigate('about')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">About</button>
            <span>•</span>
            <button onClick={() => onNavigate('contact')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Contact</button>
          </div>
        </div>

        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-semibold border border-blue-200 dark:border-blue-800">
            <Mic className="w-3.5 h-3.5 text-blue-500" />
            <span>Comprehensive Voice &amp; Accent Directory</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight">
            60 Neural AI Voices Across 9 Languages
          </h1>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-3xl mx-auto leading-relaxed">
            Browse and preview our complete catalog of natural, human-grade voice personas. Filter by language family, gender, or audition hybrid blends for your video, podcast, or audiobook project.
          </p>
        </div>

        {/* Language Category Highlights */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
          <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-1">
            <span className="text-xl">🇺🇸 🇬🇧</span>
            <p className="font-bold text-slate-900 dark:text-white">English (US &amp; UK)</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">30+ Natural Voices</p>
          </div>
          <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-1">
            <span className="text-xl">🇯🇵 🇰🇷 🇨🇳</span>
            <p className="font-bold text-slate-900 dark:text-white">East Asian</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Japanese, Korean, Mandarin</p>
          </div>
          <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-1">
            <span className="text-xl">🇫🇷 🇪🇸 🇮🇹</span>
            <p className="font-bold text-slate-900 dark:text-white">Romance Languages</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">French, Spanish, Italian</p>
          </div>
          <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-1">
            <span className="text-xl">🇧🇷</span>
            <p className="font-bold text-slate-900 dark:text-white">Portuguese (BR)</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Brazilian Melodic Voices</p>
          </div>
          <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center space-y-1 col-span-2 sm:col-span-1">
            <span className="text-xl">🇮🇳</span>
            <p className="font-bold text-slate-900 dark:text-white">Indic (Hindi)</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">Clear Expressive Hindi</p>
          </div>
        </div>

        {/* Interactive Catalog Component */}
        <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Compass className="w-5 h-5 text-blue-500" />
                <span>Explore &amp; Select Voices</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Selecting a voice updates your active synthesis persona when you return to the studio.
              </p>
            </div>
          </div>

          <VoiceCatalog
            voices={voices}
            selectedVoiceId={selectedVoiceId}
            onSelectVoice={onSelectVoice}
          />
        </div>
      </div>
    </div>
  );
};
