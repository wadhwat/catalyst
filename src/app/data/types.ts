export interface Machine {
  id: string;
  model: string;
  type: string;
  image: string;
  status: "good" | "needs-check" | "critical";
  lastCheck: string;
  hoursUntilService: number;
  alerts: number;
}

export interface InspectionResult {
  id: string;
  date: string;
  time: string;
  machineId: string;
  machine: string;
  machineType: string;
  operator: string;
  status: "passed" | "warning" | "failed";
  partsChecked: number;
  issuesFound: number;
  duration: string;
  notes?: string;
  flaggedParts?: string[];
  timestamp: number;
}
