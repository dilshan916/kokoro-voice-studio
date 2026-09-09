import React, { useState, useEffect } from 'react';
import { X, Server, Check, RefreshCw, Globe, Laptop } from 'lucide-react';
import { kokoroApi, DEFAULT_CLOUD_VPS_URL, LOCAL_DEV_URL } from '../api/kokoroApi';

interface ServerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onServerChanged: () => void;
}

export const ServerModal: React.FC<ServerModalProps> = ({ isOpen, onClose, onServerChanged }) => {
  const [customInput, setCustomInput] = useState(kokoroApi.getBaseUrl());
  const [isPinging, setIsPinging] = useState(false);
  const [pingResult, setPingResult] = useState<{ success: boolean; latencyMs?: number; error?: string } | null>(null);

  useEffect(() => {
    if (isOpen) {
      setCustomInput(kokoroApi.getBaseUrl());
      testPing(kokoroApi.getBaseUrl());
    }
  }, [isOpen]);

  const testPing = async (url: string) => {
    setIsPinging(true);
    setPingResult(null);
    try {
      const res = await kokoroApi.pingServer(url);
      setPingResult({ success: true, latencyMs: res.latencyMs });
    } catch (err: any) {
      setPingResult({ success: false, error: err.message || 'Connection failed' });
    } finally {
      setIsPinging(false);
    }
  };

  const handleSelectPreset = (url: string) => {
    setCustomInput(url);
    testPing(url);
  };

  const handleSave = () => {
    if (!customInput.trim()) return;
    kokoroApi.setBaseUrl(customInput.trim());
    onServerChanged();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-slate-900/60 dark:bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-in fade-in duration-150 select-none"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl p-6 shadow-2xl space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-700/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Backend Server Settings
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Configure TTS synthesis backend connection
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-700/60 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Live Status Card */}
        <div className="bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-4 flex items-center justify-between">
          <div className="space-y-1">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Connection Status
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  pingResult?.success
                    ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]'
                    : isPinging
                    ? 'bg-amber-400 animate-ping'
                    : 'bg-rose-500'
                }`}
              />
              <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                {isPinging ? 'Pinging...' : pingResult?.success ? 'Connected & Ready' : 'Disconnected'}
              </span>
              {pingResult?.latencyMs !== undefined && (
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold">
                  {pingResult.latencyMs} ms
                </span>
              )}
            </div>
          </div>

          <button
            onClick={() => testPing(customInput)}
            disabled={isPinging}
            className="px-3 py-1.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 text-xs text-slate-700 dark:text-slate-300 flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPinging ? 'animate-spin' : ''}`} />
            <span>Test Ping</span>
          </button>
        </div>

        {/* Server Presets */}
        <div className="space-y-2">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
            Quick Presets
          </label>
          <div className="space-y-2">
            <button
              onClick={() => handleSelectPreset(DEFAULT_CLOUD_VPS_URL)}
              className={`w-full p-3 rounded-2xl border text-left flex items-center justify-between text-xs transition-all cursor-pointer ${
                customInput === DEFAULT_CLOUD_VPS_URL
                  ? 'bg-blue-50/80 dark:bg-blue-950/40 border-blue-400 dark:border-blue-600'
                  : 'bg-slate-50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-700 hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Globe className="w-4 h-4 text-blue-500 shrink-0" />
                <div>
                  <div className="font-bold text-slate-800 dark:text-slate-200">
                    Oracle Cloud VPS (24/7 Global HTTPS)
                  </div>
                  <div className="text-[11px] text-slate-400 truncate max-w-xs sm:max-w-sm">
                    {DEFAULT_CLOUD_VPS_URL}
                  </div>
                </div>
              </div>
              {customInput === DEFAULT_CLOUD_VPS_URL && <Check className="w-4 h-4 text-blue-600" />}
            </button>

            <button
              onClick={() => handleSelectPreset(LOCAL_DEV_URL)}
              className={`w-full p-3 rounded-2xl border text-left flex items-center justify-between text-xs transition-all cursor-pointer ${
                customInput === LOCAL_DEV_URL
                  ? 'bg-blue-50/80 dark:bg-blue-950/40 border-blue-400 dark:border-blue-600'
                  : 'bg-slate-50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-700 hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Laptop className="w-4 h-4 text-blue-500 shrink-0" />
                <div>
                  <div className="font-bold text-slate-800 dark:text-slate-200">
                    Localhost (Desktop FastAPI)
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {LOCAL_DEV_URL}
                  </div>
                </div>
              </div>
              {customInput === LOCAL_DEV_URL && <Check className="w-4 h-4 text-blue-600" />}
            </button>
          </div>
        </div>

        {/* Custom URL Input */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
            Endpoint URL
          </label>
          <input
            type="text"
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            placeholder="https://your-server-url"
            className="w-full bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-2 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md shadow-blue-500/20 transition-colors cursor-pointer"
          >
            Save & Connect
          </button>
        </div>
      </div>
    </div>
  );
};
export default ServerModal;
