import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { ControlCards } from './components/ControlCards';
import { GenerationCanvas } from './components/GenerationCanvas';
import { TrustBadges } from './components/TrustBadges';
import { LastRegenerations } from './components/LastRegenerations';
import { SeoFeatures } from './components/SeoFeatures';
import { SeoFaq } from './components/SeoFaq';
import { Footer } from './components/Footer';
import { LegalDocId, isLegalDocId } from './legal/legalConfig';
import { kokoroApi } from './api/kokoroApi';
import { Voice, HealthData, UserQuota, GenerationHistoryItem } from './types';

// Lazy-loaded dialogs & Legal Center (keeps ~150KB out of initial homepage bundle)
const VoiceModal = React.lazy(() => import('./components/VoiceModal').then((m) => ({ default: m.VoiceModal })));
const PricingModal = React.lazy(() => import('./components/PricingModal').then((m) => ({ default: m.PricingModal })));
const DeveloperModal = React.lazy(() => import('./components/DeveloperModal').then((m) => ({ default: m.DeveloperModal })));
const LegalModal = React.lazy(() => import('./components/LegalModal').then((m) => ({ default: m.LegalModal })));
const LegalCenter = React.lazy(() => import('./components/LegalCenter').then((m) => ({ default: m.LegalCenter })));

const DEFAULT_INITIAL_VOICES: Voice[] = [
  { id: 'af_bella', name: 'Bella', gender: 'Female', lang: 'en-us', lang_name: 'English (US)', flag: '🇺🇸', description: 'Warm, expressive, high-retention narration' },
  { id: 'am_adam', name: 'Adam', gender: 'Male', lang: 'en-us', lang_name: 'English (US)', flag: '🇺🇸', description: 'Deep, authoritative podcast host' },
  { id: 'ff_camille', name: 'Camille', gender: 'Female', lang: 'fr-fr', lang_name: 'French', flag: '🇫🇷', description: 'Graceful, conversational Parisian French' },
  { id: 'jf_alpha', name: 'Alpha', gender: 'Female', lang: 'ja', lang_name: 'Japanese', flag: '🇯🇵', description: 'Natural, bright Japanese female voice' },
  { id: 'kf_minji', name: 'Minji', gender: 'Female', lang: 'ko', lang_name: 'Korean', flag: '🇰🇷', description: 'Melodic, warm Korean narrator' },
  { id: 'zf_xiaoxiao', name: 'Xiaoxiao', gender: 'Female', lang: 'cmn', lang_name: 'Mandarin', flag: '🇨🇳', description: 'Standard Mandarin broadcast presenter' },
  { id: 'ef_dora', name: 'Dora', gender: 'Female', lang: 'es', lang_name: 'Spanish', flag: '🇪🇸', description: 'Warm, expressive Spanish narrator' },
  { id: 'hf_alpha', name: 'Alpha', gender: 'Female', lang: 'hi', lang_name: 'Hindi', flag: '🇮🇳', description: 'Clear, expressive Hindi female narrator' },
  { id: 'if_sara', name: 'Sara', gender: 'Female', lang: 'it', lang_name: 'Italian', flag: '🇮🇹', description: 'Lively, melodic Italian voice' },
  { id: 'pf_dora', name: 'Dora (BR)', gender: 'Female', lang: 'pt-br', lang_name: 'Portuguese (BR)', flag: '🇧🇷', description: 'Natural Brazilian Portuguese voice' },
];

