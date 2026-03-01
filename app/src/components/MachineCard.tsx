import React from 'react';
import { ImageBackground, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { Machine } from '../data/machines';
import { formatTimeAgo } from '../utils/time';
import { RadialProgress } from './RadialProgress';

const STATUS_STYLES = {
  PASS: { bg: 'rgba(34,197,94,0.2)', text: '#4ADE80', border: 'rgba(34,197,94,0.4)' },
  MONITOR: { bg: 'rgba(251,191,36,0.2)', text: '#FBBF24', border: 'rgba(251,191,36,0.4)' },
  FAIL: { bg: 'rgba(248,113,113,0.2)', text: '#F87171', border: 'rgba(248,113,113,0.4)' },
};

type Props = {
  machine: Machine;
  onPress: () => void;
};

export function MachineCard({ machine, onPress }: Props) {
  const hoursSince = (Date.now() - machine.lastInspectedMs) / (1000 * 60 * 60);
  const hoursRemaining = Math.max(0, 12 - hoursSince);
  const percentage = (hoursRemaining / 12) * 100;

  let ringColor = '#2E7D32';
  if (hoursRemaining < 8 && hoursRemaining >= 4) {
    ringColor = '#ED6C02';
  } else if (hoursRemaining < 4) {
    ringColor = '#D32F2F';
  }

  const statusStyle = STATUS_STYLES[machine.status];

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.85} style={styles.card}>
      <ImageBackground source={{ uri: machine.imageUrl }} style={styles.image} imageStyle={styles.imageStyle}>
        <View style={styles.overlay} />
        <View style={styles.content}>
          <View style={styles.headerRow}>
            <View style={styles.headerText}>
              <Text style={styles.title}>{machine.name}</Text>
              <Text style={styles.vin}>VIN {machine.vin}</Text>
              <Text style={styles.lastInspected}>Last inspected {formatTimeAgo(machine.lastInspectedMs)}</Text>
            </View>
            <RadialProgress size={64} strokeWidth={4} percentage={percentage} color={ringColor}>
              <View style={[styles.statusChip, { backgroundColor: statusStyle.bg, borderColor: statusStyle.border }]}
              >
                <Text style={[styles.statusText, { color: statusStyle.text }]}>{machine.status}</Text>
              </View>
              <Text style={styles.timeLabel}>{formatTimeAgo(machine.lastInspectedMs).replace(' ago', '')}</Text>
            </RadialProgress>
          </View>
        </View>
      </ImageBackground>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 18,
    overflow: 'hidden',
    backgroundColor: '#2A2A2A',
    shadowColor: '#000',
    shadowOpacity: 0.35,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 6,
  },
  image: {
    width: '100%',
  },
  imageStyle: {
    opacity: 0.35,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(27,27,27,0.55)',
  },
  content: {
    padding: 16,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerText: {
    flex: 1,
    paddingRight: 12,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  vin: {
    color: '#9CA3AF',
    fontSize: 12,
    marginTop: 2,
  },
  lastInspected: {
    color: '#D1D5DB',
    fontSize: 13,
    marginTop: 8,
  },
  statusChip: {
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '600',
  },
  timeLabel: {
    color: '#D1D5DB',
    fontSize: 11,
    marginTop: 4,
  },
});
