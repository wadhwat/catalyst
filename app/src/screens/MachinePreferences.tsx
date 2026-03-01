import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Switch, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { RootStackParamList } from '../types/navigation';
import { Screen } from '../components/Screen';
import { DEFAULT_PREFERENCES, InspectionPreferences, MachinePreferences } from '../data/preferences';
import { getMachinePreferences, updateMachinePreferences } from '../api/preferences';
import { useMachines } from '../machines/MachinesContext';

type Props = NativeStackScreenProps<RootStackParamList, 'MachinePreferences'>;

type OverrideFlags = {
  inspectionCadenceHours: boolean;
  captureMaxDurationSec: boolean;
  frameSampleFps: boolean;
  captureResolution: boolean;
  autoUpload: boolean;
};

export function MachinePreferencesScreen({ navigation, route }: Props) {
  const { machineId } = route.params;
  const { machines } = useMachines();
  const machine = useMemo(() => machines.find((item) => item.id === machineId), [machineId, machines]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [effective, setEffective] = useState<InspectionPreferences>(DEFAULT_PREFERENCES);
  const [overridesEnabled, setOverridesEnabled] = useState<OverrideFlags>({
    inspectionCadenceHours: false,
    captureMaxDurationSec: false,
    frameSampleFps: false,
    captureResolution: false,
    autoUpload: false,
  });
  const [form, setForm] = useState({
    inspectionCadenceHours: String(DEFAULT_PREFERENCES.inspectionCadenceHours),
    captureMaxDurationSec: String(DEFAULT_PREFERENCES.captureMaxDurationSec),
    frameSampleFps: String(DEFAULT_PREFERENCES.frameSampleFps),
    captureResolution: DEFAULT_PREFERENCES.captureResolution,
    autoUpload: DEFAULT_PREFERENCES.autoUpload,
  });

  useEffect(() => {
    if (!machine) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      setUnavailable(false);
      try {
        const response = await getMachinePreferences(machine.vin);
        const effectivePrefs = response?.effective_preferences ?? DEFAULT_PREFERENCES;
        const overrides = (response?.preferences ?? {}) as MachinePreferences;
        if (!cancelled) {
          setEffective(effectivePrefs);
          setOverridesEnabled({
            inspectionCadenceHours: overrides.inspectionCadenceHours != null,
            captureMaxDurationSec: overrides.captureMaxDurationSec != null,
            frameSampleFps: overrides.frameSampleFps != null,
            captureResolution: overrides.captureResolution != null,
            autoUpload: overrides.autoUpload != null,
          });
          setForm({
            inspectionCadenceHours: String(
              overrides.inspectionCadenceHours ?? effectivePrefs.inspectionCadenceHours
            ),
            captureMaxDurationSec: String(
              overrides.captureMaxDurationSec ?? effectivePrefs.captureMaxDurationSec
            ),
            frameSampleFps: String(overrides.frameSampleFps ?? effectivePrefs.frameSampleFps),
            captureResolution: overrides.captureResolution ?? effectivePrefs.captureResolution,
            autoUpload: overrides.autoUpload ?? effectivePrefs.autoUpload,
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
  }, [machine]);

  if (!machine) {
    return (
      <Screen style={styles.container}>
        <Text style={styles.errorText}>Machine not found.</Text>
      </Screen>
    );
  }

  const parsedNumbers = {
    inspectionCadenceHours: Number(form.inspectionCadenceHours),
    captureMaxDurationSec: Number(form.captureMaxDurationSec),
    frameSampleFps: Number(form.frameSampleFps),
  };

  const handleSave = async () => {
    setError(null);
    if (
      (overridesEnabled.inspectionCadenceHours &&
        (!Number.isFinite(parsedNumbers.inspectionCadenceHours) ||
          parsedNumbers.inspectionCadenceHours <= 0)) ||
      (overridesEnabled.captureMaxDurationSec &&
        (!Number.isFinite(parsedNumbers.captureMaxDurationSec) ||
          parsedNumbers.captureMaxDurationSec <= 0)) ||
      (overridesEnabled.frameSampleFps &&
        (!Number.isFinite(parsedNumbers.frameSampleFps) || parsedNumbers.frameSampleFps <= 0))
    ) {
      setError('Enter valid numeric values for enabled overrides.');
      return;
    }

    const payload: MachinePreferences = {};
    if (overridesEnabled.inspectionCadenceHours) {
      payload.inspectionCadenceHours = parsedNumbers.inspectionCadenceHours;
    }
    if (overridesEnabled.captureMaxDurationSec) {
      payload.captureMaxDurationSec = parsedNumbers.captureMaxDurationSec;
    }
    if (overridesEnabled.frameSampleFps) {
      payload.frameSampleFps = parsedNumbers.frameSampleFps;
    }
    if (overridesEnabled.captureResolution) {
      payload.captureResolution = form.captureResolution;
    }
    if (overridesEnabled.autoUpload) {
      payload.autoUpload = form.autoUpload;
    }

    setSaving(true);
    try {
      const response = await updateMachinePreferences(machine.vin, payload);
      const effectivePrefs = response?.effective_preferences ?? effective;
      const overrides = (response?.preferences ?? payload) as MachinePreferences;
      setEffective(effectivePrefs);
      setOverridesEnabled({
        inspectionCadenceHours: overrides.inspectionCadenceHours != null,
        captureMaxDurationSec: overrides.captureMaxDurationSec != null,
        frameSampleFps: overrides.frameSampleFps != null,
        captureResolution: overrides.captureResolution != null,
        autoUpload: overrides.autoUpload != null,
      });
      setForm({
        inspectionCadenceHours: String(
          overrides.inspectionCadenceHours ?? effectivePrefs.inspectionCadenceHours
        ),
        captureMaxDurationSec: String(
          overrides.captureMaxDurationSec ?? effectivePrefs.captureMaxDurationSec
        ),
        frameSampleFps: String(overrides.frameSampleFps ?? effectivePrefs.frameSampleFps),
        captureResolution: overrides.captureResolution ?? effectivePrefs.captureResolution,
        autoUpload: overrides.autoUpload ?? effectivePrefs.autoUpload,
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
        <Text style={styles.title}>Machine Preferences</Text>
      </View>

      <View style={styles.card}>
        {loading ? (
          <ActivityIndicator color="#F4D35E" />
        ) : (
          <>
            {error && <Text style={styles.errorText}>{error}</Text>}
            {renderOverrideNumberField({
              label: 'Inspection cadence (hours)',
              value: form.inspectionCadenceHours,
              onChange: (value) => setForm((prev) => ({ ...prev, inspectionCadenceHours: value })),
              enabled: overridesEnabled.inspectionCadenceHours,
              onToggle: (value) =>
                setOverridesEnabled((prev) => ({ ...prev, inspectionCadenceHours: value })),
              effectiveValue: effective.inspectionCadenceHours,
            })}
            {renderOverrideNumberField({
              label: 'Max capture duration (sec)',
              value: form.captureMaxDurationSec,
              onChange: (value) => setForm((prev) => ({ ...prev, captureMaxDurationSec: value })),
              enabled: overridesEnabled.captureMaxDurationSec,
              onToggle: (value) =>
                setOverridesEnabled((prev) => ({ ...prev, captureMaxDurationSec: value })),
              effectiveValue: effective.captureMaxDurationSec,
            })}
            {renderOverrideNumberField({
              label: 'Frame sample FPS',
              value: form.frameSampleFps,
              onChange: (value) => setForm((prev) => ({ ...prev, frameSampleFps: value })),
              enabled: overridesEnabled.frameSampleFps,
              onToggle: (value) =>
                setOverridesEnabled((prev) => ({ ...prev, frameSampleFps: value })),
              effectiveValue: effective.frameSampleFps,
            })}

            <View style={styles.fieldGroup}>
              <View style={styles.fieldHeader}>
                <Text style={styles.label}>Capture resolution</Text>
                <Switch
                  value={overridesEnabled.captureResolution}
                  onValueChange={(value) =>
                    setOverridesEnabled((prev) => ({ ...prev, captureResolution: value }))
                  }
                  disabled={unavailable}
                  trackColor={{ true: '#F4D35E', false: '#3A3A3A' }}
                  thumbColor={overridesEnabled.captureResolution ? '#1B1B1B' : '#E5E7EB'}
                />
              </View>
              <Text style={styles.hint}>Effective: {effective.captureResolution.toUpperCase()}</Text>
              <View style={styles.toggleRow}>
                {(['720p', '1080p'] as const).map((value) => {
                  const isActive = form.captureResolution === value;
                  return (
                    <TouchableOpacity
                      key={value}
                      style={[
                        styles.resolutionOption,
                        isActive && styles.resolutionOptionActive,
                        !overridesEnabled.captureResolution && styles.resolutionOptionDisabled,
                      ]}
                      onPress={() => setForm((prev) => ({ ...prev, captureResolution: value }))}
                      disabled={!overridesEnabled.captureResolution || unavailable}
                    >
                      <Text
                        style={[
                          styles.resolutionText,
                          isActive && styles.resolutionTextActive,
                          !overridesEnabled.captureResolution && styles.resolutionTextDisabled,
                        ]}
                      >
                        {value.toUpperCase()}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>

            <View style={styles.fieldGroup}>
              <View style={styles.fieldHeader}>
                <View>
                  <Text style={styles.label}>Auto upload</Text>
                  <Text style={styles.hint}>Effective: {effective.autoUpload ? 'On' : 'Off'}</Text>
                </View>
                <Switch
                  value={overridesEnabled.autoUpload}
                  onValueChange={(value) =>
                    setOverridesEnabled((prev) => ({ ...prev, autoUpload: value }))
                  }
                  disabled={unavailable}
                  trackColor={{ true: '#F4D35E', false: '#3A3A3A' }}
                  thumbColor={overridesEnabled.autoUpload ? '#1B1B1B' : '#E5E7EB'}
                />
              </View>
              <View style={styles.switchRow}>
                <Text style={styles.hint}>Override value</Text>
                <Switch
                  value={form.autoUpload}
                  onValueChange={(value) => setForm((prev) => ({ ...prev, autoUpload: value }))}
                  disabled={!overridesEnabled.autoUpload || unavailable}
                  trackColor={{ true: '#F4D35E', false: '#3A3A3A' }}
                  thumbColor={form.autoUpload ? '#1B1B1B' : '#E5E7EB'}
                />
              </View>
            </View>

            <TouchableOpacity
              style={[styles.saveButton, unavailable && styles.saveButtonDisabled]}
              onPress={handleSave}
              disabled={saving || unavailable}
            >
              {saving ? (
                <ActivityIndicator color="#1B1B1B" />
              ) : (
                <Text style={styles.saveButtonText}>Save Overrides</Text>
              )}
            </TouchableOpacity>
          </>
        )}
      </View>
    </Screen>
  );
}

function renderOverrideNumberField({
  label,
  value,
  onChange,
  enabled,
  onToggle,
  effectiveValue,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  enabled: boolean;
  onToggle: (value: boolean) => void;
  effectiveValue: number;
}) {
  return (
    <View style={styles.fieldGroup}>
      <View style={styles.fieldHeader}>
        <Text style={styles.label}>{label}</Text>
        <Switch
          value={enabled}
          onValueChange={onToggle}
          trackColor={{ true: '#F4D35E', false: '#3A3A3A' }}
          thumbColor={enabled ? '#1B1B1B' : '#E5E7EB'}
        />
      </View>
      <Text style={styles.hint}>Effective: {effectiveValue}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        keyboardType="numeric"
        editable={enabled}
        style={[styles.input, !enabled && styles.inputDisabled]}
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
  fieldHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  hint: {
    color: '#9CA3AF',
    fontSize: 12,
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
  inputDisabled: {
    opacity: 0.6,
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
  resolutionOptionDisabled: {
    opacity: 0.6,
  },
  resolutionText: {
    color: '#9CA3AF',
    fontWeight: '600',
  },
  resolutionTextActive: {
    color: '#F4D35E',
  },
  resolutionTextDisabled: {
    color: '#6B7280',
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
