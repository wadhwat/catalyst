import React, { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { machines } from '../data/machines';
import { MachineCard } from '../components/MachineCard';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types/navigation';

export function HomeScreen({ navigation }: NativeStackScreenProps<RootStackParamList, 'Home'>) {
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    if (!query.trim()) return machines;
    const lower = query.toLowerCase();
    return machines.filter(
      (machine) =>
        machine.name.toLowerCase().includes(lower) || machine.vin.toLowerCase().includes(lower)
    );
  }, [query]);

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <View>
          <Text style={styles.title}>Fleet</Text>
        </View>
        <View style={styles.profileBubble}>
          <Text style={styles.profileText}>TW</Text>
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
        {filtered.map((machine) => (
          <MachineCard
            key={machine.id}
            machine={machine}
            onPress={() => navigation.navigate('MachineDetail', { machineId: machine.id })}
          />
        ))}
        {filtered.length === 0 && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No equipment found</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1B1B1B',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FFFFFF',
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
});
