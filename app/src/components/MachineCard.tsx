import React from 'react';
import { ImageBackground, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { DEFAULT_MACHINE_IMAGE, Machine } from '../data/machines';
import { formatTimeAgo } from '../utils/time';
import { RadialProgress } from './RadialProgress';

const STATUS_STYLES = {
  PASS: { bg: 'rgba(34,197,94,0.2)', text: '#4ADE80', border: 'rgba(34,197,94,0.4)' },
  MONITOR: { bg: 'rgba(251,191,36,0.2)', text: '#FBBF24', border: 'rgba(251,191,36,0.4)' },
  FAIL: { bg: 'rgba(248,113,113,0.2)', text: '#F87171', border: 'rgba(248,113,113,0.4)' },
  UNKNOWN: { bg: 'rgba(148,163,184,0.2)', text: '#CBD5F5', border: 'rgba(148,163,184,0.5)' },
};

type Props = {
  machine: Machine;
  onPress: () => void;
  now?: number;
};

export function MachineCard({ machine, onPress, now }: Props) {
  const current = now ?? Date.now();
  const lastInspected = machine.lastInspectedMs;
  const hasInspection = typeof lastInspected === 'number';
  const hoursSince = hasInspection ? (current - lastInspected) / (1000 * 60 * 60) : null;
  const hoursRemaining = hasInspection ? Math.max(0, 12 - (hoursSince ?? 0)) : 0;
  const percentage = hasInspection ? (hoursRemaining / 12) * 100 : 0;

  let ringColor = '#475569';
  if (hasInspection) {
    ringColor = '#2E7D32';
    if (hoursRemaining < 8 && hoursRemaining >= 4) {
      ringColor = '#ED6C02';
    } else if (hoursRemaining < 4) {
      ringColor = '#D32F2F';
    }
  }

  const statusStyle = STATUS_STYLES[machine.status];
  const statusLabel = machine.status === 'UNKNOWN' ? 'NEW' : machine.status;
  const timeAgoLabel = hasInspection ? formatTimeAgo(lastInspected as number, current) : 'No inspections yet';

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.85} style={styles.card}>
      <ImageBackground source={{ uri: machine.imageUrl || DEFAULT_MACHINE_IMAGE }} style={styles.image} imageStyle={styles.imageStyle}>
        <View style={styles.overlay} />
        <View style={styles.content}>
          <View style={styles.headerRow}>
            <View style={styles.headerText}>
              <Text style={styles.title}>{machine.name}</Text>
              <Text style={styles.vin}>VIN {machine.vin}</Text>
              <Text style={styles.lastInspected}>
                {hasInspection ? `Last inspected ${timeAgoLabel}` : timeAgoLabel}
              </Text>
            </View>
            <RadialProgress size={64} strokeWidth={4} percentage={percentage} color={ringColor}>
              <View style={[styles.statusChip, { backgroundColor: statusStyle.bg, borderColor: statusStyle.border }]}
              >
                <Text style={[styles.statusText, { color: statusStyle.text }]}>{statusLabel}</Text>
              </View>
              <Text style={styles.timeLabel}>
                {hasInspection ? formatTimeAgo(lastInspected as number, current).replace(' ago', '') : '--'}
              </Text>
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
    minWidth: 48,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 999,
    alignItems: 'center',
  },
  statusText: {
    fontSize: 9,
    fontWeight: '600',
  },
  timeLabel: {
    color: '#D1D5DB',
    fontSize: 11,
    marginTop: 4,
  },
});
