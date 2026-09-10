import React, { useState, useRef } from 'react';
import { X, UploadCloud, Mic, AlertCircle, Loader2, Music } from 'lucide-react';
import { Voice } from '../types';
import { kokoroApi } from '../api/kokoroApi';

interface CreateVoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onVoiceCreated: (newVoice: Voice) => void;
}

export const CreateVoiceModal: React.FC<CreateVoiceModalProps> = ({
  isOpen,
  onClose,
  onVoiceCreated,
}) => {
  const [voiceName, setVoiceName] = useState('');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioDuration, setAudioDuration] = useState<number | null>(null);
  const [audioPreviewUrl, setAudioPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (file: File) => {
    setErrorMessage(null);
    const validExtensions = ['.wav', '.mp3', '.m4a', '.ogg', '.flac'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));

    if (!hasValidExt) {
      setErrorMessage('Please select a supported audio format (WAV, MP3, M4A, OGG, FLAC).');
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setErrorMessage('Audio file exceeds the 15 MB limit. Please choose a smaller file.');
      return;
    }

    setAudioFile(file);
    const url = URL.createObjectURL(file);
    setAudioPreviewUrl(url);

    // Measure audio duration
    const audio = new Audio(url);
    audio.onloadedmetadata = () => {
      setAudioDuration(audio.duration);
      if (audio.duration < 3.0) {
        setErrorMessage(`Audio duration (${audio.duration.toFixed(1)}s) is too short. Please provide at least 3 seconds.`);
      } else if (audio.duration > 30.0) {
        setErrorMessage(`Audio duration (${audio.duration.toFixed(1)}s) exceeds 30 seconds. Please provide 3 to 30 seconds.`);
      }
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanName = voiceName.trim();
    if (!cleanName) {
      setErrorMessage('Please enter a name for your custom voice.');
      return;
    }

    if (!audioFile) {
      setErrorMessage('Please select an audio reference file.');
      return;
    }

    if (audioDuration !== null && (audioDuration < 3.0 || audioDuration > 30.0)) {
      setErrorMessage('Audio reference must be between 3 and 30 seconds.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await kokoroApi.uploadCustomVoice(cleanName, audioFile);
      if (response.success && response.voice) {
        onVoiceCreated(response.voice);
        onClose();
      } else {
        setErrorMessage('Failed to clone voice. Please verify audio sample and try again.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Voice cloning failed.';
      setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-slate-900/60 dark:bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-150 select-none"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-3xl shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 sm:p-6 border-b border-slate-100 dark:border-slate-700/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
              ✨
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
                Clone Custom Voice
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Zero-shot voice cloning powered by Pocket TTS
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

        {/* Content Form */}
        <form onSubmit={handleSubmit} className="p-5 sm:p-6 space-y-4">
          {/* Error Banner */}
          {errorMessage && (
            <div className="p-3.5 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start gap-2.5 text-xs text-rose-700 dark:text-rose-300">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Voice Name Input */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
              Voice Name
            </label>
            <input
              type="text"
              value={voiceName}
              onChange={(e) => setVoiceName(e.target.value)}
              placeholder="e.g. Sarah Narration, John Studio..."
              maxLength={50}
              className="w-full bg-slate-50 dark:bg-slate-900/60 text-slate-800 dark:text-slate-200 text-xs sm:text-sm px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-purple-500 transition-all"
              required
            />
          </div>

          {/* Audio Upload Dropzone */}
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
              Reference Audio (3 to 30 seconds)
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".wav,.mp3,.m4a,.ogg,.flac"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileChange(e.target.files[0]);
                }
              }}
            />

            {!audioFile ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    handleFileChange(e.dataTransfer.files[0]);
                  }
                }}
                className="border-2 border-dashed border-slate-200 dark:border-slate-700 hover:border-purple-400 dark:hover:border-purple-500 rounded-2xl p-6 text-center cursor-pointer transition-colors bg-slate-50/50 dark:bg-slate-900/30"
              >
                <UploadCloud className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Click to upload or drag & drop audio
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  WAV, MP3, M4A, OGG or FLAC (Max 15 MB)
                </div>
              </div>
            ) : (
              <div className="p-3.5 rounded-2xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-900/50 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <Music className="w-4 h-4 text-purple-600 dark:text-purple-400 shrink-0" />
                    <span className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">
                      {audioFile.name}
                    </span>
                    {audioDuration !== null && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-200/60 dark:bg-purple-800/60 text-purple-800 dark:text-purple-200 font-mono">
                        {audioDuration.toFixed(1)}s
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setAudioFile(null);
                      setAudioPreviewUrl(null);
                      setAudioDuration(null);
                    }}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs font-semibold"
                  >
                    Change
                  </button>
                </div>

                {audioPreviewUrl && (
                  <audio
                    src={audioPreviewUrl}
                    controls
                    className="w-full h-8 mt-1 rounded-lg"
                  />
                )}
              </div>
            )}
          </div>

          {/* Ethics Note */}
          <p className="text-[11px] text-slate-400 dark:text-slate-500 leading-relaxed">
            🔒 By cloning a voice, you confirm that you have permission from the original speaker to reproduce their voice for your content.
          </p>

          {/* Submit Button */}
          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !audioFile || !voiceName.trim()}
              className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-xs font-bold shadow-md transition-all flex items-center gap-2 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Cloning Voice...</span>
                </>
              ) : (
                <>
                  <Mic className="w-3.5 h-3.5" />
                  <span>Create Custom Voice</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default CreateVoiceModal;
