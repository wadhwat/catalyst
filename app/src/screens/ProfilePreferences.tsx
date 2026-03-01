import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Switch, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { RootStackParamList } from '../types/navigation';
import { Screen } from '../components/Screen';
import { DEFAULT_PREFERENCES, InspectionPreferences } from '../data/preferences';
import { getProfilePreferences, updateProfilePreferences } from '../api/preferences';

type Props = NativeStackScreenProps<RootStackParamList, 'ProfilePreferences'>;

export function ProfilePreferencesScreen({ navigation }: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [form, setForm] = useState({
    inspectionCadenceHours: String(DEFAULT_PREFERENCES.inspectionCadenceHours),
    captureMaxDurationSec: String(DEFAULT_PREFERENCES.captureMaxDurationSec),
    frameSampleFps: String(DEFAULT_PREFERENCES.frameSampleFps),
    captureResolution: DEFAULT_PREFERENCES.captureResolution,
    autoUpload: DEFAULT_PREFERENCES.autoUpload,
  });

  const parsed = useMemo(() => {
    const inspectionCadenceHours = Number(form.inspectionCadenceHours);
    const captureMaxDurationSec = Number(form.captureMaxDurationSec);
    const frameSampleFps = Number(form.frameSampleFps);
    return {
      inspectionCadenceHours,
      captureMaxDurationSec,
      frameSampleFps,
    };
  }, [form]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      setUnavailable(false);
      try {
        const response = await getProfilePreferences();
        const prefs = response?.preferences ?? response?.effective_preferences ?? DEFAULT_PREFERENCES;
        if (!cancelled) {
          setForm({
            inspectionCadenceHours: String(prefs.inspectionCadenceHours),
            captureMaxDurationSec: String(prefs.captureMaxDurationSec),
            frameSampleFps: String(prefs.frameSampleFps),
            captureResolution: prefs.captureResolution,
            autoUpload: prefs.autoUpload,
          });
        }
      } catch (err) {
        const message = String(err);
        if (!cancelled) {
          if (message.includes('Supermemory is not configured')) {
            setUnavailable(true);
            setError('Preferences unavailable (Supermemory is not configured).');
          } else {
            setError('Failed to load preferences.');
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSave = async () => {
    setError(null);
    const { inspectionCadenceHours, captureMaxDurationSec, frameSampleFps } = parsed;
    if (
      !Number.isFinite(inspectionCadenceHours) ||
      inspectionCadenceHours <= 0 ||
      !Number.isFinite(captureMaxDurationSec) ||
      captureMaxDurationSec <= 0 ||
      !Number.isFinite(frameSampleFps) ||
      frameSampleFps <= 0
    ) {
      setError('Enter valid numeric values.');
      return;
    }

    const payload: InspectionPreferences = {
      inspectionCadenceHours,
      captureMaxDurationSec,
      frameSampleFps,
      captureResolution: form.captureResolution,
      autoUpload: form.autoUpload,
    };

    setSaving(true);
    try {
      const response = await updateProfilePreferences(payload);
      const prefs = response?.preferences ?? payload;
      setForm({
        inspectionCadenceHours: String(prefs.inspectionCadenceHours),
        captureMaxDurationSec: String(prefs.captureMaxDurationSec),
        frameSampleFps: String(prefs.frameSampleFps),
        captureResolution: prefs.captureResolution,
        autoUpload: prefs.autoUpload,
      });
    } catch (err) {
      const message = String(err);
      if (message.includes('Supermemory is not configured')) {
        setUnavailable(true);
        setError('Preferences unavailable (Supermemory is not configured).');
      } else {
        setError('Failed to save preferences.');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <Screen style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backText}>Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Preferences</Text>
      </View>

      <View style={styles.card}>
        {loading ? (
          <ActivityIndicator color="#F4D35E" />
        ) : (
          <>
            {error && <Text style={styles.errorText}>{error}</Text>}
            {renderNumberField(
              'Inspection cadence (hours)',
              form.inspectionCadenceHours,
              (value) => setForm((prev) => ({ ...prev, inspectionCadenceHours: value }))
            )}
            {renderNumberField(
              'Max capture duration (sec)',
              form.captureMaxDurationSec,
              (value) => setForm((prev) => ({ ...prev, captureMaxDurationSec: value }))
            )}
            {renderNumberField('Frame sample FPS', form.frameSampleFps, (value) =>
              setForm((prev) => ({ ...prev, frameSampleFps: value }))
            )}

            <Text style={styles.label}>Capture resolution</Text>
            <View style={styles.toggleRow}>
              {(['720p', '1080p'] as const).map((value) => (
                <TouchableOpacity
                  key={value}
                  style={[
                    styles.resolutionOption,
                    form.captureResolution === value && styles.resolutionOptionActive,
                  ]}
                  onPress={() => setForm((prev) => ({ ...prev, captureResolution: value }))}
                  disabled={unavailable}
                >
                  <Text
                    style={[
                      styles.resolutionText,
                      form.captureResolution === value && styles.resolutionTextActive,
                    ]}
                  >
                    {value.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.switchRow}>
              <View>
                <Text style={styles.label}>Auto upload</Text>
                <Text style={styles.hint}>Upload immediately after capture</Text>
              </View>
              <Switch
                value={form.autoUpload}
                onValueChange={(value) => setForm((prev) => ({ ...prev, autoUpload: value }))}
                disabled={unavailable}
                trackColor={{ true: '#F4D35E', false: '#3A3A3A' }}
                thumbColor={form.autoUpload ? '#1B1B1B' : '#E5E7EB'}
              />
            </View>

            <TouchableOpacity
              style={[styles.saveButton, unavailable && styles.saveButtonDisabled]}
              onPress={handleSave}
              disabled={saving || unavailable}
            >
              {saving ? (
                <ActivityIndicator color="#1B1B1B" />
              ) : (
                <Text style={styles.saveButtonText}>Save</Text>
              )}
            </TouchableOpacity>
          </>
        )}
      </View>
    </Screen>
  );
}

function renderNumberField(label: string, value: string, onChange: (value: string) => void) {
  return (
    <View style={styles.fieldGroup}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        keyboardType="numeric"
        style={styles.input}
        placeholder="0"
        placeholderTextColor="#6B7280"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1B1B1B',
    paddingHorizontal: 16,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  backButton: {
    paddingVertical: 6,
    paddingRight: 12,
  },
  backText: {
    color: '#F4D35E',
    fontSize: 15,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
  card: {
    backgroundColor: '#2A2A2A',
    borderRadius: 16,
    padding: 16,
    gap: 14,
  },
  fieldGroup: {
    gap: 6,
  },
  label: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  hint: {
    color: '#9CA3AF',
    fontSize: 12,
    marginTop: 2,
  },
  input: {
    height: 44,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3A3A3A',
    backgroundColor: '#1F1F1F',
    paddingHorizontal: 12,
    color: '#FFFFFF',
  },
  toggleRow: {
    flexDirection: 'row',
    gap: 12,
  },
  resolutionOption: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3A3A3A',
    paddingVertical: 10,
    alignItems: 'center',
    backgroundColor: '#1F1F1F',
  },
  resolutionOptionActive: {
    borderColor: '#F4D35E',
    backgroundColor: '#2A2A2A',
  },
  resolutionText: {
    color: '#9CA3AF',
    fontWeight: '600',
  },
  resolutionTextActive: {
    color: '#F4D35E',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  saveButton: {
    marginTop: 8,
    height: 48,
    borderRadius: 14,
    backgroundColor: '#F4D35E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveButtonDisabled: {
    backgroundColor: '#6B7280',
  },
  saveButtonText: {
    color: '#1B1B1B',
    fontWeight: '700',
    fontSize: 15,
  },
  errorText: {
    color: '#FBBF24',
    fontSize: 12,
  },
});
