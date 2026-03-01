import React, { useContext, useMemo, useState } from 'react';
import { Modal, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import * as Crypto from 'expo-crypto';

import { DEFAULT_MACHINE_IMAGE, Machine } from '../data/machines';
import { MachineCard } from '../components/MachineCard';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';
import { useMachines } from '../machines/MachinesContext';
import { AuthContext } from '../auth/context';
import { useNow } from '../utils/time';
import { Screen } from '../components/Screen';

export function HomeScreen({ navigation }: NativeStackScreenProps<RootStackParamList, 'Home'>) {
  const [query, setQuery] = useState('');
  const [addOpen, setAddOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    vin: '',
    machineType: '',
    niche: '',
    imageUrl: '',
  });
  const { machines, addMachine, loading } = useMachines();
  const { user, signOut } = useContext(AuthContext);
  const now = useNow();

  const filtered = useMemo(() => {
    if (!query.trim()) return machines;
    const lower = query.toLowerCase();
    return machines.filter(
      (machine) =>
        machine.name.toLowerCase().includes(lower) || machine.vin.toLowerCase().includes(lower)
    );
  }, [query, machines]);

  return (
    <Screen style={styles.container}>
      <View style={styles.topBar}>
        <View>
          <Text style={styles.title}>Fleet</Text>
        </View>
        <View style={styles.topBarActions}>
          <TouchableOpacity style={styles.addButton} onPress={() => setAddOpen(true)}>
            <Text style={styles.addButtonText}>＋</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.profileBubble} onPress={() => setProfileOpen(true)}>
            <Text style={styles.profileText}>{getInitials(user?.display_name || user?.email)}</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.searchContainer}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search equipment..."
          placeholderTextColor="#6B7280"
          style={styles.searchInput}
        />
      </View>

      <ScrollView contentContainerStyle={styles.list} showsVerticalScrollIndicator={false}>
        {loading ? (
          <Text style={styles.emptyText}>Loading machines...</Text>
        ) : (
          filtered.map((machine) => (
          <MachineCard
            key={machine.id}
            machine={machine}
            now={now}
            onPress={() => navigation.navigate('MachineDetail', { machineId: machine.id })}
          />
          ))
        )}
        {!loading && filtered.length === 0 && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No equipment found</Text>
            <TouchableOpacity style={styles.emptyAction} onPress={() => setAddOpen(true)}>
              <Text style={styles.emptyActionText}>Add your first machine</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
      <Modal visible={addOpen} transparent animationType="fade" onRequestClose={() => setAddOpen(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Add machine</Text>
            {renderInput('Name', form.name, (value) => setForm({ ...form, name: value }))}
            {renderInput('VIN', form.vin, (value) => setForm({ ...form, vin: value }))}
            {renderInput('Machine type', form.machineType, (value) => setForm({ ...form, machineType: value }))}
            {renderInput('Niche', form.niche, (value) => setForm({ ...form, niche: value }))}
            {renderInput('Image URL (optional)', form.imageUrl, (value) => setForm({ ...form, imageUrl: value }))}
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalSecondary} onPress={() => setAddOpen(false)}>
                <Text style={styles.modalSecondaryText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalPrimary}
                onPress={() => {
                  if (!form.name.trim() || !form.vin.trim()) return;
                  const machine: Machine = {
                    id: Crypto.randomUUID(),
                    name: form.name.trim(),
                    vin: form.vin.trim(),
                    lastInspectedMs: null,
                    status: 'UNKNOWN',
                    criticalIssues: 0,
                    imageUrl: form.imageUrl.trim() || DEFAULT_MACHINE_IMAGE,
                    machineType: form.machineType.trim() || 'unknown',
                    niche: form.niche.trim() || 'general',
                    componentIssues: [],
                  };
                  addMachine(machine);
                  setForm({ name: '', vin: '', machineType: '', niche: '', imageUrl: '' });
                  setAddOpen(false);
                }}
              >
                <Text style={styles.modalPrimaryText}>Add</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={profileOpen} transparent animationType="fade" onRequestClose={() => setProfileOpen(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setProfileOpen(false)}>
          <View style={styles.menuCard}>
            <Text style={styles.menuTitle}>{user?.display_name || user?.email}</Text>
            <Text style={styles.menuItemMuted}>Manage memories (coming soon)</Text>
            <TouchableOpacity
              style={styles.menuLogout}
              onPress={async () => {
                setProfileOpen(false);
                await signOut();
              }}
            >
              <Text style={styles.menuLogoutText}>Log out</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </Screen>
  );
}

function getInitials(value?: string | null) {
  if (!value) return 'U';
  const parts = value.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

function renderInput(label: string, value: string, onChange: (value: string) => void) {
  return (
    <View style={styles.inputGroup}>
      <Text style={styles.inputLabel}>{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        style={styles.modalInput}
        placeholder={label}
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
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  topBarActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  addButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#F4D35E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  addButtonText: {
    color: '#F4D35E',
    fontSize: 18,
    fontWeight: '600',
  },
  profileBubble: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#F4D35E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1B1B1B',
  },
  searchContainer: {
    marginBottom: 16,
  },
  searchInput: {
    height: 44,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3A3A3A',
    backgroundColor: '#2A2A2A',
    color: '#FFFFFF',
    paddingHorizontal: 12,
  },
  list: {
    gap: 16,
    paddingBottom: 24,
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyText: {
    color: '#9CA3AF',
  },
  emptyAction: {
    marginTop: 12,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#F4D35E',
  },
  emptyActionText: {
    color: '#F4D35E',
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalCard: {
    width: '100%',
    backgroundColor: '#1F1F1F',
    borderRadius: 18,
    padding: 16,
    gap: 12,
  },
  modalTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  modalInput: {
    backgroundColor: '#2A2A2A',
    borderColor: '#3A3A3A',
    borderWidth: 1,
    borderRadius: 12,
    height: 44,
    paddingHorizontal: 12,
    color: '#FFFFFF',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 8,
  },
  modalSecondary: {
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  modalSecondaryText: {
    color: '#9CA3AF',
    fontWeight: '600',
  },
  modalPrimary: {
    backgroundColor: '#F4D35E',
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  modalPrimaryText: {
    color: '#1B1B1B',
    fontWeight: '700',
  },
  menuCard: {
    width: '100%',
    backgroundColor: '#1F1F1F',
    borderRadius: 18,
    padding: 16,
    gap: 12,
  },
  menuTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  menuItemMuted: {
    color: '#9CA3AF',
    fontSize: 12,
  },
  menuLogout: {
    marginTop: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    backgroundColor: '#2A2A2A',
    borderRadius: 12,
  },
  menuLogoutText: {
    color: '#F87171',
    fontWeight: '600',
    textAlign: 'center',
  },
});
