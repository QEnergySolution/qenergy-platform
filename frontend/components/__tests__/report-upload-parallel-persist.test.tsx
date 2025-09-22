import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { ReportUpload } from "../report-upload"

// Mock APIs used in component
jest.mock("@/lib/api/reports", () => ({
  getProjectHistory: jest.fn(() => Promise.resolve({ projectHistory: [], totalRecords: 0 })),
  getReportUploads: jest.fn(() => Promise.resolve({ uploads: [] })),
  persistUpload: jest.fn(),
}))

// Mock language hook to identity function
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

describe("ReportUpload parallel persist", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  const categoryOrder = ["DEV", "EPC", "Finance", "Investment"] as const

  const combinations: Array<typeof categoryOrder[number][]> = [
    ["DEV"],
    ["EPC"],
    ["Finance"],
    ["Investment"],
    ["DEV", "EPC"],
    ["DEV", "Finance"],
    ["DEV", "Investment"],
    ["EPC", "Finance"],
    ["EPC", "Investment"],
    ["Finance", "Investment"],
    ["DEV", "EPC", "Finance"],
    ["DEV", "EPC", "Investment"],
    ["DEV", "Finance", "Investment"],
    ["EPC", "Finance", "Investment"],
    ["DEV", "EPC", "Finance", "Investment"],
  ]

  it.each(combinations)("persists in parallel for categories: %s", async (...cats: typeof categoryOrder[number][]) => {
    persistUpload.mockImplementation((file: File, _useLlm: boolean, _force: boolean, _y?: string, _w?: string, category?: string) => {
      return Promise.resolve({
        taskId: `task-${file.name}`,
        uploadId: `upload-${file.name}`,
        fileName: file.name,
        year: 2025,
        cw_label: "CW01",
        category: category || "Development",
        rowsCreated: 3,
        parsedWith: "simple",
        status: "persisted",
      })
    })

    const { container } = render(<ReportUpload />)

    // Open sidebar upload panel
    fireEvent.click(screen.getByText("uploadReport"))

    // Locate the 4 file inputs (order is DEV, EPC, Finance, Investment)
    const inputs = container.querySelectorAll('input[type="file"]')
    expect(inputs.length).toBeGreaterThanOrEqual(4)

    // Map category to input index
    const indexMap: Record<string, number> = { DEV: 0, EPC: 1, Finance: 2, Investment: 3 }

    // Provide files for chosen categories
    const files = cats.map((c) => createDocxFile(`${c}_CW01_${c}.docx`))
    cats.forEach((c, i) => {
      const input = inputs[indexMap[c]] as HTMLInputElement
      const file = files[i]
      fireEvent.change(input, { target: { files: [file] } })
    })

    // Click Save to Database
    fireEvent.click(screen.getByText("Save to Database"))

    // Expect each file result to appear
    for (const file of files) {
      await waitFor(() => expect(screen.getAllByText(file.name)[0]).toBeInTheDocument())
    }

    // Ensure persistUpload called for each provided file
    expect(persistUpload).toHaveBeenCalledTimes(files.length)
  })
})


