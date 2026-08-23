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
