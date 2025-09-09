import { apiClient } from './client';
import {
  ProjectHistory,
  ProjectHistoryCreate,
  ProjectHistoryUpdate,
  ProjectHistoryPagination,
  ProjectHistoryContent,
} from '../types/project-history';

export interface GetProjectHistoryParams {
  project_code?: string;
  category?: string;
  cw_label?: string;
  start_cw?: string;
  end_cw?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}

export interface GetProjectHistoryContentParams {
  project_code: string;
  cw_label: string;
  category?: string;
}

export const projectHistoryApi = {
  /**
   * Get project history entries with filtering and pagination
   */
  getProjectHistory: async (params: GetProjectHistoryParams = {}) => {
    const queryParams = apiClient.buildQueryParams(params);
    return apiClient.get<ProjectHistoryPagination>(`/project-history${queryParams}`);
  },

  /**
   * Get the summary content for a specific project, CW label, and category
   */
  getProjectHistoryContent: async (params: GetProjectHistoryContentParams) => {
    const queryParams = apiClient.buildQueryParams(params);
    return apiClient.get<ProjectHistoryContent>(`/project-history/content${queryParams}`);
  },

  /**
   * Get a project history entry by its ID
   */
  getProjectHistoryById: async (historyId: string) => {
    return apiClient.get<ProjectHistory>(`/project-history/${historyId}`);
  },

  /**
   * Create a new project history entry
   */
  createProjectHistory: async (history: ProjectHistoryCreate) => {
    return apiClient.post<ProjectHistory>('/project-history', history);
  },

  /**
   * Update a project history entry by its ID
   */
  updateProjectHistory: async (historyId: string, history: ProjectHistoryUpdate) => {
    return apiClient.put<ProjectHistory>(`/project-history/${historyId}`, history);
  },

  /**
   * Upsert a project history entry by project_code and log_date
   */
  upsertProjectHistory: async (history: ProjectHistoryCreate) => {
    return apiClient.post<ProjectHistory>('/project-history/upsert', history);
  },

  /**
   * Delete a project history entry by its ID
   */
  deleteProjectHistory: async (historyId: string) => {
    return apiClient.delete(`/project-history/${historyId}`);
  },
};
