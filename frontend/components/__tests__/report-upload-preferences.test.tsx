import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ReportUpload } from '../report-upload'

// Mock APIs used in component
jest.mock('@/lib/api/reports', () => ({
  getProjectHistory: jest.fn(() => Promise.resolve({ projectHistory: [], totalRecords: 0 })),
  getReportUploads: jest.fn(() => Promise.resolve({ uploads: [] }))
}))

// Mock language hook
jest.mock('@/hooks/use-language', () => ({
  useLanguage: () => ({ t: (key: string) => key })
}))

describe('ReportUpload Preferences', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.clearAllMocks()
  })

  it('does not show AI toggle in upload UI by default', () => {
    render(<ReportUpload />)
    // The explicit AI toggle section text should not be present anymore
    expect(screen.queryByText('AI-Powered Parsing')).not.toBeInTheDocument()
  })

  it('opens preferences and defaults to simple, persists choice', async () => {
    render(<ReportUpload />)

    // Open sidebar upload panel
    const openUpload = screen.getByText('uploadReport')
    fireEvent.click(openUpload)

    // Open preferences dialog via settings button
    const settingsButtons = screen.getAllByRole('button')
    const settingsBtn = settingsButtons.find(btn => btn.getAttribute('aria-label') === 'Preferences')!
    fireEvent.click(settingsBtn)

    // Expect default selection to be Simple
    await waitFor(() => {
      expect(screen.getByText(/Parsing Mode/i)).toBeInTheDocument()
    })

    // Save without changes -> should persist "simple"
    const saveBtn = screen.getByText('Save')
    fireEvent.click(saveBtn)

    expect(localStorage.getItem('qenergy-parser-preference')).toBe('simple')

    // Re-open preferences and choose AI, then save
    fireEvent.click(settingsBtn)
    const aiLabel = screen.getByText(/AI parsing/i)
    fireEvent.click(aiLabel)
    const saveBtn2 = screen.getByText('Save')
    fireEvent.click(saveBtn2)

    expect(localStorage.getItem('qenergy-parser-preference')).toBe('ai')
  })
})


