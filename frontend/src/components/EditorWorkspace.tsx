import React, { useState, useMemo } from 'react';
import {
  FileText,
  Users,
  Layers,
  Sparkles,
  Zap,
  Clock,
  RotateCcw,
  Languages,
  Plus,
  Trash2,
  ChevronUp,
  ChevronDown,
  Timer,
  RefreshCw,
  Code,
} from 'lucide-react';
import { Voice, DialogueBlock } from '../types';
import { VoiceSelectDropdown } from './VoiceSelectDropdown';

interface EditorWorkspaceProps {
  text: string;
  onChangeText: (text: string) => void;
  selectedVoice: Voice | null;
  voices: Voice[];
  isRendering: boolean;
  onRenderSpeech: (customText?: string) => void;
  speed: number;
  onOpenSettings: () => void;
  selectedPreset: string;
}

const INITIAL_DIALOGUE_BLOCKS: DialogueBlock[] = [
  {
    id: 'block-1',
    speakerName: 'Bella',
    voiceId: 'af_bella',
    lang: 'en-us',
    text: 'Welcome to Kokoro Voice Studio Pro!',
    pauseAfterSec: 0.4,
  },
  {
    id: 'block-2',
    speakerName: 'Adam',
    voiceId: 'am_adam',
    lang: 'en-us',
    text: 'Experience ultra-realistic neural speech synthesis with zero latency.',
    pauseAfterSec: 0.4,
  },
  {
    id: 'block-3',
    speakerName: 'Camille',
    voiceId: 'ff_camille',
    lang: 'fr-fr',
    text: 'Bonjour à tous! Nous prenons en charge plus de neuf langues.',
    pauseAfterSec: 0.4,
  },
  {
    id: 'block-4',
    speakerName: 'Alpha',
    voiceId: 'jf_alpha',
    lang: 'ja',
    text: '日本語の勉強はとても楽しいです。東京へ行きます。',
    pauseAfterSec: 0.4,
  },
];

