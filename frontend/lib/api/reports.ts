const BASE_URL = (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) || "http://localhost:8002/api";

export interface BulkUploadOkItem {
  fileName: string;
  status: "ok";
  year: number;
  cw_label: string;
  category_raw: "DEV" | "EPC" | "FINANCE" | "INVESTMENT";
  category: "Development" | "EPC" | "Finance" | "Investment";
  rows: Array<{
    project_name?: string;
    category: string;
    entry_type: string;
    cw_label: string;
    title?: string | null;
    summary: string;
    next_actions?: string | null;
    owner?: string | null;
    attachment_url?: string | null;
    source_text?: string | null;
  }>;
  parsedWith?: "llm" | "simple";
  errors: Array<{ code: string; message: string; meta?: unknown }>;
}

export interface BulkUploadErrorItem {
  fileName: string;
  status: "error";
  errors: Array<{ code: string; message: string; meta?: unknown }>;
}

export interface BulkUploadResponse {
  results: Array<BulkUploadOkItem | BulkUploadErrorItem>;
  summary: { 
    filesAccepted: number; 
    filesRejected: number; 
    rowsTotal: number;
    parsedWith?: "llm" | "simple";
  };
}

export interface SingleUploadResponse {
  taskId: string;
  fileName: string;
  mimeType?: string;
  size?: number;
  year: number;
  cw_label: string;
  category_raw: "DEV" | "EPC" | "FINANCE" | "INVESTMENT";
  category: "Development" | "EPC" | "Finance" | "Investment";
  rows: Array<{
    project_name?: string;
    category: string;
    entry_type: string;
    cw_label: string;
    title?: string | null;
    summary: string;
    next_actions?: string | null;
    owner?: string | null;
    attachment_url?: string | null;
    source_text?: string | null;
  }>;
  parsedWith?: "llm" | "simple";
  errors: Array<{ code: string; message: string; meta?: unknown }>;
}

export interface TaskUpdate {
  task_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  current_step: "upload_received" | "document_loading" | "text_extraction" | "llm_processing" | "data_validation" | "saving_results" | "completed";
  progress: number; // 0-100
  message: string;
  timestamp: string;
  error_message?: string;
  result_count?: number;
}

export async function uploadSingle(file: File, useLlm: boolean = false): Promise<SingleUploadResponse> {
  const form = new FormData();
  form.append("file", file, file.name);
  
  const url = new URL(`${BASE_URL.replace(/\/$/, "")}/reports/upload`);
  if (useLlm) {
    url.searchParams.set("use_llm", "true");
  }
  
  const res = await fetch(url.toString(), {
    method: "POST",
    body: form,
  });
  
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Upload failed: ${res.status} ${text}`);
  }
  
  return (await res.json()) as SingleUploadResponse;
}

export async function uploadBulk(files: File[], useLlm: boolean = false): Promise<BulkUploadResponse> {
  const form = new FormData();
  for (const f of files) {
    form.append("files", f, f.name);
  }
  
  const url = new URL(`${BASE_URL.replace(/\/$/, "")}/reports/upload/bulk`);
  if (useLlm) {
    url.searchParams.set("use_llm", "true");
  }
  
  const res = await fetch(url.toString(), {
    method: "POST",
    body: form,
  });
  
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Bulk upload failed: ${res.status} ${text}`);
  }
  
  return (await res.json()) as BulkUploadResponse;
}

export function createTaskEventSource(taskId: string): EventSource {
  const url = `${BASE_URL.replace(/\/$/, "")}/tasks/${taskId}/stream`;
  return new EventSource(url);
}

export async function getTaskStatus(taskId: string): Promise<TaskUpdate> {
  const res = await fetch(`${BASE_URL.replace(/\/$/, "")}/tasks/${taskId}`);
  
  if (!res.ok) {
    throw new Error(`Failed to get task status: ${res.status}`);
  }
  
  return (await res.json()) as TaskUpdate;
}

export interface PersistUploadResponse {
  taskId: string;
  uploadId: string;
  fileName: string;
  year: number;
  cw_label: string;
  category: "Development" | "EPC" | "Finance" | "Investment";
  rowsCreated: number;
  parsedWith: "llm" | "simple";
  status: "persisted";
}

