import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiClient } from "./client";

describe("ApiClient", () => {
  const originalFetch = global.fetch;
  beforeEach(() => {
    global.fetch = vi.fn();
  });
  
  it("prefixes base URL and parses JSON", async () => {
    const client = new ApiClient({ baseUrl: "http://example.com/api" });
    (global.fetch as any).mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), { status: 200 })
    );
    const res = await client.get<{ ok: boolean }>("/health");
    expect(res.ok).toBe(true);
    expect((global.fetch as any).mock.calls[0][0]).toBe("http://example.com/api/health");
  });

  it("throws on non-2xx", async () => {
    const client = new ApiClient({ baseUrl: "http://example.com/api" });
    (global.fetch as any).mockResolvedValueOnce(new Response("bad", { status: 500 }));
    await expect(client.get("/boom")).rejects.toThrow(/API 500/);
  });

  afterAll(() => {
    global.fetch = originalFetch as any;
  });
});


