import { apiClient } from './client';
import {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectPagination,
  ProjectBulkUpsertRequest,
  ProjectBulkUpsertResponse,
} from '../types/project';

export interface GetProjectsParams {
  search?: string;
  status?: number;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}

export const projectsApi = {
  /**
   * Get projects with pagination, filtering, and sorting
   */
  getProjects: async (params: GetProjectsParams = {}) => {
    const queryParams = apiClient.buildQueryParams(params);
    return apiClient.get<ProjectPagination>(`/projects${queryParams}`);
  },

  /**
   * Get a project by its business key (project_code)
   */
  getProject: async (projectCode: string) => {
    return apiClient.get<Project>(`/projects/${projectCode}`);
  },

  /**
   * Create a new project
   */
  createProject: async (project: ProjectCreate) => {
    return apiClient.post<Project>('/projects', project);
  },

  /**
   * Update a project by its business key (project_code)
   */
  updateProject: async (projectCode: string, project: ProjectUpdate) => {
    return apiClient.put<Project>(`/projects/${projectCode}`, project);
  },

  /**
   * Soft delete a project (set status=0) by its business key (project_code)
   */
  deleteProject: async (projectCode: string) => {
    return apiClient.delete(`/projects/${projectCode}`);
  },

  /**
   * Bulk upsert projects by project_code
   */
  bulkUpsertProjects: async (request: ProjectBulkUpsertRequest) => {
    return apiClient.post<ProjectBulkUpsertResponse>('/projects/bulk-upsert', request);
  },
};