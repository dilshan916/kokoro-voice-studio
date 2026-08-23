import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { VoiceCatalog } from './components/VoiceCatalog';
import { EditorWorkspace } from './components/EditorWorkspace';
import { MasterInspector } from './components/MasterInspector';
import { AudioPlayerBar } from './components/AudioPlayerBar';
import { kokoroApi } from './api/kokoroApi';
import { Voice, HealthData, AudioTrack } from './types';

// Fallback initial voice list if server is initializing
const DEFAULT_INITIAL_VOICES: Voice[] = [
  { id: 'af_bella', name: 'Bella', gender: 'Female', lang: 'en-us', lang_name: 'English (US)', flag: '🇺🇸', description: 'Warm, expressive, high-retention narration' },
  { id: 'am_adam', name: 'Adam', gender: 'Male', lang: 'en-us', lang_name: 'English (US)', flag: '🇺🇸', description: 'Deep, authoritative, podcast host style' },
  { id: 'ff_camille', name: 'Camille', gender: 'Female', lang: 'fr-fr', lang_name: 'French', flag: '🇫🇷', description: 'Graceful, conversational Parisian French' },
  { id: 'jf_alpha', name: 'Alpha', gender: 'Female', lang: 'ja', lang_name: 'Japanese', flag: '🇯🇵', description: 'Natural, bright Japanese female voice' },
  { id: 'kf_minji', name: 'Minji', gender: 'Female', lang: 'ko', lang_name: 'Korean', flag: '🇰🇷', description: 'Melodic, warm Seoul dialect female narrator' },
  { id: 'zf_xiaoxiao', name: 'Xiaoxiao', gender: 'Female', lang: 'cmn', lang_name: 'Mandarin', flag: '🇨🇳', description: 'Clear standard Mandarin broadcast presenter' },
  { id: 'ef_dora', name: 'Dora', gender: 'Female', lang: 'es', lang_name: 'Spanish', flag: '🇪🇸', description: 'Warm, expressive Spanish narrator' },
  { id: 'hf_alpha', name: 'Alpha (अल्फा)', gender: 'Female', lang: 'hi', lang_name: 'Hindi', flag: '🇮🇳', description: 'Clear, expressive Hindi female narrator' },
  { id: 'if_sara', name: 'Sara', gender: 'Female', lang: 'it', lang_name: 'Italian', flag: '🇮🇹', description: 'Lively, melodic, authentic Italian voice' },
  { id: 'pf_dora', name: 'Dora (BR)', gender: 'Female', lang: 'pt-br', lang_name: 'Portuguese (BR)', flag: '🇧🇷', description: 'Natural, warm Brazilian Portuguese voice' },
];

