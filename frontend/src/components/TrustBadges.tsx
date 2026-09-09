import React from 'react';
import { Zap, ShieldCheck, Cloud } from 'lucide-react';

export const TrustBadges: React.FC = () => {
  return (
    <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 py-6 text-xs text-slate-500 dark:text-slate-400 select-none">
      <div className="flex items-center gap-2">
        <Zap className="w-4 h-4 text-blue-500" />
        <span className="font-medium">High Quality Audio</span>
      </div>

      <div className="h-3 w-px bg-slate-200 dark:bg-slate-700 hidden sm:block" />

      <div className="flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-500" />
        <span className="font-medium">100% Safe & Secure</span>
      </div>

      <div className="h-3 w-px bg-slate-200 dark:bg-slate-700 hidden sm:block" />

      <div className="flex items-center gap-2">
        <Cloud className="w-4 h-4 text-blue-400" />
        <span className="font-medium">No Installation Required</span>
      </div>
    </div>
  );
};
export default TrustBadges;
