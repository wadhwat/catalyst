export type ClassificationStatus = 'PASS' | 'MONITOR' | 'FAIL' | 'UNKNOWN';

export interface VLMClassification {
  status: ClassificationStatus;
  score: number;
  confidence: number;
  reasoning?: string;
}

export interface CorrectionRequest {
  item_id: string;
  vin: string;
  client_trace_id: string;
  original_status: string;
  original_score: number;
  original_confidence: number;
  original_reasoning?: string;
  corrected_status: string;
  corrected_score: number;
  correction_notes: string;
  frame_sha256: string;
  frame_filename?: string;
}

export interface CorrectionResponse {
  id: string;
  item_id: string;
  vin: string;
  created_at: string;
  original_status: string;
  original_score: number;
  corrected_status: string;
  corrected_score: number;
  correction_notes: string;
}

export interface InspectionReport {
  client_trace_id: string;
  vin: string;
  summary: { status: string; notes?: string };
  items: Array<{
    id: string;
    status: string;
    score: number;
    notes?: string;
    evidence: string[];
  }>;
}

export interface InspectionResponse {
  client_trace_id: string;
  received: {
    machine_type: string;
    niche: string;
    vin: string;
    filename: string;
    content_type: string;
    saved_path: string;
  };
  evidence_frames: string[];
  frame_warning?: string;
  report: InspectionReport;
  vlm_classifications: Record<string, VLMClassification>;
  memory_context: unknown[];
  memory_write_status: Record<string, string>;
}
