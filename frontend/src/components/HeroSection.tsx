import React from 'react';

export const HeroSection: React.FC = React.memo(() => {
  return (
    <section className="text-center pt-8 pb-6 px-4 max-w-3xl mx-auto select-none">
      {/* Main Title */}
      <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-3">
        Turn Your Text Into Realistic Speech
      </h1>

      {/* Subtitle */}
      <p className="text-slate-600 dark:text-slate-300 text-sm sm:text-base leading-relaxed max-w-2xl mx-auto">
        Create natural-sounding audio with our advanced AI voices. Perfect for videos, podcasts, presentations and more.
      </p>
    </section>
  );
});
export default HeroSection;
