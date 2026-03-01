export type MachineStatus = 'PASS' | 'MONITOR' | 'FAIL' | 'UNKNOWN';

export type Machine = {
  id: string;
  name: string;
  vin: string;
  lastInspectedMs: number | null;
  status: MachineStatus;
  criticalIssues: number;
  criticalIssueLabels?: string[];
  componentIssues?: Array<{ component: string; count: number }>;
  imageUrl?: string;
  machineType: string;
  niche: string;
};
export const DEFAULT_MACHINE_IMAGE =
  'https://images.unsplash.com/photo-1471513671800-b09c87e1497c?auto=format&fit=crop&w=1200&q=80';
