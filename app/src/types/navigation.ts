import { InspectionReportContent } from './report';

export type RootStackParamList = {
  Login: undefined;
  Home: undefined;
  MachineDetail: { machineId: string };
  MachinePreferences: { machineId: string };
  ProfilePreferences: undefined;
  InspectionCapture: { machineId: string };
  InspectionReport: {
    machineId: string;
    inspectionId?: string;
    report?: InspectionReportContent;
    reportPdfUrl?: string | null;
  };
};
