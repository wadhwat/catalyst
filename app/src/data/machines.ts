export type MachineStatus = 'PASS' | 'MONITOR' | 'FAIL';

export type Machine = {
  id: string;
  name: string;
  vin: string;
  lastInspectedMs: number;
  status: MachineStatus;
  criticalIssues: number;
  criticalIssueLabels?: string[];
  componentIssues?: Array<{ component: string; count: number }>;
  imageUrl: string;
  machineType: string;
  niche: string;
};

const hours = (value: number) => value * 60 * 60 * 1000;

export const machines: Machine[] = [
  {
    id: '1',
    name: 'CAT 908M',
    vin: '1HGCM826...',
    lastInspectedMs: Date.now() - hours(3),
    status: 'PASS',
    criticalIssues: 0,
    componentIssues: [
      { component: 'Hydraulics', count: 1 },
      { component: 'Tires', count: 0 },
      { component: 'Engine', count: 0 },
    ],
    imageUrl: 'https://images.unsplash.com/photo-1715681025163-24ffe5ae32ea?auto=format&fit=crop&w=1200&q=80',
    machineType: 'wheel_loader',
    niche: 'construction',
  },
  {
    id: '2',
    name: 'JCB 3CX',
    vin: '2HGES165...',
    lastInspectedMs: Date.now() - hours(7),
    status: 'MONITOR',
    criticalIssues: 2,
    criticalIssueLabels: ['Cooling system overheating', 'Hydraulic seepage'],
    componentIssues: [
      { component: 'Cooling', count: 3 },
      { component: 'Hoses', count: 2 },
      { component: 'Hydraulics', count: 1 },
    ],
    imageUrl: 'https://images.unsplash.com/photo-1652922660696-60c68ec51582?auto=format&fit=crop&w=1200&q=80',
    machineType: 'backhoe',
    niche: 'earthworks',
  },
  {
    id: '3',
    name: 'Komatsu D65',
    vin: '3FADP4BJ...',
    lastInspectedMs: Date.now() - hours(1),
    status: 'PASS',
    criticalIssues: 0,
    componentIssues: [
      { component: 'Engine', count: 0 },
      { component: 'Hydraulics', count: 0 },
    ],
    imageUrl: 'https://images.unsplash.com/photo-1627451945663-5c1daa80cb20?auto=format&fit=crop&w=1200&q=80',
    machineType: 'dozer',
    niche: 'mining',
  },
  {
    id: '4',
    name: 'Volvo EC380',
    vin: '4T1BF1FK...',
    lastInspectedMs: Date.now() - hours(11),
    status: 'FAIL',
    criticalIssues: 5,
    criticalIssueLabels: ['Engine temperature spike', 'Hydraulic line rupture', 'Cab glass crack'],
    componentIssues: [
      { component: 'Engine', count: 4 },
      { component: 'Cooling', count: 3 },
      { component: 'Hoses', count: 2 },
    ],
    imageUrl: 'https://images.unsplash.com/photo-1630288215006-a7058b0bfd89?auto=format&fit=crop&w=1200&q=80',
    machineType: 'excavator',
    niche: 'infrastructure',
  },
  {
    id: '5',
    name: 'Bobcat S650',
    vin: '5TDKZ3DC...',
    lastInspectedMs: Date.now() - hours(5),
    status: 'MONITOR',
    criticalIssues: 1,
    criticalIssueLabels: ['Hose wear detected'],
    componentIssues: [
      { component: 'Hoses', count: 3 },
      { component: 'Tires', count: 1 },
    ],
    imageUrl: 'https://images.unsplash.com/photo-1630628535113-e1cc025c8c34?auto=format&fit=crop&w=1200&q=80',
    machineType: 'skid_steer',
    niche: 'sitework',
  },
];
