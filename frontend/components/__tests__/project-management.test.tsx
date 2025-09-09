import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ProjectManagement } from "../project-management";
import * as projectsApi from "@/lib/services/projects-api";
import { UiProject } from "@/lib/services/projects";

// Mock the API functions
jest.mock("@/lib/services/projects-api", () => ({
  fetchProjectsFromApi: jest.fn(),
  createProject: jest.fn(),
  updateProject: jest.fn(),
  deleteProject: jest.fn(),
  bulkUpsertProjects: jest.fn(),
}));

// Mock the hooks
jest.mock("@/hooks/use-language", () => ({
  useLanguage: () => ({
    t: (key: string) => key, // Return the key as the translation
  }),
}));

jest.mock("@/components/ui/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

const mockProjects: UiProject[] = [
  { id: "1", code: "TEST001", name: "Test Project 1", portfolio: "Portfolio A", active: true },
  { id: "2", code: "TEST002", name: "Test Project 2", portfolio: "Portfolio B", active: false },
  { id: "3", code: "TEST003", name: "Test Project 3", portfolio: "Portfolio A", active: true },
];

describe("ProjectManagement Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (projectsApi.fetchProjectsFromApi as jest.Mock).mockResolvedValue(mockProjects);
  });

  test("renders project management title", async () => {
    render(<ProjectManagement />);
    expect(screen.getByText("projectManagementTitle")).toBeInTheDocument();
  });

  test("loads and displays projects", async () => {
    render(<ProjectManagement />);
    
    // Should show loading initially
    expect(screen.getByText("loading...")).toBeInTheDocument();
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText("TEST001")).toBeInTheDocument();
      expect(screen.getByText("TEST002")).toBeInTheDocument();
      expect(screen.getByText("TEST003")).toBeInTheDocument();
    });
    
    // Check if API was called
    expect(projectsApi.fetchProjectsFromApi).toHaveBeenCalledTimes(1);
  });

  test("filters projects by search term", async () => {
    render(<ProjectManagement />);
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText("TEST001")).toBeInTheDocument();
    });
    
    // Search for "TEST001"
    const searchInput = screen.getByPlaceholderText("searchPlaceholder");
    fireEvent.change(searchInput, { target: { value: "TEST001" } });
    
    // Should show TEST001 but not TEST002 or TEST003
    expect(screen.getByText("TEST001")).toBeInTheDocument();
    expect(screen.queryByText("TEST002")).not.toBeInTheDocument();
    expect(screen.queryByText("TEST003")).not.toBeInTheDocument();
  });

  test("filters projects by active status", async () => {
    render(<ProjectManagement />);
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText("TEST001")).toBeInTheDocument();
    });
    
    // By default, should only show active projects
    expect(screen.getByText("TEST001")).toBeInTheDocument();
    expect(screen.queryByText("TEST002")).not.toBeInTheDocument();
    expect(screen.getByText("TEST003")).toBeInTheDocument();
    
    // Uncheck "Show Active Only"
    const checkbox = screen.getByLabelText("showActiveOnly");
    fireEvent.click(checkbox);
    
    // Should show all projects now
    expect(screen.getByText("TEST001")).toBeInTheDocument();
    expect(screen.getByText("TEST002")).toBeInTheDocument();
    expect(screen.getByText("TEST003")).toBeInTheDocument();
  });

  test("toggles project status", async () => {
    (projectsApi.updateProject as jest.Mock).mockResolvedValue({
      id: "1",
      code: "TEST001",
      name: "Test Project 1",
      portfolio: "Portfolio A",
      active: false,
    });
    
    render(<ProjectManagement />);
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText("TEST001")).toBeInTheDocument();
    });
    
    // Find the status button for TEST001 and click it
    const statusButtons = screen.getAllByText("active");
    fireEvent.click(statusButtons[0]);
    
    // Should call updateProject
    await waitFor(() => {
      expect(projectsApi.updateProject).toHaveBeenCalledWith("TEST001", { active: false });
    });
  });

  test("selects and deselects projects", async () => {
    render(<ProjectManagement />);
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText("TEST001")).toBeInTheDocument();
    });
    
    // Select the first project
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]); // First project checkbox (index 1 because index 0 is the "select all" checkbox)
    
    // Remove button should show count
    expect(screen.getByText("removeSelected (1)")).toBeInTheDocument();
    
    // Deselect the project
    fireEvent.click(checkboxes[1]);
    
    // Remove button should show count 0
    expect(screen.getByText("removeSelected (0)")).toBeInTheDocument();
  });

  test("selects all projects", async () => {
    render(<ProjectManagement />);
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText("TEST001")).toBeInTheDocument();
    });
    
    // First uncheck "Show Active Only" to show all projects
    const activeOnlyCheckbox = screen.getByLabelText("showActiveOnly");
    fireEvent.click(activeOnlyCheckbox);
    
    // Select all projects
    const selectAllCheckbox = screen.getAllByRole("checkbox")[0]; // The "select all" checkbox
    fireEvent.click(selectAllCheckbox);
    
    // Remove button should show count of all projects
    expect(screen.getByText("removeSelected (3)")).toBeInTheDocument();
    
    // Deselect all projects
    fireEvent.click(selectAllCheckbox);
    
    // Remove button should show count 0
    expect(screen.getByText("removeSelected (0)")).toBeInTheDocument();
  });

  test("opens add project dialog", async () => {
    render(<ProjectManagement />);
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText("TEST001")).toBeInTheDocument();
    });
    
    // Click the "Add Project" button
    const addButton = screen.getByText("addProject");
    fireEvent.click(addButton);
    
    // Dialog should be open
    await waitFor(() => {
      expect(screen.getByText("addProject")).toBeInTheDocument(); // Dialog title
    });
  });

  test("opens excel upload dialog", async () => {
    render(<ProjectManagement />);
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText("TEST001")).toBeInTheDocument();
    });
    
    // Click the "Upload Excel" button
    const uploadButton = screen.getByText("uploadExcel");
    fireEvent.click(uploadButton);
    
    // Dialog should be open
    await waitFor(() => {
      expect(screen.getByText("uploadExcel")).toBeInTheDocument(); // Dialog title
    });
  });

  test("handles API error", async () => {
    (projectsApi.fetchProjectsFromApi as jest.Mock).mockRejectedValue(new Error("API error"));
    
    render(<ProjectManagement />);
    
    // Should show error
    await waitFor(() => {
      expect(screen.getByText("error")).toBeInTheDocument();
      expect(screen.getByText("failedToLoadProjects")).toBeInTheDocument();
    });
  });
});
