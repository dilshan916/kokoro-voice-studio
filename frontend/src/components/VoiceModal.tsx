import React, { useState, useMemo } from 'react';
import { X, Search, Check, Sparkles } from 'lucide-react';
import { Voice } from '../types';
import { CountryFlag } from './CountryFlag';

interface VoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  voices: Voice[];
  selectedVoiceId: string;
  onSelectVoice: (voice: Voice) => void;
}

export const VoiceModal: React.FC<VoiceModalProps> = ({
  isOpen,
  onClose,
  voices,
  selectedVoiceId,
  onSelectVoice,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLang, setSelectedLang] = useState('all');
  const [selectedGender, setSelectedGender] = useState<'all' | 'Female' | 'Male'>('all');
  const [activeTab, setActiveTab] = useState<'catalog' | 'blender'>('catalog');

  // Voice Blender states
  const [blendVoiceA, setBlendVoiceA] = useState('af_bella');
  const [blendVoiceB, setBlendVoiceB] = useState('am_adam');
  const [blendRatio, setBlendRatio] = useState(50);

  const languageFilters = [
    { code: 'all', label: 'All', flag: '🌐' },
    { code: 'en-us', label: 'English (US)', flag: '🇺🇸' },
    { code: 'en-gb', label: 'English (UK)', flag: '🇬🇧' },
    { code: 'fr-fr', label: 'French', flag: '🇫🇷' },
    { code: 'ja', label: 'Japanese', flag: '🇯🇵' },
    { code: 'ko', label: 'Korean', flag: '🇰🇷' },
    { code: 'cmn', label: 'Mandarin', flag: '🇨🇳' },
    { code: 'es', label: 'Spanish', flag: '🇪🇸' },
    { code: 'hi', label: 'Hindi', flag: '🇮🇳' },
    { code: 'it', label: 'Italian', flag: '🇮🇹' },
    { code: 'pt-br', label: 'Portuguese', flag: '🇧🇷' },
  ];

  const filteredVoices = useMemo(() => {
    return voices.filter((v) => {
      if (selectedLang !== 'all' && v.lang !== selectedLang) return false;
      if (selectedGender !== 'all' && v.gender !== selectedGender) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          v.name.toLowerCase().includes(q) ||
          v.id.toLowerCase().includes(q) ||
          v.description.toLowerCase().includes(q) ||
          v.lang_name.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [voices, selectedLang, selectedGender, searchQuery]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-slate-900/60 dark:bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-150 select-none"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl shadow-2xl flex flex-col max-h-[88vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-5 sm:p-6 border-b border-slate-100 dark:border-slate-700/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
              🎙️
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
                Choose a Voice
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                60 natural neural voices across 9+ international languages
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Catalog vs Blender Tabs */}
            <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-xl text-xs font-medium">
              <button
                onClick={() => setActiveTab('catalog')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeTab === 'catalog'
                    ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm font-semibold'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                Voices
              </button>
              <button
                onClick={() => setActiveTab('blender')}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 ${
                  activeTab === 'blender'
                    ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm font-semibold'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Sparkles className="w-3 h-3 text-blue-500" />
                Blender
              </button>
            </div>

            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-700/60 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white flex items-center justify-center transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {activeTab === 'catalog' ? (
          <>
            {/* Search & Filter Controls */}
            <div className="p-4 sm:p-6 pb-2 space-y-3 border-b border-slate-100 dark:border-slate-700/60">
              <div className="flex items-center gap-3">
                {/* Search Bar */}
                <div className="relative flex-1">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by voice name, language, or accent..."
                    className="w-full bg-slate-50 dark:bg-slate-900/60 text-slate-800 dark:text-slate-200 text-xs sm:text-sm pl-10 pr-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-blue-500 transition-all"
                  />
                </div>

                {/* Gender Filter Pills */}
                <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-xl text-xs font-medium shrink-0">
                  {(['all', 'Female', 'Male'] as const).map((g) => (
                    <button
                      key={g}
                      onClick={() => setSelectedGender(g)}
                      className={`px-2.5 py-1 rounded-lg transition-all capitalize ${
                        selectedGender === g
                          ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 font-bold shadow-sm'
                          : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              {/* Language Filter Chips */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-xs">
                {languageFilters.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => setSelectedLang(lang.code)}
                    className={`px-2.5 py-1 rounded-full whitespace-nowrap transition-all flex items-center gap-1.5 ${
                      selectedLang === lang.code
                        ? 'bg-blue-600 text-white font-semibold shadow-sm'
                        : 'bg-slate-100 dark:bg-slate-900/80 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60'
                    }`}
                  >
                    <CountryFlag lang={lang.code} className="w-3.5 h-3.5 rounded-full object-cover shrink-0" />
                    <span>{lang.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Voice Cards Grid */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {filteredVoices.map((voice) => {
                const isSelected = selectedVoiceId === voice.id;
                return (
                  <div
                    key={voice.id}
                    onClick={() => {
                      onSelectVoice(voice);
                      onClose();
                    }}
                    className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                      isSelected
                        ? 'bg-blue-50/90 dark:bg-blue-950/60 border-blue-500 shadow-md shadow-blue-500/10'
                        : 'bg-slate-50/50 dark:bg-slate-900/40 hover:bg-slate-100 dark:hover:bg-slate-900/80 border-slate-200/80 dark:border-slate-700/80'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-10 h-10 rounded-full overflow-hidden shadow-sm border border-slate-200/80 dark:border-slate-700 flex items-center justify-center shrink-0 bg-slate-100 dark:bg-slate-800">
                        <CountryFlag lang={voice.lang} className="w-full h-full object-cover" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white truncate">
                          {voice.name}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                          {voice.gender} • {voice.lang_name}
                        </div>
                      </div>
                    </div>

                    {isSelected && (
                      <div className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0">
                        <Check className="w-3 h-3 stroke-[3]" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          /* Voice Blender Tab */
          <div className="p-6 space-y-6 overflow-y-auto">
            <div className="bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/50 rounded-2xl p-4 text-xs text-blue-900 dark:text-blue-300">
              💡 <strong>Voice Blender:</strong> Seamlessly interpolate neural voice embeddings to create completely unique voice identities!
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Voice A */}
              <div className="bg-slate-50 dark:bg-slate-900/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-700">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-2">
                  Voice A ({100 - blendRatio}%)
                </label>
                <select
                  value={blendVoiceA}
                  onChange={(e) => setBlendVoiceA(e.target.value)}
                  className="w-full bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs"
                >
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.flag} {v.name} ({v.gender} • {v.lang_name})
                    </option>
                  ))}
                </select>
              </div>

              {/* Voice B */}
              <div className="bg-slate-50 dark:bg-slate-900/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-700">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-2">
                  Voice B ({blendRatio}%)
                </label>
                <select
                  value={blendVoiceB}
                  onChange={(e) => setBlendVoiceB(e.target.value)}
                  className="w-full bg-white dark:bg-slate-800 text-slate-900 dark:text-white border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs"
                >
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.flag} {v.name} ({v.gender} • {v.lang_name})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Blend Ratio Slider */}
            <div className="bg-slate-50 dark:bg-slate-900/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-700">
              <div className="flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                <span>Weight: {blendVoiceA}</span>
                <span className="text-blue-600 font-bold">{100 - blendRatio}% / {blendRatio}%</span>
                <span>Weight: {blendVoiceB}</span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                value={blendRatio}
                onChange={(e) => setBlendRatio(parseInt(e.target.value, 10))}
                className="w-full accent-blue-600 cursor-pointer"
              />
            </div>

            {/* Apply Blended Voice Button */}
            <button
              onClick={() => {
                const ratioDecimal = (blendRatio / 100).toFixed(2);
                const blendedId = `${blendVoiceA}(${(1 - blendRatio / 100).toFixed(2)})+${blendVoiceB}(${ratioDecimal})`;
                const nameA = voices.find((v) => v.id === blendVoiceA)?.name || blendVoiceA;
                const nameB = voices.find((v) => v.id === blendVoiceB)?.name || blendVoiceB;
                const customBlendedVoice: Voice = {
                  id: blendedId,
                  name: `${nameA} × ${nameB}`,
                  gender: 'Neutral',
                  lang: voices.find((v) => v.id === blendVoiceA)?.lang || 'en-us',
                  lang_name: 'Hybrid Blend',
                  flag: '✨',
                  description: `Custom neural blend: ${100 - blendRatio}% ${nameA} + ${blendRatio}% ${nameB}`,
                };
                onSelectVoice(customBlendedVoice);
                onClose();
              }}
              className="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs sm:text-sm shadow-md transition-all cursor-pointer"
            >
              Apply Hybrid Blended Voice
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
export default VoiceModal;
