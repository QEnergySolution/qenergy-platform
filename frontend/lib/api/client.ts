/**
 * Base API client for making requests to the backend
 */

export interface ApiClientOptions {
  baseUrl?: string;
  headers?: Record<string, string>;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export class ApiClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';
    this.headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
  }

  private async request<T>(
    method: string,
    path: string,
    data?: any,
    customHeaders?: Record<string, string>
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${path}`;
    const headers = { ...this.headers, ...customHeaders };

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined,
      });

      // Handle 204 No Content responses specially
      if (response.status === 204) {
        return {
          data: undefined as unknown as T, // No content to return
          status: 204,
        };
      }

      const isJson = response.headers.get('content-type')?.includes('application/json');
      
      // Only try to parse as JSON if the content-type is json
      let responseData;
      if (isJson) {
        try {
          responseData = await response.json();
        } catch (parseError) {
          console.warn('Failed to parse JSON response:', parseError);
          responseData = await response.text();
        }
      } else {
        responseData = await response.text();
      }

      if (!response.ok) {
        return {
          error: isJson && typeof responseData === 'object' && responseData.detail 
            ? responseData.detail 
            : 'An error occurred',
          status: response.status,
        };
      }

      return {
        data: responseData as T,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0, // 0 indicates network error
      };
    }
  }

  async get<T>(path: string, customHeaders?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>('GET', path, undefined, customHeaders);
  }

  async post<T>(path: string, data?: any, customHeaders?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>('POST', path, data, customHeaders);
  }

  async put<T>(path: string, data?: any, customHeaders?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', path, data, customHeaders);
  }

  async delete<T>(path: string, customHeaders?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', path, undefined, customHeaders);
  }

  // Helper method to build query parameters
  buildQueryParams(params: Record<string, any>): string {
    const query = Object.entries(params)
      .filter(([_, value]) => value !== undefined && value !== null)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');
    
    return query ? `?${query}` : '';
  }
}

// Export a singleton instance
export const apiClient = new ApiClient();