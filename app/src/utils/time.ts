export function formatTimeAgo(timestampMs: number): string {
  const now = Date.now();
  const diffMs = Math.max(0, now - timestampMs);
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
