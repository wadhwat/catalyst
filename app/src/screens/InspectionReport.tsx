import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Image, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { RootStackParamList } from '../types/navigation';
import { InspectionReportContent } from '../types/report';
import { getReportById } from '../api/reports';
import { resolveMediaUrl } from '../api/client';
import { useMachines } from '../machines/MachinesContext';
import { Screen } from '../components/Screen';

function formatItemLabel(id: string): string {
  return id
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function InspectionReportScreen({
  route,
  navigation,
}: NativeStackScreenProps<RootStackParamList, 'InspectionReport'>) {
  const { machineId, inspectionId, report: initialReport } = route.params;
  const { machines } = useMachines();
  const machine = machines.find((item) => item.id === machineId);
  const [report, setReport] = useState<InspectionReportContent | undefined>(initialReport);
  const [loading, setLoading] = useState(!initialReport);
  const [resolved, setResolved] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchReport = async () => {
      if (report || !inspectionId) return;
      setLoading(true);
      try {
        const content = await getReportById(inspectionId);
        if (content) {
          setReport(content);
          return;
        }
        Alert.alert('Report unavailable', 'No inspection report found.');
      } catch (error) {
        Alert.alert('Report unavailable', String(error));
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [inspectionId, report]);

  const flagged = useMemo(() => {
    if (!report) return [];
    return report.items.filter((item) => item.status !== 'PASS');
  }, [report]);

  return (
    <Screen style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{machine?.name ?? 'Inspection Report'}</Text>
      </View>

      {loading ? (
        <View style={styles.loading}>
          <ActivityIndicator color="#F4D35E" />
        </View>
      ) : !report ? (
        <View style={styles.loading}>
          <Text style={styles.mutedText}>No report data available.</Text>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Inspection Report</Text>
            <Text style={styles.summaryStatus}>{report.summary.status}</Text>
            {report.summary.notes ? (
              <Text style={styles.summaryNotes}>{report.summary.notes}</Text>
            ) : null}
          </View>
          {report.narrative ? (
            <View style={styles.narrativeCard}>
              <Text style={styles.sectionTitle}>Narrative</Text>
              <Text style={styles.narrativeText}>{report.narrative}</Text>
            </View>
          ) : null}

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Flagged Parts</Text>
            {flagged.length === 0 ? (
              <Text style={styles.mutedText}>No flagged issues found.</Text>
            ) : (
              flagged.map((item) => {
                const evidenceList = item.evidence_urls ?? (item as any).evidence ?? [];
                const evidenceUrl = evidenceList[0] || '';
                return (
                  <View key={item.id} style={styles.flagCard}>
                    {evidenceUrl ? (
                      <Image source={{ uri: resolveMediaUrl(evidenceUrl) }} style={styles.flagImage} />
                    ) : (
                      <View style={styles.flagPlaceholder}>
                        <Text style={styles.flagPlaceholderText}>No image</Text>
                      </View>
                    )}
                    <View style={styles.flagContent}>
                      <Text style={styles.flagTitle}>{formatItemLabel(item.id)}</Text>
                      {item.notes ? <Text style={styles.flagNotes}>{item.notes}</Text> : null}
                      <TouchableOpacity
                        style={styles.resolveButton}
                        onPress={() =>
                          setResolved((prev) => ({
                            ...prev,
                            [item.id]: !prev[item.id],
                          }))
                        }
                      >
                        <Text style={styles.resolveText}>
                          {resolved[item.id] ? 'Resolved' : 'Mark resolved'}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                );
              })
            )}
          </View>
        </ScrollView>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1B1B1B',
  },
  topBar: {
    paddingHorizontal: 16,
    paddingBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backText: {
    color: '#F4D35E',
    fontSize: 14,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    padding: 16,
    gap: 16,
    paddingBottom: 40,
  },
  summaryCard: {
    backgroundColor: '#2A2A2A',
    borderRadius: 16,
    padding: 16,
  },
  summaryTitle: {
    color: '#9CA3AF',
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  summaryStatus: {
    color: '#F4D35E',
    fontSize: 20,
    fontWeight: '700',
    marginTop: 8,
  },
  summaryNotes: {
    color: '#D1D5DB',
    marginTop: 8,
  },
  narrativeCard: {
    backgroundColor: '#2A2A2A',
    borderRadius: 16,
    padding: 16,
    gap: 8,
  },
  narrativeText: {
    color: '#E5E7EB',
    fontSize: 14,
    lineHeight: 20,
  },
  section: {
    backgroundColor: '#2A2A2A',
    borderRadius: 16,
    padding: 16,
    gap: 16,
  },
  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  mutedText: {
    color: '#9CA3AF',
  },
  flagCard: {
    backgroundColor: '#1F1F1F',
    borderRadius: 12,
    overflow: 'hidden',
  },
  flagImage: {
    width: '100%',
    height: 160,
  },
  flagPlaceholder: {
    height: 160,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#111827',
  },
  flagPlaceholderText: {
    color: '#6B7280',
  },
  flagContent: {
    padding: 12,
    gap: 8,
  },
  flagTitle: {
    color: '#F9FAFB',
    fontSize: 15,
    fontWeight: '600',
  },
  flagNotes: {
    color: '#D1D5DB',
    fontSize: 13,
  },
  resolveButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#F4D35E',
  },
  resolveText: {
    color: '#F4D35E',
    fontSize: 12,
    fontWeight: '600',
  },
});
