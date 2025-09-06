const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002/api";

export interface ApiClientOptions {
  baseUrl?: string;
  headers?: Record<string, string>;
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly defaultHeaders: Record<string, string>;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? DEFAULT_BASE_URL;
    this.defaultHeaders = {
      "Content-Type": "application/json",
      ...options.headers,
    };
  }

  async get<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(this.resolve(path), {
      method: "GET",
      headers: this.defaultHeaders,
      ...init,
    });
    return this.parseJson<T>(response);
  }

  async post<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
    const response = await fetch(this.resolve(path), {
      method: "POST",
      headers: this.defaultHeaders,
      body: JSON.stringify(body ?? {}),
      ...init,
    });
    return this.parseJson<T>(response);
  }

  async put<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
    const response = await fetch(this.resolve(path), {
      method: "PUT",
      headers: this.defaultHeaders,
      body: JSON.stringify(body ?? {}),
      ...init,
    });
    return this.parseJson<T>(response);
  }

  async delete<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(this.resolve(path), {
      method: "DELETE",
      headers: this.defaultHeaders,
      ...init,
    });
    return this.parseJson<T>(response);
  }

  private resolve(path: string): string {
    if (path.startsWith("http")) return path;
    return `${this.baseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
  }

  private async parseJson<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new Error(`API ${response.status}: ${text}`);
    }
    return (await response.json()) as T;
  }
}

export const apiClient = new ApiClient();


