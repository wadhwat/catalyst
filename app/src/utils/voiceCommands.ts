/**
 * Voice command helpers for "start video" / "stop video".
 * Uses expo-speech-recognition (requires dev build; Expo Go will fallback to button-only).
 */

const START_PHRASES = ['start video', 'start recording', 'begin', 'record'];
const STOP_PHRASES = ['stop video', 'stop recording', 'end', 'stop'];

export function matchVoiceCommand(transcript: string): 'start' | 'stop' | null {
  const t = transcript.toLowerCase().trim();
  for (const p of START_PHRASES) {
    if (t.includes(p)) return 'start';
  }
  for (const p of STOP_PHRASES) {
    if (t.includes(p)) return 'stop';
  }
  return null;
}
