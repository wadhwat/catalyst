import { apiFetch } from './client';

export type MemorySearchRequest = {
  query?: string;
  tags?: string[];
  limit?: number;
  metadata?: Record<string, unknown>;
};

export type MemorySearchResponse = {
  results: Record<string, unknown>[];
};

export async function searchMemories(payload: MemorySearchRequest): Promise<MemorySearchResponse> {
  return apiFetch<MemorySearchResponse>('/memories/search', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
