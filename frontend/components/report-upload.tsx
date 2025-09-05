"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Upload, Save, X, CheckCircle, FileText, Brain, Zap, Clock, AlertCircle, Eye, Calendar, User, FolderOpen, RefreshCw } from "lucide-react"
import { useLanguage } from "@/hooks/use-language"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { getProjectHistory, type ProjectHistoryFilters } from "@/lib/api/reports"

interface ReportData {
  id: string
  projectCode: string
  projectName: string
  category: string
  reportContent: string
  cwLabel?: string
  logDate?: string
  title?: string
  nextActions?: string
  owner?: string
}

interface UploadResult {
  category: string
  fileName: string
  projectsAdded: number
  status: "success" | "error"
  parsedWith?: "llm" | "simple"
  errors?: { code: string; message: string }[]
}

interface TaskProgress {
  taskId: string
  fileName: string
  status: "pending" | "processing" | "completed" | "failed"
  progress: number
  message: string
  currentStep: string
  resultCount?: number
  errorMessage?: string
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
  const [reports, setReports] = useState<ReportData[]>([])
  const [isLoadingReports, setIsLoadingReports] = useState(false)
  const [actualLoadedYear, setActualLoadedYear] = useState<string>("")
  const [actualLoadedWeek, setActualLoadedWeek] = useState<string>("")
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
  const [useLlmParser, setUseLlmParser] = useState(false)
  const [processingStatus, setProcessingStatus] = useState<{ [fileName: string]: "processing" | "complete" | "error" }>({})
  const [taskProgresses, setTaskProgresses] = useState<{ [taskId: string]: TaskProgress }>({})
  const [eventSources, setEventSources] = useState<{ [taskId: string]: EventSource }>({})
  const [persistResults, setPersistResults] = useState<{ [fileName: string]: any }>({})
  const [reportUploads, setReportUploads] = useState<any[]>([])
  const [selectedUpload, setSelectedUpload] = useState<any>(null)
  const [uploadHistory, setUploadHistory] = useState<any>(null)
  const [isLoadingUploads, setIsLoadingUploads] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: currentYear - 2024 + 1 }, (_, i) => 2024 + i)

  // Load project history data from database
  const loadProjectHistory = useCallback(async () => {
    if (!selectedYear || !selectedWeek) return

    setIsLoadingReports(true)
    try {
      const filters: ProjectHistoryFilters = {
        year: parseInt(selectedYear),
        cwLabel: selectedWeek
      }

      console.log(`Loading data for ${selectedYear} ${selectedWeek}`)
      const response = await getProjectHistory(filters)
      
      // Transform API response to ReportData format
      const transformedReports: ReportData[] = response.projectHistory.map(record => ({
        id: record.id,
        projectCode: record.projectCode,
        projectName: record.projectName || record.projectCode,
        category: record.category || "Development",
        reportContent: record.summary || "",
        cwLabel: record.cwLabel,
        logDate: record.logDate,
        title: record.title,
        nextActions: record.nextActions,
        owner: record.owner
      }))

      setReports(transformedReports)
      
      // Record the actual loaded year and week for display
      setActualLoadedYear(selectedYear)
      setActualLoadedWeek(selectedWeek)
    } catch (error) {
      console.error("Failed to load project history:", error)
      // Fallback to empty array on error
      setReports([])
    } finally {
      setIsLoadingReports(false)
    }
  }, [selectedYear, selectedWeek])

  // Load data when year and week are selected
  useEffect(() => {
    loadProjectHistory()
  }, [loadProjectHistory])

  // Load report uploads
  const loadReportUploads = useCallback(async () => {
    setIsLoadingUploads(true)
    try {
      const { getReportUploads } = await import("@/lib/api/reports")
      const result = await getReportUploads()
      setReportUploads(result.uploads)
    } catch (error) {
      console.error("Failed to load report uploads:", error)
    } finally {
      setIsLoadingUploads(false)
    }
  }, [])

  // Load upload history
  const loadUploadHistory = useCallback(async (uploadId: string) => {
    setIsLoadingHistory(true)
    try {
      const { getUploadProjectHistory } = await import("@/lib/api/reports")
      const result = await getUploadProjectHistory(uploadId)
      setUploadHistory(result)
    } catch (error) {
      console.error("Failed to load upload history:", error)
    } finally {
      setIsLoadingHistory(false)
    }
  }, [])

  // Load uploads on component mount
  useEffect(() => {
    void loadReportUploads()
  }, [loadReportUploads])

  // Task monitoring function
  const startTaskMonitoring = useCallback((taskId: string, fileName: string) => {
    // Initialize task progress
    setTaskProgresses(prev => ({
      ...prev,
      [taskId]: {
        taskId,
        fileName,
        status: "pending",
        progress: 0,
        message: "Starting...",
        currentStep: "upload_received"
      }
    }))

    // Create EventSource for real-time updates
    try {
      void import("@/lib/api/reports").then(({ createTaskEventSource }) => {
        const eventSource = createTaskEventSource(taskId)

        eventSource.onmessage = (event: MessageEvent) => {
          try {
            const update = JSON.parse(event.data)
            if (update.type === 'heartbeat') return

            setTaskProgresses(prev => ({
              ...prev,
              [taskId]: {
                taskId: update.task_id,
                fileName,
                status: update.status,
                progress: update.progress,
                message: update.message,
                currentStep: update.current_step,
                resultCount: update.result_count,
                errorMessage: update.error_message
              }
            }))

            // If task is completed, close event source
            if (update.status === 'completed' || update.status === 'failed') {
              eventSource.close()
              setEventSources(prev => {
                const newSources = { ...prev }
                delete newSources[taskId]
                return newSources
              })
            }
          } catch (error) {
            console.error('Error parsing task update:', error)
          }
        }

        eventSource.onerror = (error: Event) => {
          console.error('EventSource error:', error)
          eventSource.close()
          setEventSources(prev => {
            const newSources = { ...prev }
            delete newSources[taskId]
            return newSources
          })
        }

        setEventSources(prev => ({ ...prev, [taskId]: eventSource }))
      })
    } catch (error) {
      console.error('Failed to start task monitoring:', error)
    }
  }, [])

  // Cleanup event sources on unmount
  useEffect(() => {
    return () => {
      Object.values(eventSources).forEach(source => source.close())
    }
  }, [eventSources])

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

  // Set intelligent default values - prefer showing data over current date
  useEffect(() => {
    const setIntelligentDefaults = async () => {
      try {
        // First try current year and current week
        const currentWeekStr = `CW${getCurrentWeek().toString().padStart(2, "0")}`
        const currentYearStr = currentYear.toString()
        
        const currentResponse = await getProjectHistory({
          year: currentYear,
          cwLabel: currentWeekStr
        })
        
        if (currentResponse.totalRecords > 0) {
          // Use current date if data exists
          setSelectedYear(currentYearStr)
          setSelectedWeek(currentWeekStr)
          setActualLoadedYear(currentYearStr)
          setActualLoadedWeek(currentWeekStr)
          return
        }
        
        // If no data for current period, try to find the most recent data
        const allResponse = await getProjectHistory({})
        if (allResponse.totalRecords > 0 && allResponse.projectHistory.length > 0) {
          // Use the most recent record's date
          const mostRecent = allResponse.projectHistory[0] // API returns sorted by date DESC
          const logDate = new Date(mostRecent.logDate)
          const recentYear = logDate.getFullYear().toString()
          const recentWeek = mostRecent.cwLabel
          
          console.log(`Setting defaults to most recent data: ${recentYear} ${recentWeek}`)
          setSelectedYear(recentYear)
          setSelectedWeek(recentWeek)
          setActualLoadedYear(recentYear)
          setActualLoadedWeek(recentWeek)
        } else {
          // Fallback to current date
          setSelectedYear(currentYearStr)
          setSelectedWeek(currentWeekStr)
        }
      } catch (error) {
        console.error("Failed to set intelligent defaults:", error)
        // Fallback to current date
        setSelectedYear(currentYear.toString())
        setSelectedWeek(`CW${getCurrentWeek().toString().padStart(2, "0")}`)
      }
    }
    
    void setIntelligentDefaults()
  }, [currentYear])

  const handleReportContentChange = (reportId: string, content: string) => {
    setReports((prev) =>
      prev.map((report) => (report.id === reportId ? { ...report, reportContent: content } : report)),
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
    setProcessingStatus({})
    setTaskProgresses({})
    
    const results: UploadResult[] = []
    const filesToProcess = Object.entries(uploadFiles).filter(([_, file]) => file)

    for (const [category, file] of filesToProcess) {
      if (file) {
        try {
          // Mark as processing
          setProcessingStatus(prev => ({ ...prev, [file.name]: "processing" }))
          
          const { uploadSingle } = await import("@/lib/api/reports")
          const res = await uploadSingle(file, useLlmParser)
          
          // Start task monitoring
          if (res.taskId) {
            startTaskMonitoring(res.taskId, res.fileName)
          }
          
          // Mark as complete
          setProcessingStatus(prev => ({ ...prev, [file.name]: "complete" }))
          
          results.push({
            category: res.category || category,
            fileName: res.fileName,
            projectsAdded: Array.isArray(res.rows) ? res.rows.length : 0,
            status: "success",
            parsedWith: res.parsedWith || "simple",
          })
        } catch (e) {
          console.error(`Upload failed for ${file.name}:`, e)
          
          // Mark as error
          setProcessingStatus(prev => ({ ...prev, [file.name]: "error" }))
          
          results.push({
            category,
            fileName: file.name,
            projectsAdded: 0,
            status: "error",
            errors: [{ code: "UPLOAD_ERROR", message: String(e) }]
          })
        }
      }
    }

    setUploadResults(results)
    setIsUploading(false)

    // Clear processing status after showing results for a moment
    setTimeout(() => setProcessingStatus({}), 3000)

    // Reset file selection
    setUploadFiles({
      DEV: null,
      EPC: null,
      Finance: null,
      Investment: null,
    })
  }

  const handlePersistToDatabase = async () => {
    setIsUploading(true)
    setProcessingStatus({})
    setTaskProgresses({})
    
    const results: UploadResult[] = []
    const filesToProcess = Object.entries(uploadFiles).filter(([_, file]) => file)

    for (const [category, file] of filesToProcess) {
      if (file) {
        try {
          // Mark as processing
          setProcessingStatus(prev => ({ ...prev, [file.name]: "processing" }))
          
          const { persistUpload } = await import("@/lib/api/reports")
          const res = await persistUpload(file, useLlmParser)
          
          // Start task monitoring
          if (res.taskId) {
            startTaskMonitoring(res.taskId, res.fileName)
          }
          
          // Store persist result
          setPersistResults(prev => ({ ...prev, [file.name]: res }))
          
          // Mark as complete
          setProcessingStatus(prev => ({ ...prev, [file.name]: "complete" }))
          
          // Refresh uploads table
          void loadReportUploads()
          
          results.push({
            category: res.category || category,
            fileName: res.fileName,
            projectsAdded: res.rowsCreated || 0,
            status: "success",
            parsedWith: res.parsedWith || "simple",
          })
        } catch (e) {
          console.error(`Database persistence failed for ${file.name}:`, e)
          
          // Mark as error
          setProcessingStatus(prev => ({ ...prev, [file.name]: "error" }))
          
          results.push({
            category,
            fileName: file.name,
            projectsAdded: 0,
            status: "error",
            errors: [{ code: "PERSISTENCE_ERROR", message: String(e) }]
          })
        }
      }
    }

    setUploadResults(results)
    setIsUploading(false)

    // Clear processing status after showing results for a moment
    setTimeout(() => setProcessingStatus({}), 3000)

    // Reset file selection
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
      const res = await uploadBulk(bulkFiles, useLlmParser)
      const results = res.results.map((r: any) => (
        r.status === "ok"
          ? {
              category: r.category ?? "Unknown",
              fileName: r.fileName,
              projectsAdded: Array.isArray(r.rows) ? r.rows.length : 0,
              status: "success" as const,
              parsedWith: r.parsedWith || "simple",
            }
          : {
              category: "",
              fileName: r.fileName,
              projectsAdded: 0,
              status: "error" as const,
              parsedWith: undefined,
              errors: r.errors ?? [],
            }
      ))
      setUploadResults(results)
    } catch (e) {
      console.error("Upload failed:", e)
      setUploadResults([{
        category: "",
        fileName: "Bulk Upload",
        projectsAdded: 0,
        status: "error",
        errors: [{ code: "NETWORK_ERROR", message: String(e) }]
      }])
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
          <div className="flex items-center justify-between">
            <CardTitle>{t("reportList")}</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={loadProjectHistory}
              disabled={isLoadingReports || !selectedYear || !selectedWeek}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingReports ? 'animate-spin' : ''}`} />
              {t("refresh")}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingReports ? (
            <div className="flex items-center justify-center py-8">
              <div className="flex items-center space-x-2">
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>{t("loading")}...</span>
              </div>
            </div>
          ) : !selectedYear || !selectedWeek ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <span>{t("selectYearAndWeek")}</span>
            </div>
          ) : reports.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <span>{t("noReportsFound")}</span>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground mb-4">
                {t("showingReports", { count: reports.length, year: actualLoadedYear || selectedYear, week: actualLoadedWeek || selectedWeek })}
              </div>
              <div className="space-y-4">
                {reports.map((report) => (
                  <div
                    key={report.id}
                    className="flex gap-4 p-4 border rounded-lg hover:shadow-md transition-shadow bg-card"
                  >
                  {/* Project Code - Fixed width */}
                  <div className="w-24 flex-shrink-0 flex items-start">
                    <span className="font-mono text-xs bg-muted px-2 py-1 rounded font-medium truncate w-full text-center">
                      {report.projectCode}
                    </span>
                  </div>

                  {/* Project Name - Fixed width */}
                  <div className="w-40 flex-shrink-0 flex items-start">
                    <span className="font-medium text-sm leading-tight line-clamp-3" title={report.projectName}>
                      {report.projectName}
                    </span>
                  </div>

                  {/* Category - Fixed width */}
                  <div className="w-24 flex-shrink-0 flex items-start">
                    <span className="text-xs bg-secondary px-2 py-1 rounded truncate w-full text-center">
                      {report.category}
                    </span>
                  </div>

                  {/* Report Content - Fixed width with scrollbar */}
                  <div className="flex-1 min-w-0">
                    <div className="h-32 border rounded-md">
                      <Textarea
                        value={report.reportContent}
                        onChange={(e) => handleReportContentChange(report.id, e.target.value)}
                        placeholder={t("reportContentPlaceholder")}
                        className="h-full resize-none text-sm border-none focus:ring-1 focus:ring-ring overflow-auto"
                      />
                    </div>
                  </div>
                </div>
              ))}
              </div>
            </div>
          )}
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

          {/* LLM Parser Toggle */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-blue-600" />
                  <Label htmlFor="llm-toggle" className="text-lg font-semibold">AI-Powered Parsing</Label>
                  <Badge variant={useLlmParser ? "default" : "secondary"} className="ml-2">
                    {useLlmParser ? "ENABLED" : "DISABLED"}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  {useLlmParser 
                    ? "🧠 AI will intelligently extract multiple projects and detailed information from your documents"
                    : "📝 Standard parsing will extract basic content as a single summary entry"
                  }
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Zap className={`w-4 h-4 ${useLlmParser ? 'text-yellow-500' : 'text-gray-400'}`} />
                <Switch
                  id="llm-toggle"
                  checked={useLlmParser}
                  onCheckedChange={setUseLlmParser}
                />
              </div>
            </div>
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
                      {uploadFiles[category] && uploadFiles[category]?.name && processingStatus[uploadFiles[category]?.name || ""] && (
                        <div className="mt-2">
                          {processingStatus[uploadFiles[category]?.name || ""] === "processing" && (
                            <div className="flex items-center gap-2 text-blue-600 text-sm">
                              <div className="animate-spin rounded-full h-3 w-3 border-2 border-blue-600 border-t-transparent"></div>
                              {useLlmParser ? "AI Processing..." : "Processing..."}
                            </div>
                          )}
                          {processingStatus[uploadFiles[category]?.name || ""] === "complete" && (
                            <div className="flex items-center gap-2 text-green-600 text-sm">
                              <CheckCircle className="w-3 h-3" />
                              Complete
                            </div>
                          )}
                          {processingStatus[uploadFiles[category]?.name || ""] === "error" && (
                            <div className="flex items-center gap-2 text-red-600 text-sm">
                              <X className="w-3 h-3" />
                              Error
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Real-time Task Progress Section */}
            {Object.keys(taskProgresses).length > 0 && (
              <div className="border-t pt-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-3">
                  <Clock className="w-6 h-6 text-blue-500" />
                  Processing Status
                </h3>
                <div className="space-y-4">
                  {Object.values(taskProgresses).map((task) => (
                    <div key={task.taskId} className="bg-white dark:bg-gray-800 border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4" />
                          <span className="font-medium">{task.fileName}</span>
                          {task.status === "processing" && useLlmParser && (
                            <Badge variant="default" className="bg-blue-500">
                              <Brain className="w-3 h-3 mr-1" />
                              AI
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {task.status === "processing" && (
                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                          )}
                          {task.status === "completed" && (
                            <CheckCircle className="w-4 h-4 text-green-600" />
                          )}
                          {task.status === "failed" && (
                            <AlertCircle className="w-4 h-4 text-red-600" />
                          )}
                          <span className="text-sm font-medium">{task.progress}%</span>
                        </div>
                      </div>
                      
                      <Progress value={task.progress} className="mb-2" />
                      
                      <div className="text-sm text-muted-foreground">
                        {task.message}
                        {task.resultCount !== undefined && (
                          <span className="text-green-600 font-medium ml-2">
                            ({task.resultCount} entries extracted)
                          </span>
                        )}
                      </div>
                      
                      {task.errorMessage && (
                        <div className="mt-2 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                          Error: {task.errorMessage}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

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
                              <div className="flex items-center gap-2 mb-1">
                                <div className="font-semibold text-green-800 dark:text-green-200 text-lg">
                                  {result.category}
                                </div>
                                {result.parsedWith === "llm" && (
                                  <Badge variant="default" className="bg-blue-500 text-white">
                                    <Brain className="w-3 h-3 mr-1" />
                                    AI
                                  </Badge>
                                )}
                                {result.parsedWith === "simple" && (
                                  <Badge variant="secondary" className="bg-gray-500 text-white">
                                    <FileText className="w-3 h-3 mr-1" />
                                    Basic
                                  </Badge>
                                )}
                              </div>
                              <div className="text-green-600 dark:text-green-300">{result.fileName}</div>
                              <div className="font-medium text-green-700 dark:text-green-200">
                                {result.projectsAdded} {t("projectsAdded")}
                              </div>
                              {persistResults[result.fileName] && (
                                <div className="text-sm text-blue-600 font-medium">
                                  💾 Saved to database (Upload ID: {persistResults[result.fileName].uploadId.slice(0, 8)}...)
                                </div>
                              )}
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
                className={useLlmParser 
                  ? "bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600" 
                  : ""}
              >
                {useLlmParser && <Brain className="w-4 h-4 mr-2" />}
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
              variant="outline"
              className="text-lg px-8 py-4"
            >
              <FileText className="w-5 h-5 mr-2" />
              {isUploading ? "Processing..." : "Preview Only"}
            </Button>
            <Button
              onClick={handlePersistToDatabase}
              disabled={isUploading || Object.values(uploadFiles).every((file) => !file)}
              className={`text-lg px-8 py-4 ${
                useLlmParser 
                  ? "bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600" 
                  : "bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
              }`}
            >
              {useLlmParser ? <Brain className="w-4 h-4 mr-2" /> : <Upload className="w-5 h-5 mr-2" />}
              {isUploading ? "Saving..." : "Save to Database"}
            </Button>
          </div>
        </div>
      </div>

      {/* Report Uploads Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5" />
            Report Uploads History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingUploads ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
              <span className="ml-2">Loading uploads...</span>
            </div>
          ) : reportUploads.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FolderOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No report uploads found</p>
              <p className="text-sm">Upload a report to see it here</p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>File Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>CW Label</TableHead>
                    <TableHead>Projects</TableHead>
                    <TableHead>Uploaded</TableHead>
                    <TableHead>Created By</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportUploads.map((upload) => (
                    <TableRow key={upload.id}>
                      <TableCell className="font-medium">
                        {upload.originalFilename}
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={
                            upload.status === 'parsed' ? 'default' : 
                            upload.status === 'failed' ? 'destructive' : 
                            'secondary'
                          }
                        >
                          {upload.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{upload.cwLabel}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {upload.projectCount} project{upload.projectCount !== 1 ? 's' : ''}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Calendar className="w-3 h-3" />
                          {new Date(upload.uploadedAt).toLocaleDateString()}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <User className="w-3 h-3" />
                          {upload.createdBy}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => {
                                setSelectedUpload(upload)
                                void loadUploadHistory(upload.id)
                              }}
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              View History
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh]">
                            <DialogHeader>
                              <DialogTitle className="flex items-center gap-2">
                                <FileText className="w-5 h-5" />
                                Project History for {selectedUpload?.originalFilename}
                              </DialogTitle>
                              <DialogDescription>
                                {selectedUpload && `Uploaded on ${new Date(selectedUpload.uploadedAt).toLocaleString()}`}
                              </DialogDescription>
                            </DialogHeader>
                            
                            {isLoadingHistory ? (
                              <div className="flex items-center justify-center py-8">
                                <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
                                <span className="ml-2">Loading project history...</span>
                              </div>
                            ) : uploadHistory ? (
                              <ScrollArea className="h-[60vh]">
                                <div className="space-y-4">
                                  <div className="bg-muted/50 rounded-lg p-4">
                                    <h4 className="font-semibold mb-2">Upload Summary</h4>
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                      <div>
                                        <span className="font-medium">Status:</span> {uploadHistory.upload.status}
                                      </div>
                                      <div>
                                        <span className="font-medium">CW Label:</span> {uploadHistory.upload.cwLabel}
                                      </div>
                                      <div>
                                        <span className="font-medium">Total Records:</span> {uploadHistory.totalRecords}
                                      </div>
                                      <div>
                                        <span className="font-medium">Parsed:</span>{" "}
                                        {uploadHistory.upload.parsedAt 
                                          ? new Date(uploadHistory.upload.parsedAt).toLocaleString()
                                          : "Not parsed"
                                        }
                                      </div>
                                    </div>
                                  </div>

                                  <div>
                                    <h4 className="font-semibold mb-3">Project History Records</h4>
                                    {uploadHistory.projectHistory.length === 0 ? (
                                      <p className="text-muted-foreground text-center py-4">
                                        No project history records found
                                      </p>
                                    ) : (
                                      <div className="space-y-3">
                                        {uploadHistory.projectHistory.map((record: any) => (
                                          <div key={record.id} className="border rounded-lg p-4">
                                            <div className="flex items-start justify-between mb-2">
                                              <div>
                                                <h5 className="font-medium">
                                                  {record.projectCode} - {record.projectName || "Unknown Project"}
                                                </h5>
                                                <div className="flex items-center gap-2 mt-1">
                                                  <Badge variant="outline">{record.category}</Badge>
                                                  <Badge variant="secondary">{record.entryType}</Badge>
                                                </div>
                                              </div>
                                              <div className="text-sm text-muted-foreground">
                                                {record.logDate && new Date(record.logDate).toLocaleDateString()}
                                              </div>
                                            </div>
                                            
                                            {record.title && (
                                              <h6 className="font-medium text-sm mb-2">{record.title}</h6>
                                            )}
                                            
                                            {record.summary && (
                                              <p className="text-sm text-muted-foreground mb-2">
                                                {record.summary}
                                              </p>
                                            )}
                                            
                                            {record.nextActions && (
                                              <div className="text-sm">
                                                <span className="font-medium">Next Actions:</span> {record.nextActions}
                                              </div>
                                            )}
                                            
                                            {record.owner && (
                                              <div className="text-sm text-muted-foreground mt-1">
                                                <span className="font-medium">Owner:</span> {record.owner}
                                              </div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </ScrollArea>
                            ) : (
                              <div className="text-center py-8 text-muted-foreground">
                                Select an upload to view its project history
                              </div>
                            )}
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
