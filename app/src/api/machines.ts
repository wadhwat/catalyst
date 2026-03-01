import { apiFetch } from './client';
import { Machine } from '../data/machines';

export type MachineCreateInput = {
  name: string;
  vin: string;
  machineType: string;
  niche: string;
  imageUrl?: string;
};

export async function getMachines(): Promise<Machine[]> {
  return apiFetch<Machine[]>('/machines', { method: 'GET' });
}

export async function createMachine(input: MachineCreateInput): Promise<Machine> {
  return apiFetch<Machine>('/machines', {
    method: 'POST',
    body: JSON.stringify({
      name: input.name,
      vin: input.vin,
      machine_type: input.machineType,
      niche: input.niche,
      image_url: input.imageUrl ?? null,
    }),
  });
}