export interface DuplicateFileResponse {
  status: "duplicate_detected";
  message: string;
  isDuplicate: true;
  existingFile: {
    id: string;
    filename: string;
    uploadedAt: string;
    status: string;
  };
  currentFile: {
    filename: string;
    sha256: string;
  };
}

export interface CheckDuplicateResponse {
  isDuplicate: boolean;
  existingFile?: {
    id: string;
    filename: string;
    uploadedAt: string;
    status: string;
  };
  currentFile: {
    filename: string;
    sha256: string;
  };
}

export async function checkDuplicate(file: File): Promise<CheckDuplicateResponse> {
  const form = new FormData();
  form.append("file", file, file.name);
  
  const url = `${BASE_URL.replace(/\/$/, "")}/reports/upload/check-duplicate`;
  
  const res = await fetch(url, {
    method: "POST",
    body: form,
  });
  
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Check duplicate failed: ${res.status} ${text}`);
  }
  
  return (await res.json()) as CheckDuplicateResponse;
}

export async function persistUpload(file: File, useLlm: boolean = false, forceImport: boolean = false): Promise<PersistUploadResponse | DuplicateFileResponse> {
  const form = new FormData();
  form.append("file", file, file.name);
  
  const url = new URL(`${BASE_URL.replace(/\/$/, "")}/reports/upload/persist`);
  if (useLlm) {
    url.searchParams.set("use_llm", "true");
  }
  if (forceImport) {
    url.searchParams.set("force_import", "true");
  }
  
  const res = await fetch(url.toString(), {
    method: "POST",
    body: form,
  });
  
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Persist upload failed: ${res.status} ${text}`);
  }
  
  const result = await res.json();
  
  // Check if it's a duplicate detection response
  if (result.status === "duplicate_detected") {
    return result as DuplicateFileResponse;
  }
  
  return result as PersistUploadResponse;
}

export interface ReportUpload {
  id: string;
  originalFilename: string;
  status: "received" | "parsed" | "failed" | "partial";
  cwLabel: string;
  uploadedAt: string;
  parsedAt: string | null;
  createdBy: string;
  projectCount: number;
}

export interface ProjectHistoryRecord {
  id: string;
  projectCode: string;
  projectName: string | null;
  category: string;
  entryType: string;
  logDate: string | null;
  cwLabel: string;
  title: string | null;
  summary: string | null;
  nextActions: string | null;
  owner: string | null;
  sourceText: string | null;
  createdAt: string;
}

export interface UploadHistoryResponse {
  upload: {
    id: string;
    originalFilename: string;
    status: string;
    cwLabel: string;
    uploadedAt: string;
    parsedAt: string | null;
  };
  projectHistory: ProjectHistoryRecord[];
  totalRecords: number;
}

export async function getReportUploads(): Promise<{ uploads: ReportUpload[] }> {
  const res = await fetch(`${BASE_URL.replace(/\/$/, "")}/reports/uploads`);
  
  if (!res.ok) {
    throw new Error(`Failed to get report uploads: ${res.status}`);
  }
  
  return (await res.json()) as { uploads: ReportUpload[] };
}

export async function getUploadProjectHistory(uploadId: string): Promise<UploadHistoryResponse> {
  const res = await fetch(`${BASE_URL.replace(/\/$/, "")}/reports/uploads/${uploadId}/history`);
  
  if (!res.ok) {
    throw new Error(`Failed to get upload history: ${res.status}`);
  }
  
  return (await res.json()) as UploadHistoryResponse;
}

export interface ProjectHistoryFilters {
  year?: number;
  cwLabel?: string;
  category?: string;
}

export interface ProjectHistoryResponse {
  projectHistory: ProjectHistoryRecord[];
  totalRecords: number;
  filters: ProjectHistoryFilters;
}

export async function getProjectHistory(filters?: ProjectHistoryFilters): Promise<ProjectHistoryResponse> {
  const url = new URL(`${BASE_URL.replace(/\/$/, "")}/project-history`);
  
  if (filters?.year) {
    url.searchParams.set("year", filters.year.toString());
  }
  if (filters?.cwLabel) {
    url.searchParams.set("cw_label", filters.cwLabel);
  }
  if (filters?.category) {
    url.searchParams.set("category", filters.category);
  }
  
  const res = await fetch(url.toString());
  
  if (!res.ok) {
    throw new Error(`Failed to get project history: ${res.status}`);
  }
  
  return (await res.json()) as ProjectHistoryResponse;
}


