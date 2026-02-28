import { createContext, useContext, useReducer, useEffect, type ReactNode } from "react";
import type { Machine, InspectionResult } from "../data/types";
import { INITIAL_MACHINES, INITIAL_HISTORY } from "../data/initialData";

interface AppState {
  machines: Machine[];
  history: InspectionResult[];
}

type Action = { type: "COMPLETE_INSPECTION"; payload: InspectionResult };

function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "COMPLETE_INSPECTION": {
      const result = action.payload;
      const newHistory = [result, ...state.history];
      const newMachines = state.machines.map((m) => {
        if (m.id !== result.machineId) return m;
        return {
          ...m,
          status:
            result.issuesFound === 0
              ? ("good" as const)
              : result.issuesFound <= 2
                ? ("needs-check" as const)
                : ("critical" as const),
          lastCheck: "Just now",
          alerts: result.issuesFound,
          hoursUntilService:
            result.issuesFound === 0 ? 500 : m.hoursUntilService,
        };
      });
      return { machines: newMachines, history: newHistory };
    }
    default:
      return state;
  }
}

const STORAGE_KEY = "catalyst-inspection-state";

function getInitialState(): AppState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return JSON.parse(stored);
  } catch {
    // ignore parse errors
  }
  return { machines: INITIAL_MACHINES, history: INITIAL_HISTORY };
}

const InspectionContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

export function InspectionProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, null, getInitialState);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  return (
    <InspectionContext.Provider value={{ state, dispatch }}>
      {children}
    </InspectionContext.Provider>
  );
}

export function useInspection() {
  const ctx = useContext(InspectionContext);
  if (!ctx)
    throw new Error("useInspection must be used within InspectionProvider");
  return ctx;
}
