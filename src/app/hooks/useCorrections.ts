import { useState, useCallback } from 'react';
import type { CorrectionRequest, CorrectionResponse } from '../types/inspection';

const API_BASE = import.meta.env.VITE_API_URL || '';

export function useCorrections() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitCorrection = useCallback(
    async (correction: CorrectionRequest, token: string): Promise<CorrectionResponse | null> => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/corrections`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(correction),
        });

        if (!response.ok) {
          const detail = await response.text();
          throw new Error(detail || `HTTP ${response.status}`);
        }

        return await response.json();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const searchCorrections = useCallback(
    async (
      params: { item_id?: string; vin?: string; limit?: number },
      token: string
    ): Promise<CorrectionResponse[]> => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/corrections/search`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(params),
        });

        if (!response.ok) {
          const detail = await response.text();
          throw new Error(detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        return data.corrections || [];
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return [];
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    loading,
    error,
    submitCorrection,
    searchCorrections,
  };
}
