import axios from 'axios';
import { HealthData, RenderRequest, RenderResponse } from '../types';

// Dynamic API base URL (uses current origin in desktop/browser mode, or fallback to port 8000)
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (typeof window !== 'undefined' && window.location.origin ? window.location.origin : 'http://127.0.0.1:8000');

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000, // 10 minutes (600 seconds) for long multi-paragraph & multi-speaker scripts
  headers: {
    'Content-Type': 'application/json',
  },
});

export const kokoroApi = {
  /**
   * Check backend health and retrieve system configuration & 60 catalog voices.
   */
  async getHealth(): Promise<HealthData> {
    const response = await apiClient.get<HealthData>('/health');
    return response.data;
  },

  /**
   * Synthesize text into mastered speech audio.
   */
  async renderSpeech(payload: RenderRequest): Promise<RenderResponse> {
    const response = await apiClient.post<RenderResponse>('/render', payload);
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
    return `${API_BASE_URL}/audio/${filename}`;
  },
};
