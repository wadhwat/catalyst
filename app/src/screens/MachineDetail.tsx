import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import * as DocumentPicker from 'expo-document-picker';
import * as Crypto from 'expo-crypto';

import { RootStackParamList } from '../types/navigation';
import { machines } from '../data/machines';
import { uploadInspection } from '../api/inspect';
import { searchMemories } from '../api/memories';
import { InspectionReportContent } from '../types/report';
import { formatShortDate } from '../utils/time';

export function MachineDetailScreen({
  navigation,
  route,
}: NativeStackScreenProps<RootStackParamList, 'MachineDetail'>) {
  const { machineId } = route.params;
  const machine = useMemo(() => machines.find((item) => item.id === machineId), [machineId]);
  const [uploading, setUploading] = useState(false);
  const [history, setHistory] = useState<InspectionReportContent[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [resolvedIssues, setResolvedIssues] = useState<Record<string, boolean>>({});

  const loadHistory = useCallback(async () => {
    if (!machine) return;
    setHistoryLoading(true);
    try {
      const response = await searchMemories({
        tags: [`vin:${machine.vin}`, 'kind:inspection_report'],
        limit: 20,
      });
      const results = response?.results ?? [];
      const parsed = results
        .map((result) => {
          const content = (result as any).content as InspectionReportContent | undefined;
          if (!content || !content.client_trace_id) return null;
          return content;
        })
        .filter(Boolean) as InspectionReportContent[];

      parsed.sort((a, b) => {
        const aTime = a.observed_at ? new Date(a.observed_at).getTime() : 0;
        const bTime = b.observed_at ? new Date(b.observed_at).getTime() : 0;
        return bTime - aTime;
      });
      setHistory(parsed);
    } catch (error) {
      Alert.alert('History unavailable', String(error));
    } finally {
      setHistoryLoading(false);
    }
  }, [machine]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  if (!machine) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Machine not found.</Text>
      </View>
    );
  }

  const handleUploadRecorded = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({ type: 'video/*', copyToCacheDirectory: true });
      if (result.canceled || !result.assets?.length) return;
      const asset = result.assets[0];
      const fileUri = asset.uri;
      const fileName = asset.name ?? `inspection-${Date.now()}.mp4`;
      const mimeType = asset.mimeType ?? 'video/mp4';

      setUploading(true);
      const clientTraceId = Crypto.randomUUID();
      const response = await uploadInspection({
        fileUri,
        fileName,
        mimeType,
        machineType: machine.machineType,
        niche: machine.niche,
        vin: machine.vin,
        clientTraceId,
      });

      const report: InspectionReportContent = {
        vin: machine.vin,
        client_trace_id: response.client_trace_id,
        observed_at: new Date().toISOString(),
        summary: response.report.summary,
        items: response.report.items.map((item) => ({
          id: item.id,
          status: item.status,
          notes: item.notes,
          evidence_urls: item.evidence,
        })),
      };

      navigation.navigate('InspectionReport', {
        machineId: machine.id,
        inspectionId: response.client_trace_id,
        report,
      });
    } catch (error) {
      Alert.alert('Upload failed', String(error));
    } finally {
      setUploading(false);
    }
  };

  const issueLabels = machine.criticalIssueLabels ?? [];

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backText}>Back</Text>
        </TouchableOpacity>
        <Text style={styles.machineTitle}>{machine.name}</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => navigation.navigate('InspectionCapture', { machineId: machine.id })}
          disabled={uploading}
        >
          <Text style={styles.primaryButtonText}>Start Inspection</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={handleUploadRecorded}
          disabled={uploading}
        >
          {uploading ? (
            <ActivityIndicator color="#F4D35E" />
          ) : (
            <Text style={styles.secondaryButtonText}>Upload Recorded Video</Text>
          )}
        </TouchableOpacity>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Critical Issues</Text>
          {issueLabels.length === 0 ? (
            <Text style={styles.mutedText}>No critical issues reported.</Text>
          ) : (
            issueLabels.map((issue) => (
              <View key={issue} style={styles.issueRow}>
                <Text style={styles.issueText}>{issue}</Text>
                <TouchableOpacity
                  style={[
                    styles.issueAction,
                    resolvedIssues[issue] && { backgroundColor: '#1F2937', borderColor: '#4B5563' },
                  ]}
                  onPress={() =>
                    setResolvedIssues((prev) => ({
                      ...prev,
                      [issue]: !prev[issue],
                    }))
                  }
                >
                  <Text style={styles.issueActionText}>
                    {resolvedIssues[issue] ? 'Resolved' : 'Mark resolved'}
                  </Text>
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Issues by Component</Text>
          {(machine.componentIssues ?? []).map((item) => (
            <View key={item.component} style={styles.componentRow}>
              <Text style={styles.componentLabel}>{item.component}</Text>
              <View style={styles.componentCountBadge}>
                <Text style={styles.componentCountText}>{item.count}</Text>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Inspection History</Text>
          {historyLoading ? (
            <ActivityIndicator color="#F4D35E" />
          ) : history.length === 0 ? (
            <Text style={styles.mutedText}>No inspections yet.</Text>
          ) : (
            history.map((item) => (
              <TouchableOpacity
                key={item.client_trace_id}
                style={styles.historyRow}
                onPress={() =>
                  navigation.navigate('InspectionReport', {
                    machineId: machine.id,
                    inspectionId: item.client_trace_id,
                    report: item,
                  })
                }
              >
                <View>
                  <Text style={styles.historyDate}>{formatShortDate(item.observed_at)}</Text>
                  <Text style={styles.historyStatus}>{item.summary.status}</Text>
                </View>
                <Text style={styles.historyChevron}>›</Text>
              </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1B1B1B',
  },
  topBar: {
    paddingTop: 16,
    paddingHorizontal: 16,
    paddingBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    paddingVertical: 6,
    paddingRight: 12,
  },
  backText: {
    color: '#F4D35E',
    fontSize: 15,
  },
  machineTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 40,
    gap: 20,
  },
  primaryButton: {
    height: 56,
    backgroundColor: '#F4D35E',
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonText: {
    color: '#1B1B1B',
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    height: 48,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: '#F4D35E',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2A2A2A',
  },
  secondaryButtonText: {
    color: '#F4D35E',
    fontSize: 14,
    fontWeight: '600',
  },
  section: {
    backgroundColor: '#2A2A2A',
    borderRadius: 16,
    padding: 16,
    gap: 12,
  },
  sectionTitle: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 16,
  },
  mutedText: {
    color: '#9CA3AF',
  },
  issueRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  issueText: {
    color: '#FCA5A5',
    flex: 1,
  },
  issueAction: {
    borderWidth: 1,
    borderColor: '#F4D35E',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  issueActionText: {
    color: '#F4D35E',
    fontSize: 12,
    fontWeight: '600',
  },
  componentRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  componentLabel: {
    color: '#E5E7EB',
    fontSize: 14,
  },
  componentCountBadge: {
    backgroundColor: '#111827',
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  componentCountText: {
    color: '#F4D35E',
    fontSize: 12,
    fontWeight: '600',
  },
  historyRow: {
    backgroundColor: '#1F1F1F',
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  historyDate: {
    color: '#E5E7EB',
    fontSize: 14,
    fontWeight: '600',
  },
  historyStatus: {
    color: '#F4D35E',
    fontSize: 12,
    marginTop: 4,
  },
  historyChevron: {
    color: '#9CA3AF',
    fontSize: 22,
  },
  errorText: {
    color: '#F87171',
    fontSize: 16,
    padding: 24,
  },
});
