"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Upload, Save, X, CheckCircle, FileText } from "lucide-react"
import { useLanguage } from "@/hooks/use-language"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

interface ReportData {
  projectCode: string
  projectName: string
  category: string
  reportContent: string
}

interface UploadResult {
  category: string
  fileName: string
  projectsAdded: number
  status: "success" | "error"
  errors?: { code: string; message: string }[]
}

const sampleReports: ReportData[] = [
  {
    projectCode: "2ES00006",
    projectName: "Don_Rodrigo_PV",
    category: "EPC",
    reportContent:
      "(ESP) Guadajoz / Las Coronadas / Don Rodrigo 157.5Mwp\n(DON)\nPunch List ongoing, and PV plant together with SET are waiting to proceed with Hot commissioning\nTower 21 civil works done, and erection will proceed withing this week\nNCH has started, estimated to finish will be between Oct. and Nov. 2025.",
  },
  {
    projectCode: "2ES00009",
    projectName: "Boedo 1",
    category: "Finance",
    reportContent:
      "Weekly maintenance completed. All turbines operational at 98% efficiency. Weather conditions favorable for next week operations.",
  },
  {
    projectCode: "2ES00010",
    projectName: "Boedo 2",
    category: "DEV",
    reportContent:
      "Scheduled inspection performed. Minor repairs needed on turbine 3. Expected completion by end of week.",
  },
  {
    projectCode: "2DE00001",
    projectName: "Illmersdorf",
    category: "Investment",
    reportContent:
      "Solar panel cleaning completed. Energy output increased by 5%. Next maintenance scheduled for next month.",
  },
  {
    projectCode: "2DE00002",
    projectName: "Garwitz",
    category: "EPC",
    reportContent: "Weather monitoring system updated. New sensors installed. Data collection improved significantly.",
  },
  {
    projectCode: "2DE00003",
    projectName: "Matzlow",
    category: "Finance",
    reportContent: "Quarterly safety inspection passed. All systems within normal parameters. Team training completed.",
  },
  {
    projectCode: "2DE00004",
    projectName: "IM 24 Tangerhütte",
    category: "DEV",
    reportContent: "Grid connection testing in progress. Expected completion next week. All preliminary tests passed.",
  },
  {
    projectCode: "2DE00005",
    projectName: "IM 07 Blankensee",
    category: "Investment",
    reportContent:
      "Foundation work completed. Turbine installation scheduled for next phase. Weather conditions monitored.",
  },
]

