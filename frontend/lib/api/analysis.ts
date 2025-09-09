import { apiClient } from './client'

export interface AnalysisResult {
  id: string
  project_code: string
  project_name?: string | null
  category?: string | null
  cw_label: string
  language: 'EN' | 'KO'
  risk_lvl?: number | null
  risk_desc?: string | null
  similarity_lvl?: number | null
  similarity_desc?: string | null
  negative_words?: { words: string[]; count: number } | null
  past_content?: string | null
  latest_content?: string | null
  created_at: string
  created_by: string
}

export interface AnalysisRequest {
  past_cw: string
  latest_cw: string
  language?: 'EN' | 'KO'
  category?: 'Development' | 'EPC' | 'Finance' | 'Investment' | null
  created_by?: string
}

export interface AnalysisResponse {
  message: string
  analyzed_count: number
  skipped_count: number
  results: AnalysisResult[]
}

export interface ProjectCandidate {
  project_code: string
  project_name?: string | null
  categories: string[]
  cw_labels: string[]
}

export class AnalysisService {
  /**
   * Trigger analysis for reports between two calendar weeks
   */
  async analyzeReports(request: AnalysisRequest): Promise<AnalysisResponse> {
    const payload = {
      past_cw: request.past_cw,
      latest_cw: request.latest_cw,
      language: request.language || 'EN',
      category: request.category || null,
      created_by: request.created_by || 'frontend-user'
    }

    const resp = await apiClient.post<AnalysisResponse>('/analysis', payload)
    if (resp.error || !resp.data) {
      throw new Error(resp.error || 'Failed to analyze reports')
    }
    return resp.data
  }

  /**
   * Get existing analysis results
   */
  async getAnalysisResults(
    pastCw: string,
    latestCw: string,
    language?: 'EN' | 'KO',
    category?: 'Development' | 'EPC' | 'Finance' | 'Investment'
  ): Promise<AnalysisResult[]> {
    const params = new URLSearchParams({
      past_cw: pastCw,
      latest_cw: latestCw
    })

    if (language) params.append('language', language)
    if (category) params.append('category', category)

    const resp = await apiClient.get<AnalysisResult[]>(`/analysis/weekly?${params}`)
    if (resp.error || !resp.data) {
      throw new Error(resp.error || 'Failed to fetch analysis results')
    }
    return resp.data
  }

  /**
   * Get candidate projects present in either calendar week
   */
  async getProjectCandidates(
    pastCw: string,
    latestCw: string,
    category?: 'Development' | 'EPC' | 'Finance' | 'Investment'
  ): Promise<ProjectCandidate[]> {
    const params = new URLSearchParams({
      past_cw: pastCw,
      latest_cw: latestCw
    })

    if (category) params.append('category', category)

    const resp = await apiClient.get<ProjectCandidate[]>(`/project-candidates?${params}`)
    if (resp.error || !resp.data) {
      throw new Error(resp.error || 'Failed to fetch project candidates')
    }
    return resp.data
  }

  /**
   * Convert backend analysis result to frontend format for compatibility
   */
  convertToFrontendFormat(result: AnalysisResult): {
    projectCode: string
    projectName: string
    category: string
    pastReportContent: string
    latestReportContent: string
    riskLevel: number
    riskOpinion: string
    similarity: number
    similarityOpinion: string
    negativeWords: string[]
  } {
    return {
      projectCode: result.project_code,
      projectName: result.project_name || result.project_code,
      category: result.category || 'Unknown',
      pastReportContent: result.past_content || 'No past content available',
      latestReportContent: result.latest_content || 'No latest content available',
      riskLevel: Math.round(result.risk_lvl || 0),
      riskOpinion: result.risk_desc || 'No risk assessment available',
      similarity: Math.round(result.similarity_lvl || 0),
      similarityOpinion: result.similarity_desc || 'No similarity assessment available',
      negativeWords: result.negative_words?.words || []
    }
  }

  /**
   * Get analysis results in frontend format
   */
  async getAnalysisResultsFormatted(
    pastCw: string,
    latestCw: string,
    language?: 'EN' | 'KO',
    category?: 'Development' | 'EPC' | 'Finance' | 'Investment'
  ) {
    const results = await this.getAnalysisResults(pastCw, latestCw, language, category)
    return results.map(result => this.convertToFrontendFormat(result))
  }
}

export const analysisService = new AnalysisService()