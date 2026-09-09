import React from 'react';
import {
  X,
  Shield,
  FileText,
  AlertTriangle,
  Sparkles,
  Cookie,
  Scale,
  RefreshCw,
  Info,
  Mail,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { ALL_LEGAL_DOCS, LegalDocId } from '../legal/legalContent';

export type LegalTab = LegalDocId;

interface LegalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenDocument?: (docId: LegalDocId) => void;
  initialTab?: LegalDocId;
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

export const LegalModal: React.FC<LegalModalProps> = ({
  isOpen,
  onClose,
  onOpenDocument,
}) => {
  if (!isOpen) return null;

  const handleSelectDoc = (docId: LegalDocId) => {
    if (onOpenDocument) {
      onOpenDocument(docId);
    }
    onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/60 dark:bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-150 select-none"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-7 shadow-2xl space-y-6 max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-950/60 border border-blue-200/60 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-xs">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span>Legal &amp; Policy Center</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                  Overview
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Transparent legal compliance, on-premise AI privacy disclosures, and terms of service
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 9 Policy Overview Cards Grid */}
        <div className="overflow-y-auto flex-1 pr-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {ALL_LEGAL_DOCS.map((doc) => {
              const Icon = ICON_MAP[doc.iconName] || Shield;

              return (
                <div
                  key={doc.id}
                  onClick={() => handleSelectDoc(doc.id)}
                  className="group relative p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 hover:bg-blue-50/60 dark:hover:bg-blue-950/40 border border-slate-200/80 dark:border-slate-700/70 hover:border-blue-300 dark:hover:border-blue-800 transition-all cursor-pointer flex flex-col justify-between shadow-xs hover:shadow-md"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="w-8 h-8 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-105 transition-transform shadow-2xs">
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">
                        {doc.sections.length} sections
                      </span>
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {doc.title}
                      </h4>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed mt-1">
                        {doc.subtitle}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 mt-2 border-t border-slate-200/40 dark:border-slate-700/50 flex items-center justify-between text-xs font-semibold text-blue-600 dark:text-blue-400">
                    <span>Read full policy</span>
                    <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer Banner */}
        <div className="p-3.5 rounded-2xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
            <Shield className="w-4 h-4 text-emerald-500 shrink-0" />
            <span className="text-[11px]">
              Built with zero-login device identifiers &amp; on-premise Kokoro-82M neural inference.
            </span>
          </div>
          <button
            onClick={() => handleSelectDoc('privacy')}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors flex items-center gap-1.5 shrink-0 text-xs cursor-pointer shadow-xs"
          >
            <span>Open Dedicated Legal Center</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
export default LegalModal;
