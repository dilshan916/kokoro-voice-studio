export interface Voice {
  id: string;
  name: string;
  gender: 'Female' | 'Male' | 'Neutral';
  lang: string;
  lang_name: string;
  flag: string;
  description: string;
}

export interface LanguageOption {
  code: string;
  name: string;
  flag: string;
}

export interface HealthData {
  status: 'ready' | 'loading' | 'error';
  version: string;
  model_loaded: boolean;
  voices_count: number;
  output_directory: string;
  supported_languages: LanguageOption[];
  mastering_presets: string[];
  voices: Voice[];
}

export interface RenderRequest {
  text: string;
  voice_id: string;
  speed: number;
  eq_preset: string;
  lang: string;
  output_format: 'wav' | 'mp3';
  pause_punctuation_ms?: number;
  pause_paragraph_ms?: number;
}

export interface RenderResponse {
  success: boolean;
  audio_path: string;
  audio_url: string;
  filename: string;
  duration: number;
  sample_rate: number;
  file_size_bytes: number;
  voice_id: string;
  voice_name: string;
  lang_resolved: string;
  eq_preset: string;
  audio_base64?: string;
  srt_content?: string;
  srt_filename?: string;
}

export interface DialogueBlock {
  id: string;
  speakerName: string;
  voiceId: string;
  lang: string;
  text: string;
  pauseAfterSec: number;
}

export interface AudioTrack {
  id: string;
  title: string;
  voice_name: string;
  voice_flag: string;
  audio_url: string;
  duration: number;
  filename: string;
  lang: string;
  eq_preset: string;
  audio_base64?: string;
  srt_content?: string;
  srt_filename?: string;
}

export interface UserQuota {
  device_id: string;
  tier: 'free' | 'pro';
  monthly_limit: number;
  monthly_usage: number;
  remaining_chars: number | string;
  is_pro?: boolean;
  billing_cycle_month?: string;
  has_subscription?: boolean;
  cancel_at_period_end?: boolean;
  subscription_expires_at?: string;
}

export interface GenerationHistoryItem {
  id: string;
  title: string;
  voice_name: string;
  voice_flag: string;
  audio_url: string;
  filename: string;
  duration: number;
  timestamp: number;
  formatted_time: string;
  srt_content?: string;
  srt_filename?: string;
  audio_base64?: string;
}

export interface ApiKeyItem {
  key_id: string;
  api_key: string;
  masked_key: string;
  name: string;
  tier: string;
  monthly_usage: number;
  monthly_limit: number;
  is_active: boolean;
  created_at: string;
  last_used_at?: string | null;
}


