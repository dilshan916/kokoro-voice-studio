import React, { useState, useMemo, useEffect } from 'react';
import { Search, Sliders, Check, Sparkles } from 'lucide-react';
import { Voice } from '../types';

interface VoiceCatalogProps {
  voices: Voice[];
  selectedVoiceId: string;
  onSelectVoice: (voice: Voice) => void;
}

export const VoiceCatalog: React.FC<VoiceCatalogProps> = ({
  voices,
  selectedVoiceId,
  onSelectVoice,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLangFilter, setSelectedLangFilter] = useState('all');
  const [selectedGenderFilter, setSelectedGenderFilter] = useState<'all' | 'Female' | 'Male'>('all');
  const [showBlender, setShowBlender] = useState(false);
  const [blendVoiceA, setBlendVoiceA] = useState('af_bella');
  const [blendVoiceB, setBlendVoiceB] = useState('am_adam');
  const [blendRatio, setBlendRatio] = useState(50);

  // Distinct language filter options with flags
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

  // Filtered voice catalog
  const filteredVoices = useMemo(() => {
    return voices.filter((v) => {
      // Language filter
      if (selectedLangFilter !== 'all' && v.lang !== selectedLangFilter) {
        return false;
      }
      // Gender filter
      if (selectedGenderFilter !== 'all' && v.gender !== selectedGenderFilter) {
        return false;
      }
      // Search query
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
  }, [voices, selectedLangFilter, selectedGenderFilter, searchQuery]);

  // Dynamically filter blender voices according to currently active language filter
  const blenderVoiceOptions = useMemo(() => {
    if (selectedLangFilter === 'all') {
      return voices;
    }
    const matching = voices.filter((v) => v.lang === selectedLangFilter);
    return matching.length > 0 ? matching : voices;
  }, [voices, selectedLangFilter]);

  // Synchronize Voice A & B to matching language options
  useEffect(() => {
    if (blenderVoiceOptions.length > 0) {
      const hasA = blenderVoiceOptions.some((v) => v.id === blendVoiceA);
      const hasB = blenderVoiceOptions.some((v) => v.id === blendVoiceB);

      if (!hasA) {
        setBlendVoiceA(blenderVoiceOptions[0].id);
      }
      if (!hasB) {
        setBlendVoiceB(
          blenderVoiceOptions.length > 1 ? blenderVoiceOptions[1].id : blenderVoiceOptions[0].id
        );
      }
    }
  }, [blenderVoiceOptions, blendVoiceA, blendVoiceB]);

  return (
    <aside className="w-80 h-full bg-studio-surface/60 backdrop-blur-xl border-r border-white/[0.06] flex flex-col shrink-0 select-none overflow-hidden">
      {/* Top Search & Filter Bar */}
      <div className="p-4 space-y-3 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
            Voices ({filteredVoices.length})
          </span>
          <button
            onClick={() => setShowBlender(!showBlender)}
            className={`px-2.5 py-1 rounded-lg text-xs flex items-center gap-1 font-medium transition-all ${
              showBlender
                ? 'bg-brand-primary text-white shadow-glow-primary'
                : 'bg-white/[0.04] hover:bg-white/[0.08] text-gray-400 hover:text-white border border-white/[0.06]'
            }`}
          >
            <Sliders className="w-3 h-3" />
            <span>Mixer</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search voices, accents, styles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand-primary/60 focus:bg-white/[0.06] transition-all"
          />
        </div>

        {/* Gender Filter Toggle Pills */}
        <div className="flex gap-1 bg-white/[0.02] p-1 rounded-xl border border-white/[0.06] text-xs">
          {(['all', 'Female', 'Male'] as const).map((gender) => (
            <button
              key={gender}
              onClick={() => setSelectedGenderFilter(gender)}
              className={`flex-1 py-1 rounded-lg text-center font-medium capitalize transition-all ${
                selectedGenderFilter === gender
                  ? 'bg-white/[0.1] text-white font-semibold shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {gender}
            </button>
          ))}
        </div>

        {/* Language Filter Pills */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {languageFilters.map((lf) => (
            <button
              key={lf.code}
              onClick={() => setSelectedLangFilter(lf.code)}
              className={`px-2.5 py-1 rounded-full text-[11px] whitespace-nowrap flex items-center gap-1.5 font-medium transition-all ${
                selectedLangFilter === lf.code
                  ? 'bg-white text-black font-semibold shadow-sm'
                  : 'bg-white/[0.04] text-gray-400 hover:text-white hover:bg-white/[0.08]'
              }`}
            >
              <span>{lf.flag}</span>
              <span>{lf.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Voice Blender Drawer */}
      {showBlender && (
        <div className="p-3.5 bg-brand-primary/[0.04] border-b border-brand-primary/20 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-brand-primary flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" /> Character Voice Blender
            </span>
            <span className="font-mono text-[11px] text-gray-400">
              {100 - blendRatio}% A / {blendRatio}% B
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label className="text-[10px] text-gray-400 block mb-1">Voice A</label>
              <select
                value={blendVoiceA}
                onChange={(e) => setBlendVoiceA(e.target.value)}
                className="w-full bg-studio-surface border border-white/[0.08] rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-brand-primary"
              >
                {blenderVoiceOptions.map((v) => (
                  <option key={`a-${v.id}`} value={v.id} className="bg-[#151824] text-white">
                    {v.flag} {v.name} ({v.gender})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-gray-400 block mb-1">Voice B</label>
              <select
                value={blendVoiceB}
                onChange={(e) => setBlendVoiceB(e.target.value)}
                className="w-full bg-studio-surface border border-white/[0.08] rounded-lg p-1.5 text-xs text-white focus:outline-none focus:border-brand-primary"
              >
                {blenderVoiceOptions.map((v) => (
                  <option key={`b-${v.id}`} value={v.id} className="bg-[#151824] text-white">
                    {v.flag} {v.name} ({v.gender})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <input
            type="range"
            min="0"
            max="100"
            value={blendRatio}
            onChange={(e) => setBlendRatio(Number(e.target.value))}
            className="w-full h-1.5 bg-white/[0.08] rounded-lg cursor-pointer"
          />
        </div>
      )}

      {/* Voice Cards Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredVoices.map((voice) => {
          const isSelected = selectedVoiceId === voice.id;

          return (
            <div
              key={voice.id}
              onClick={() => onSelectVoice(voice)}
              className={`p-3 rounded-xl cursor-pointer transition-all border ${
                isSelected
                  ? 'bg-brand-primary/10 border-brand-primary/50 shadow-glow-primary'
                  : 'bg-white/[0.02] hover:bg-white/[0.05] border-transparent hover:border-white/[0.08]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-white/[0.06] flex items-center justify-center text-sm shrink-0">
                    {voice.flag}
                  </div>
                  <div>
                    <div className="flex items-center space-x-1.5">
                      <span className="font-semibold text-xs text-white">
                        {voice.name}
                      </span>
                      <span className="text-[10px] text-gray-500 font-mono">
                        {voice.id}
                      </span>
                    </div>
                    <span className="text-[10px] text-gray-400">
                      {voice.gender} • {voice.lang_name}
                    </span>
                  </div>
                </div>

                {isSelected && (
                  <div className="w-5 h-5 rounded-full bg-brand-primary flex items-center justify-center shrink-0 shadow-glow-primary">
                    <Check className="w-3 h-3 text-white stroke-[3]" />
                  </div>
                )}
              </div>

              <p className="text-[11px] text-gray-400 line-clamp-2 mt-2 leading-relaxed">
                {voice.description}
              </p>
            </div>
          );
        })}

        {filteredVoices.length === 0 && (
          <div className="text-center py-12 text-gray-500 text-xs">
            <p>No voices found matching search.</p>
          </div>
        )}
      </div>
    </aside>
  );
};
