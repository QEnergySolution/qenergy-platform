import { apiClient } from "./client";
import type { ProjectListItem } from "../types/project";

export interface ListProjectsParams {
  q?: string;
  status?: 0 | 1;
  page?: number;
  page_size?: number;
}

export async function listProjects(params: ListProjectsParams = {}): Promise<ProjectListItem[]> {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.status !== undefined) search.set("status", String(params.status));
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const query = search.toString();
  const path = query ? `/projects?${query}` : "/projects";
  return apiClient.get<ProjectListItem[]>(path);
}


