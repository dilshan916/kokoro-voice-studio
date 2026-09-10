import axios from 'axios';
import { HealthData, RenderRequest, RenderResponse, UserQuota, Voice } from '../types';

export const DEFAULT_CLOUD_VPS_URL = 'https://saytts.site';
export const LOCAL_DEV_URL = 'http://127.0.0.1:8000';

/**
 * Resolve active API Base URL:
 * 1. User manual override in localStorage ('kokoro_api_url')
 * 2. If app is hosted directly on VPS or localhost:8000, use window.location.origin
 * 3. Default to public HTTPS domain
 */
export function getApiBaseUrl(): string {
  if (typeof window === 'undefined') return DEFAULT_CLOUD_VPS_URL;

  const stored = localStorage.getItem('kokoro_api_url');
  if (stored && stored.trim()) {
    return stored.trim().replace(/\/+$/, '');
  }

  const origin = window.location.origin || '';
  if (
    origin.includes('saytts.site') ||
    origin.includes('trycloudflare.com') ||
    origin.includes('161.118.193.63') ||
    origin.includes(':8000')
  ) {
    return origin.replace(/\/+$/, '');
  }

  return DEFAULT_CLOUD_VPS_URL;
}

/**
 * Retrieve or generate persistent anonymous Device ID for zero-login quota management.
 */
export function getDeviceId(): string {
  if (typeof window === 'undefined') return 'dev_server';

  let devId = localStorage.getItem('kokoro_device_id');
  if (!devId) {
    const randomHex = Array.from(crypto.getRandomValues(new Uint8Array(8)))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    devId = `dev_web_${randomHex}`;
    localStorage.setItem('kokoro_device_id', devId);
  }
  return devId;
}

