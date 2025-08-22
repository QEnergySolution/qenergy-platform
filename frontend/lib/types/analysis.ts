export interface WeeklyReportAnalysis {
  id: string;
  project_code: string;
  category?: string | null;
  cw_label: string; // e.g. CW32
  language: "EN" | "DE" | "ES" | "FR" | "PT" | "KO";
  risk_lvl?: number | null; // 0..100
  risk_desc?: string | null;
  similarity_lvl?: number | null; // 0..100
  similarity_desc?: string | null;
  negative_words?: unknown; // JSONB
  created_at: string;
  created_by: string;
}


