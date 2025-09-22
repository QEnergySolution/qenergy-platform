import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { ReportUpload } from "../report-upload"

// Mock APIs used in component
jest.mock("@/lib/api/reports", () => ({
  getProjectHistory: jest.fn(() => Promise.resolve({ projectHistory: [], totalRecords: 0 })),
  getReportUploads: jest.fn(() => Promise.resolve({ uploads: [] })),
  persistUpload: jest.fn(),
}))

// Mock language hook
jest.mock("@/hooks/use-language", () => ({
  useLanguage: () => ({ t: (key: string) => key })
}))

const { persistUpload } = jest.requireMock("@/lib/api/reports") as {
  persistUpload: jest.Mock
}

function createDocxFile(name: string): File {
  const blob = new Blob(["test"], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" })
  return new File([blob], name)
}

describe("ReportUpload duplicate queue", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("queues multiple duplicates and shows dialogs sequentially", async () => {
    // First call returns duplicate for DEV
    // Second call returns duplicate for EPC
    // Third call is success (Finance) to validate mixed results
    const duplicateResponse = (filename: string) => ({
      status: "duplicate_detected",
      message: `Duplicate found for ${filename}`,
      isDuplicate: true,
      existingFile: {
        id: "existing-id",
        filename,
        uploadedAt: new Date().toISOString(),
        status: "parsed",
      },
      currentFile: {
        filename,
        sha256: "abc",
      },
    })

    persistUpload.mockImplementation((_file: File, _useLlm: boolean, _force: boolean, _y?: string, _w?: string, category?: string) => {
      if (category === "DEV" || category === "EPC") {
        return Promise.resolve(duplicateResponse(`${category}.docx`))
      }
      return Promise.resolve({
        taskId: `ok-${category}`,
        uploadId: `u-${category}`,
        fileName: `${category}.docx`,
        year: 2025,
        cw_label: "CW01",
        category: category || "Development",
        rowsCreated: 2,
        parsedWith: "simple",
        status: "persisted",
      })
    })

    const { container } = render(<ReportUpload />)
    fireEvent.click(screen.getByText("uploadReport"))

    const inputs = container.querySelectorAll('input[type="file"]')
    const indexMap: Record<string, number> = { DEV: 0, EPC: 1, Finance: 2, Investment: 3 }

    const dev = createDocxFile("DEV.docx")
    const epc = createDocxFile("EPC.docx")
    const fin = createDocxFile("Finance.docx")

    fireEvent.change(inputs[indexMap.DEV] as HTMLInputElement, { target: { files: [dev] } })
    fireEvent.change(inputs[indexMap.EPC] as HTMLInputElement, { target: { files: [epc] } })
    fireEvent.change(inputs[indexMap.Finance] as HTMLInputElement, { target: { files: [fin] } })

    fireEvent.click(screen.getByText("Save to Database"))

    // First duplicate dialog should appear for DEV
    await waitFor(() => expect(screen.getByText("File Duplicate Warning")).toBeInTheDocument())
    expect(screen.getByText(/DEV.docx/)).toBeInTheDocument()

    // Cancel first
    fireEvent.click(screen.getByText("Cancel Import"))

    // Next duplicate dialog should appear for EPC
    await waitFor(() => expect(screen.getByText(/EPC.docx/)).toBeInTheDocument())

    // Continue import for EPC
    fireEvent.click(screen.getByText("Continue Import (Overwrite Duplicate Data)"))

    // Eventually we should see results including pending entries for duplicates and success for Finance
    await waitFor(() => {
      expect(persistUpload).toHaveBeenCalled()
      // Finance success result shown
      expect(screen.getAllByText("Finance.docx")[0]).toBeInTheDocument()
    })
  })
})


