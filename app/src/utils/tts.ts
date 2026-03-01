/**
 * ElevenLabs TTS feedback. Calls backend /api/tts to avoid exposing API key.
 * Falls back to expo-speech if backend TTS fails or ElevenLabs is not configured.
 */

import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import * as Speech from 'expo-speech';
import { buildUrl } from '../api/client';

export async function speak(text: string): Promise<void> {
  try {
    const url = buildUrl('/api/tts');
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (res.ok && res.headers.get('content-type')?.includes('audio')) {
      const arrayBuffer = await res.arrayBuffer();
      const uint8 = new Uint8Array(arrayBuffer);
      let base64 = '';
      const chunk = 8192;
      for (let i = 0; i < uint8.length; i += chunk) {
        const slice = uint8.subarray(i, i + chunk);
        base64 += String.fromCharCode.apply(null, Array.from(slice));
      }
      base64 = btoa(base64);
      const cacheDir = FileSystem.cacheDirectory || FileSystem.documentDirectory;
      const uri = `${cacheDir}tts_${Date.now()}.mp3`;
      await FileSystem.writeAsStringAsync(uri, base64, {
        encoding: FileSystem.EncodingType.Base64,
      });
      const { sound } = await Audio.Sound.createAsync({ uri });
      await sound.playAsync();
      sound.setOnPlaybackStatusUpdate((s) => {
        if (s.isLoaded && s.didJustFinishAndNotYetLooped) {
          sound.unloadAsync();
          FileSystem.deleteAsync(uri, { idempotent: true });
        }
      });
      return;
    }
  } catch {
    // Fallback to expo-speech
  }
  Speech.speak(text, { rate: 0.9 });
}
