"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Search, Download, MessageSquare, ChevronUp, ChevronDown, Eye } from "lucide-react"
import { useLanguage } from "@/hooks/use-language"

interface ProjectDetailData {
  projectCode: string
  projectName: string
  category: string
  weekData: { [key: string]: string }
}

type SortField = "projectCode" | "projectName" | "category"
type SortDirection = "asc" | "desc"

export function ProjectDetail() {
  const { t } = useLanguage()

  // Form state with localStorage persistence
  const [selectedProject, setSelectedProject] = useState<string>("2ES00009") // Updated default value
  const [selectedCategory, setSelectedCategory] = useState<string>("EPC") // Updated default value
  const [startWeek, setStartWeek] = useState<string>("CW01") // Updated default value
  const [endWeek, setEndWeek] = useState<string>("CW52") // Updated default value

  // Table state
  const [searchResults, setSearchResults] = useState<ProjectDetailData[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [sortField, setSortField] = useState<SortField>("projectCode")
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc")

  // Ask AI drawer state
  const [isAskAIOpen, setIsAskAIOpen] = useState(false)
  const [aiQuestion, setAiQuestion] = useState("")

  // Sample data
  const projects = [
    { code: "2ES00009", name: "Boedo 1" },
    { code: "2ES00010", name: "Boedo 2" },
    { code: "2DE00001", name: "Illmersdorf" },
    { code: "2DE00002", name: "Garwitz" },
    { code: "2DE00003", name: "Matzlow" },
  ]

  const categories = ["EPC", "Finance", "DEV", "Investment"]

  // Generate weeks for current year
  const currentYear = new Date().getFullYear()
  const weeks = Array.from({ length: 52 }, (_, i) => `CW${String(i + 1).padStart(2, "0")}`)

  // Load saved selections from localStorage
  useEffect(() => {
    const savedProject = localStorage.getItem("projectDetail_selectedProject")
    const savedCategory = localStorage.getItem("projectDetail_selectedCategory")
    const savedStartWeek = localStorage.getItem("projectDetail_startWeek")
    const savedEndWeek = localStorage.getItem("projectDetail_endWeek")

    if (savedProject) setSelectedProject(savedProject)
    if (savedCategory) setSelectedCategory(savedCategory)
    if (savedStartWeek) setStartWeek(savedStartWeek)
    if (savedEndWeek) setEndWeek(savedEndWeek)
  }, [])

  // Save selections to localStorage
  useEffect(() => {
    if (selectedProject) localStorage.setItem("projectDetail_selectedProject", selectedProject)
  }, [selectedProject])

  useEffect(() => {
    if (selectedCategory) localStorage.setItem("projectDetail_selectedCategory", selectedCategory)
  }, [selectedCategory])

  useEffect(() => {
    if (startWeek) localStorage.setItem("projectDetail_startWeek", startWeek)
  }, [startWeek])

  useEffect(() => {
    if (endWeek) localStorage.setItem("projectDetail_endWeek", endWeek)
  }, [endWeek])

  const handleSearch = async () => {
    if (!selectedProject || !startWeek || !endWeek) {
      alert(t("pleaseSelectRequiredFields"))
      return
    }

    setIsSearching(true)

    // Simulate API call
    setTimeout(() => {
      const mockData: ProjectDetailData[] = [
        {
          projectCode: selectedProject,
          projectName: projects.find((p) => p.code === selectedProject)?.name || "",
          category: selectedCategory || "EPC",
          weekData: {
            "2025-CW24": "Project milestone completed. All systems operational.",
            "2025-CW25": "Minor maintenance performed. Energy output increased by 3%.",
            "2025-CW26": "Weather conditions favorable. Production at 98% capacity.",
            "2025-CW27": "Scheduled inspection completed. No issues found.",
          },
        },
      ]
      setSearchResults(mockData)
      setIsSearching(false)
    }, 1500)
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("asc")
    }
  }

  const sortedResults = [...searchResults].sort((a, b) => {
    const aValue = a[sortField]
    const bValue = b[sortField]
    const modifier = sortDirection === "asc" ? 1 : -1
    return aValue.localeCompare(bValue) * modifier
  })

  const handleDownloadExcel = () => {
    // Simulate Excel download
    alert(t("downloadingExcel"))
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === "asc" ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Eye className="w-8 h-8" />
          {t("projectDetail")}
        </h1>
      </div>

      <Card className="border-2 border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-xl text-primary">{t("searchFilters")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {/* Project Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-black dark:text-white">{t("project")} *</label>
              <Select value={selectedProject} onValueChange={setSelectedProject}>
                <SelectTrigger>
                  <SelectValue placeholder={t("selectProject")} />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((project) => (
                    <SelectItem key={project.code} value={project.code}>
                      {project.code} - {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Category Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-black dark:text-white">
                {t("category")} ({t("optional")})
              </label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder={t("selectCategory")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="EPC">{t("allCategories")}</SelectItem>
                  {categories.map((category) => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Start Week */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-black dark:text-white">{t("startWeek")} *</label>
              <Select value={startWeek} onValueChange={setStartWeek}>
                <SelectTrigger>
                  <SelectValue placeholder={t("selectStartWeek")} />
                </SelectTrigger>
                <SelectContent>
                  {weeks.map((week) => (
                    <SelectItem key={week} value={week}>
                      {currentYear}-{week}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* End Week */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-black dark:text-white">{t("endWeek")} *</label>
              <Select value={endWeek} onValueChange={setEndWeek}>
                <SelectTrigger>
                  <SelectValue placeholder={t("selectEndWeek")} />
                </SelectTrigger>
                <SelectContent>
                  {weeks.map((week) => (
                    <SelectItem key={week} value={week}>
                      {currentYear}-{week}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons moved outside the Card */}
      <div className="flex items-center gap-4">
        <Button
          onClick={handleSearch}
          disabled={isSearching || !selectedProject || !startWeek || !endWeek}
          className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
          size="lg"
        >
          <Search className="w-4 h-4 mr-2" />
          {isSearching ? t("searching") : t("search")}
        </Button>

        {searchResults.length > 0 && !isSearching && (
          <>
            <Button
              onClick={() => setIsAskAIOpen(true)}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
              size="lg"
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              {t("askAI")}
            </Button>
            <Button
              onClick={handleDownloadExcel}
              className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
              size="lg"
            >
              <Download className="w-4 h-4 mr-2" />
              {t("downloadExcel")}
            </Button>
          </>
        )}
      </div>

      {/* Results Section */}
      {searchResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t("projectHistory")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("projectCode")}>
                      <div className="flex items-center gap-2">
                        {t("projectCode")}
                        <SortIcon field="projectCode" />
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("projectName")}>
                      <div className="flex items-center gap-2">
                        {t("projectName")}
                        <SortIcon field="projectName" />
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer hover:bg-muted/50" onClick={() => handleSort("category")}>
                      <div className="flex items-center gap-2">
                        {t("category")}
                        <SortIcon field="category" />
                      </div>
                    </TableHead>
                    <TableHead>2025-CW24</TableHead>
                    <TableHead>2025-CW25</TableHead>
                    <TableHead>2025-CW26</TableHead>
                    <TableHead>2025-CW27</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedResults.map((result, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{result.projectCode}</TableCell>
                      <TableCell>{result.projectName}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{result.category}</Badge>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">{result.weekData["2025-CW24"]}</TableCell>
                      <TableCell className="max-w-xs truncate">{result.weekData["2025-CW25"]}</TableCell>
                      <TableCell className="max-w-xs truncate">{result.weekData["2025-CW26"]}</TableCell>
                      <TableCell className="max-w-xs truncate">{result.weekData["2025-CW27"]}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Ask AI Drawer */}
      {isAskAIOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50">
          <div className="w-full h-[80vh] bg-background border-t rounded-t-lg animate-in slide-in-from-bottom duration-300">
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b">
                <div>
                  <h2 className="text-xl font-semibold">{t("faqAIFeedback")}</h2>
                  <p className="text-sm text-muted-foreground">{t("poweredByAILLM")}</p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setIsAskAIOpen(false)}>
                  ×
                </Button>
              </div>

              {/* Content */}
              <div className="flex-1 p-6 space-y-4">
                <div className="space-y-4">
                  <h3 className="text-lg font-medium">{t("projectAnalysisQuestions")}</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Button
                      variant="outline"
                      className="h-auto p-4 text-left justify-start bg-transparent"
                      onClick={() => setAiQuestion(t("projectChallengesQuestion"))}
                    >
                      <div>
                        <div className="font-medium">{t("projectChallenges")}</div>
                        <div className="text-sm text-muted-foreground mt-1">{t("askAboutChallenges")}</div>
                      </div>
                    </Button>
                    <Button
                      variant="outline"
                      className="h-auto p-4 text-left justify-start bg-transparent"
                      onClick={() => setAiQuestion(t("consistencyCheckQuestion"))}
                    >
                      <div>
                        <div className="font-medium">{t("consistencyCheck")}</div>
                        <div className="text-sm text-muted-foreground mt-1">{t("checkConsistency")}</div>
                      </div>
                    </Button>
                    <Button
                      variant="outline"
                      className="h-auto p-4 text-left justify-start bg-transparent"
                      onClick={() => setAiQuestion(t("futureRisksQuestion"))}
                    >
                      <div>
                        <div className="font-medium">{t("futureRisks")}</div>
                        <div className="text-sm text-muted-foreground mt-1">{t("identifyRisks")}</div>
                      </div>
                    </Button>
                  </div>
                </div>

                {/* Question Input */}
                <div className="flex gap-2 mt-8">
                  <input
                    type="text"
                    value={aiQuestion}
                    onChange={(e) => setAiQuestion(e.target.value)}
                    placeholder={t("enterYourQuestion")}
                    className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <Button onClick={() => alert("AI analysis started!")}>{t("ask")}</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
