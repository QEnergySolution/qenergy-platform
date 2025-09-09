export type EntryType = 
  | 'Report'
  | 'Issue'
  | 'Decision'
  | 'Maintenance'
  | 'Meeting minutes'
  | 'Mid-update';

export type Category = 
  | 'Development'
  | 'EPC'
  | 'Finance'
  | 'Investment';

export interface ProjectHistory {
  id: string;
  project_code: string;
  category?: string;
  entry_type: EntryType;
  log_date: string;
  cw_label?: string;
  title?: string;
  summary: string;
  next_actions?: string;
  owner?: string;
  attachment_url?: string;
  source_text?: string;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export interface ProjectHistoryCreate {
  project_code: string;
  category?: string;
  entry_type: EntryType;
  log_date: string;
  cw_label?: string;
  title?: string;
  summary: string;
  next_actions?: string;
  owner?: string;
  attachment_url?: string;
}

export interface ProjectHistoryUpdate {
  category?: string;
  entry_type?: EntryType;
  title?: string;
  summary?: string;
  next_actions?: string;
  owner?: string;
  attachment_url?: string;
}

export interface ProjectHistoryPagination {
  items: ProjectHistory[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProjectHistoryContent {
  project_code: string;
  cw_label: string;
  category?: string;
  content: string;
}