export const EditorWorkspace: React.FC<EditorWorkspaceProps> = ({
  text,
  onChangeText,
  selectedVoice,
  voices,
  isRendering,
  onRenderSpeech,
  speed,
  onOpenSettings,
  selectedPreset,
}) => {
  const [activeTab, setActiveTab] = useState<'single' | 'drama' | 'batch' | 'phonemes'>('single');

  // Interactive Multi-Speaker Drama Blocks state
  const [dialogueBlocks, setDialogueBlocks] = useState<DialogueBlock[]>(INITIAL_DIALOGUE_BLOCKS);
  const [showRawScriptView, setShowRawScriptView] = useState(false);
  const [openDropdownBlockId, setOpenDropdownBlockId] = useState<string | null>(null);

  // Live metrics calculation for single speech
  const charCount = text.length;
  const isCJK = useMemo(() => {
    return /[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\uac00-\ud7af]/.test(text);
  }, [text]);

  const wordCount = useMemo(() => {
    const trimmed = text.trim();
    return trimmed ? trimmed.split(/\s+/).length : 0;
  }, [text]);

  const estimatedSeconds = useMemo(() => {
    if (!text.trim()) return 0;
    if (isCJK) {
      // CJK reading pace is ~5.5 characters per second
      const cjkSec = (charCount / 5.5) / Math.max(0.5, speed);
      return Math.round(cjkSec);
    }
    if (wordCount === 0) return 0;
    const baseMinutes = wordCount / 150;
    const adjustedSeconds = (baseMinutes * 60) / Math.max(0.5, speed);
    return Math.round(adjustedSeconds);
  }, [text, isCJK, charCount, wordCount, speed]);

  // Estimated duration for drama script
  const dramaEstimatedSeconds = useMemo(() => {
    let totalWords = 0;
    let totalPause = 0;
    dialogueBlocks.forEach((b) => {
      const words = b.text.trim() ? b.text.trim().split(/\s+/).length : 0;
      totalWords += words;
      totalPause += b.pauseAfterSec;
    });
    const speechSec = (totalWords / 150) * 60 / Math.max(0.5, speed);
    return Math.round(speechSec + totalPause);
  }, [dialogueBlocks, speed]);

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const insertPause = (pauseStr: string) => {
    onChangeText(text + (text.endsWith(' ') || text === '' ? '' : ' ') + pauseStr + ' ');
  };

  // Compile Dialogue Blocks into Tagged Script
  const compileDialogueScript = (): string => {
    return dialogueBlocks
      .filter((b) => b.text.trim().length > 0)
      .map((b) => {
        const langTag = b.lang && b.lang !== 'en-us' && b.lang !== 'auto' ? ` (${b.lang})` : '';
        const speakerTag = `[${b.speakerName}${langTag}]: ${b.text.trim()}`;
        if (b.pauseAfterSec > 0) {
          return `${speakerTag}\n[pause ${b.pauseAfterSec}s]`;
        }
        return speakerTag;
      })
      .join('\n');
  };

  // Drama Block Handlers
  const handleAddBlock = () => {
    const fallbackVoice = voices[0] || { id: 'af_bella', name: 'Bella', lang: 'en-us' };
    const newBlock: DialogueBlock = {
      id: `block-${Date.now()}`,
      speakerName: fallbackVoice.name.split(' ')[0],
      voiceId: fallbackVoice.id,
      lang: fallbackVoice.lang,
      text: '',
      pauseAfterSec: 0.4,
    };
    setDialogueBlocks([...dialogueBlocks, newBlock]);
  };

  const handleUpdateBlock = (id: string, updates: Partial<DialogueBlock>) => {
    setDialogueBlocks((prev) =>
      prev.map((b) => (b.id === id ? { ...b, ...updates } : b))
    );
  };

  const handleDeleteBlock = (id: string) => {
    if (dialogueBlocks.length <= 1) return;
    setDialogueBlocks((prev) => prev.filter((b) => b.id !== id));
  };

  const handleMoveBlock = (index: number, direction: 'up' | 'down') => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === dialogueBlocks.length - 1)
    ) {
      return;
    }
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    const updated = [...dialogueBlocks];
    const [moved] = updated.splice(index, 1);
    updated.splice(targetIndex, 0, moved);
    setDialogueBlocks(updated);
  };

  const handleVoiceChangeForBlock = (id: string, newVoiceId: string) => {
    const v = voices.find((vox) => vox.id === newVoiceId);
    if (v) {
      handleUpdateBlock(id, {
        voiceId: v.id,
        speakerName: v.name.split(' ')[0],
        lang: v.lang,
      });
    }
  };

  const handleRenderDrama = () => {
    const compiled = compileDialogueScript();
    if (!compiled.trim()) return;
    onChangeText(compiled);
    onRenderSpeech(compiled);
  };

  return (
    <main className="flex-1 h-full bg-studio-bg flex flex-col overflow-hidden select-none">
      {/* Top Tab Bar & Active Voice Pill */}
      <div className="h-14 px-8 flex items-center justify-between border-b border-white/[0.06] shrink-0">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setActiveTab('single')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-all ${
              activeTab === 'single'
                ? 'bg-white/[0.08] text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            <FileText className="w-3.5 h-3.5 text-brand-primary" />
            <span>Text to Speech</span>
          </button>

          <button
            onClick={() => setActiveTab('drama')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-all ${
              activeTab === 'drama'
                ? 'bg-white/[0.08] text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            <Users className="w-3.5 h-3.5 text-brand-secondary" />
            <span>Multi-Speaker Studio</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-brand-secondary/20 text-brand-secondary">
              {dialogueBlocks.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('batch')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-all ${
              activeTab === 'batch'
                ? 'bg-white/[0.08] text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-brand-accent" />
            <span>Batch Jobs</span>
          </button>

          <button
            onClick={() => setActiveTab('phonemes')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-all ${
              activeTab === 'phonemes'
                ? 'bg-white/[0.08] text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/[0.04]'
            }`}
          >
            <Languages className="w-3.5 h-3.5 text-brand-success" />
            <span>Phonemes</span>
          </button>
        </div>

        {/* Active Voice Pill & EQ Preset Shortcut */}
        {selectedVoice && (
          <div className="flex items-center space-x-2">
            <button
              onClick={onOpenSettings}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] text-xs text-gray-300 transition-all"
              title="Click to adjust voice & audio settings"
            >
              <span className="text-sm">{selectedVoice.flag}</span>
              <span className="font-medium text-white">{selectedVoice.name}</span>
              <span className="text-gray-500">•</span>
              <span className="text-gray-400 font-mono text-[11px]">{selectedVoice.lang_name}</span>
              <span className="text-gray-500">•</span>
              <span className="text-brand-accent text-[11px]">{selectedPreset}</span>
            </button>
          </div>
        )}
      </div>

      {/* Tab 1: Single Speech Editor */}
      {activeTab === 'single' && (
        <div className="flex-1 flex flex-col p-8 overflow-hidden space-y-4 max-w-5xl w-full mx-auto">
          {/* Main Spacious Canvas */}
          <div className="flex-1 rounded-2xl bg-studio-surface/50 border border-white/[0.08] backdrop-blur-md p-6 flex flex-col shadow-panel focus-within:border-brand-primary/40 focus-within:bg-studio-surface/70 transition-all">
            {/* Textarea */}
            <textarea
              value={text}
              onChange={(e) => onChangeText(e.target.value)}
              placeholder="Type or paste text here to generate natural speech..."
              className="w-full flex-1 bg-transparent text-base md:text-lg text-gray-100 placeholder-gray-500 resize-none focus:outline-none leading-relaxed font-sans scrollbar-thin select-text"
            />

            {/* Editor Bottom Bar */}
            <div className="pt-4 border-t border-white/[0.06] flex items-center justify-between text-xs text-gray-400">
              {/* Metrics & Pause Shortcuts */}
              <div className="flex items-center space-x-5">
                <div className="flex items-center space-x-3 text-xs">
                  <span>
                    <strong className="text-white font-mono">{charCount}</strong> characters
                  </span>
                  {!isCJK && (
                    <>
                      <span className="text-gray-600">•</span>
                      <span>
                        <strong className="text-white font-mono">{wordCount}</strong> words
                      </span>
                    </>
                  )}
                  <span className="text-gray-600">•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-gray-400" />
                    <strong className="text-white font-mono">~{formatSeconds(estimatedSeconds)}</strong>
                  </span>
                </div>

                {/* Pause helper chips */}
                <div className="hidden sm:flex items-center space-x-1.5 pl-2 border-l border-white/[0.06]">
                  <button
                    onClick={() => insertPause('[pause 0.3s]')}
                    className="px-2 py-0.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-[11px] text-gray-400 hover:text-white transition-all"
                  >
                    +0.3s
                  </button>
                  <button
                    onClick={() => insertPause('[pause 0.5s]')}
                    className="px-2 py-0.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-[11px] text-gray-400 hover:text-white transition-all"
                  >
                    +0.5s
                  </button>
                  <button
                    onClick={() => insertPause('[pause 1.0s]')}
                    className="px-2 py-0.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-[11px] text-gray-400 hover:text-white transition-all"
                  >
                    +1.0s
                  </button>
                </div>
              </div>

              {/* Big Primary Generate Button */}
              <button
                onClick={() => onRenderSpeech()}
                disabled={isRendering || !text.trim()}
                className={`px-6 py-2.5 rounded-xl font-semibold text-xs flex items-center gap-2 transition-all ${
                  isRendering
                    ? 'bg-brand-primary/50 text-white cursor-wait'
                    : text.trim()
                    ? 'bg-white hover:bg-gray-100 text-black shadow-lg shadow-white/10 active:scale-95'
                    : 'bg-white/[0.05] text-gray-500 cursor-not-allowed border border-white/[0.04]'
                }`}
              >
                {isRendering ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin text-white" />
                    <span>Synthesizing...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5 fill-black text-black" />
                    <span>Generate Speech</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Interactive Multi-Speaker Drama Studio */}
      {activeTab === 'drama' && (
        <div className="flex-1 flex flex-col p-8 overflow-hidden space-y-4 max-w-5xl w-full mx-auto">
          {/* Drama Toolbar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 text-xs text-gray-400">
              <span className="font-semibold text-white">Interactive Dialogue Blocks</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-brand-secondary" />
                Est. <strong className="text-white font-mono">~{formatSeconds(dramaEstimatedSeconds)}</strong>
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowRawScriptView(!showRawScriptView)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 border transition-all ${
                  showRawScriptView
                    ? 'bg-brand-secondary text-black border-brand-secondary font-semibold'
                    : 'bg-white/[0.04] hover:bg-white/[0.08] text-gray-300 border-white/[0.08]'
                }`}
              >
                <Code className="w-3.5 h-3.5" />
                <span>{showRawScriptView ? 'Block Cards' : 'View Raw Script'}</span>
              </button>

              <button
                onClick={() => setDialogueBlocks(INITIAL_DIALOGUE_BLOCKS)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/[0.06] transition-all"
                title="Reset sample drama"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Block Cards List / Raw Script View */}
          {showRawScriptView ? (
            <div className="flex-1 rounded-2xl bg-studio-surface/50 border border-white/[0.08] p-5 flex flex-col shadow-panel">
              <textarea
                readOnly
                value={compileDialogueScript()}
                className="w-full flex-1 bg-transparent text-sm font-mono text-gray-300 resize-none focus:outline-none leading-relaxed select-text"
              />
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto pr-2 space-y-3">
              {dialogueBlocks.map((block, index) => {
                const currentVoice = voices.find((v) => v.id === block.voiceId);

                return (
                  <React.Fragment key={block.id}>
                    {/* Speaker Block Card */}
                    <div
                      className={`relative p-4 rounded-2xl bg-studio-surface/60 border border-white/[0.08] hover:border-white/[0.15] backdrop-blur-md transition-all space-y-3 shadow-panel ${
                        openDropdownBlockId === block.id ? 'z-40' : 'z-10'
                      }`}
                    >
                      {/* Card Header: Voice Selector & Actions */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {/* Avatar Flag */}
                          <div className="w-8 h-8 rounded-xl bg-white/[0.06] flex items-center justify-center text-base shrink-0 shadow-sm">
                            {currentVoice?.flag || '🎙️'}
                          </div>

                          {/* Custom Dark Theme Voice Selector Dropdown */}
                          <div className="flex items-center space-x-2">
                            <VoiceSelectDropdown
                              value={block.voiceId}
                              onChange={(newVid) => handleVoiceChangeForBlock(block.id, newVid)}
                              voices={voices}
                              onOpenChange={(isOpen) =>
                                setOpenDropdownBlockId(isOpen ? block.id : null)
                              }
                            />
                            <span className="text-[10px] font-mono text-gray-500 bg-white/[0.04] px-2 py-0.5 rounded-md">
                              {block.lang}
                            </span>
                          </div>
                        </div>

                        {/* Block Reorder & Delete Actions */}
                        <div className="flex items-center space-x-1 text-gray-400">
                          <button
                            onClick={() => handleMoveBlock(index, 'up')}
                            disabled={index === 0}
                            className="p-1 rounded hover:bg-white/[0.08] hover:text-white disabled:opacity-20 transition-colors"
                            title="Move line up"
                          >
                            <ChevronUp className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleMoveBlock(index, 'down')}
                            disabled={index === dialogueBlocks.length - 1}
                            className="p-1 rounded hover:bg-white/[0.08] hover:text-white disabled:opacity-20 transition-colors"
                            title="Move line down"
                          >
                            <ChevronDown className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteBlock(block.id)}
                            disabled={dialogueBlocks.length <= 1}
                            className="p-1 rounded hover:bg-rose-500/20 hover:text-rose-400 disabled:opacity-20 transition-colors ml-1"
                            title="Delete line"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* Dialogue Line Textarea */}
                      <textarea
                        value={block.text}
                        onChange={(e) => handleUpdateBlock(block.id, { text: e.target.value })}
                        placeholder={`Enter line for ${block.speakerName}...`}
                        rows={2}
                        className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl p-3 text-sm text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:border-brand-secondary/50 focus:bg-white/[0.05] leading-relaxed transition-all select-text font-sans"
                      />
                    </div>

                    {/* Adjustable Inter-Block Pause Pill */}
                    {index < dialogueBlocks.length - 1 && (
                      <div className="flex items-center justify-center my-1">
                        <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] text-[11px] text-gray-400">
                          <Timer className="w-3 h-3 text-brand-secondary" />
                          <span>Pause:</span>
                          <button
                            onClick={() =>
                              handleUpdateBlock(block.id, {
                                pauseAfterSec:
                                  block.pauseAfterSec === 0.2
                                    ? 0.4
                                    : block.pauseAfterSec === 0.4
                                    ? 0.8
                                    : 0.2,
                              })
                            }
                            className="font-mono font-bold text-white bg-white/[0.08] px-2 py-0.5 rounded-full hover:bg-white/[0.15] transition-colors"
                            title="Click to cycle pause duration (0.2s / 0.4s / 0.8s)"
                          >
                            {block.pauseAfterSec.toFixed(2)}s
                          </button>
                        </div>
                      </div>
                    )}
                  </React.Fragment>
                );
              })}

              {/* Add New Speaker Line Button */}
              <div className="pt-2 flex justify-center">
                <button
                  onClick={handleAddBlock}
                  className="px-5 py-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-brand-primary text-xs font-semibold text-gray-200 hover:text-white flex items-center gap-2 transition-all shadow-sm active:scale-98"
                >
                  <Plus className="w-4 h-4 text-brand-primary" />
                  <span>Add Speaker Line</span>
                </button>
              </div>
            </div>
          )}

          {/* Drama Bottom Bar: Render Multi-Speaker Speech */}
          <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between">
            <div className="text-xs text-gray-500">
              <span>{dialogueBlocks.length} characters assigned</span>
            </div>

            <button
              onClick={handleRenderDrama}
              disabled={isRendering || dialogueBlocks.every((b) => !b.text.trim())}
              className={`px-6 py-2.5 rounded-xl font-semibold text-xs flex items-center gap-2 transition-all ${
                isRendering
                  ? 'bg-brand-secondary/50 text-black cursor-wait'
                  : 'bg-white hover:bg-gray-100 text-black shadow-lg shadow-white/10 active:scale-95'
              }`}
            >
              {isRendering ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin text-black" />
                  <span>Synthesizing Drama...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-black" />
                  <span>Generate Multi-Speaker Audio</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Tab 3: Batch Queue */}
      {activeTab === 'batch' && (
        <div className="flex-1 p-8 flex flex-col items-center justify-center text-center text-gray-400 space-y-3">
          <Layers className="w-10 h-10 opacity-30 text-brand-primary" />
          <h3 className="text-sm font-semibold text-white">Batch Audio Production Queue</h3>
          <p className="text-xs max-w-sm">
            Import bulk text files or split large scripts into chaptered audio files.
          </p>
          <button className="px-4 py-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] text-xs text-white transition-all flex items-center gap-2">
            <Plus className="w-3.5 h-3.5 text-brand-primary" />
            <span>Add Batch Job</span>
          </button>
        </div>
      )}

      {/* Tab 4: Phoneme Inspector */}
      {activeTab === 'phonemes' && (
        <div className="flex-1 p-8 flex flex-col space-y-4 max-w-4xl w-full mx-auto overflow-y-auto">
          <div className="text-xs text-gray-400">
            <h3 className="font-semibold text-white mb-1">G2P Phoneme Analyzer</h3>
            <p>
              Inspects morphological POS tagging (Janome), Mandarin pitch arrows, and Kokoro IPA token conversion.
            </p>
          </div>

          <div className="bg-studio-surface/50 p-4 rounded-2xl border border-white/[0.08] space-y-2">
            <div className="text-[11px] font-semibold text-brand-primary">INPUT SCRIPT</div>
            <div className="text-xs text-gray-300 font-mono bg-black/30 p-3 rounded-xl border border-white/[0.04]">
              {text || '(Empty text)'}
            </div>
          </div>

          <div className="bg-studio-surface/50 p-4 rounded-2xl border border-white/[0.08] space-y-2">
            <div className="text-[11px] font-semibold text-emerald-400">PIPELINE RULES</div>
            <ul className="text-xs text-gray-400 space-y-1.5 font-mono">
              <li>• Japanese: Janome Morphological POS (は→wa, へ→e) + _JA_M2P</li>
              <li>• Mandarin: Pinyin frontend with Kokoro tone arrows</li>
              <li>• French & European: eSpeak-NG with unified IPA token mapping</li>
            </ul>
          </div>
        </div>
      )}
    </main>
  );
};
