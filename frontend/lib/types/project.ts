export interface Project {
  id: string;
  project_code: string;
  project_name: string;
  portfolio_cluster?: string | null;
  status: 0 | 1;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
}

export type ProjectListItem = Pick<
  Project,
  "project_code" | "project_name" | "portfolio_cluster" | "status"
>;


