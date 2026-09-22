import React from 'react';
import { ArrowLeft, BookOpen, Sliders, Cpu, CheckCircle2, Video, Wand2 } from 'lucide-react';

interface GuidePageProps {
  onBackToStudio: () => void;
  onNavigate: (route: string) => void;
}

export const GuidePage: React.FC<GuidePageProps> = ({ onBackToStudio, onNavigate }) => {
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
            <button onClick={() => onNavigate('voices')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Voices</button>
            <span>•</span>
            <button onClick={() => onNavigate('about')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">About</button>
            <span>•</span>
            <button onClick={() => onNavigate('contact')} className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">Contact</button>
          </div>
        </div>

        {/* Title */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-semibold border border-blue-200 dark:border-blue-800">
            <BookOpen className="w-3.5 h-3.5 text-blue-500" />
            <span>Official Documentation &amp; User Manual</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight">
            Complete Audio Mastering &amp; Speech Synthesis Guide
          </h1>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-3xl leading-relaxed">
            Master the art of neural text-to-speech generation. Learn how the Kokoro-82M engine generates lifelike voices, how to apply studio mastering EQ presets, and how to export synchronized SRT subtitles for video production.
          </p>
        </div>

        {/* Section 1: The Technology */}
        <section className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">1. How Kokoro-82M Neural Synthesis Works</h2>
              <span className="text-xs text-slate-500 dark:text-slate-400">StyleTTS2 Architecture • 82 Million Parameters • Phonemization Pipeline</span>
            </div>
          </div>

          <div className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed space-y-4">
            <p>
              Traditional Text-to-Speech engines relied on concatenative synthesis (piecing together pre-recorded phoneme snippets) or bulky parameter models that produced robotic, mechanical cadence. Kokoro-82M takes an entirely modern deep learning approach based on continuous style latent representations.
            </p>
            <p>
              When you submit a script to Kokoro Voice Studio, the audio generation pipeline executes in three synchronized stages:
            </p>
            <ol className="list-decimal list-inside space-y-2 pl-2 text-xs font-medium">
              <li><strong>Phonetic Transduction:</strong> Your raw text is converted into international phonetic alphabet (IPA) tokens using rule-based phonemizers, ensuring correct stress patterns and elision across all 9 supported languages.</li>
              <li><strong>Style Vector Conditioning:</strong> The neural network is seeded with a 256-dimensional style embedding vector corresponding to your chosen voice (e.g., Bella, Adam, Nicole). This vector controls pitch contour, vocal fry, breathiness, and emotional inflection.</li>
              <li><strong>Adversarial Neural Vocoding:</strong> The generator computes mel-spectrogram slices in parallel and reconstructs pristine 24,000Hz (24kHz) floating-point PCM audio with natural harmonic overtone distribution.</li>
            </ol>
          </div>
        </section>

        {/* Section 2: Audio Mastering Presets */}
        <section className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">2. Studio Mastering EQ Presets Explained</h2>
              <span className="text-xs text-slate-500 dark:text-slate-400">Acoustic Loudness (-14 LUFS) • Parametric EQ • Bass Resonance</span>
            </div>
          </div>

          <div className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed space-y-4">
            <p>
              Raw AI speech can often sound flat or lack the acoustic presence of a professional condenser microphone inside a sound-dampened booth. Kokoro Voice Studio includes a built-in mastering engine that automatically post-processes your audio through 8 specialized acoustic profiles:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="font-bold text-sm text-blue-600 dark:text-blue-400">Clean Studio (Default)</span>
                <p className="text-xs text-slate-600 dark:text-slate-400">Applies an 80Hz high-pass filter to eliminate sub-bass room rumble, gently scoops muddy 300Hz frequencies, and normalizes integrated loudness to -14.0 LUFS.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="font-bold text-sm text-indigo-600 dark:text-indigo-400">Warm Podcast Host (+Bass)</span>
                <p className="text-xs text-slate-600 dark:text-slate-400">Boosts the 120Hz–180Hz proximity effect, mimicking a Shure SM7B dynamic microphone. Ideal for long-form interviews and explanatory video essays.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="font-bold text-sm text-amber-600 dark:text-amber-400">Deep Cinematic Trailer</span>
                <p className="text-xs text-slate-600 dark:text-slate-400">Emphasizes sub-octave chest resonance and high-end air (10kHz+). Perfect for movie teasers, dramatic fiction, and documentary intros.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="font-bold text-sm text-emerald-600 dark:text-emerald-400">Radio Broadcast (Punchy)</span>
                <p className="text-xs text-slate-600 dark:text-slate-400">Aggressive multiband compression and mid-range forwardness (1kHz–3kHz) designed to cut through dense background music and road noise.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="font-bold text-sm text-purple-600 dark:text-purple-400">Crisp Air (Commercial)</span>
                <p className="text-xs text-slate-600 dark:text-slate-400">Gentle high-shelf boost (+3dB at 8kHz) enhancing sibilance definition and crisp consonants for television commercials and tech promotions.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="font-bold text-sm text-rose-600 dark:text-rose-400">Raw Unprocessed</span>
                <p className="text-xs text-slate-600 dark:text-slate-400">Delivers untouched 24kHz floating-point PCM output straight from the neural vocoder. Ideal for audio engineers performing custom mastering in a DAW.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Section 3: Subtitles & Video Editing */}
        <section className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 dark:text-amber-400">
              <Video className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">3. Synchronized Subtitles (.SRT) for Video Creators</h2>
              <span className="text-xs text-slate-500 dark:text-slate-400">CapCut • Adobe Premiere Pro • DaVinci Resolve • TikTok &amp; Reels</span>
            </div>
          </div>

          <div className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed space-y-4">
            <p>
              Every audio render generated by Kokoro Voice Studio produces a synchronized SubRip (<code>.srt</code>) file alongside the high-resolution MP3/WAV. The timestamps are calculated at sentence and phrase boundaries using acoustic energy tracking.
            </p>

            <div className="p-5 rounded-2xl bg-slate-900 text-slate-200 font-mono text-xs space-y-2 overflow-x-auto">
              <span className="text-slate-500">// Example Generated SubRip File (.srt)</span>
              <p>1<br />00:00:00,000 --&gt; 00:00:02,450<br />Welcome to Kokoro Studio!</p>
              <p>2<br />00:00:02,450 --&gt; 00:00:05,800<br />Create natural-sounding audio with advanced AI voices.</p>
            </div>

            <div className="space-y-2">
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">How to Import Subtitles into Popular Editors:</h3>
              <ul className="list-disc list-inside text-xs space-y-1.5 text-slate-600 dark:text-slate-300">
                <li><strong>CapCut (Desktop/Mobile):</strong> Click <em>Text</em> $\rightarrow$ <em>Auto Captions / Local Subtitles</em> $\rightarrow$ Import your downloaded <code>.srt</code> file. Your captions will align frame-perfect with the voiceover.</li>
                <li><strong>Adobe Premiere Pro:</strong> Drag the <code>.srt</code> file directly onto a new Captions track above your audio track. Premiere automatically conforms text styles and animation presets.</li>
                <li><strong>DaVinci Resolve:</strong> Drag the <code>.srt</code> file onto your timeline. In the Inspector panel, configure font family, stroke borders, and text drop-shadow.</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Section 4: Voice Blending */}
        <section className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-rose-50 dark:bg-rose-900/30 flex items-center justify-center text-rose-600 dark:text-rose-400">
              <Wand2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">4. Voice Blending &amp; Style Vector Interpolation</h2>
              <span className="text-xs text-slate-500 dark:text-slate-400">Neural Latent Algebra • Hybrid Vocal Personas</span>
            </div>
          </div>

          <div className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed space-y-4">
            <p>
              One of the most powerful features of Kokoro Voice Studio is the <strong>Voice Blender</strong>. Because neural voices exist as numerical style embeddings in latent vector space, two different vocal identities can be mathematically interpolated:
            </p>
            <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-blue-900 dark:text-blue-200 font-mono text-xs text-center">
              v_hybrid = (α × Voice_A) + ((1 - α) × Voice_B)
            </div>
            <p>
              For example, blending <strong>70% Bella</strong> (warm, expressive female) with <strong>30% Nicole</strong> (crisp, professional narrator) produces a distinct, proprietary vocal signature that makes your brand videos or audiobooks stand out from standard AI voices.
            </p>
          </div>
        </section>

        {/* Section 5: Best Practices for Natural Cadence */}
        <section className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <span>5. Pro Tips for Script Formatting &amp; Punctuation</span>
          </h2>
          <div className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed space-y-2">
            <p>To obtain the most lifelike inflection from Kokoro-82M, format your input script with these guidelines:</p>
            <ul className="list-disc list-inside text-xs space-y-1.5 pl-2">
              <li><strong>Punctuation Controls Pauses:</strong> Use commas (<code>,</code>) for short conversational breaths (200ms) and periods (<code>.</code>) or em-dashes (<code>—</code>) for deliberate sentence pauses (400ms).</li>
              <li><strong>Acronyms:</strong> Write acronyms with spaces or periods (e.g., <code>N. A. S. A.</code> or <code>N A S A</code>) to force letter-by-letter pronunciation rather than word blending.</li>
              <li><strong>Pacing:</strong> Standard conversational speed is between <code>0.95x</code> and <code>1.05x</code>. For dramatic storytelling, try <code>0.90x</code> with the <em>Deep Cinematic Trailer</em> preset.</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
};
