import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AnalysisService } from '../analysis'
import * as client from '../client'

// Mock the API client
vi.mock('../client', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
  }
}))

describe('AnalysisService', () => {
  let analysisService: AnalysisService
  const mockApiClient = client.apiClient as any

  beforeEach(() => {
    analysisService = new AnalysisService()
    vi.clearAllMocks()
  })

  describe('analyzeReports', () => {
    it('should call the analyze endpoint with correct payload', async () => {
      const mockResponse = {
        data: {
          message: 'Analysis completed',
          analyzed_count: 2,
          skipped_count: 0,
          results: []
        }
      }

      mockApiClient.post.mockResolvedValue(mockResponse)

      const request = {
        past_cw: 'CW31',
        latest_cw: 'CW32',
        language: 'EN' as const,
        category: 'EPC' as const,
        created_by: 'test-user'
      }

      const result = await analysisService.analyzeReports(request)

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/reports/analyze', {
        past_cw: 'CW31',
        latest_cw: 'CW32',
        language: 'EN',
        category: 'EPC',
        created_by: 'test-user'
      })

      expect(result).toEqual(mockResponse.data)
    })

    it('should use default values when optional fields are not provided', async () => {
      const mockResponse = {
        data: {
          message: 'Analysis completed',
          analyzed_count: 1,
          skipped_count: 0,
          results: []
        }
      }

      mockApiClient.post.mockResolvedValue(mockResponse)

      const request = {
        past_cw: 'CW31',
        latest_cw: 'CW32'
      }

      await analysisService.analyzeReports(request)

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/reports/analyze', {
        past_cw: 'CW31',
        latest_cw: 'CW32',
        language: 'EN',
        category: null,
        created_by: 'frontend-user'
      })
    })
  })

  describe('getAnalysisResults', () => {
    it('should call the weekly-analysis endpoint with correct parameters', async () => {
      const mockResponse = {
        data: [{
          id: '1',
          project_code: 'TEST001',
          cw_label: 'CW32',
          language: 'EN',
          risk_lvl: 50,
          risk_desc: 'Medium risk',
          similarity_lvl: 75,
          similarity_desc: 'Similar content',
          negative_words: { words: ['delay'], count: 1 },
          created_at: '2024-01-01T00:00:00Z',
          created_by: 'test'
        }]
      }

      mockApiClient.get.mockResolvedValue(mockResponse)

      const result = await analysisService.getAnalysisResults('CW31', 'CW32', 'EN', 'EPC')

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/weekly-analysis?past_cw=CW31&latest_cw=CW32&language=EN&category=EPC')
      expect(result).toEqual(mockResponse.data)
    })

    it('should handle optional parameters correctly', async () => {
      const mockResponse = { data: [] }
      mockApiClient.get.mockResolvedValue(mockResponse)

      await analysisService.getAnalysisResults('CW31', 'CW32')

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/weekly-analysis?past_cw=CW31&latest_cw=CW32')
    })
  })

  describe('getProjectCandidates', () => {
    it('should call the by-cw-pair endpoint with correct parameters', async () => {
      const mockResponse = {
        data: [{
          project_code: 'TEST001',
          project_name: 'Test Project',
          categories: ['EPC'],
          cw_labels: ['CW31', 'CW32']
        }]
      }

      mockApiClient.get.mockResolvedValue(mockResponse)

      const result = await analysisService.getProjectCandidates('CW31', 'CW32', 'EPC')

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/projects/by-cw-pair?past_cw=CW31&latest_cw=CW32&category=EPC')
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('convertToFrontendFormat', () => {
    it('should convert backend result to frontend format', () => {
      const backendResult = {
        id: '1',
        project_code: 'TEST001',
        project_name: 'Test Project',
        category: 'EPC',
        cw_label: 'CW32',
        language: 'EN' as const,
        risk_lvl: 75,
        risk_desc: 'High risk detected',
        similarity_lvl: 45,
        similarity_desc: 'Low similarity',
        negative_words: { words: ['delay', 'problem'], count: 2 },
        created_at: '2024-01-01T00:00:00Z',
        created_by: 'test'
      }

      const result = analysisService.convertToFrontendFormat(backendResult)

      expect(result).toEqual({
        projectCode: 'TEST001',
        projectName: 'Test Project',
        category: 'EPC',
        pastReportContent: 'Past report content',
        latestReportContent: 'Latest report content',
        riskLevel: 75,
        riskOpinion: 'High risk detected',
        similarity: 45,
        similarityOpinion: 'Low similarity',
        negativeWords: ['delay', 'problem']
      })
    })

    it('should handle null/undefined values correctly', () => {
      const backendResult = {
        id: '1',
        project_code: 'TEST001',
        project_name: null,
        category: null,
        cw_label: 'CW32',
        language: 'EN' as const,
        risk_lvl: null,
        risk_desc: null,
        similarity_lvl: null,
        similarity_desc: null,
        negative_words: null,
        created_at: '2024-01-01T00:00:00Z',
        created_by: 'test'
      }

      const result = analysisService.convertToFrontendFormat(backendResult)

      expect(result).toEqual({
        projectCode: 'TEST001',
        projectName: 'TEST001',
        category: 'Unknown',
        pastReportContent: 'Past report content',
        latestReportContent: 'Latest report content',
        riskLevel: 0,
        riskOpinion: 'No risk assessment available',
        similarity: 0,
        similarityOpinion: 'No similarity assessment available',
        negativeWords: []
      })
    })
  })
})
