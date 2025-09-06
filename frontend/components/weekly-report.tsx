"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { FileText, Play, Square, Download, ArrowUpDown, ChevronUp, ChevronDown, MessageSquare, X } from "lucide-react"
import { useLanguage } from "@/hooks/use-language"
import { analysisService } from "@/lib/api/analysis"
import { getProjectHistory } from "@/lib/api/reports"
import { useToast } from "@/hooks/use-toast"

interface AnalysisResult {
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
}

type SortField = "projectCode" | "projectName" | "riskLevel" | "similarity" | "negativeWords"
type SortDirection = "asc" | "desc"

// Mock data removed - now using real API

export function WeeklyReport() {
  const { t } = useLanguage()

  // Report selection states
  const [pastYear, setPastYear] = useState<string>("")
  const [pastWeek, setPastWeek] = useState<string>("")
  const [latestYear, setLatestYear] = useState<string>("")
  const [latestWeek, setLatestWeek] = useState<string>("")
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const isCategoryValid = selectedCategory && selectedCategory !== "all"

  // Analysis states
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([])
  const [hasAnalyzed, setHasAnalyzed] = useState(false)

  // Sorting states
  const [sortField, setSortField] = useState<SortField>("projectCode")
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc")

  const [isAskAIOpen, setIsAskAIOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<"challenges" | "consistency" | "risks">("challenges")
  const [aiQuestion, setAiQuestion] = useState("")
  const [error, setError] = useState<string | null>(null)
  
  const { toast } = useToast()

  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: currentYear - 2024 + 1 }, (_, i) => 2024 + i)
  const categories = [
    { value: "all", label: "All Categories" },
    { value: "Development", label: "Development" },
    { value: "EPC", label: "EPC" },
    { value: "Finance", label: "Finance" },
    { value: "Investment", label: "Investment" }
  ]

  // Track weeks that actually have records for a given year (and optional category)
  const [availableWeeksByYear, setAvailableWeeksByYear] = useState<Record<string, Set<string>>>({})

  const getCurrentWeek = () => {
    const now = new Date()
    const startOfYear = new Date(now.getFullYear(), 0, 1)
    const days = Math.floor((now.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000))
    const weekNumber = Math.ceil((days + startOfYear.getDay() + 1) / 7)
    return Math.min(weekNumber, 52)
  }

  const getWeeksForYear = (_year: number) => {
    const weeks = []
    for (let i = 1; i <= 52; i++) {
      weeks.push(`CW${i.toString().padStart(2, "0")}`)
    }
    return weeks
  }

  useEffect(() => {
    const currentWeek = getCurrentWeek()
    setLatestYear(currentYear.toString())
    setLatestWeek(`CW${currentWeek.toString().padStart(2, "0")}`)

    // Set past week to previous week
    if (currentWeek > 1) {
      setPastYear(currentYear.toString())
      setPastWeek(`CW${(currentWeek - 1).toString().padStart(2, "0")}`)
    } else {
      setPastYear((currentYear - 1).toString())
      setPastWeek("CW52")
    }
  }, [currentYear])

  // Load available weeks for the chosen years and category
  useEffect(() => {
    const loadAvailableWeeks = async (year: string | null) => {
      if (!year) return
      try {
        const resp = await getProjectHistory({
          year: Number.parseInt(year),
          // If category is "all" we don't filter so that any week with any data is enabled
          category: selectedCategory && selectedCategory !== "all" ? selectedCategory : undefined,
        })
        const weekSet = new Set<string>(resp.projectHistory.map((r) => r.cwLabel))
        setAvailableWeeksByYear((prev) => ({ ...prev, [year]: weekSet }))
      } catch {
        // On error, leave weeks disabled by default for safety
        setAvailableWeeksByYear((prev) => ({ ...prev, [year]: new Set() }))
      }
    }

    void loadAvailableWeeks(pastYear)
    void loadAvailableWeeks(latestYear)
  }, [pastYear, latestYear, selectedCategory])

  // Load existing analysis results when CW selection changes
  useEffect(() => {
    const loadExistingResults = async () => {
      if (!pastWeek || !latestWeek) return
      if (!isCategoryValid) return

      try {
        const categoryFilter = selectedCategory as "Development" | "EPC" | "Finance" | "Investment"
        const backendResults = await analysisService.getAnalysisResults(
          pastWeek,
          latestWeek,
          "EN",
          categoryFilter
        )
        const results = backendResults.map(result => {
          const formatted = analysisService.convertToFrontendFormat(result)
          if (formatted.category === "Unknown") {
            formatted.category = selectedCategory
          }
          return formatted
        })
        if (results.length > 0) {
          setAnalysisResults(results)
          setHasAnalyzed(true)
        }
      } catch (error) {
        // Silently fail - this is just loading existing results
        console.log("No existing results found:", error)
      }
    }

    void loadExistingResults()
  }, [pastWeek, latestWeek, selectedCategory, isCategoryValid])

  const canStartAnalysis = pastYear && pastWeek && latestYear && latestWeek && isCategoryValid

  const startAnalysis = async () => {
    if (!canStartAnalysis) {
      if (!isCategoryValid) {
        toast({
          title: "Category Required",
          description: "'All' is not supported yet. Please select a specific category.",
          variant: "destructive",
        })
      }
      return
    }

    setIsAnalyzing(true)
    setAnalysisProgress(0)
    setAnalysisResults([])
    setError(null)

    try {
      // First, get candidate projects to show progress
      const categoryFilter = selectedCategory as "Development" | "EPC" | "Finance" | "Investment"
      const candidates = await analysisService.getProjectCandidates(
        pastWeek, 
        latestWeek, 
        categoryFilter
      )
      const totalProjects = candidates.length

      if (totalProjects === 0) {
        toast({
          title: "No Projects Found",
          description: "No projects found for the selected calendar weeks.",
          variant: "destructive",
        })
        setIsAnalyzing(false)
        return
      }

      // Start analysis
      setAnalysisProgress(20) // Show initial progress

      const response = await analysisService.analyzeReports({
        past_cw: pastWeek,
        latest_cw: latestWeek,
        language: "EN", // Could be made configurable
        category: categoryFilter,
        created_by: "frontend-user"
      })

      setAnalysisProgress(80)

      // Convert results to frontend format
      const formattedResults = response.results.map(result => {
        const formatted = analysisService.convertToFrontendFormat(result)
        if (formatted.category === "Unknown") {
          formatted.category = selectedCategory
        }
        return formatted
      })

      setAnalysisResults(formattedResults)
      setAnalysisProgress(100)

      toast({
        title: "Analysis Complete",
        description: response.message,
      })

      setHasAnalyzed(true)
    } catch (error) {
      console.error("Analysis failed:", error)
      const errorMessage = error instanceof Error ? error.message : "Analysis failed"
      setError(errorMessage)
      
      toast({
        title: "Analysis Failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  const stopAnalysis = () => {
    setIsAnalyzing(false)
    setAnalysisProgress(0)
  }

  const downloadExcel = () => {
    console.log("Downloading Excel file...")
  }

  const openAskAI = () => {
    setIsAskAIOpen(true)
  }

  const closeAskAI = () => {
    setIsAskAIOpen(false)
    setAiQuestion("")
  }

  const handleTabClick = (tab: "challenges" | "consistency" | "risks") => {
    setActiveTab(tab)

    // Set default questions for each tab
    switch (tab) {
      case "challenges":
        setAiQuestion("What are key challenges across all divisions in the latest report?")
        break
      case "consistency":
        setAiQuestion(
          "Please check if there are any consistency errors in the latest report. If there is a consistency error, I would like to know where the errors are in the file. If possible, show it on a table and clearly show which item it occurred in",
        )
        break
      case "risks":
        setAiQuestion("What strategic risks and opportunities are shaping the QENERGY's future growth?")
        break
    }
  }

  const handleAskAI = () => {
    if (!aiQuestion.trim()) return
    console.log("Asking AI:", aiQuestion)
    // TODO: Implement actual AI query
    setAiQuestion("")
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleAskAI()
    }
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  const isIncomplete = (r: AnalysisResult) => !r.pastReportContent?.trim() || !r.latestReportContent?.trim()
  const sortedResults = [...analysisResults].sort((a, b) => {
    const aIncomplete = isIncomplete(a)
    const bIncomplete = isIncomplete(b)
    if (aIncomplete !== bIncomplete) return aIncomplete ? 1 : -1 // incomplete rows go last

    let aValue: any = a[sortField]
    let bValue: any = b[sortField]

    if (sortField === "negativeWords") {
      aValue = a.negativeWords.length
      bValue = b.negativeWords.length
    }

    if (typeof aValue === "string") {
      return sortDirection === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue)
    }

    return sortDirection === "asc" ? aValue - bValue : bValue - aValue
  })

  const SortButton = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <button onClick={() => handleSort(field)} className="flex items-center gap-1 hover:text-primary transition-colors">
      {children}
      {sortField === field &&
        (sortDirection === "asc" ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
      {sortField !== field && <ArrowUpDown className="w-4 h-4 opacity-50" />}
    </button>
  )

  const getRiskColor = (risk: number) => {
    if (risk >= 70) return "text-red-600 bg-red-100 dark:bg-red-900/20"
    if (risk >= 40) return "text-orange-600 bg-orange-100 dark:bg-orange-900/20"
    return "text-green-600 bg-green-100 dark:bg-green-900/20"
  }

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 80) return "text-green-600 bg-green-100 dark:bg-green-900/20"
    if (similarity >= 50) return "text-orange-600 bg-orange-100 dark:bg-orange-900/20"
    return "text-red-600 bg-red-100 dark:bg-red-900/20"
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <FileText className="w-8 h-8" />
          {t("weeklyReport")}
        </h1>
      </div>

      {/* Report Selection - Emphasized UI */}
      <Card className="border-2 border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-xl text-primary">{t("selectReportsForAnalysis")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Category Selection */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-black dark:text-white">Category Filter</h3>
              <div className="max-w-md">
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select category (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((category) => (
                      <SelectItem key={category.value} value={category.value}>
                        {category.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex gap-12">
              {/* Past Report Selection */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-black dark:text-white">{t("pastReport")}</h3>
              <div className="grid grid-cols-2 gap-4 max-w-md">
                <div>
                  <label className="block text-sm font-medium mb-2">{t("year")}</label>
                  <Select value={pastYear} onValueChange={setPastYear}>
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
                  <label className="block text-sm font-medium mb-2">{t("weekCW")}</label>
                  <Select value={pastWeek} onValueChange={setPastWeek}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder={t("selectWeek")} />
                    </SelectTrigger>
                    <SelectContent>
                      {pastYear &&
                        getWeeksForYear(Number.parseInt(pastYear)).map((week) => {
                          const hasData = availableWeeksByYear[pastYear]?.has(week)
                          return (
                            <SelectItem key={week} value={week} disabled={!hasData} className={!hasData ? "text-muted-foreground" : undefined}>
                              {week}
                            </SelectItem>
                          )
                        })}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Latest Report Selection */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-black dark:text-white">{t("latestReport")}</h3>
              <div className="grid grid-cols-2 gap-4 max-w-md">
                <div>
                  <label className="block text-sm font-medium mb-2">{t("year")}</label>
                  <Select value={latestYear} onValueChange={setLatestYear}>
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
                  <label className="block text-sm font-medium mb-2">{t("weekCW")}</label>
                  <Select value={latestWeek} onValueChange={setLatestWeek}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder={t("selectWeek")} />
                    </SelectTrigger>
                    <SelectContent>
                      {latestYear &&
                        getWeeksForYear(Number.parseInt(latestYear)).map((week) => {
                          const hasData = availableWeeksByYear[latestYear]?.has(week)
                          return (
                            <SelectItem key={week} value={week} disabled={!hasData} className={!hasData ? "text-muted-foreground" : undefined}>
                              {week}
                            </SelectItem>
                          )
                        })}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex items-center gap-4">
        <Button
          onClick={startAnalysis}
          disabled={!canStartAnalysis || isAnalyzing}
          className="bg-green-600 hover:bg-green-700"
          size="lg"
        >
          <Play className="w-4 h-4 mr-2" />
          {t("startAnalysis")}
        </Button>

        {isAnalyzing && (
          <Button onClick={stopAnalysis} variant="destructive" size="lg">
            <Square className="w-4 h-4 mr-2" />
            {t("stopAnalysis")}
          </Button>
        )}

        {hasAnalyzed && !isAnalyzing && (
          <>
            <Button onClick={downloadExcel} variant="outline" size="lg">
              <Download className="w-4 h-4 mr-2" />
              {t("downloadExcel")}
            </Button>
            <Button onClick={openAskAI} className="bg-blue-600 hover:bg-blue-700" size="lg">
              <MessageSquare className="w-4 h-4 mr-2" />
              {t("askAI")}
            </Button>
          </>
        )}
      </div>

      {/* Progress Bar */}
      {isAnalyzing && (
        <Card>
          <CardContent className="p-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{t("analyzingReports")}</span>
                <span>{Math.round(analysisProgress)}%</span>
              </div>
              <Progress value={analysisProgress} className="w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="text-red-700">
              <strong>Error:</strong> {error}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Results */}
      {analysisResults.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">{t("analysisResults")}</h2>
            <div className="text-sm text-muted-foreground">
              {selectedCategory && selectedCategory !== "all" ? `Category: ${selectedCategory}` : "All Categories"} | 
              {pastWeek} → {latestWeek} | 
              {analysisResults.length} projects analyzed
            </div>
          </div>

          {/* Results Table */}
          <div className="border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="p-3 text-left">
                      <SortButton field="projectCode">{t("projectCode")}</SortButton>
                    </th>
                    <th className="p-3 text-left">
                      <SortButton field="projectName">{t("projectName")}</SortButton>
                    </th>
                    <th className="p-3 text-left">{t("category")}</th>
                    <th className="p-3 text-left">{t("pastReportContent")}</th>
                    <th className="p-3 text-left">{t("latestReportContent")}</th>
                    <th className="p-3 text-left">
                      <SortButton field="riskLevel">{t("riskLevel")}</SortButton>
                    </th>
                    <th className="p-3 text-left">{t("riskOpinion")}</th>
                    <th className="p-3 text-left">
                      <SortButton field="similarity">{t("similarity")}</SortButton>
                    </th>
                    <th className="p-3 text-left">{t("similarityOpinion")}</th>
                    <th className="p-3 text-left">
                      <SortButton field="negativeWords">{t("negativeWords")}</SortButton>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedResults.map((result, _index) => {
                    const rowIncomplete = isIncomplete(result)
                    const riskBadgeClass = rowIncomplete ? "text-muted-foreground bg-muted" : getRiskColor(result.riskLevel)
                    const similarityBadgeClass = rowIncomplete ? "text-muted-foreground bg-muted" : getSimilarityColor(result.similarity)
                    return (
                    <tr key={result.projectCode} className={`border-t hover:bg-muted/50 ${rowIncomplete ? "opacity-60" : ""}`}>
                      <td className="p-3 font-mono text-sm">{result.projectCode}</td>
                      <td className="p-3 font-medium">{result.projectName}</td>
                      <td className="p-3">
                        <span className="px-2 py-1 rounded text-sm bg-muted">{result.category}</span>
                      </td>
                      <td className="p-3 w-96 align-top">
                        <div className="max-h-48 overflow-y-auto whitespace-pre-wrap text-sm pr-2">
                          {result.pastReportContent}
                        </div>
                      </td>
                      <td className="p-3 w-96 align-top">
                        <div className="max-h-48 overflow-y-auto whitespace-pre-wrap text-sm pr-2">
                          {result.latestReportContent}
                        </div>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-sm ${riskBadgeClass}`}>
                          {rowIncomplete ? "-" : `${result.riskLevel}%`}
                        </span>
                      </td>
                      <td className="p-3 w-96 align-top">
                        <div className="max-h-48 overflow-y-auto whitespace-pre-wrap text-sm pr-2">
                          {result.riskOpinion}
                        </div>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-sm ${similarityBadgeClass}`}>
                          {rowIncomplete ? "-" : `${result.similarity}%`}
                        </span>
                      </td>
                      <td className="p-3 w-96 align-top">
                        <div className="max-h-48 overflow-y-auto whitespace-pre-wrap text-sm pr-2">
                          {result.similarityOpinion}
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-1">
                          {result.negativeWords.slice(0, 3).map((word, i) => (
                            <span key={i} className="px-1 py-0.5 bg-red-100 text-red-800 text-xs rounded">
                              {word}
                            </span>
                          ))}
                          {result.negativeWords.length > 3 && (
                            <span className="text-xs text-muted-foreground">+{result.negativeWords.length - 3}</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {isAskAIOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 bg-black/50 z-40" onClick={closeAskAI} />

          {/* Drawer */}
          <div className="fixed bottom-0 left-0 right-0 bg-background border-t shadow-lg z-50 animate-in slide-in-from-bottom duration-300 h-[90vh]">
            <div className="max-w-7xl mx-auto h-full flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b flex-shrink-0">
                <div>
                  <h3 className="text-lg font-semibold">{t("faqAIFeedback")}</h3>
                  <p className="text-sm text-muted-foreground">{t("poweredByAILLM")}</p>
                </div>
                <Button variant="ghost" size="sm" onClick={closeAskAI}>
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Tabs */}
              <div className="flex border-b flex-shrink-0">
                <button
                  onClick={() => handleTabClick("challenges")}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "challenges"
                      ? "border-primary text-primary bg-primary/10"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t("qChallenges")}
                </button>
                <button
                  onClick={() => handleTabClick("consistency")}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "consistency"
                      ? "border-primary text-primary bg-primary/10"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t("consistencyCheck")}
                </button>
                <button
                  onClick={() => handleTabClick("risks")}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === "risks"
                      ? "border-primary text-primary bg-primary/10"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t("futureRisks")}
                </button>
              </div>

              {/* Content */}
              <div className="p-6 flex-1 overflow-y-auto">
                {activeTab === "challenges" && (
                  <div className="space-y-4">
                    <p className="text-muted-foreground">{t("challengesTabContent")}</p>
                  </div>
                )}
                {activeTab === "consistency" && (
                  <div className="space-y-4">
                    <p className="text-muted-foreground">{t("consistencyTabContent")}</p>
                  </div>
                )}
                {activeTab === "risks" && (
                  <div className="space-y-4">
                    <p className="text-muted-foreground">{t("risksTabContent")}</p>
                  </div>
                )}
              </div>

              {/* Question Input */}
              <div className="p-4 border-t bg-muted/30 flex-shrink-0">
                <div className="flex gap-2">
                  <Input
                    value={aiQuestion}
                    onChange={(e) => setAiQuestion(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={t("enterYourQuestion")}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleAskAI}
                    disabled={!aiQuestion.trim()}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {t("ask")}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
