import React from 'react';
import { Github, Smartphone, Heart, Shield, ExternalLink } from 'lucide-react';
import { LegalDocId, LEGAL_CONFIG } from '../legal/legalConfig';

interface FooterProps {
  onOpenVoices: () => void;
  onOpenPricing: () => void;
  onOpenDevelopers: () => void;
  onOpenLegal: (docId: LegalDocId) => void;
}

export const Footer: React.FC<FooterProps> = React.memo(({
  onOpenVoices,
  onOpenPricing,
  onOpenDevelopers,
  onOpenLegal,
}) => {
  return (
    <footer className="w-full bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl border-t border-slate-200/80 dark:border-slate-800 py-12 px-4 select-none mt-12 text-xs text-slate-500 dark:text-slate-400">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 lg:gap-12 pb-10 border-b border-slate-100 dark:border-slate-800/80">
        {/* Brand & Bio (Col 1-5) */}
        <div className="md:col-span-5 flex flex-col items-start gap-3">
          <div className="flex items-center gap-2">
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
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm leading-relaxed">
            High-performance AI text-to-speech studio powered by open-weights Kokoro-82M ONNX.
            Ultra-fast CPU inference, 60 international neural voices, studio mastering EQ, and synchronized subtitle export.
          </p>

          <div className="flex items-center gap-3 pt-1">
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
            Product
          </span>
          <ul className="space-y-2 text-xs font-medium text-slate-600 dark:text-slate-400">
            <li>
              <a href="#home" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                Text to Speech
              </a>
            </li>
            <li>
              <button
                onClick={onOpenVoices}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                60 AI Voices
              </button>
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
              <button
                onClick={() => onOpenLegal('privacy')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Privacy Policy
              </button>
            </li>
            <li>
              <button
                onClick={() => onOpenLegal('terms')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Terms of Service
              </button>
            </li>
            <li>
              <button
                onClick={() => onOpenLegal('acceptable-use')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Acceptable Use Policy
              </button>
            </li>
            <li>
              <button
                onClick={() => onOpenLegal('ai-policy')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                AI &amp; Voice Ethics Policy
              </button>
            </li>
            <li>
              <button
                onClick={() => onOpenLegal('cookies')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Cookie &amp; Storage Policy
              </button>
            </li>
            <li>
              <button
                onClick={() => onOpenLegal('dmca')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Copyright / DMCA
              </button>
            </li>
            <li>
              <button
                onClick={() => onOpenLegal('refunds')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Refund &amp; Cancellation
              </button>
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
              <button
                onClick={() => onOpenLegal('about')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                About Us
              </button>
            </li>
            <li>
              <button
                onClick={() => onOpenLegal('contact')}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer text-left"
              >
                Contact Us
              </button>
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
