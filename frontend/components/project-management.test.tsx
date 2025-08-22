import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ProjectManagement } from "./project-management";
import * as projectsService from "../lib/services/projects";

// Mock the language hook
vi.mock("@/hooks/use-language", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("ProjectManagement", () => {
  beforeEach(() => {
    vi.spyOn(projectsService, "fetchProjects").mockResolvedValue([
      { id: "1", code: "2ES00009", name: "Boedo 1", portfolio: "Herrera", active: true },
      { id: "2", code: "2ES00010", name: "Boedo 2", portfolio: "Herrera", active: true },
      { id: "3", code: "2DE00001", name: "Illmersdorf", portfolio: "Illmersdorf", active: false },
    ]);
  });

  it("loads and displays projects from service", async () => {
    render(<ProjectManagement />);
    
    await waitFor(() => {
      expect(screen.getByText("Boedo 1")).toBeInTheDocument();
      expect(screen.getByText("Boedo 2")).toBeInTheDocument();
    });
    // Illmersdorf is inactive and hidden by default filter
    expect(screen.queryByText("Illmersdorf")).not.toBeInTheDocument();
  });

  it("filters projects by search keyword", async () => {
    render(<ProjectManagement />);
    
    await waitFor(() => {
      expect(screen.getByText("Boedo 1")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("searchPlaceholder");
    fireEvent.change(searchInput, { target: { value: "Boedo" } });

    expect(screen.getByText("Boedo 1")).toBeInTheDocument();
    expect(screen.getByText("Boedo 2")).toBeInTheDocument();
    expect(screen.queryByText("Illmersdorf")).not.toBeInTheDocument();
  });

  it("shows inactive projects when active filter is unchecked", async () => {
    render(<ProjectManagement />);
    
    await waitFor(() => {
      expect(screen.getByText("Boedo 1")).toBeInTheDocument();
    });

    // Initially, inactive projects are hidden
    expect(screen.queryByText("Illmersdorf")).not.toBeInTheDocument();

    // Uncheck the active filter
    const activeCheckbox = screen.getByLabelText("showActiveOnly");
    fireEvent.click(activeCheckbox);

    // Now inactive projects should be visible (use getAllByText since it appears in multiple cells)
    expect(screen.getAllByText("Illmersdorf").length).toBeGreaterThan(0);
  });

  it("allows selecting individual projects", async () => {
    render(<ProjectManagement />);
    
    await waitFor(() => {
      expect(screen.getByText("Boedo 1")).toBeInTheDocument();
    });

    const firstProjectCheckbox = screen.getAllByRole("checkbox")[1]; // Skip select-all checkbox
    fireEvent.click(firstProjectCheckbox);

    // Check for the remove button with count
    expect(screen.getByText(/removeSelected/)).toBeInTheDocument();
  });

  it("allows selecting all projects", async () => {
    render(<ProjectManagement />);
    
    await waitFor(() => {
      expect(screen.getByText("Boedo 1")).toBeInTheDocument();
    });

    const selectAllCheckbox = screen.getAllByRole("checkbox")[0];
    fireEvent.click(selectAllCheckbox);

    // Check for the remove button with count
    expect(screen.getByText(/removeSelected/)).toBeInTheDocument();
  });

  it("handles status button clicks without errors", async () => {
    render(<ProjectManagement />);
    
    await waitFor(() => {
      expect(screen.getByText("Boedo 1")).toBeInTheDocument();
    });

    // Get the first active status button
    const statusButtons = screen.getAllByText("active");
    expect(statusButtons.length).toBeGreaterThan(0);
    
    // Click the first button - this should not cause any errors
    fireEvent.click(statusButtons[0]);

    // Verify the component is still functional after the click
    expect(screen.getByText("projectManagementTitle")).toBeInTheDocument();
  });
});
