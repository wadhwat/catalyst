import { useEffect, useState } from 'react';

export function formatTimeAgo(timestampMs: number, nowMs: number = Date.now()): string {
  const diffMs = Math.max(0, nowMs - timestampMs);
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  if (hours < 1) {
    const minutes = Math.max(1, Math.floor(diffMs / (1000 * 60)));
    return `${minutes}m ago`;
  }
  return `${hours}h ago`;
}

export function formatShortDate(iso: string | undefined): string {
  if (!iso) return 'Unknown';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return 'Unknown';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function useNow(intervalMs: number = 60000): number {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}