function parseLegalRoute(): { isLegal: boolean; docId: LegalDocId } {
  if (typeof window === 'undefined') return { isLegal: false, docId: 'privacy' };

  const pathname = window.location.pathname.toLowerCase();
  const hash = window.location.hash.toLowerCase();

  // Match /legal, /legal/privacy, /legal/terms, etc.
  if (pathname.startsWith('/legal')) {
    const sub = pathname.replace(/^\/legal\/?/, '').split('/')[0];
    return { isLegal: true, docId: isLegalDocId(sub) ? sub : 'privacy' };
  }

  // Match #/legal/..., #legal/...
  if (hash.startsWith('#/legal') || hash.startsWith('#legal')) {
    const sub = hash.replace(/^#\/?legal\/?/, '').split('/')[0];
    return { isLegal: true, docId: isLegalDocId(sub) ? sub : 'privacy' };
  }

  // Match direct hash: #privacy, #terms, etc.
  const directHash = hash.replace(/^#\/?/, '');
  if (isLegalDocId(directHash)) {
    return { isLegal: true, docId: directHash };
  }

  return { isLegal: false, docId: 'privacy' };
}

export const App: React.FC = () => {
  // Theme State
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('kokoro_theme');
      return saved === 'dark';
    }
    return false;
  });

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('kokoro_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('kokoro_theme', 'light');
    }
  }, [isDarkMode]);

  // Backend Health & Metadata
  const [health, setHealth] = useState<HealthData | null>(null);
  const [quota, setQuota] = useState<UserQuota | null>(null);
  const [presets, setPresets] = useState<string[]>([
    'Clean Studio (Default)',
    'Warm Podcast Host (+Bass)',
    'Deep Cinematic Trailer',
    'Radio Broadcast (Punchy)',
    'Crisp Air (Commercial)',
    'Vintage Tube Warmth',
    'Bassy Narration',
    'Raw Unprocessed',
  ]);

  // Studio Settings
  const [text, setText] = useState('Welcome to Kokoro Studio! Create natural-sounding audio with our advanced AI voices.');
  const [selectedVoice, setSelectedVoice] = useState<Voice>(DEFAULT_INITIAL_VOICES[0]);
  const [speed, setSpeed] = useState<number>(1.0);
  const [selectedPreset, setSelectedPreset] = useState<string>('Clean Studio (Default)');
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [paymentNotice, setPaymentNotice] = useState<{ type: 'success' | 'cancelled'; message: string } | null>(null);

  // Modals
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [isPricingModalOpen, setIsPricingModalOpen] = useState(false);
  const [isDeveloperModalOpen, setIsDeveloperModalOpen] = useState(false);
  const [isLegalModalOpen, setIsLegalModalOpen] = useState(false);

  // View Routing State (Studio vs Dedicated Legal Center)
  const [currentView, setCurrentView] = useState<'studio' | 'legal'>(() => {
    return parseLegalRoute().isLegal ? 'legal' : 'studio';
  });
  const [activeLegalDoc, setActiveLegalDoc] = useState<LegalDocId>(() => {
    return parseLegalRoute().docId;
  });

  // Handle browser back/forward (popstate)
  useEffect(() => {
    const handlePopState = () => {
      const route = parseLegalRoute();
      if (route.isLegal) {
        setCurrentView('legal');
        setActiveLegalDoc(route.docId);
      } else {
        setCurrentView('studio');
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateToLegal = (docId: LegalDocId) => {
    setActiveLegalDoc(docId);
    setCurrentView('legal');
    setIsLegalModalOpen(false);
    if (typeof window !== 'undefined') {
      window.history.pushState(null, '', `/legal/${docId}`);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const navigateToStudio = () => {
    setCurrentView('studio');
    if (typeof window !== 'undefined') {
      window.history.pushState(null, '', '/');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // History & Playback
  const [history, setHistory] = useState<GenerationHistoryItem[]>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('kokoro_history');
        if (saved) return JSON.parse(saved);
      } catch (e) {
        console.warn('Failed to parse history:', e);
      }
    }
    return [];
  });

  const [activeTrackId, setActiveTrackId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackProgress, setPlaybackProgress] = useState<number>(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize Global Audio Element
  useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;

    audio.onended = () => {
      setIsPlaying(false);
      setPlaybackProgress(0);
    };

    let lastProgressUpdate = 0;
    audio.ontimeupdate = () => {
      const now = performance.now();
      if (now - lastProgressUpdate > 120) {
        lastProgressUpdate = now;
        if (audio.duration) {
          setPlaybackProgress(audio.currentTime / audio.duration);
        }
      }
    };

    audio.onerror = (e) => {
      console.warn('Audio playback error:', e);
      setIsPlaying(false);
    };

    return () => {
      audio.pause();
      audio.src = '';
    };
  }, []);

  // Fetch backend health & quota
  const refreshData = useCallback(async () => {
    try {
      const [healthData, quotaData] = await Promise.allSettled([
        kokoroApi.getHealth(),
        kokoroApi.getUserQuota(),
      ]);

      if (healthData.status === 'fulfilled') {
        setHealth(healthData.value);
        if (healthData.value.mastering_presets?.length) {
          setPresets(healthData.value.mastering_presets);
        }
      } else {
        setHealth(null);
      }

      if (quotaData.status === 'fulfilled') {
        setQuota(quotaData.value);
      }
    } catch (err) {
      console.warn('Failed to refresh data:', err);
    }
  }, []);

  useEffect(() => {
    refreshData();
    const timer = setInterval(refreshData, 20000);
    return () => clearInterval(timer);
  }, [refreshData]);

  // Check for Stripe Checkout return query params (?payment=success or ?payment=cancelled)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const params = new URLSearchParams(window.location.search);
      const paymentStatus = params.get('payment');
      if (paymentStatus === 'success') {
        setPaymentNotice({
          type: 'success',
          message: '🎉 Payment successful! Your device has been upgraded to PRO Unlimited.',
        });
        refreshData();
        const cleanUrl = window.location.pathname + (window.location.hash || '');
        window.history.replaceState(null, '', cleanUrl);
      } else if (paymentStatus === 'cancelled') {
        setPaymentNotice({
          type: 'cancelled',
          message: 'Checkout was cancelled. No charges were made.',
        });
        const cleanUrl = window.location.pathname + (window.location.hash || '');
        window.history.replaceState(null, '', cleanUrl);
      }
    } catch (e) {
      console.warn('Failed to parse URL payment params:', e);
    }
  }, [refreshData]);

  // Audio Playback Controls
  const playTrack = (item: GenerationHistoryItem) => {
    if (!audioRef.current) return;
    if (activeTrackId === item.id) {
      audioRef.current.play().then(() => setIsPlaying(true)).catch(console.warn);
      return;
    }

    setActiveTrackId(item.id);
    audioRef.current.src = item.audio_url;
    audioRef.current.play().then(() => setIsPlaying(true)).catch(console.warn);
  };

  const pauseTrack = () => {
    if (!audioRef.current) return;
    audioRef.current.pause();
    setIsPlaying(false);
  };

  // Convert to Audio Handler
  const handleConvert = async () => {
    const trimmed = text.trim();
    if (!trimmed || isRendering) return;

    setIsRendering(true);
    setErrorMessage(null);

    try {
      const response = await kokoroApi.renderSpeech({
        text: trimmed,
        voice_id: selectedVoice.id,
        speed,
        eq_preset: selectedPreset,
        lang: selectedVoice.lang || 'auto',
        output_format: 'mp3',
      });

      // Prepare audio URL (use Base64 blob if returned to avoid download managers)
      let playbackUrl = response.audio_url;
      if (response.audio_base64) {
        try {
          const binaryString = atob(response.audio_base64);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const blob = new Blob([bytes.buffer], { type: 'audio/mpeg' });
          playbackUrl = URL.createObjectURL(blob);
        } catch (e) {
          console.warn('Base64 decode error:', e);
        }
      }

      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      const newItem: GenerationHistoryItem = {
        id: response.filename,
        title: trimmed.length > 35 ? trimmed.substring(0, 32) + '...' : trimmed,
        voice_name: response.voice_name || selectedVoice.name,
        voice_flag: selectedVoice.flag,
        audio_url: playbackUrl,
        filename: response.filename,
        duration: response.duration,
        timestamp: Date.now(),
        formatted_time: timeStr,
        srt_content: response.srt_content,
        srt_filename: response.srt_filename,
        audio_base64: response.audio_base64,
      };

      const updatedHistory = [newItem, ...history.slice(0, 19)];
      setHistory(updatedHistory);
      try {
        localStorage.setItem('kokoro_history', JSON.stringify(updatedHistory));
      } catch (e) {}

      // Auto-play the newly generated speech!
      playTrack(newItem);

      // Refresh quota
      refreshData();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? detail.message || JSON.stringify(detail) : detail || err.message || 'Speech generation failed';
      setErrorMessage(msg);
    } finally {
      setIsRendering(false);
    }
  };

  const handleClearHistory = () => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setIsPlaying(false);
    setActiveTrackId(null);
    setHistory([]);
    try {
      localStorage.removeItem('kokoro_history');
    } catch (e) {}
  };

  const voices = health?.voices && health.voices.length > 0 ? health.voices : DEFAULT_INITIAL_VOICES;

  // Render Dedicated Full Legal Center if in legal view
  if (currentView === 'legal') {
    return (
      <React.Suspense
        fallback={
          <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-500">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <span>Loading Legal Documentation...</span>
            </div>
          </div>
        }
      >
        <LegalCenter
          initialDocId={activeLegalDoc}
          onSelectDoc={navigateToLegal}
          onBackToStudio={navigateToStudio}
          isDarkMode={isDarkMode}
          onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
        />
      </React.Suspense>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#eaf3ff] via-[#e2edfc] to-[#d8e7fa] dark:from-[#0b0f19] dark:via-[#0e1322] dark:to-[#090d16] text-slate-900 dark:text-slate-100 font-sans transition-colors duration-200">
      {/* 1. Clean Top Navbar */}
      <Navbar
        health={health}
        quota={quota}
        onOpenVoices={() => setIsVoiceModalOpen(true)}
        onOpenPricing={() => setIsPricingModalOpen(true)}
        onOpenDevelopers={() => setIsDeveloperModalOpen(true)}
        isDarkMode={isDarkMode}
        onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
      />

      {/* Payment Notice Banner */}
      {paymentNotice && (
        <div className="max-w-4xl mx-auto w-full px-4 mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
          <div
            className={`p-3.5 rounded-2xl text-xs flex items-center justify-between shadow-sm ${
              paymentNotice.type === 'success'
                ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300 shadow-emerald-500/10'
                : 'bg-amber-500/15 border border-amber-500/30 text-amber-700 dark:text-amber-300 shadow-amber-500/10'
            }`}
          >
            <div className="flex items-center gap-2 font-semibold">
              <span>{paymentNotice.message}</span>
            </div>
            <button
              onClick={() => setPaymentNotice(null)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 font-bold px-2 py-0.5 rounded-lg cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Error Alert Banner */}
      {errorMessage && (
        <div className="max-w-4xl mx-auto w-full px-4 mt-4">
          <div className="bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 p-3.5 rounded-2xl text-xs flex items-center justify-between shadow-sm">
            <span>⚠️ {errorMessage}</span>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-500 hover:text-rose-700 font-bold px-2 py-0.5 rounded-lg"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* 2. Main Studio Canvas Layout Matching Reference Image */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 py-4 flex flex-col justify-start space-y-6">
        {/* Hero Section */}
        <HeroSection />

        {/* 2 Control Cards: SELECT VOICE & AUDIO OPTIONS */}
        <ControlCards
          selectedVoice={selectedVoice}
          onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
          speed={speed}
          onChangeSpeed={setSpeed}
          selectedPreset={selectedPreset}
          onChangePreset={setSelectedPreset}
          presets={presets}
        />

        {/* Text Input & Centered Convert Button */}
        <GenerationCanvas
          text={text}
          onChangeText={setText}
          onConvert={handleConvert}
          isRendering={isRendering}
          maxChars={quota?.tier === 'pro' ? 20000 : 2000}
        />

        {/* Trust Badges */}
        <TrustBadges />

        {/* 3. Crawlable SEO Features Grid */}
        <SeoFeatures />

        {/* 4. Interactive SEO FAQ Accordion */}
        <SeoFaq />
      </main>

      {/* 5. Semantic SEO Footer */}
      <Footer
        onOpenVoices={() => setIsVoiceModalOpen(true)}
        onOpenPricing={() => setIsPricingModalOpen(true)}
        onOpenDevelopers={() => setIsDeveloperModalOpen(true)}
        onOpenLegal={(docId) => navigateToLegal(docId)}
      />

      {/* 3. Floating "LAST REGENERATIONS" Widget on Bottom-Right */}
      <LastRegenerations
        history={history}
        onClearHistory={handleClearHistory}
        activeTrackId={activeTrackId}
        onPlayTrack={playTrack}
        onPauseTrack={pauseTrack}
        isPlaying={isPlaying}
        playbackProgress={playbackProgress}
      />

      {/* 4. Modals (Lazy Loaded on Demand) */}
      <React.Suspense fallback={null}>
        {isVoiceModalOpen && (
          <VoiceModal
            isOpen={isVoiceModalOpen}
            onClose={() => setIsVoiceModalOpen(false)}
            voices={voices}
            selectedVoiceId={selectedVoice.id}
            onSelectVoice={setSelectedVoice}
            onVoiceCreated={() => refreshData()}
            onVoiceDeleted={() => refreshData()}
          />
        )}

        {isPricingModalOpen && (
          <PricingModal
            isOpen={isPricingModalOpen}
            onClose={() => setIsPricingModalOpen(false)}
            quota={quota}
            onQuotaUpdated={refreshData}
          />
        )}

        {isDeveloperModalOpen && (
          <DeveloperModal
            isOpen={isDeveloperModalOpen}
            onClose={() => setIsDeveloperModalOpen(false)}
            voices={voices}
            quota={quota}
            onOpenPricing={() => {
              setIsDeveloperModalOpen(false);
              setIsPricingModalOpen(true);
            }}
          />
        )}

        {isLegalModalOpen && (
          <LegalModal
            isOpen={isLegalModalOpen}
            onClose={() => setIsLegalModalOpen(false)}
            onOpenDocument={(docId) => navigateToLegal(docId)}
          />
        )}
      </React.Suspense>
    </div>
  );
};

export default App;
