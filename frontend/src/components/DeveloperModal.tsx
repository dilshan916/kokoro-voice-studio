import React, { useState, useEffect } from 'react';
import {
  X,
  Key,
  Terminal,
  Copy,
  Check,
  Trash2,
  Plus,
  ShieldCheck,
  Sparkles,
  Layers,
  Search,
  ExternalLink,
  Code2,
} from 'lucide-react';
import { kokoroApi } from '../api/kokoroApi';
import { ApiKeyItem, Voice, UserQuota } from '../types';

interface DeveloperModalProps {
  isOpen: boolean;
  onClose: () => void;
  voices: Voice[];
  quota: UserQuota | null;
  onOpenPricing: () => void;
}

export const DeveloperModal: React.FC<DeveloperModalProps> = ({
  isOpen,
  onClose,
  voices,
  quota,
  onOpenPricing,
}) => {
  const [activeTab, setActiveTab] = useState<'keys' | 'code' | 'voices'>('keys');
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [isLoadingKeys, setIsLoadingKeys] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [isCreatingKey, setIsCreatingKey] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);
  const [copiedCodeSnippet, setCopiedCodeSnippet] = useState(false);
  const [codeLanguage, setCodeLanguage] = useState<'python_openai' | 'curl' | 'node_openai' | 'python_requests'>('python_openai');
  const [voiceSearch, setVoiceSearch] = useState('');
  const [copiedVoiceId, setCopiedVoiceId] = useState<string | null>(null);
  const [keyError, setKeyError] = useState<string | null>(null);

  const baseUrl = kokoroApi.getBaseUrl();
  const apiEndpoint = `${baseUrl}/v1/audio/speech`;

  const isFreePlan = quota?.tier !== 'pro';
  const isKeyLimitReached = isFreePlan && keys.length >= 1;

  // Fetch keys when modal opens
  useEffect(() => {
    if (isOpen) {
      setKeyError(null);
      loadKeys();
    } else {
      setNewlyCreatedKey(null);
      setKeyError(null);
    }
  }, [isOpen]);

  const loadKeys = async () => {
    setIsLoadingKeys(true);
    try {
      const res = await kokoroApi.getDeveloperKeys();
      setKeys(res.keys || []);
    } catch (err) {
      console.warn('Failed to load API keys:', err);
    } finally {
      setIsLoadingKeys(false);
    }
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setKeyError(null);
    if (isCreatingKey || isKeyLimitReached) return;
    setIsCreatingKey(true);
    try {
      const res = await kokoroApi.createDeveloperKey(newKeyName.trim() || 'Default API Key');
      setNewlyCreatedKey(res.api_key);
      setNewKeyName('');
      await loadKeys();
    } catch (err: any) {
      console.error('Failed to create key:', err);
      const msg =
        err?.response?.data?.detail?.error?.message ||
        err?.response?.data?.detail?.message ||
        err?.response?.data?.detail ||
        'Failed to generate API key.';
      setKeyError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsCreatingKey(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!window.confirm('Are you sure you want to revoke this API key? Applications using it will stop working immediately.')) {
      return;
    }
    try {
      await kokoroApi.revokeDeveloperKey(keyId);
      await loadKeys();
    } catch (err) {
      console.error('Failed to revoke key:', err);
    }
  };

  const copyToClipboard = (text: string, id: string, isSnippet = false) => {
    navigator.clipboard.writeText(text);
    if (isSnippet) {
      setCopiedCodeSnippet(true);
      setTimeout(() => setCopiedCodeSnippet(false), 2000);
    } else {
      setCopiedKeyId(id);
      setTimeout(() => setCopiedKeyId(null), 2000);
    }
  };

  const copyVoiceId = (vid: string) => {
    navigator.clipboard.writeText(vid);
    setCopiedVoiceId(vid);
    setTimeout(() => setCopiedVoiceId(null), 2000);
  };

  if (!isOpen) return null;

  // Active key or placeholder
  const activeToken = newlyCreatedKey || (keys.length > 0 ? keys[0].api_key : 'sk_live_kokoro_your_key_here');

  // Code snippets generator
  const getCodeSnippet = () => {
    switch (codeLanguage) {
      case 'python_openai':
        return `from openai import OpenAI

# 1. Initialize official OpenAI SDK with your Kokoro Studio base_url
client = OpenAI(
    base_url="${baseUrl}/v1",
    api_key="${activeToken}",
)

# 2. Synthesize speech with neural audio model
response = client.audio.speech.create(
    model="kokoro",
    voice="af_bella",  # Choose from 60 Kokoro neural voices
    input="Hello! Generating ultra-realistic speech with Kokoro Voice Studio.",
    response_format="mp3",
    speed=1.0,
)

# 3. Save directly to file
response.stream_to_file("output.mp3")
print("Audio saved successfully to output.mp3!")`;

      case 'curl':
        return `curl -X POST "${apiEndpoint}" \\
  -H "Authorization: Bearer ${activeToken}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "kokoro",
    "voice": "af_bella",
    "input": "Ultra-fast neural speech synthesis with Kokoro Voice Studio.",
    "response_format": "mp3",
    "speed": 1.0
  }' \\
  --output speech.mp3`;

      case 'node_openai':
        return `import OpenAI from "openai";
import fs from "fs";

const openai = new OpenAI({
  baseURL: "${baseUrl}/v1",
  apiKey: "${activeToken}",
});

async function main() {
  const mp3 = await openai.audio.speech.create({
    model: "kokoro",
    voice: "af_bella",
    input: "Kokoro Studio API delivers studio-quality audio with sub-second latency.",
    response_format: "mp3",
  });

  const buffer = Buffer.from(await mp3.arrayBuffer());
  await fs.promises.writeFile("output.mp3", buffer);
  console.log("Audio generated and written to output.mp3");
}

main();`;

      case 'python_requests':
        return `import requests

url = "${apiEndpoint}"
headers = {
    "Authorization": "Bearer ${activeToken}",
    "Content-Type": "application/json",
}
payload = {
    "model": "kokoro",
    "voice": "af_bella",
    "input": "Generating high-retention audio with Kokoro API.",
    "response_format": "mp3",
    "speed": 1.0,
}

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    with open("speech.mp3", "wb") as f:
        f.write(response.content)
    print("Downloaded speech.mp3 successfully!")
else:
    print("Error:", response.status_code, response.text)`;
    }
  };

  const filteredVoices = voices.filter(
    (v) =>
      v.id.toLowerCase().includes(voiceSearch.toLowerCase()) ||
      v.name.toLowerCase().includes(voiceSearch.toLowerCase()) ||
      v.lang_name.toLowerCase().includes(voiceSearch.toLowerCase())
  );

  return (
    <div
      className="fixed inset-0 bg-slate-900/60 dark:bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-150 select-none"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 sm:p-7 shadow-2xl space-y-6 max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-blue-50 dark:bg-blue-950/60 border border-blue-200/60 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-blue-400 shadow-sm">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">Developer Platform &amp; API</h3>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  OpenAI Compatible
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Ultra-fast, studio-grade neural speech synthesis and developer REST API.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800/80 rounded-2xl border border-slate-200/60 dark:border-slate-700/50 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('keys')}
            className={`flex-1 py-2 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-all ${
              activeTab === 'keys'
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>API Keys</span>
          </button>
          <button
            onClick={() => setActiveTab('code')}
            className={`flex-1 py-2 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-all ${
              activeTab === 'code'
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Quickstart &amp; SDKs</span>
          </button>
          <button
            onClick={() => setActiveTab('voices')}
            className={`flex-1 py-2 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-all ${
              activeTab === 'voices'
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Voice Catalog (60)</span>
          </button>
        </div>

        {/* Tab Content Container */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-1">
          {/* TAB 1: API KEYS */}
          {activeTab === 'keys' && (
            <div className="space-y-6">
              {/* Newly Created Key Banner (Shown only once) */}
              {newlyCreatedKey && (
                <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/80 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-bold text-sm">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Your New API Key Has Been Created!</span>
                  </div>
                  <p className="text-xs text-emerald-700 dark:text-emerald-400">
                    Copy this key now. For your security, you will not be able to view the full secret key again.
                  </p>
                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="text"
                      readOnly
                      value={newlyCreatedKey}
                      className="flex-1 text-xs font-mono bg-white dark:bg-slate-900 border border-emerald-300 dark:border-emerald-700 rounded-xl px-3 py-2 text-slate-800 dark:text-slate-200 select-all"
                    />
                    <button
                      onClick={() => copyToClipboard(newlyCreatedKey, 'new_key')}
                      className="flex items-center gap-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold transition-all shrink-0"
                    >
                      {copiedKeyId === 'new_key' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedKeyId === 'new_key' ? 'Copied!' : 'Copy Key'}</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Quota & Usage Overview */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 space-y-1">
                  <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Current Plan</span>
                  <div className="flex items-center justify-between">
                    <span className="text-base font-extrabold uppercase text-slate-900 dark:text-white">
                      {quota?.tier === 'pro' ? 'Pro Unlimited' : 'Free Tier'}
                    </span>
                    {quota?.tier === 'pro' ? (
                      <span className="p-1 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
                        <Sparkles className="w-4 h-4" />
                      </span>
                    ) : (
                      <button
                        onClick={onOpenPricing}
                        className="text-[11px] font-bold text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        Upgrade
                      </button>
                    )}
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 space-y-1">
                  <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Monthly Usage</span>
                  <div className="text-base font-extrabold text-slate-900 dark:text-white">
                    {quota?.monthly_usage?.toLocaleString() || 0}{' '}
                    <span className="text-xs font-normal text-slate-400">characters</span>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 space-y-1">
                  <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Remaining Balance</span>
                  <div className="text-base font-extrabold text-slate-900 dark:text-white">
                    {quota?.tier === 'pro'
                      ? 'Unlimited'
                      : `${((quota?.monthly_limit || 30000) - (quota?.monthly_usage || 0)).toLocaleString()} chars`}
                  </div>
                </div>
              </div>

              {/* Error Banner */}
              {keyError && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-between gap-2 text-xs text-red-700 dark:text-red-400">
                  <span>{keyError}</span>
                  <button onClick={() => setKeyError(null)} className="text-xs font-bold hover:underline shrink-0">Dismiss</button>
                </div>
              )}

              {/* Create Key Form */}
              <form onSubmit={handleCreateKey} className="flex flex-col sm:flex-row gap-2">
                <input
                  type="text"
                  placeholder={
                    isKeyLimitReached
                      ? "Limit reached (1/1 active key on Free plan)"
                      : "Key name (e.g. Production Voice Bot, Discord App, Local Dev)"
                  }
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  disabled={isCreatingKey || isKeyLimitReached}
                  className="flex-1 px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
                />
                <button
                  type="submit"
                  disabled={isCreatingKey || isKeyLimitReached}
                  className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-sm shrink-0 ${
                    isKeyLimitReached
                      ? 'bg-slate-200 dark:bg-slate-700/80 text-slate-400 dark:text-slate-500 cursor-not-allowed border border-slate-300/50 dark:border-slate-600/50'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  <Plus className="w-4 h-4" />
                  <span>
                    {isCreatingKey
                      ? 'Generating...'
                      : isKeyLimitReached
                      ? '1/1 Key Limit (Free)'
                      : 'Create New Secret Key'}
                  </span>
                </button>
              </form>

              {/* Active Keys List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-600 dark:text-slate-300">
                  <span>Your Secret API Keys</span>
                  <span>
                    {keys.length} Active Key{keys.length === 1 ? '' : 's'}
                    {isFreePlan && ' (1 Max on Free)'}
                  </span>
                </div>

                {isLoadingKeys ? (
                  <div className="text-center py-8 text-xs text-slate-400">Loading your API keys...</div>
                ) : keys.length === 0 ? (
                  <div className="text-center py-10 bg-slate-50 dark:bg-slate-800/40 rounded-2xl border border-dashed border-slate-200 dark:border-slate-700/60 p-6 space-y-2">
                    <Key className="w-8 h-8 mx-auto text-slate-400" />
                    <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">No API keys generated yet</p>
                    <p className="text-[11px] text-slate-400 max-w-sm mx-auto">
                      Create your first secret key above to start using Kokoro TTS in your apps, chatbots, or backend workflows.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {keys.map((k) => (
                      <div
                        key={k.key_id}
                        className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-900 dark:text-white">{k.name}</span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                              {k.masked_key}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center gap-3">
                            <span>Created: {new Date(k.created_at).toLocaleDateString()}</span>
                            <span>•</span>
                            <span>Spent this month: {k.monthly_usage.toLocaleString()} chars</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 self-end sm:self-center">
                          <button
                            onClick={() => copyToClipboard(k.api_key, k.key_id)}
                            className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-xl transition-all"
                            title="Copy Key Token"
                          >
                            {copiedKeyId === k.key_id ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                          </button>
                          <button
                            onClick={() => handleRevokeKey(k.key_id)}
                            className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-xl transition-all"
                            title="Revoke Key"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: CODE SNIPPETS & OPENAI COMPATIBILITY */}
          {activeTab === 'code' && (
            <div className="space-y-4">
              {/* Highlight Box */}
              <div className="p-4 rounded-2xl bg-blue-50/80 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/80 flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                <div className="space-y-1 text-xs">
                  <span className="font-bold text-blue-900 dark:text-blue-200">
                    High-Performance Speech API
                  </span>
                  <p className="text-blue-700 dark:text-blue-300">
                    Easily integrate with existing applications and AI agent frameworks (LangChain, AutoGen, CrewAI, Botpress). Simply point <code className="bg-blue-100 dark:bg-blue-900/60 px-1 py-0.5 rounded font-mono text-[11px]">base_url</code> to Kokoro Studio to get 60 ultra-realistic voices with high retention.
                  </p>
                </div>
              </div>

              {/* Language Selector */}
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => setCodeLanguage('python_openai')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    codeLanguage === 'python_openai'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                  }`}
                >
                  Python (OpenAI SDK)
                </button>
                <button
                  onClick={() => setCodeLanguage('curl')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    codeLanguage === 'curl'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                  }`}
                >
                  cURL
                </button>
                <button
                  onClick={() => setCodeLanguage('node_openai')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    codeLanguage === 'node_openai'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                  }`}
                >
                  Node.js (OpenAI SDK)
                </button>
                <button
                  onClick={() => setCodeLanguage('python_requests')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    codeLanguage === 'python_requests'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                  }`}
                >
                  Python (Requests)
                </button>
              </div>

              {/* Code Snippet Box */}
              <div className="relative rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden group">
                <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 text-xs text-slate-400 font-mono">
                  <span>POST /v1/audio/speech</span>
                  <button
                    onClick={() => copyToClipboard(getCodeSnippet(), 'snippet', true)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] transition-colors"
                  >
                    {copiedCodeSnippet ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedCodeSnippet ? 'Copied!' : 'Copy Code'}</span>
                  </button>
                </div>
                <pre className="p-4 text-xs font-mono text-slate-200 overflow-x-auto leading-relaxed">
                  <code>{getCodeSnippet()}</code>
                </pre>
              </div>

              {/* Rate Limits & Anti-DDoS Policy Card */}
              <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 text-xs space-y-1.5">
                <div className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-blue-500" />
                  <span>Rate Limits & Anti-DDoS Protection</span>
                </div>
                <div className="space-y-1 text-[11px] text-slate-600 dark:text-slate-400">
                  <p>
                    • <strong className="text-slate-800 dark:text-slate-200">Free Tier:</strong> Maximum 1 active API key, 1 concurrent request, and an enforced 5-second anti-DDoS pacing delay between calls.
                  </p>
                  <p>
                    • <strong className="text-slate-800 dark:text-slate-200">Pro Unlimited:</strong> Unlimited API keys, high-speed concurrent generation, and 0-second delay.
                  </p>
                </div>
              </div>

              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Interactive Swagger documentation is available at:</span>
                <a
                  href={`${baseUrl}/docs`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-bold text-blue-500 hover:underline flex items-center gap-1"
                >
                  <span>{baseUrl}/docs</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          )}

          {/* TAB 3: VOICE CATALOG */}
          {activeTab === 'voices' && (
            <div className="space-y-4">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by voice name, ID (e.g. af_bella, jf_alpha), or language..."
                  value={voiceSearch}
                  onChange={(e) => setVoiceSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[420px] overflow-y-auto pr-1">
                {filteredVoices.map((v) => (
                  <div
                    key={v.id}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/60 flex items-center justify-between gap-2"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span className="text-lg shrink-0">{v.flag}</span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-slate-900 dark:text-white truncate">{v.name}</span>
                          <span className="text-[10px] text-slate-400 shrink-0">({v.gender})</span>
                        </div>
                        <span className="text-[11px] font-mono text-blue-600 dark:text-blue-400 block truncate">
                          {v.id}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => copyVoiceId(v.id)}
                      className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-xl transition-colors shrink-0"
                      title="Copy Voice ID"
                    >
                      {copiedVoiceId === v.id ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