export const App: React.FC = () => {
  // Backend health & system metadata
  const [health, setHealth] = useState<HealthData | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);

  // Editor states
  const [text, setText] = useState(
    'Welcome to Kokoro Studio! Generate natural, expressive speech across 60 neural voices in English, French, Japanese, Korean, Mandarin, Spanish, Hindi, Italian, and Portuguese.'
  );
  const [selectedVoice, setSelectedVoice] = useState<Voice>(DEFAULT_INITIAL_VOICES[0]);

  // Audio Inspector (Slide-over drawer)
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(false);
  const [presets, setPresets] = useState<string[]>([
    'Clean Studio (Default)',
    'Warm Podcast Host (+Bass)',
    'Deep Cinematic Trailer',
    'Radio Broadcast (Punchy)',
    'Crisp Air (Commercial)',
    'Vintage Tube Warmth',
    'Bassy Narration',
    'Flat / Raw (Unprocessed)',
  ]);
  const [selectedPreset, setSelectedPreset] = useState<string>('Clean Studio (Default)');
  const [speed, setSpeed] = useState<number>(1.0);
  const [outputFormat, setOutputFormat] = useState<'wav' | 'mp3'>('wav');
  const [pausePunctuationMs, setPausePunctuationMs] = useState<number>(150);
  const [pauseParagraphMs, setPauseParagraphMs] = useState<number>(400);

  // Rendering & Playback state
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const [currentTrack, setCurrentTrack] = useState<AudioTrack | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Poll backend health
  const fetchHealth = useCallback(async () => {
    try {
      setIsCheckingHealth(true);
      const data = await kokoroApi.getHealth();
      setHealth(data);
      if (data.mastering_presets && data.mastering_presets.length > 0) {
        setPresets(data.mastering_presets);
      }
      setErrorMessage(null);
    } catch (err: any) {
      console.warn('FastAPI backend health check failed:', err.message);
      setHealth(null);
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, health?.status === 'ready' ? 15000 : 4000);
    return () => clearInterval(interval);
  }, [fetchHealth, health?.status]);

  // Handler for synthesizing speech
  const handleRenderSpeech = async (customText?: string) => {
    const textToRender = (customText || text).trim();
    if (!textToRender || isRendering) return;

    setIsRendering(true);
    setErrorMessage(null);

    try {
      const response = await kokoroApi.renderSpeech({
        text: textToRender,
        voice_id: selectedVoice.id,
        speed: speed,
        eq_preset: selectedPreset,
        lang: selectedVoice.lang || 'auto',
        output_format: outputFormat,
        pause_punctuation_ms: pausePunctuationMs,
        pause_paragraph_ms: pauseParagraphMs,
      });

      // If audio_base64 is returned from server, create in-memory Blob URL (100% immune to IDM / download managers)
      let playbackUrl = response.audio_url;
      if (response.audio_base64) {
        try {
          const binaryString = atob(response.audio_base64);
          const len = binaryString.length;
          const bytes = new Uint8Array(len);
          for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const mimeType = response.filename.endsWith('.mp3') ? 'audio/mpeg' : 'audio/wav';
          const audioBlob = new Blob([bytes.buffer], { type: mimeType });
          playbackUrl = URL.createObjectURL(audioBlob);
        } catch (e) {
          console.warn('Failed to parse base64 audio into blob:', e);
        }
      }

      // Update active playback track
      const newTrack: AudioTrack = {
        id: response.filename,
        title: textToRender.length > 40 ? textToRender.substring(0, 37) + '...' : textToRender,
        voice_name: response.voice_name || selectedVoice.name,
        voice_flag: selectedVoice.flag,
        audio_url: playbackUrl,
        duration: response.duration,
        filename: response.filename,
        lang: response.lang_resolved,
        eq_preset: response.eq_preset,
        audio_base64: response.audio_base64,
        srt_content: response.srt_content,
        srt_filename: response.srt_filename,
      };

      setCurrentTrack(newTrack);
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Failed to generate speech';
      setErrorMessage(detail);
      console.error('Render error:', err);
    } finally {
      setIsRendering(false);
    }
  };

  const voices = health?.voices && health.voices.length > 0 ? health.voices : DEFAULT_INITIAL_VOICES;

  return (
    <div className="h-screen w-screen flex flex-col bg-studio-bg overflow-hidden text-gray-100 font-sans antialiased">
      {/* 1. Top Clean Navbar */}
      <Navbar
        health={health}
        isLoading={isCheckingHealth}
        onRefreshHealth={fetchHealth}
        onToggleInspector={() => setIsInspectorOpen(!isInspectorOpen)}
        isInspectorOpen={isInspectorOpen}
      />

      {/* Error Alert Banner */}
      {errorMessage && (
        <div className="bg-rose-500/10 border-b border-rose-500/20 px-6 py-2 text-xs text-rose-300 flex items-center justify-between z-40">
          <span>⚠️ {errorMessage}</span>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-white hover:text-rose-200 font-bold px-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* 2. Main 2-Column Clean Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: Clean Voice Catalog */}
        <VoiceCatalog
          voices={voices}
          selectedVoiceId={selectedVoice.id}
          onSelectVoice={setSelectedVoice}
        />

        {/* Center Column: Spacious Editor Canvas */}
        <EditorWorkspace
          text={text}
          onChangeText={setText}
          selectedVoice={selectedVoice}
          voices={voices}
          isRendering={isRendering}
          onRenderSpeech={handleRenderSpeech}
          speed={speed}
          onOpenSettings={() => setIsInspectorOpen(true)}
          selectedPreset={selectedPreset}
        />
      </div>

      {/* 3. Slide-over Audio Master Settings Drawer */}
      <MasterInspector
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
        selectedPreset={selectedPreset}
        onSelectPreset={setSelectedPreset}
        presets={presets}
        speed={speed}
        onChangeSpeed={setSpeed}
        outputFormat={outputFormat}
        onChangeOutputFormat={setOutputFormat}
        pausePunctuationMs={pausePunctuationMs}
        onChangePausePunctuationMs={setPausePunctuationMs}
        pauseParagraphMs={pauseParagraphMs}
        onChangePauseParagraphMs={setPauseParagraphMs}
      />

      {/* 4. Bottom Sticky Player Bar */}
      <AudioPlayerBar currentTrack={currentTrack} />
    </div>
  );
};

export default App;
