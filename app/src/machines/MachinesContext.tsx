import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { Machine } from '../data/machines';

const STORAGE_PREFIX = 'machines:';

type MachinesContextValue = {
  machines: Machine[];
  loading: boolean;
  addMachine: (machine: Machine) => void;
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
  const [hydrated, setHydrated] = useState(false);

  const storageKey = `${STORAGE_PREFIX}${userId}`;

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const raw = await AsyncStorage.getItem(storageKey);
        if (!raw) {
          if (!cancelled) {
            setMachines([]);
          }
          return;
        }
        const parsed = JSON.parse(raw) as Machine[];
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
          setHydrated(true);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [storageKey]);

  useEffect(() => {
    if (!hydrated) return;
    AsyncStorage.setItem(storageKey, JSON.stringify(machines)).catch(() => {});
  }, [machines, storageKey, hydrated]);

  const addMachine = useCallback((machine: Machine) => {
    setMachines((prev) => [machine, ...prev]);
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
