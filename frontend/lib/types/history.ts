export interface ProjectHistoryEntry {
  id: string;
  project_code: string;
  category?: string | null;
  entry_type: "Report" | "Issue" | "Decision" | "Maintenance" | "Meeting minutes" | "Mid-update";
  log_date: string; // YYYY-MM-DD
  cw_label?: string | null;
  title?: string | null;
  summary: string;
  next_actions?: string | null;
  owner?: string | null;
  attachment_url?: string | null;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}


