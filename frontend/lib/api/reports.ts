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

export async function uploadSingle(
  file: File, 
  useLlm: boolean = false,
  overrideYear?: string,
  overrideWeek?: string,
  overrideCategory?: string
): Promise<SingleUploadResponse> {
  const form = new FormData();
  form.append("file", file, file.name);
  
  const url = new URL(`${BASE_URL.replace(/\/$/, "")}/reports/upload`);
  if (useLlm) {
    url.searchParams.set("use_llm", "true");
  }
  
  // Add override parameters if provided
  if (overrideYear) {
    url.searchParams.set("override_year", overrideYear);
  }
  if (overrideWeek) {
    url.searchParams.set("override_week", overrideWeek);
  }
  if (overrideCategory) {
    url.searchParams.set("override_category", overrideCategory);
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

export async function uploadBulk(
  files: File[], 
  useLlm: boolean = false,
  overrideYear?: string,
  overrideWeek?: string,
  overrideCategory?: string
): Promise<BulkUploadResponse> {
  const form = new FormData();
  for (const f of files) {
    form.append("files", f, f.name);
  }
  
  const url = new URL(`${BASE_URL.replace(/\/$/, "")}/reports/upload/bulk`);
  if (useLlm) {
    url.searchParams.set("use_llm", "true");
  }
  
  // Add override parameters if provided
  if (overrideYear) {
    url.searchParams.set("override_year", overrideYear);
  }
  if (overrideWeek) {
    url.searchParams.set("override_week", overrideWeek);
  }
  if (overrideCategory) {
    url.searchParams.set("override_category", overrideCategory);
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

export async function persistUpload(
  file: File, 
  useLlm: boolean = false, 
  forceImport: boolean = false,
  overrideYear?: string,
  overrideWeek?: string,
  overrideCategory?: string
): Promise<PersistUploadResponse | DuplicateFileResponse> {
  const form = new FormData();
  form.append("file", file, file.name);
  
  const url = new URL(`${BASE_URL.replace(/\/$/, "")}/reports/upload/persist`);
  if (useLlm) {
    url.searchParams.set("use_llm", "true");
  }
  if (forceImport) {
    url.searchParams.set("force_import", "true");
  }
  
  // Add override parameters if provided
  if (overrideYear) {
    url.searchParams.set("override_year", overrideYear);
  }
  if (overrideWeek) {
    url.searchParams.set("override_week", overrideWeek);
  }
  if (overrideCategory) {
    url.searchParams.set("override_category", overrideCategory);
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

  // Backend now properly supports year filtering
  if (filters?.year) {
    url.searchParams.set("year", String(filters.year));
    console.log(`Applying year filter: ${filters.year}`);
  }
  if (filters?.cwLabel) {
    url.searchParams.set("cw_label", filters.cwLabel);
  }
  if (filters?.category) {
    url.searchParams.set("category", filters.category);
  }
  
  // Add pagination parameters
  url.searchParams.set("page", "1");
  url.searchParams.set("page_size", "100"); // Get a reasonable number of records

  console.log('Fetching project history from:', url.toString());
  const res = await fetch(url.toString());

  if (!res.ok) {
    console.error('Failed to get project history:', res.status, await res.text().catch(() => ''));
    throw new Error(`Failed to get project history: ${res.status}`);
  }

  const data = await res.json();
  console.log(`Project history API response: ${data.items?.length || 0} items, total: ${data.total || 0}`);

  // Adapt backend pagination shape { items, total, page, page_size } to frontend shape
  if (Array.isArray(data?.items) && typeof data?.total === "number") {
    const projectHistory = (data.items as any[]).map((it) => ({
      id: String(it.id),
      projectCode: String(it.project_code),
      projectName: it.project_name ?? null, // backend doesn't provide; keep null if missing
      category: String(it.category ?? ""),
      entryType: String(it.entry_type ?? ""),
      logDate: it.log_date ?? null,
      cwLabel: String(it.cw_label ?? ""),
      title: it.title ?? null,
      summary: it.summary ?? null,
      nextActions: it.next_actions ?? null,
      owner: it.owner ?? null,
      sourceText: it.source_text ?? null,
      createdAt: String(it.created_at ?? ""),
    }));

    const response: ProjectHistoryResponse = {
      projectHistory,
      totalRecords: Number(data.total),
      filters: {
        year: filters?.year,
        cwLabel: filters?.cwLabel,
        category: filters?.category,
      },
    };
    return response;
  }

  // If backend already returns the expected shape, just return it
  return data as ProjectHistoryResponse;
}


// Fetch all cw_labels for a given year (and optional category) by paginating
export async function getCwLabelsForYear(year: number, category?: string): Promise<Set<string>> {
  const labels = new Set<string>();
  let page = 1;
  const pageSize = 100; // backend max

  try {
    while (true) {
      const url = new URL(`${BASE_URL.replace(/\/$/, "")}/project-history`);
      url.searchParams.set("year", String(year));
      url.searchParams.set("page", String(page));
      url.searchParams.set("page_size", String(pageSize));
      if (category) url.searchParams.set("category", category);

      console.log(`Fetching CW labels for year ${year}, category ${category || 'all'}, page ${page}`);
      const res = await fetch(url.toString());
      if (!res.ok) {
        console.error(`Failed to fetch CW labels: ${res.status}`);
        break;
      }
      
      const data = await res.json();
      if (Array.isArray(data?.items)) {
        for (const it of data.items) {
          if (it?.cw_label && it.cw_label.startsWith('CW')) {
            labels.add(String(it.cw_label));
          }
        }
      }
      
      const total = Number(data?.total ?? 0);
      const pages = Math.ceil(total / pageSize) || 1;
      console.log(`Found ${labels.size} unique CW labels for year ${year}, ${total} total records, ${pages} pages`);
      
      if (page >= pages) break;
      page += 1;
    }
  } catch (error) {
    console.error(`Error fetching CW labels for year ${year}:`, error);
  }
  
  return labels;
}

