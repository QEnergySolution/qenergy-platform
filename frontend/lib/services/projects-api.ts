import { projectsApi } from '../api/projects';
import { UiProject } from './projects';
import { Project, ProjectCreate, ProjectUpdate } from '../types/project';

// Convert backend Project to frontend UiProject
const mapToUiProject = (project: Project): UiProject => {
  return {
    id: project.id,
    code: project.project_code,
    name: project.project_name,
    portfolio: project.portfolio_cluster || '',
    active: project.status === 1
  };
};

// Convert frontend UiProject to backend ProjectCreate/ProjectUpdate
const mapToProjectCreate = (project: UiProject): ProjectCreate => {
  return {
    project_code: project.code,
    project_name: project.name,
    portfolio_cluster: project.portfolio,
    status: project.active ? 1 : 0
  };
};

const mapToProjectUpdate = (project: Partial<UiProject>): ProjectUpdate => {
  const update: ProjectUpdate = {};
  
  if (project.name !== undefined) {
    update.project_name = project.name;
  }
  
  if (project.portfolio !== undefined) {
    update.portfolio_cluster = project.portfolio;
  }
  
  if (project.active !== undefined) {
    update.status = project.active ? 1 : 0;
  }
  
  return update;
};

export async function fetchProjectsFromApi(): Promise<UiProject[]> {
  try {
    // Add query parameters for pagination and sorting
    const params = {
      page: 1,
      page_size: 100, // Get a reasonable number of records
      sort_by: 'updated_at',
      sort_order: 'desc'
    };
    
    const response = await projectsApi.getProjects(params);
    
    if (response.error) {
      console.error('Error fetching projects:', response.error);
      return [];
    }
    
    // Add more detailed logging to diagnose issues
    console.log('Projects API response:', response);
    
    if (!response.data || !Array.isArray(response.data.items)) {
      console.error('Invalid projects data format:', response.data);
      return [];
    }
    
    return response.data.items.map(mapToUiProject) || [];
  } catch (error) {
    console.error('Error fetching projects:', error);
    return [];
  }
}

export async function createProject(project: UiProject): Promise<UiProject | null> {
  try {
    const projectData = mapToProjectCreate(project);
    const response = await projectsApi.createProject(projectData);
    
    if (response.error) {
      console.error('Error creating project:', response.error);
      return null;
    }
    
    return mapToUiProject(response.data!);
  } catch (error) {
    console.error('Error creating project:', error);
    return null;
  }
}

export async function updateProject(projectCode: string, project: Partial<UiProject>): Promise<UiProject | null> {
  try {
    const projectData = mapToProjectUpdate(project);
    const response = await projectsApi.updateProject(projectCode, projectData);
    
    if (response.error) {
      console.error('Error updating project:', response.error);
      return null;
    }
    
    return mapToUiProject(response.data!);
  } catch (error) {
    console.error('Error updating project:', error);
    return null;
  }
}

export async function deleteProject(projectCode: string): Promise<boolean> {
  try {
    const response = await projectsApi.deleteProject(projectCode);
    
    if (response.error) {
      console.error('Error deleting project:', response.error);
      return false;
    }
    
    // 204 No Content is the expected success response for deletion
    return response.status === 204;
  } catch (error) {
    // Handle any unexpected errors
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error('Error deleting project:', errorMessage);
    return false;
  }
}

export async function bulkUpsertProjects(projects: UiProject[], markMissingAsInactive: boolean = false): Promise<{
  success: boolean;
  createdCount?: number;
  updatedCount?: number;
  inactivatedCount?: number;
  errors?: Array<{ rowIndex: number; projectCode?: string; errorMessage: string }>;
}> {
  try {
    const projectsData = projects.map(mapToProjectCreate);
    const response = await projectsApi.bulkUpsertProjects({
      projects: projectsData,
      mark_missing_as_inactive: markMissingAsInactive
    });
    
    if (response.error) {
      console.error('Error bulk upserting projects:', response.error);
      return { success: false };
    }
    
    return response.data!;
  } catch (error) {
    console.error('Error bulk upserting projects:', error);
    return { success: false };
  }
}
