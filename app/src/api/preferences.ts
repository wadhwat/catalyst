import { apiFetch } from './client';
import { InspectionPreferences, MachinePreferences } from '../data/preferences';

export type PreferencesResponse<T> = {
  preferences: T;
  effective_preferences: InspectionPreferences;
  updated_at?: string | null;
  source: 'default' | 'memory';
};

export function getProfilePreferences(): Promise<PreferencesResponse<InspectionPreferences>> {
  return apiFetch('/preferences/profile', { method: 'GET' });
}

export function updateProfilePreferences(
  preferences: InspectionPreferences
): Promise<PreferencesResponse<InspectionPreferences>> {
  return apiFetch('/preferences/profile', {
    method: 'PUT',
    body: JSON.stringify(preferences),
  });
}

export function getMachinePreferences(vin: string): Promise<PreferencesResponse<MachinePreferences>> {
  return apiFetch(`/preferences/machine/${encodeURIComponent(vin)}`, { method: 'GET' });
}

export function updateMachinePreferences(
  vin: string,
  preferences: MachinePreferences
): Promise<PreferencesResponse<MachinePreferences>> {
  return apiFetch(`/preferences/machine/${encodeURIComponent(vin)}`, {
    method: 'PUT',
    body: JSON.stringify(preferences),
  });
}
