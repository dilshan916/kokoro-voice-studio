import React from 'react';

export const HeroSection: React.FC = React.memo(() => {
  return (
    <section className="text-center pt-8 pb-6 px-4 max-w-3xl mx-auto select-none">
      {/* Main Title */}
      <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-2">
        Kokoro <span className="text-blue-600 dark:text-blue-400">Voice Studio</span>
      </h1>

      {/* Subtitle / Tagline */}
      <p className="text-blue-600 dark:text-blue-400 font-semibold text-sm sm:text-base mb-2">
        Free Neural AI Text to Speech &amp; Kokoro TTS Online
      </p>

      {/* Description */}
      <p className="text-slate-600 dark:text-slate-300 text-sm sm:text-base leading-relaxed max-w-2xl mx-auto">
        Create natural-sounding audio with 60 advanced AI voices across 9+ languages. Includes studio EQ mastering and synchronized SRT subtitles. 100% free, no signup required.
      </p>
    </section>
  );
});
export default HeroSection;
