import { describe, it, expect, vi, beforeEach } from "vitest";
import * as clientMod from "./client";
import { listProjects } from "./projects";

describe("projects API", () => {
  beforeEach(() => {
    vi.spyOn(clientMod, "apiClient", "get").mockReturnValue({
      get: vi.fn().mockResolvedValueOnce([
        { project_code: "2ES00009", project_name: "Boedo 1", portfolio_cluster: "Herrera", status: 1 },
      ]),
    } as any);
  });

  it("lists projects with default params", async () => {
    const res = await listProjects();
    expect(res.length).toBe(1);
    expect(res[0].project_code).toBe("2ES00009");
  });
});


