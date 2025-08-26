const BASE_URL = (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) || "http://localhost:8002/api";

export interface BulkUploadOkItem {
  fileName: string;
  status: "ok";
  year: number;
  cw_label: string;
  category_raw: "DEV" | "EPC" | "FINANCE" | "INVESTMENT";
  category: "Development" | "EPC" | "Finance" | "Investment";
  rows: Array<{
    category: string;
    entry_type: string;
    cw_label: string;
    title?: string | null;
    summary: string;
    next_actions?: string | null;
    owner?: string | null;
    attachment_url?: string | null;
  }>;
  errors: Array<{ code: string; message: string; meta?: unknown }>;
}

export interface BulkUploadErrorItem {
  fileName: string;
  status: "error";
  errors: Array<{ code: string; message: string; meta?: unknown }>;
}

export interface BulkUploadResponse {
  results: Array<BulkUploadOkItem | BulkUploadErrorItem>;
  summary: { filesAccepted: number; filesRejected: number; rowsTotal: number };
}

export async function uploadBulk(files: File[]): Promise<BulkUploadResponse> {
  const form = new FormData();
  for (const f of files) {
    form.append("files", f, f.name);
  }
  const res = await fetch(`${BASE_URL.replace(/\/$/, "")}/reports/upload/bulk`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Bulk upload failed: ${res.status} ${text}`);
  }
  return (await res.json()) as BulkUploadResponse;
}


