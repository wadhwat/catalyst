import { apiFetch } from './client';
import { InspectionReportContent } from '../types/report';

export async function getReportsForVin(vin: string): Promise<InspectionReportContent[]> {
  return apiFetch<InspectionReportContent[]>(`/reports?vin=${encodeURIComponent(vin)}`, {
    method: 'GET',
  });
}

export async function getReportById(reportId: string): Promise<InspectionReportContent> {
  return apiFetch<InspectionReportContent>(`/reports/${encodeURIComponent(reportId)}`, {
    method: 'GET',
  });
}
