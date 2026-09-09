import React, { useState, useRef, useEffect } from 'react';
import { Sun, Moon, Server, Smartphone, Terminal, Menu } from 'lucide-react';
import { HealthData, UserQuota } from '../types';

interface NavbarProps {
  health: HealthData | null;
  quota: UserQuota | null;
  onOpenVoices: () => void;
  onOpenPricing: () => void;
  onOpenDevelopers: () => void;
  onOpenServer: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  quota,
  onOpenVoices,
  onOpenPricing,
  onOpenDevelopers,
  onOpenServer,
  isDarkMode,
  onToggleDarkMode,
}) => {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const isOnline = health?.status === 'ready';
  const isPro = quota?.tier === 'pro';

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-blue-100/60 dark:border-slate-800 select-none">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Left: Brand Logo & Title */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full overflow-hidden shadow-md shadow-blue-500/20 flex items-center justify-center">
            <img src="/favicon.png?v=round1" alt="Kokoro Studio App Icon" className="w-full h-full object-cover" />
          </div>
          <span className="font-extrabold text-lg tracking-tight text-slate-900 dark:text-white font-sans">
            Kokoro<span className="text-blue-600 font-bold ml-0.5">Studio</span>
          </span>
        </div>

        {/* Center: Clean Nav Links (Home, Voices, Pricing - NO API/Docs) */}
        <nav className="hidden sm:flex items-center gap-8 text-sm font-medium text-slate-600 dark:text-slate-300">
          <a
            href="#home"
            className="text-slate-900 dark:text-white font-semibold hover:text-blue-600 transition-colors"
          >
            Home
          </a>
          <button
            onClick={onOpenVoices}
            className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
          >
            Voices
          </button>
          <button
            onClick={onOpenPricing}
            className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <span>Pricing</span>
            {isPro && (
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-600 dark:text-amber-400 font-bold">
                PRO
              </span>
            )}
          </button>
          <button
            onClick={onOpenDevelopers}
            className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <Terminal className="w-3.5 h-3.5 text-blue-500" />
            <span>API</span>
          </button>
          <a
            href="https://github.com/dilshan916/kokoro-mobile/releases/download/v1.0.0/kokoro-voice-studio-v1.0.0-universal.apk"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors flex items-center gap-1.5"
            title="Download Android Mobile APK"
          >
            <Smartphone className="w-3.5 h-3.5 text-indigo-500" />
            <span>Mobile App</span>
          </a>
        </nav>

        {/* Right: Theme Toggle & User Avatar Dropdown */}
        <div className="flex items-center gap-3">
          {/* Light / Dark Mode Toggle */}
          <button
            onClick={onToggleDarkMode}
            className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center transition-colors cursor-pointer shadow-sm"
            title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>

          {/* Three-Line Menu Dropdown */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white flex items-center justify-center transition-all cursor-pointer shadow-sm relative"
              title="Menu"
              aria-label="Toggle menu"
            >
              <Menu className="w-4 h-4 text-white" />
              {/* Online Status Dot */}
              <span
                className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white dark:border-slate-900 ${
                  isOnline ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
                title={isOnline ? 'Online' : 'Offline'}
              />
            </button>

            {/* Dropdown Menu */}
            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl p-3 space-y-2 z-50 text-xs animate-in fade-in slide-in-from-top-2 duration-150">
                {/* Quota Summary */}
                <div
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    onOpenPricing();
                  }}
                  className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 hover:bg-blue-50/60 dark:hover:bg-blue-950/30 border border-slate-200/60 dark:border-slate-700/60 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between font-bold text-slate-800 dark:text-slate-200 mb-1">
                    <span>Account Plan</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                        isPro
                          ? 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                          : 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
                      }`}
                    >
                      {isPro ? '⭐ PRO Unlimited' : 'Free Tier'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    {isPro
                      ? 'Enjoy unlimited speech generations'
                      : `${quota?.monthly_usage || 0} / 20,000 characters used`}
                  </div>
                </div>

                {/* Developer API & Keys */}
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    onOpenDevelopers();
                  }}
                  className="w-full p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 text-left flex items-center justify-between text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    <Terminal className="w-3.5 h-3.5 text-blue-500" />
                    Developer API &amp; Keys
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-md font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                    REST API
                  </span>
                </button>

                {/* Server Status & Settings */}
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    onOpenServer();
                  }}
                  className="w-full p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 text-left flex items-center justify-between text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
                >
                  <span className="flex items-center gap-2">
                    <Server className="w-3.5 h-3.5 text-blue-500" />
                    Server Connection
                  </span>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-md font-semibold ${
                      isOnline
                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                        : 'bg-rose-500/10 text-rose-500'
                    }`}
                  >
                    {isOnline ? 'Online' : 'Offline'}
                  </span>
                </button>

                {/* Mobile App Download */}
                <a
                  href="https://github.com/dilshan916/kokoro-mobile/releases/download/v1.0.0/kokoro-voice-studio-v1.0.0-universal.apk"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 text-left flex items-center gap-2 text-slate-700 dark:text-slate-200 transition-colors"
                >
                  <Smartphone className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Download Mobile APK</span>
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
export default Navbar;
