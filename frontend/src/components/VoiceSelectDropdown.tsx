import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Search, Check } from 'lucide-react';
import { Voice } from '../types';

interface VoiceSelectDropdownProps {
  value: string;
  onChange: (voiceId: string) => void;
  voices: Voice[];
  className?: string;
  onOpenChange?: (isOpen: boolean) => void;
}

export const VoiceSelectDropdown: React.FC<VoiceSelectDropdownProps> = ({
  value,
  onChange,
  voices,
  className = '',
  onOpenChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  const selectedVoice = voices.find((v) => v.id === value) || voices[0];

  const handleToggle = (nextState: boolean) => {
    setIsOpen(nextState);
    if (onOpenChange) {
      onOpenChange(nextState);
    }
  };

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        handleToggle(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Filter voices based on search input
  const filteredVoices = voices.filter((v) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      v.name.toLowerCase().includes(q) ||
      v.id.toLowerCase().includes(q) ||
      v.lang_name.toLowerCase().includes(q) ||
      v.description.toLowerCase().includes(q)
    );
  });

  return (
    <div
      ref={dropdownRef}
      className={`relative inline-block ${isOpen ? 'z-50' : 'z-10'} ${className}`}
    >
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => handleToggle(!isOpen)}
        className="flex items-center space-x-2 bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.08] hover:border-white/[0.15] rounded-xl px-3 py-1.5 text-xs text-white transition-all shadow-sm focus:outline-none focus:border-brand-primary"
      >
        <span className="text-sm shrink-0">{selectedVoice?.flag || '🎙️'}</span>
        <span className="font-semibold text-white truncate max-w-[130px]">
          {selectedVoice?.name || 'Select Voice'}
        </span>
        <span className="text-[10px] text-gray-400 font-mono">
          ({selectedVoice?.lang_name || selectedVoice?.lang})
        </span>
        <ChevronDown
          className={`w-3.5 h-3.5 text-gray-400 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-white' : ''
          }`}
        />
      </button>

      {/* Popover Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 top-full mt-1.5 w-72 max-h-80 bg-studio-surface border border-white/[0.12] rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden backdrop-blur-2xl animate-in fade-in zoom-in-95 duration-150">
          {/* Quick Search Header */}
          <div className="p-2.5 border-b border-white/[0.06] bg-studio-bg/60">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-400" />
              <input
                type="text"
                autoFocus
                placeholder="Search 60 voices..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-white/[0.05] border border-white/[0.08] rounded-lg pl-8 pr-2.5 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand-primary"
              />
            </div>
          </div>

          {/* Voices Scroll List */}
          <div className="flex-1 overflow-y-auto p-1.5 space-y-1">
            {filteredVoices.map((v) => {
              const isSelected = v.id === value;

              return (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => {
                    onChange(v.id);
                    setIsOpen(false);
                    setSearch('');
                  }}
                  className={`w-full p-2 rounded-xl text-left flex items-center justify-between transition-all ${
                    isSelected
                      ? 'bg-brand-primary text-white font-medium shadow-sm'
                      : 'hover:bg-white/[0.06] text-gray-200'
                  }`}
                >
                  <div className="flex items-center space-x-2.5 overflow-hidden">
                    <span className="text-sm shrink-0">{v.flag}</span>
                    <div className="overflow-hidden">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-xs font-semibold truncate">{v.name}</span>
                        <span
                          className={`text-[10px] font-mono ${
                            isSelected ? 'text-white/80' : 'text-gray-500'
                          }`}
                        >
                          {v.id}
                        </span>
                      </div>
                      <div
                        className={`text-[10px] truncate ${
                          isSelected ? 'text-white/80' : 'text-gray-400'
                        }`}
                      >
                        {v.gender} • {v.lang_name}
                      </div>
                    </div>
                  </div>

                  {isSelected && <Check className="w-4 h-4 shrink-0 text-white stroke-[2.5]" />}
                </button>
              );
            })}

            {filteredVoices.length === 0 && (
              <div className="py-6 text-center text-xs text-gray-500">
                No voices found matching "{search}"
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
