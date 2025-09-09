/**
 * Test category filtering functionality in ReportUpload component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ReportUpload } from '../report-upload'
import { getProjectHistory } from '@/lib/api/reports'

// Mock the API
jest.mock('@/lib/api/reports', () => ({
  getProjectHistory: jest.fn(),
  getReportUploads: jest.fn(() => Promise.resolve({ uploads: [] }))
}))

// Mock the language hook
jest.mock('@/hooks/use-language', () => ({
  useLanguage: () => ({
    t: (key: string) => {
      const translations: { [key: string]: string } = {
        selectReportPeriod: 'Select Report Period',
        year: 'Year',
        weekCW: 'Week (CW)',
        category: 'Category',
        selectYear: 'Select Year',
        selectWeek: 'Select Week (CW)',
        selectCategory: 'Select Category',
        allCategories: 'All Categories',
        reportList: 'Project History',
        refresh: 'Refresh',
        loading: 'Loading',
        selectYearAndWeek: 'Please select year and week',
        noReportsFound: 'No reports found',
        showingReports: 'Showing {{count}} reports for {{year}} / {{week}}'
      }
      return translations[key] || key
    }
  })
}))

const mockGetProjectHistory = getProjectHistory as jest.MockedFunction<typeof getProjectHistory>

const mockProjectHistoryResponse = {
  projectHistory: [
    {
      id: '1',
      projectCode: 'TEST001',
      projectName: 'Test Project 1',
      category: 'Development',
      entryType: 'Report',
      logDate: '2025-01-01',
      cwLabel: 'CW01',
      title: 'Test Title 1',
      summary: 'Test Summary 1',
      nextActions: null,
      owner: null,
      sourceText: null,
      createdAt: '2025-01-01T00:00:00Z'
    },
    {
      id: '2',
      projectCode: 'TEST002',
      projectName: 'Test Project 2',
      category: 'EPC',
      entryType: 'Report',
      logDate: '2025-01-01',
      cwLabel: 'CW01',
      title: 'Test Title 2',
      summary: 'Test Summary 2',
      nextActions: null,
      owner: null,
      sourceText: null,
      createdAt: '2025-01-01T00:00:00Z'
    }
  ],
  totalRecords: 2,
  filters: {
    year: 2025,
    cwLabel: 'CW01',
    category: undefined
  }
}

describe('ReportUpload Category Filter', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetProjectHistory.mockResolvedValue(mockProjectHistoryResponse)
  })

  it('renders category select dropdown', async () => {
    render(<ReportUpload />)
    
    expect(screen.getByText('Category')).toBeInTheDocument()
    expect(screen.getByText('Select Category')).toBeInTheDocument()
  })

  it('includes category options in dropdown', async () => {
    render(<ReportUpload />)
    
    // Click on category dropdown
    const categorySelect = screen.getByText('Select Category')
    fireEvent.click(categorySelect)
    
    // Check for category options
    await waitFor(() => {
      expect(screen.getByText('All Categories')).toBeInTheDocument()
      expect(screen.getByText('Development')).toBeInTheDocument()
      expect(screen.getByText('EPC')).toBeInTheDocument()
      expect(screen.getByText('Finance')).toBeInTheDocument()
      expect(screen.getByText('Investment')).toBeInTheDocument()
    })
  })

  it('calls API without category filter when no category selected', async () => {
    render(<ReportUpload />)
    
    // Set year and week to trigger API call
    const yearSelect = screen.getByText('Select Year')
    fireEvent.click(yearSelect)
    
    await waitFor(() => {
      const year2025 = screen.getByText('2025')
      fireEvent.click(year2025)
    })
    
    const weekSelect = screen.getByText('Select Week (CW)')
    fireEvent.click(weekSelect)
    
    await waitFor(() => {
      const cw01 = screen.getByText('CW01')
      fireEvent.click(cw01)
    })
    
    // Verify API was called without category
    await waitFor(() => {
      expect(mockGetProjectHistory).toHaveBeenCalledWith({
        year: 2025,
        cwLabel: 'CW01'
      })
    })
  })

  it('calls API with category filter when category selected', async () => {
    render(<ReportUpload />)
    
    // Set year and week
    const yearSelect = screen.getByText('Select Year')
    fireEvent.click(yearSelect)
    
    await waitFor(() => {
      const year2025 = screen.getByText('2025')
      fireEvent.click(year2025)
    })
    
    const weekSelect = screen.getByText('Select Week (CW)')
    fireEvent.click(weekSelect)
    
    await waitFor(() => {
      const cw01 = screen.getByText('CW01')
      fireEvent.click(cw01)
    })
    
    // Clear previous calls
    jest.clearAllMocks()
    
    // Select category
    const categorySelect = screen.getByText('Select Category')
    fireEvent.click(categorySelect)
    
    await waitFor(() => {
      const developmentOption = screen.getByText('Development')
      fireEvent.click(developmentOption)
    })
    
    // Verify API was called with category
    await waitFor(() => {
      expect(mockGetProjectHistory).toHaveBeenCalledWith({
        year: 2025,
        cwLabel: 'CW01',
        category: 'Development'
      })
    })
  })

  it('updates API call when category is changed', async () => {
    render(<ReportUpload />)
    
    // Set year and week first
    const yearSelect = screen.getByText('Select Year')
    fireEvent.click(yearSelect)
    
    await waitFor(() => {
      const year2025 = screen.getByText('2025')
      fireEvent.click(year2025)
    })
    
    const weekSelect = screen.getByText('Select Week (CW)')
    fireEvent.click(weekSelect)
    
    await waitFor(() => {
      const cw01 = screen.getByText('CW01')
      fireEvent.click(cw01)
    })
    
    // Select Development category
    const categorySelect = screen.getByText('Select Category')
    fireEvent.click(categorySelect)
    
    await waitFor(() => {
      const developmentOption = screen.getByText('Development')
      fireEvent.click(developmentOption)
    })
    
    // Clear previous calls
    jest.clearAllMocks()
    
    // Change to EPC category
    fireEvent.click(categorySelect)
    
    await waitFor(() => {
      const epcOption = screen.getByText('EPC')
      fireEvent.click(epcOption)
    })
    
    // Verify API was called with new category
    await waitFor(() => {
      expect(mockGetProjectHistory).toHaveBeenCalledWith({
        year: 2025,
        cwLabel: 'CW01',
        category: 'EPC'
      })
    })
  })

  it('clears category filter when "All Categories" selected', async () => {
    render(<ReportUpload />)
    
    // Set year and week
    const yearSelect = screen.getByText('Select Year')
    fireEvent.click(yearSelect)
    
    await waitFor(() => {
      const year2025 = screen.getByText('2025')
      fireEvent.click(year2025)
    })
    
    const weekSelect = screen.getByText('Select Week (CW)')
    fireEvent.click(weekSelect)
    
    await waitFor(() => {
      const cw01 = screen.getByText('CW01')
      fireEvent.click(cw01)
    })
    
    // First select a specific category
    const categorySelect = screen.getByText('Select Category')
    fireEvent.click(categorySelect)
    
    await waitFor(() => {
      const developmentOption = screen.getByText('Development')
      fireEvent.click(developmentOption)
    })
    
    // Clear previous calls
    jest.clearAllMocks()
    
    // Select "All Categories"
    fireEvent.click(categorySelect)
    
    await waitFor(() => {
      const allCategoriesOption = screen.getByText('All Categories')
      fireEvent.click(allCategoriesOption)
    })
    
    // Verify API was called without category filter (value "all" should not be sent to API)
    await waitFor(() => {
      expect(mockGetProjectHistory).toHaveBeenCalledWith({
        year: 2025,
        cwLabel: 'CW01'
      })
    })
  })
})
