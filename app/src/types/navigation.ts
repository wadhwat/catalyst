import { InspectionReportContent } from './report';

export type RootStackParamList = {
  Login: undefined;
  Home: undefined;
  MachineDetail: { machineId: string };
  InspectionCapture: { machineId: string };
  InspectionReport: {
    machineId: string;
    inspectionId?: string;
    report?: InspectionReportContent;
  };
};
