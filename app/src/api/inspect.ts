import { apiFetch } from './client';

export type InspectResponse = {
  inspection_id: string;
  client_trace_id: string;
  report_pdf_url?: string | null;
  evidence_urls: string[];
  findings?: Array<Record<string, unknown>>;
  narrative?: string | null;
  report: {
    summary: { status: string; notes?: string };
    items: Array<{
      id: string;
      status: string;
      notes?: string;
      evidence?: string[];
      recommended_parts?: string[];
    }>;
  };
};

export type UploadInspectionPayload = {
  fileUri: string;
  fileName: string;
  mimeType: string;
  machineType: string;
  niche: string;
  vin: string;
  clientTraceId: string;
  engineerNotes?: string;
};

export async function uploadInspection(payload: UploadInspectionPayload): Promise<InspectResponse> {
  const form = new FormData();
  form.append('machine_type', payload.machineType);
  form.append('niche', payload.niche);
  form.append('client_trace_id', payload.clientTraceId);
  form.append('vin', payload.vin);
  if (payload.engineerNotes) {
    form.append('engineer_notes', payload.engineerNotes);
  }
  form.append('file', {
    uri: payload.fileUri,
    name: payload.fileName,
    type: payload.mimeType,
  } as unknown as Blob);

  return apiFetch<InspectResponse>('/inspect', {
    method: 'POST',
    body: form,
  });
}
