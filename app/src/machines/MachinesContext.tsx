import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { Machine } from '../data/machines';
import { createMachine as createMachineApi, getMachines, MachineCreateInput } from '../api/machines';

type MachinesContextValue = {
  machines: Machine[];
  loading: boolean;
  addMachine: (machine: MachineCreateInput) => Promise<Machine | null>;
  updateMachine: (id: string, updates: Partial<Machine>) => void;
  setMachines: React.Dispatch<React.SetStateAction<Machine[]>>;
};

const MachinesContext = createContext<MachinesContextValue | null>(null);

type Props = {
  userId: number;
  children: React.ReactNode;
};

export function MachinesProvider({ userId, children }: Props) {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const parsed = await getMachines();
        if (!cancelled) {
          setMachines(Array.isArray(parsed) ? parsed : []);
        }
      } catch {
        if (!cancelled) {
          setMachines([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const addMachine = useCallback(async (machine: MachineCreateInput) => {
    try {
      const created = await createMachineApi(machine);
      setMachines((prev) => [created, ...prev]);
      return created;
    } catch {
      return null;
    }
  }, []);

  const updateMachine = useCallback((id: string, updates: Partial<Machine>) => {
    setMachines((prev) => prev.map((item) => (item.id === id ? { ...item, ...updates } : item)));
  }, []);

  const value = useMemo(
    () => ({
      machines,
      loading,
      addMachine,
      updateMachine,
      setMachines,
    }),
    [machines, loading, addMachine, updateMachine]
  );

  return <MachinesContext.Provider value={value}>{children}</MachinesContext.Provider>;
}

export function useMachines(): MachinesContextValue {
  const context = useContext(MachinesContext);
  if (!context) {
    throw new Error('useMachines must be used within MachinesProvider');
  }
  return context;
}
