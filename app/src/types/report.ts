export type ReportSummary = {
  status: string;
  notes?: string | null;
};

export type ReportItem = {
  id: string;
  status: string;
  notes?: string | null;
  evidence_urls?: string[];
  recommended_parts?: string[];
};

export type InspectionReportContent = {
  vin: string;
  client_trace_id: string;
  observed_at?: string;
  summary: ReportSummary;
  items: ReportItem[];
  narrative?: string | null;
};
