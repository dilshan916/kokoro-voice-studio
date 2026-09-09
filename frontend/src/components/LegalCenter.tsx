import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  ArrowLeft,
  Shield,
  FileText,
  AlertTriangle,
  Sparkles,
  Cookie,
  Scale,
  RefreshCw,
  Info,
  Mail,
  Search,
  X,
  ChevronRight,
  Sun,
  Moon,
  Calendar,
  Clock,
  ExternalLink,
  ChevronDown,
} from 'lucide-react';
import {
  ALL_LEGAL_DOCS,
  LegalDocId,
  LegalDocument,
  getLegalDoc,
  LEGAL_CONFIG,
} from '../legal/legalContent';

interface LegalCenterProps {
  initialDocId?: LegalDocId;
  onSelectDoc?: (id: LegalDocId) => void;
  onBackToStudio: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

const ICON_MAP = {
  Shield,
  FileText,
  AlertTriangle,
  Sparkles,
  Cookie,
  Scale,
  RefreshCw,
  Info,
  Mail,
};

export const LegalCenter: React.FC<LegalCenterProps> = ({
  initialDocId = 'privacy',
  onSelectDoc,
  onBackToStudio,
  isDarkMode,
  onToggleDarkMode,
}) => {
  const [activeDocId, setActiveDocId] = useState<LegalDocId>(initialDocId);
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const contentTopRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialDocId) {
      setActiveDocId(initialDocId);
    }
  }, [initialDocId]);

  const activeDoc: LegalDocument = useMemo(() => {
    return getLegalDoc(activeDocId) || ALL_LEGAL_DOCS[0];
  }, [activeDocId]);

  const handleDocChange = (docId: LegalDocId) => {
    setActiveDocId(docId);
    setSearchQuery('');
    setMobileMenuOpen(false);
    if (onSelectDoc) {
      onSelectDoc(docId);
    }
    // Smooth scroll to top of document content
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Filter sections by search query
  const filteredSections = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return activeDoc.sections;

    return activeDoc.sections.filter((section) => {
      const titleMatch = section.title.toLowerCase().includes(q);
      const contentMatch = section.content.some((paragraph) =>
        paragraph.toLowerCase().includes(q)
      );
      return titleMatch || contentMatch;
    });
  }, [activeDoc, searchQuery]);

  const CurrentDocIcon = ICON_MAP[activeDoc.iconName] || Shield;

  // Jump to specific section anchor
  const scrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Find next doc for bottom navigation
  const currentDocIndex = ALL_LEGAL_DOCS.findIndex((d) => d.id === activeDoc.id);
  const nextDoc = ALL_LEGAL_DOCS[(currentDocIndex + 1) % ALL_LEGAL_DOCS.length];

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#eaf3ff] via-[#e2edfc] to-[#d8e7fa] dark:from-[#0b0f19] dark:via-[#0e1322] dark:to-[#090d16] text-slate-900 dark:text-slate-100 font-sans transition-colors duration-200">
      {/* 1. Header Bar */}
      <header className="sticky top-0 z-40 w-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-slate-200/80 dark:border-slate-800 shadow-sm transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          {/* Left: Back & Brand */}
          <div className="flex items-center gap-3 sm:gap-4">
            <button
              onClick={onBackToStudio}
              className="group flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-blue-50 dark:hover:bg-blue-950/60 border border-slate-200/80 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:text-blue-600 dark:hover:text-blue-400 transition-all cursor-pointer shadow-xs"
              aria-label="Back to Studio"
            >
              <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-0.5" />
              <span>Back to Studio</span>
            </button>

            <div className="h-5 w-px bg-slate-200 dark:bg-slate-700 hidden sm:block" />

            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full overflow-hidden shadow-xs flex items-center justify-center bg-blue-600 shrink-0">
                <img
                  src="/favicon.png?v=round1"
                  alt="Kokoro Studio"
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
              </div>
              <div>
                <span className="font-extrabold text-sm sm:text-base tracking-tight text-slate-900 dark:text-white">
                  Kokoro<span className="text-blue-600">Studio</span>
                </span>
                <span className="ml-1.5 text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-md bg-blue-100 dark:bg-blue-950/80 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/80">
                  Legal Center
                </span>
              </div>
            </div>
          </div>

          {/* Right: Search & Theme Toggle */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Live Search Input */}
            <div className="relative hidden md:block w-64 lg:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder={`Search ${activeDoc.shortTitle}...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-8 py-1.5 bg-slate-100/90 dark:bg-slate-800/90 border border-slate-200/80 dark:border-slate-700/80 rounded-xl text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-md"
                  aria-label="Clear search"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Dark Mode Toggle */}
            <button
              onClick={onToggleDarkMode}
              className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              aria-label="Toggle theme"
            >
              {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Search Bar */}
        <div className="p-2 px-4 border-t border-slate-200/60 dark:border-slate-800 md:hidden bg-white/40 dark:bg-slate-900/40">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder={`Search ${activeDoc.shortTitle}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 bg-slate-100/90 dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                aria-label="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* 2. Main Content Area: Sidebar + Article */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-8" ref={contentTopRef}>
        {/* Mobile Dropdown Policy Selector */}
        <div className="lg:hidden mb-6">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="w-full p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between text-left"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <CurrentDocIcon className="w-4 h-4" />
              </div>
              <div>
                <span className="text-xs text-slate-400 block font-medium">Active Policy Document</span>
                <span className="text-sm font-bold text-slate-900 dark:text-white">{activeDoc.title}</span>
              </div>
            </div>
            <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${mobileMenuOpen ? 'rotate-180' : ''}`} />
          </button>

          {mobileMenuOpen && (
            <div className="mt-2 p-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl space-y-1 animate-in fade-in slide-in-from-top-2 duration-150">
              {ALL_LEGAL_DOCS.map((doc) => {
                const Icon = ICON_MAP[doc.iconName] || Shield;
                const isActive = doc.id === activeDoc.id;
                return (
                  <button
                    key={doc.id}
                    onClick={() => handleDocChange(doc.id)}
                    className={`w-full p-2.5 rounded-xl flex items-center justify-between text-left transition-all ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold border border-blue-200/60 dark:border-blue-800'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60 font-medium'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 shrink-0" />
                      <span className="text-xs">{doc.title}</span>
                    </div>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {doc.sections.length} sec
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* 3. Sticky Left Sidebar Navigation (Desktop) */}
          <aside className="hidden lg:block lg:col-span-4 sticky top-24 space-y-4">
            <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border border-slate-200/80 dark:border-slate-800/90 rounded-3xl p-4 shadow-sm space-y-2">
              <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                  Legal &amp; Company Policies
                </span>
              </div>

              <nav className="space-y-1" aria-label="Legal documents">
                {ALL_LEGAL_DOCS.map((doc) => {
                  const Icon = ICON_MAP[doc.iconName] || Shield;
                  const isActive = doc.id === activeDoc.id;

                  return (
                    <button
                      key={doc.id}
                      onClick={() => handleDocChange(doc.id)}
                      className={`w-full p-2.5 px-3 rounded-2xl flex items-center justify-between text-left transition-all group cursor-pointer ${
                        isActive
                          ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20 font-bold'
                          : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/70 font-medium'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
                            isActive
                              ? 'bg-white/20 text-white'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400'
                          }`}
                        >
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                        <span className="text-xs truncate">{doc.title}</span>
                      </div>
                      <span
                        className={`text-[10px] font-mono shrink-0 px-2 py-0.5 rounded-full ${
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-400'
                        }`}
                      >
                        {doc.sections.length}
                      </span>
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Quick Summary Card */}
            <div className="p-4 rounded-3xl bg-blue-50/60 dark:bg-blue-950/20 border border-blue-200/50 dark:border-blue-900/40 text-xs space-y-2 text-slate-600 dark:text-slate-300">
              <div className="flex items-center gap-2 font-bold text-blue-900 dark:text-blue-300">
                <Shield className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span>Zero-Login Privacy Guarantee</span>
              </div>
              <p className="text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">
                Speech synthesis is processed on-premise using the Kokoro-82M model without transmitting your text to third-party AI APIs.
              </p>
            </div>
          </aside>

          {/* 4. Main Article & Sections Content Area */}
          <main className="lg:col-span-8 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200/80 dark:border-slate-800 rounded-3xl p-6 sm:p-10 shadow-sm space-y-8">
            {/* Document Header */}
            <header className="border-b border-slate-100 dark:border-slate-800 pb-6 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200/60 dark:border-blue-800 text-xs font-semibold">
                  <CurrentDocIcon className="w-3.5 h-3.5" />
                  <span>{activeDoc.shortTitle}</span>
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500 font-mono">
                  <Clock className="w-3 h-3" />
                  <span>Last Updated: {activeDoc.lastUpdated}</span>
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500 font-mono">
                  <Calendar className="w-3 h-3" />
                  <span>Effective: {activeDoc.effectiveDate}</span>
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {activeDoc.title}
              </h1>

              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl">
                {activeDoc.subtitle}
              </p>
            </header>

            {/* Quick Table of Contents Jump Pills */}
            {!searchQuery && activeDoc.sections.length > 2 && (
              <div className="space-y-2 pt-1 pb-3">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 block">
                  Table of Contents
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {activeDoc.sections.map((section) => (
                    <button
                      key={section.id}
                      onClick={() => scrollToSection(section.id)}
                      className="text-[11px] font-medium px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-950/50 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
                    >
                      {section.title.split('.')[0] || section.id}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Search Match Notice */}
            {searchQuery && (
              <div className="p-3 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/80 flex items-center justify-between text-xs text-amber-800 dark:text-amber-300">
                <span>
                  Showing <strong>{filteredSections.length}</strong> matching section{filteredSections.length !== 1 ? 's' : ''} for "{searchQuery}"
                </span>
                <button
                  onClick={() => setSearchQuery('')}
                  className="font-bold underline hover:opacity-80 cursor-pointer"
                >
                  Reset Filter
                </button>
              </div>
            )}

            {/* Sections Article Body */}
            <article className="space-y-8 divide-y divide-slate-100 dark:divide-slate-800/60">
              {filteredSections.length === 0 ? (
                <div className="py-12 text-center space-y-3">
                  <Search className="w-8 h-8 text-slate-400 mx-auto" />
                  <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">No matching sections found</h3>
                  <p className="text-xs text-slate-400 max-w-sm mx-auto">
                    Try searching for another keyword like "data", "audio", "device", or "commercial".
                  </p>
                  <button
                    onClick={() => setSearchQuery('')}
                    className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors"
                  >
                    Clear Search
                  </button>
                </div>
              ) : (
                filteredSections.map((section, idx) => (
                  <section
                    key={section.id}
                    id={section.id}
                    className={`space-y-3 scroll-mt-24 ${idx > 0 ? 'pt-8' : ''}`}
                  >
                    <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <span>{section.title}</span>
                    </h2>

                    <div className="space-y-3 text-xs sm:text-[13px] leading-relaxed text-slate-600 dark:text-slate-300">
                      {section.content.map((paragraph, pIdx) => {
                        // Custom styling for bullet lines
                        if (paragraph.startsWith('•') || paragraph.startsWith('- ')) {
                          return (
                            <div key={pIdx} className="flex items-start gap-2 pl-2">
                              <span className="text-blue-500 font-bold shrink-0 mt-0.5">•</span>
                              <p className="flex-1">{paragraph.replace(/^[•\-]\s*/, '')}</p>
                            </div>
                          );
                        }

                        // Highlight configure placeholders
                        if (paragraph.includes('[CONFIGURE:')) {
                          return (
                            <p key={pIdx} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 font-mono text-xs text-slate-800 dark:text-slate-200">
                              {paragraph}
                            </p>
                          );
                        }

                        return <p key={pIdx}>{paragraph}</p>;
                      })}
                    </div>
                  </section>
                ))
              )}
            </article>

            {/* Bottom Next Document Banner */}
            <div className="pt-8 border-t border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <span className="text-[11px] text-slate-400 block font-medium">Continue Reading</span>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  {nextDoc.title}
                </span>
              </div>
              <button
                onClick={() => handleDocChange(nextDoc.id)}
                className="group flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-50 dark:bg-blue-950/60 hover:bg-blue-600 text-blue-600 dark:text-blue-400 hover:text-white border border-blue-200 dark:border-blue-800 text-xs font-semibold transition-all cursor-pointer"
              >
                <span>Read {nextDoc.shortTitle}</span>
                <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </button>
            </div>
          </main>
        </div>
      </div>

      {/* 5. Minimal Footer */}
      <footer className="w-full bg-white/60 dark:bg-slate-900/60 backdrop-blur-xl border-t border-slate-200/80 dark:border-slate-800 py-8 px-4 mt-auto text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-[11px]">
            <span>&copy; {new Date().getFullYear()} {LEGAL_CONFIG.serviceName}. All rights reserved.</span>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 text-[11px] font-medium text-slate-600 dark:text-slate-400">
            {ALL_LEGAL_DOCS.slice(0, 6).map((d) => (
              <button
                key={d.id}
                onClick={() => handleDocChange(d.id)}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
              >
                {d.shortTitle}
              </button>
            ))}
            <a
              href={LEGAL_CONFIG.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-900 dark:hover:text-white flex items-center gap-1"
            >
              <span>GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default LegalCenter;
