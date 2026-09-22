import React from 'react';
import { Github, Smartphone, Heart, Shield, ExternalLink, Coffee, BookOpen, Mic } from 'lucide-react';
import { LegalDocId, LEGAL_CONFIG } from '../legal/legalConfig';

interface FooterProps {
  onOpenVoices: () => void;
  onOpenPricing: () => void;
  onOpenDevelopers: () => void;
  onOpenLegal: (docId: LegalDocId) => void;
  onNavigate?: (route: string) => void;
}

export const Footer: React.FC<FooterProps> = React.memo(({
  onOpenVoices,
  onOpenPricing,
  onOpenDevelopers,
  onOpenLegal,
  onNavigate,
}) => {
  const handleLegalClick = (e: React.MouseEvent, docId: LegalDocId) => {
    e.preventDefault();
    onOpenLegal(docId);
    window.history.pushState({}, '', `/legal/${docId}`);
  };

  const handleNavClick = (e: React.MouseEvent, route: string) => {
    if (onNavigate) {
      e.preventDefault();
      onNavigate(route);
      window.history.pushState({}, '', `/${route === 'home' ? '' : route}`);
    } else if (route === 'voices') {
      e.preventDefault();
      onOpenVoices();
    }
  };

  return (
    <footer className="w-full bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl border-t border-slate-200/80 dark:border-slate-800 py-12 px-4 select-none mt-12 text-xs text-slate-500 dark:text-slate-400">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 lg:gap-12 pb-10 border-b border-slate-100 dark:border-slate-800/80">
        {/* Brand & Bio (Col 1-5) */}
        <div className="md:col-span-5 flex flex-col items-start gap-3">
          <a
            href="/"
            onClick={(e) => handleNavClick(e, 'home')}
            className="flex items-center gap-2"
          >
            <div className="w-8 h-8 rounded-full overflow-hidden shadow-xs flex items-center justify-center bg-blue-600">
              <img
                src="/logo-96.webp"
                alt="Kokoro Studio App Icon"
                width="32"
                height="32"
                loading="lazy"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </div>
            <span className="font-extrabold text-base text-slate-900 dark:text-white">
              Kokoro<span className="text-blue-600">Studio</span>
            </span>
          </a>

          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm leading-relaxed">
            High-performance AI text-to-speech studio powered by open-weights Kokoro-82M ONNX.
            Ultra-fast CPU inference, 60 international neural voices, studio mastering EQ, and synchronized subtitle export.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <a
              href="https://github.com/dilshan916/kokoro-mobile/releases/download/v1.0.0/kokoro-voice-studio-v1.0.0-universal.apk"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors text-xs font-semibold"
            >
              <Smartphone className="w-3.5 h-3.5 text-indigo-500" />
              <span>Download Mobile APK</span>
            </a>
            <a
              href="https://buymeacoffee.com/alphacreations"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 dark:text-amber-400 transition-colors text-xs font-semibold"
            >
              <Coffee className="w-3.5 h-3.5 text-amber-500" />
              <span>Buy Me a Coffee</span>
            </a>
            <a
              href={LEGAL_CONFIG.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors text-xs font-semibold"
            >
              <Github className="w-3.5 h-3.5" />
              <span>GitHub</span>
            </a>
          </div>
        </div>

        {/* Product Column (Col 6-7) */}
        <div className="md:col-span-2 flex flex-col gap-2.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-900 dark:text-white">
            Product &amp; Guides
          </span>
          <ul className="space-y-2 text-xs font-medium text-slate-600 dark:text-slate-400">
            <li>
              <a
                href="/"
                onClick={(e) => handleNavClick(e, 'home')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Text to Speech
              </a>
            </li>
            <li>
              <a
                href="/voices"
                onClick={(e) => handleNavClick(e, 'voices')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors inline-flex items-center gap-1"
              >
                <Mic className="w-3 h-3 text-indigo-500" />
                <span>60 AI Voices</span>
              </a>
            </li>
            <li>
              <a
                href="/guide"
                onClick={(e) => handleNavClick(e, 'guide')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors inline-flex items-center gap-1"
              >
                <BookOpen className="w-3 h-3 text-blue-500" />
                <span>Mastering Guide</span>
              </a>
            </li>
            <li>
              <button
                onClick={onOpenPricing}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Pricing &amp; Quota
              </button>
            </li>
            <li>
              <button
                onClick={onOpenDevelopers}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Developer API
              </button>
            </li>
          </ul>
        </div>

        {/* Legal Column (Col 8-10) */}
        <div className="md:col-span-3 flex flex-col gap-2.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-900 dark:text-white flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-blue-500" />
            <span>Legal &amp; Policies</span>
          </span>
          <ul className="space-y-2 text-xs font-medium text-slate-600 dark:text-slate-400">
            <li>
              <a
                href="/legal/privacy"
                onClick={(e) => handleLegalClick(e, 'privacy')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Privacy Policy
              </a>
            </li>
            <li>
              <a
                href="/legal/terms"
                onClick={(e) => handleLegalClick(e, 'terms')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Terms of Service
              </a>
            </li>
            <li>
              <a
                href="/legal/acceptable-use"
                onClick={(e) => handleLegalClick(e, 'acceptable-use')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Acceptable Use Policy
              </a>
            </li>
            <li>
              <a
                href="/legal/ai-policy"
                onClick={(e) => handleLegalClick(e, 'ai-policy')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                AI &amp; Voice Ethics Policy
              </a>
            </li>
            <li>
              <a
                href="/legal/cookies"
                onClick={(e) => handleLegalClick(e, 'cookies')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Cookie &amp; Storage Policy
              </a>
            </li>
            <li>
              <a
                href="/legal/dmca"
                onClick={(e) => handleLegalClick(e, 'dmca')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Copyright / DMCA
              </a>
            </li>
            <li>
              <a
                href="/legal/refunds"
                onClick={(e) => handleLegalClick(e, 'refunds')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Refund &amp; Cancellation
              </a>
            </li>
          </ul>
        </div>

        {/* Company Column (Col 11-12) */}
        <div className="md:col-span-2 flex flex-col gap-2.5">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-900 dark:text-white">
            Company
          </span>
          <ul className="space-y-2 text-xs font-medium text-slate-600 dark:text-slate-400">
            <li>
              <a
                href="/about"
                onClick={(e) => handleNavClick(e, 'about')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                About Us
              </a>
            </li>
            <li>
              <a
                href="/contact"
                onClick={(e) => handleNavClick(e, 'contact')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Contact &amp; Support
              </a>
            </li>
            <li>
              <a
                href={LEGAL_CONFIG.githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors inline-flex items-center gap-1"
              >
                <span>GitHub Project</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom Copyright */}
      <div className="max-w-6xl mx-auto pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-600 dark:text-slate-400">
        <div>
          &copy; {new Date().getFullYear()} {LEGAL_CONFIG.serviceName}. All rights reserved.
        </div>
        <div className="flex items-center gap-1">
          <span>Crafted with</span>
          <Heart className="w-3 h-3 text-rose-500 fill-current" />
          <span>by <a href="https://github.com/dilshan916" target="_blank" rel="noopener noreferrer" className="text-slate-600 dark:text-slate-300 font-semibold hover:underline">Dilshan Chandrarathne</a></span>
        </div>
      </div>
    </footer>
  );
});
export default Footer;
