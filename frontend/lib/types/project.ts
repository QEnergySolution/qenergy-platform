export interface Project {
  id: string;
  project_code: string;
  project_name: string;
  portfolio_cluster?: string;
  status: number;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export interface ProjectCreate {
  project_code: string;
  project_name: string;
  portfolio_cluster?: string;
  status: number;
}

export interface ProjectUpdate {
  project_name?: string;
  portfolio_cluster?: string;
  status?: number;
}

export interface ProjectPagination {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProjectBulkUpsertRow {
  project_code: string;
  project_name: string;
  portfolio_cluster?: string;
  status: number;
}

export interface ProjectBulkUpsertRequest {
  projects: ProjectBulkUpsertRow[];
  mark_missing_as_inactive?: boolean;
}

export interface ProjectBulkUpsertError {
  row_index: number;
  project_code?: string;
  error_message: string;
}

export interface ProjectBulkUpsertResponse {
  success: boolean;
  created_count?: number;
  updated_count?: number;
  inactivated_count?: number;
  errors?: ProjectBulkUpsertError[];
}