export function ReportUpload() {
  const { t } = useLanguage()
  const [selectedYear, setSelectedYear] = useState<string>("")
  const [selectedWeek, setSelectedWeek] = useState<string>("")
  const [reports, setReports] = useState<ReportData[]>(sampleReports)
  const [isSaving, setIsSaving] = useState(false)
  const [isUploadDrawerOpen, setIsUploadDrawerOpen] = useState(false)
  const [uploadFiles, setUploadFiles] = useState<{ [key: string]: File | null }>({
    DEV: null,
    EPC: null,
    Finance: null,
    Investment: null,
  })
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [bulkFiles, setBulkFiles] = useState<File[]>([])

  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: currentYear - 2024 + 1 }, (_, i) => 2024 + i)

  const getCurrentWeek = () => {
    const now = new Date()
    const startOfYear = new Date(now.getFullYear(), 0, 1)
    const days = Math.floor((now.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000))
    const weekNumber = Math.ceil((days + startOfYear.getDay() + 1) / 7)
    return Math.min(weekNumber, 52) // Cap at 52 weeks
  }

  const getWeeksForYear = (_year: number) => {
    const weeks = []
    for (let i = 1; i <= 52; i++) {
      weeks.push(`CW${i.toString().padStart(2, "0")}`)
    }
    return weeks
  }

  useEffect(() => {
    setSelectedYear(currentYear.toString())
    setSelectedWeek(`CW${getCurrentWeek().toString().padStart(2, "0")}`)
  }, [currentYear])

  const handleReportContentChange = (projectCode: string, content: string) => {
    setReports((prev) =>
      prev.map((report) => (report.projectCode === projectCode ? { ...report, reportContent: content } : report)),
    )
  }

  const handleSaveAllReports = async () => {
    setIsSaving(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))
    setIsSaving(false)
    // Show success message (in real app, this would save to backend)
    console.log("All reports saved for", selectedYear, selectedWeek)
  }

  const handleUploadReport = () => {
    setIsUploadDrawerOpen(true)
    setUploadResults([])
  }

  const handleFileSelect = (category: string, file: File | null) => {
    setUploadFiles((prev) => ({
      ...prev,
      [category]: file,
    }))
  }

  const handleUploadFiles = async () => {
    setIsUploading(true)

    const results: UploadResult[] = []

    for (const [category, file] of Object.entries(uploadFiles)) {
      if (file) {
        // 업로드 시뮬레이션
        await new Promise((resolve) => setTimeout(resolve, 500))

        // 랜덤한 프로젝트 수 생성 (1-15개)
        const projectsAdded = Math.floor(Math.random() * 15) + 1

        results.push({
          category,
          fileName: file.name,
          projectsAdded,
          status: "success",
        })
      }
    }

    setUploadResults(results)
    setIsUploading(false)

    // 파일 선택 초기화
    setUploadFiles({
      DEV: null,
      EPC: null,
      Finance: null,
      Investment: null,
    })
  }

  const handleBulkUpload = async () => {
    setIsUploading(true)
    try {
      const { uploadBulk } = await import("@/lib/api/reports")
      const res = await uploadBulk(bulkFiles)
      const results = res.results.map((r: any) => (
        r.status === "ok"
          ? {
              category: r.category ?? "Unknown",
              fileName: r.fileName,
              projectsAdded: Array.isArray(r.rows) ? r.rows.length : 0,
              status: "success" as const,
            }
          : {
              category: "",
              fileName: r.fileName,
              projectsAdded: 0,
              status: "error" as const,
              errors: r.errors ?? [],
            }
      ))
      setUploadResults(results)
    } catch (e) {
      console.error(e)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Upload className="w-8 h-8" />
          {t("reportUploadTitle")}
        </h1>
        <div className="flex gap-2">
          <Button
            onClick={handleUploadReport}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            size="lg"
          >
            <Upload className="w-4 h-4 mr-2" />
            {t("uploadReport")}
          </Button>
          <Button
            onClick={handleSaveAllReports}
            disabled={isSaving}
            className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            size="lg"
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? t("saving") : t("save")}
          </Button>
        </div>
      </div>

      {/* Year/Week Selection */}
      <Card className="border-2 border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-xl text-primary">{t("selectReportPeriod")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6 max-w-md">
            <div>
              <label className="block text-sm font-medium mb-2 text-black dark:text-white">{t("year")}</label>
              <Select value={selectedYear} onValueChange={setSelectedYear}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={t("selectYear")} />
                </SelectTrigger>
                <SelectContent>
                  {years.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-black dark:text-white">{t("weekCW")}</label>
              <Select value={selectedWeek} onValueChange={setSelectedWeek}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={t("selectWeek")} />
                </SelectTrigger>
                <SelectContent>
                  {selectedYear &&
                    getWeeksForYear(Number.parseInt(selectedYear)).map((week) => (
                      <SelectItem key={week} value={week}>
                        {week}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report List */}
      <Card>
        <CardHeader>
          <CardTitle>{t("reportList")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4">
              {reports.map((report) => (
                <div
                  key={report.projectCode}
                  className="grid grid-cols-12 gap-4 p-4 border rounded-lg hover:shadow-md transition-shadow bg-card"
                >
                  {/* Project Code */}
                  <div className="col-span-2 flex items-start">
                    <span className="font-mono text-sm bg-muted px-2 py-1 rounded font-medium">
                      {report.projectCode}
                    </span>
                  </div>

                  {/* Project Name */}
                  <div className="col-span-2 flex items-start">
                    <span className="font-medium">{report.projectName}</span>
                  </div>

                  {/* Category */}
                  <div className="col-span-2 flex items-start">
                    <span className="text-sm bg-secondary px-2 py-1 rounded">{report.category}</span>
                  </div>

                  {/* Report Content */}
                  <div className="col-span-6">
                    <Textarea
                      value={report.reportContent}
                      onChange={(e) => handleReportContentChange(report.projectCode, e.target.value)}
                      placeholder={t("reportContentPlaceholder")}
                      className="min-h-[120px] resize-none text-sm"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Backdrop */}
      {isUploadDrawerOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity duration-300"
          onClick={() => setIsUploadDrawerOpen(false)}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-[90vw] bg-background border-l shadow-2xl z-50 transform transition-transform duration-300 ease-in-out overflow-y-auto ${
          isUploadDrawerOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between border-b pb-4">
            <div className="flex items-center gap-3">
              <Upload className="w-6 h-6" />
              <h2 className="text-2xl font-bold">{t("weeklyReportUpload")}</h2>
              <span className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-base font-medium">
                {selectedYear} / {selectedWeek}
              </span>
            </div>
            <Button variant="ghost" size="icon" onClick={() => setIsUploadDrawerOpen(false)} className="hover:bg-muted">
              <X className="w-6 h-6" />
            </Button>
          </div>

          {/* File Selection Section */}
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold mb-6">{t("fileSelection")}</h3>
              <div className="grid grid-cols-4 gap-4">
                {["DEV", "EPC", "Finance", "Investment"].map((category) => (
                  <div
                    key={category}
                    className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center space-y-4 min-h-[180px] hover:border-primary/50 transition-colors"
                  >
                    <h4 className="font-semibold text-lg">{category}</h4>
                    <div className="space-y-3">
                      <p className="text-muted-foreground text-sm">{t("dragOrClickToUpload")}</p>
                      <div className="relative">
                        <input
                          type="file"
                          accept=".docx"
                          onChange={(e) => handleFileSelect(category, e.target.files?.[0] || null)}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        <Button variant="outline" className="w-full bg-transparent py-2 text-sm">
                          {uploadFiles[category] ? uploadFiles[category]?.name : t("chooseFile")}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Upload Results Section */}
            {uploadResults.length > 0 && (
              <div className="border-t pt-8">
                <h3 className="text-xl font-semibold mb-6 flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-500" />
                  {t("uploadResults")}
                </h3>
                <div className="grid grid-cols-2 gap-6">
                  {uploadResults.map((result, index) => (
                    <div key={index}>
                      {result.status === "success" ? (
                        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
                          <div className="flex items-center gap-4">
                            <FileText className="w-6 h-6 text-green-600" />
                            <div className="flex-1">
                              <div className="font-semibold text-green-800 dark:text-green-200 text-lg">
                                {result.category}
                              </div>
                              <div className="text-green-600 dark:text-green-300">{result.fileName}</div>
                              <div className="font-medium text-green-700 dark:text-green-200">
                                {result.projectsAdded} {t("projectsAdded")}
                              </div>
                            </div>
                            <CheckCircle className="w-6 h-6 text-green-500" />
                          </div>
                        </div>
                      ) : (
                        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
                          <div className="flex items-start gap-4">
                            <FileText className="w-6 h-6 text-red-600" />
                            <div className="flex-1">
                              <div className="font-semibold text-red-800 dark:text-red-200 text-lg">{result.fileName}</div>
                              <ul className="mt-2 list-disc list-inside text-red-700 dark:text-red-300 text-sm">
                                {(result.errors || []).map((e, i) => (
                                  <li key={i}>{e.code}: {e.message}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="text-blue-800 dark:text-blue-200 text-lg">
                    <strong>
                      {t("totalProjectsAdded")}: {uploadResults.reduce((sum, result) => sum + result.projectsAdded, 0)}
                    </strong>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Bulk Folder Import */}
          <div className="border-t pt-6">
            <h3 className="text-xl font-semibold mb-1">Import from Folder</h3>
            <p className="text-sm text-muted-foreground mb-3">Only .docx files will be processed.</p>
            <div className="flex items-center gap-4">
              <div className="relative">
                <input
                  type="file"
                  accept=".docx"
                  // @ts-expect-error - webkitdirectory is not in the standard HTML input attributes
                  webkitdirectory="true"
                  multiple
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={(e) => {
                    const files = Array.from(e.target.files || []).filter((f) => f.name.toLowerCase().endsWith('.docx'))
                    setBulkFiles(files)
                  }}
                />
                <Button variant="outline" className="bg-transparent py-2 text-sm">
                  {t("chooseFolder")}
                </Button>
              </div>
              <div className="text-sm text-muted-foreground">
                {bulkFiles.length > 0 ? `${bulkFiles.length} files selected` : t("noFilesSelected")}
              </div>
              <Button
                variant="default"
                disabled={isUploading || bulkFiles.length === 0}
                onClick={handleBulkUpload}
              >
                {isUploading ? t("uploading") : t("uploadFolder")}
              </Button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-4 pt-6 border-t">
            <Button variant="outline" onClick={() => setIsUploadDrawerOpen(false)} className="text-lg px-8 py-4">
              <X className="w-5 h-5 mr-2" />
              {t("close")}
            </Button>
            <Button
              onClick={handleUploadFiles}
              disabled={isUploading || Object.values(uploadFiles).every((file) => !file)}
              className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-lg px-8 py-4"
            >
              <Upload className="w-5 h-5 mr-2" />
              {isUploading ? t("uploading") : t("upload")}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
