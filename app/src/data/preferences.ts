export type CaptureResolution = '720p' | '1080p';

export type InspectionPreferences = {
  inspectionCadenceHours: number;
  captureMaxDurationSec: number;
  frameSampleFps: number;
  captureResolution: CaptureResolution;
  autoUpload: boolean;
};

export type MachinePreferences = Partial<InspectionPreferences>;

export const DEFAULT_PREFERENCES: InspectionPreferences = {
  inspectionCadenceHours: 12,
  captureMaxDurationSec: 120,
  frameSampleFps: 1,
  captureResolution: '1080p',
  autoUpload: true,
};
