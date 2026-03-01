import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Camera, CameraView } from 'expo-camera';
import * as Crypto from 'expo-crypto';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { RootStackParamList } from '../types/navigation';
import { uploadInspection } from '../api/inspect';
import { InspectionReportContent } from '../types/report';
import { useMachines } from '../machines/MachinesContext';
import { Screen } from '../components/Screen';

export function InspectionCaptureScreen({
  navigation,
  route,
}: NativeStackScreenProps<RootStackParamList, 'InspectionCapture'>) {
  const { machineId } = route.params;
  const { machines } = useMachines();
  const machine = machines.find((item) => item.id === machineId);
  const [permission, setPermission] = useState<{ granted: boolean; canAskAgain?: boolean } | null>(null);
  const cameraRef = useRef<CameraView | null>(null);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    let active = true;
    Camera.getCameraPermissionsAsync()
      .then((response) => {
        if (active) {
          setPermission(response);
        }
      })
      .catch(() => {
        if (active) {
          setPermission({ granted: false, canAskAgain: true });
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;
    if (recording) {
      timer = setInterval(() => {
        setElapsed((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsed(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [recording]);

  if (!machine) {
    return (
      <Screen style={styles.container}>
        <Text style={styles.errorText}>Machine not found.</Text>
      </Screen>
    );
  }

  if (!permission) {
    return (
      <Screen style={styles.container}>
        <ActivityIndicator color="#F4D35E" />
      </Screen>
    );
  }

  if (!permission.granted) {
    return (
      <Screen style={styles.container}>
        <Text style={styles.infoText}>Camera access is required to start an inspection.</Text>
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={async () => {
            try {
              const response = await Camera.requestCameraPermissionsAsync();
              setPermission(response);
            } catch {
              setPermission({ granted: false, canAskAgain: false });
            }
          }}
        >
          <Text style={styles.primaryButtonText}>Enable Camera</Text>
        </TouchableOpacity>
      </Screen>
    );
  }

  const handleStart = async () => {
    if (recording || uploading || !cameraRef.current) return;
    setRecording(true);
    try {
      const video = await cameraRef.current.recordAsync({
        maxDuration: 300,
      });
      if (!video?.uri) return;
      setUploading(true);
      const clientTraceId = Crypto.randomUUID();
      const response = await uploadInspection({
        fileUri: video.uri,
        fileName: `inspection-${clientTraceId}.mp4`,
        mimeType: 'video/mp4',
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
        narrative: response.narrative ?? null,
      };

      navigation.replace('InspectionReport', {
        machineId: machine.id,
        inspectionId: response.client_trace_id,
        report,
      });
    } catch (error) {
      Alert.alert('Inspection failed', String(error));
    } finally {
      setUploading(false);
      setRecording(false);
    }
  };

  const handleStop = async () => {
    if (!recording || !cameraRef.current) return;
    await cameraRef.current.stopRecording();
    setRecording(false);
  };

  const timerLabel = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')}`;

  return (
    <Screen style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backText}>Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{machine.name}</Text>
      </View>

      <View style={styles.cameraWrapper}>
        <CameraView ref={cameraRef} style={styles.camera} facing="back" mode="video" />
        <View style={styles.overlay}>
          <Text style={styles.timer}>{timerLabel}</Text>
          <View style={styles.controls}>
            <TouchableOpacity
              style={[styles.controlButton, recording ? styles.stopButton : styles.startButton]}
              onPress={recording ? handleStop : handleStart}
              disabled={uploading}
            >
              {uploading ? (
                <ActivityIndicator color="#1B1B1B" />
              ) : (
                <Text style={styles.controlText}>{recording ? 'Stop Inspection' : 'Start Recording'}</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
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
    fontWeight: '600',
    fontSize: 16,
  },
  cameraWrapper: {
    flex: 1,
    margin: 16,
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    padding: 16,
    backgroundColor: 'rgba(0,0,0,0.55)',
  },
  timer: {
    color: '#F4D35E',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  controls: {
    alignItems: 'center',
  },
  controlButton: {
    borderRadius: 18,
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  startButton: {
    backgroundColor: '#F4D35E',
  },
  stopButton: {
    backgroundColor: '#F87171',
  },
  controlText: {
    color: '#1B1B1B',
    fontWeight: '700',
  },
  infoText: {
    color: '#D1D5DB',
    textAlign: 'center',
    marginHorizontal: 24,
    marginTop: 24,
  },
  primaryButton: {
    marginTop: 20,
    backgroundColor: '#F4D35E',
    marginHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 16,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#1B1B1B',
    fontWeight: '700',
  },
  errorText: {
    color: '#F87171',
    textAlign: 'center',
    marginTop: 40,
  },
});