const apiClient = axios.create({
  timeout: 600000, // 10 minutes for long multi-speaker scripts
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically inject current API Base URL and Device ID on every request
apiClient.interceptors.request.use((config) => {
  config.baseURL = getApiBaseUrl();
  config.headers['X-Device-Id'] = getDeviceId();
  return config;
});

export const kokoroApi = {
  getBaseUrl(): string {
    return getApiBaseUrl();
  },

  setBaseUrl(newUrl: string): void {
    if (typeof window !== 'undefined') {
      const cleanUrl = newUrl.trim().replace(/\/+$/, '');
      localStorage.setItem('kokoro_api_url', cleanUrl);
    }
  },

  resetBaseUrl(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('kokoro_api_url');
    }
  },

  getDeviceId(): string {
    return getDeviceId();
  },

  /**
   * Test connection to an arbitrary backend URL and return response latency in ms.
   */
  async pingServer(targetUrl?: string): Promise<{ latencyMs: number; data: HealthData }> {
    const url = (targetUrl || getApiBaseUrl()).replace(/\/+$/, '');
    const start = performance.now();
    const response = await axios.get<HealthData>(`${url}/health`, {
      timeout: 10000,
      headers: { 'X-Device-Id': getDeviceId() },
    });
    const latencyMs = Math.round(performance.now() - start);
    return { latencyMs, data: response.data };
  },

  /**
   * Check backend health and retrieve system configuration & 60 catalog voices.
   */
  async getHealth(): Promise<HealthData> {
    const response = await apiClient.get<HealthData>('/health');
    return response.data;
  },

  /**
   * Fetch device quota, usage, and subscription tier.
   */
  async getUserQuota(): Promise<UserQuota> {
    const devId = getDeviceId();
    const response = await apiClient.get<UserQuota>(`/v1/user/quota?device_id=${encodeURIComponent(devId)}`);
    return response.data;
  },

  /**
   * Redeem VIP promo or license key (e.g. KOKORO-VIP-FRIEND) to upgrade device to Pro.
   */
  async redeemLicense(code: string): Promise<{ success: boolean; message: string; quota: any }> {
    const devId = getDeviceId();
    const response = await apiClient.post('/v1/user/redeem-license', {
      device_id: devId,
      code: code.trim(),
    });
    return response.data;
  },

  /**
   * Synthesize text into mastered speech audio.
   */
  async renderSpeech(payload: RenderRequest): Promise<RenderResponse> {
    const response = await apiClient.post<RenderResponse>('/render', {
      ...payload,
      device_id: getDeviceId(),
    });
    return response.data;
  },

  /**
   * Fetch all mastering EQ presets.
   */
  async getPresets(): Promise<string[]> {
    const response = await apiClient.get<{ count: number; presets: string[] }>('/presets');
    return response.data.presets;
  },

  /**
   * Format streamable audio URL.
   */
  getAudioStreamUrl(filename: string): string {
    return `${getApiBaseUrl()}/audio/${filename}`;
  },

  /**
   * Developer API: List all active API keys for this device.
   */
  async getDeveloperKeys(): Promise<{ device_id: string; quota: UserQuota; keys: any[] }> {
    const devId = getDeviceId();
    const response = await apiClient.get(`/v1/developer/keys?device_id=${encodeURIComponent(devId)}`);
    return response.data;
  },

  /**
   * Developer API: Generate a new API key.
   */
  async createDeveloperKey(name: string = 'Default API Key'): Promise<any> {
    const devId = getDeviceId();
    const response = await apiClient.post('/v1/developer/keys', {
      name,
      device_id: devId,
    });
    return response.data;
  },

  /**
   * Developer API: Revoke an existing API key.
   */
  async revokeDeveloperKey(keyId: string): Promise<{ success: boolean; message: string }> {
    const devId = getDeviceId();
    const response = await apiClient.delete(`/v1/developer/keys/${encodeURIComponent(keyId)}?device_id=${encodeURIComponent(devId)}`);
    return response.data;
  },

  /**
   * Create secure checkout session link for Pro subscription.
   */
  async createCheckoutSession(returnUrl?: string): Promise<{ checkout_url: string | null; message?: string }> {
    const devId = getDeviceId();
    const response = await apiClient.post('/v1/billing/create-checkout-session', {
      device_id: devId,
      return_url: returnUrl,
    });
    return response.data;
  },

  /**
   * Toggle subscription auto-renewal (turn on or off).
   */
  async toggleAutoRenew(cancelAtPeriodEnd: boolean): Promise<{ success: boolean; message: string; quota: UserQuota; cancel_at_period_end: boolean }> {
    const devId = getDeviceId();
    const response = await apiClient.post('/v1/billing/toggle-auto-renew', {
      device_id: devId,
      cancel_at_period_end: cancelAtPeriodEnd,
    });
    return response.data;
  },

  /**
   * Cancel subscription (immediate or at period end).
   */
  async cancelSubscription(immediate: boolean = false): Promise<{ success: boolean; message: string; quota: UserQuota }> {
    const devId = getDeviceId();
    const response = await apiClient.post('/v1/billing/cancel-subscription', {
      device_id: devId,
      immediate,
    });
    return response.data;
  },

  /**
   * Fetch custom voices created by this device.
   */
  async getCustomVoices(): Promise<{ voices: Voice[] }> {
    const response = await apiClient.get<{ voices: Voice[] }>('/api/voices/custom');
    return response.data;
  },

  /**
   * Upload reference audio file to clone a custom voice.
   */
  async uploadCustomVoice(name: string, file: File): Promise<{ success: boolean; voice: Voice }> {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('file', file);
    const response = await apiClient.post<{ success: boolean; voice: Voice }>('/api/voices/custom', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Delete a custom voice owned by this device.
   */
  async deleteCustomVoice(voiceId: string): Promise<{ success: boolean; deleted_id: string }> {
    const response = await apiClient.delete<{ success: boolean; deleted_id: string }>(`/api/voices/custom/${encodeURIComponent(voiceId)}`);
    return response.data;
  },
};


