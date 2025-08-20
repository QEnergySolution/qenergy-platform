"use client"

import type React from "react"
import { useState, useMemo, useRef } from "react"
import { Search, Plus, Minus, Check, X, Upload, FolderCog } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useLanguage } from "@/hooks/use-language"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

interface Project {
  id: string
  code: string
  name: string
  portfolio: string
  active: boolean
}

const initialProjects: Project[] = [
  { id: "1", code: "2ES00009", name: "Boedo 1", portfolio: "Herrera", active: true },
  { id: "2", code: "2ES00010", name: "Boedo 2", portfolio: "Herrera", active: true },
  { id: "3", code: "2DE00001", name: "Illmersdorf", portfolio: "Illmersdorf", active: true },
  { id: "4", code: "2DE00002", name: "Garwitz", portfolio: "Lunaco", active: false },
  { id: "5", code: "2DE00003", name: "Matzlow", portfolio: "Lunaco", active: true },
  { id: "6", code: "2DE00004", name: "IM 24 Tangerhütte", portfolio: "Aristoteles_1", active: true },
  { id: "7", code: "2DE00005", name: "IM 07 Blankensee", portfolio: "Aristoteles_2", active: false },
  { id: "8", code: "2DE00006", name: "IM 44 Gondorf", portfolio: "Aristoteles_3", active: true },
  { id: "9", code: "2DE00007", name: "Letzendorf", portfolio: "Advice2Energy", active: true },
  { id: "10", code: "2DE00013", name: "Bosseborn_2", portfolio: "Bosseborn_2", active: true },
  { id: "11", code: "2DE00015", name: "Wethen", portfolio: "Wethen", active: false },
  { id: "12", code: "2DE00016", name: "Oberndorf", portfolio: "Oberndorf", active: true },
  { id: "13", code: "2DE00017", name: "IM 16 Bad Freienwalde", portfolio: "Aristoteles_2", active: true },
  { id: "14", code: "2DE00018", name: "IM 37 Barnim", portfolio: "Aristoteles_2", active: true },
  { id: "15", code: "2DE00019", name: "Dahlen", portfolio: "Dahlen", active: false },
  { id: "16", code: "2DE00023", name: "IM 18 Reichenberg", portfolio: "Aristoteles_2", active: true },
  { id: "17", code: "2ES00007", name: "Cabrovales 1", portfolio: "Cabrovales 1", active: true },
  { id: "18", code: "2ES00011", name: "Torozos 1", portfolio: "Zaratan_PV", active: true },
  { id: "19", code: "2ES00012", name: "Torozos 2", portfolio: "Zaratan_PV", active: true },
  { id: "20", code: "2ES00013", name: "Torozos 3", portfolio: "Zaratan_PV", active: true },
]

export function ProjectManagement() {
  const [projects, setProjects] = useState<Project[]>(initialProjects)
  const [searchKeyword, setSearchKeyword] = useState("")
  const [showActiveOnly, setShowActiveOnly] = useState(true)
  const [selectedProjects, setSelectedProjects] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { t } = useLanguage()

  const filteredProjects = useMemo(() => {
    return projects.filter((project) => {
      const matchesSearch =
        project.code.toLowerCase().includes(searchKeyword.toLowerCase()) ||
        project.name.toLowerCase().includes(searchKeyword.toLowerCase()) ||
        project.portfolio.toLowerCase().includes(searchKeyword.toLowerCase())

      const matchesActiveFilter = showActiveOnly ? project.active : true

      return matchesSearch && matchesActiveFilter
    })
  }, [projects, searchKeyword, showActiveOnly])

  const toggleProjectStatus = (projectId: string) => {
    setProjects((prev) =>
      prev.map((project) => (project.id === projectId ? { ...project, active: !project.active } : project)),
    )
  }

  const addNewProject = () => {
    const newProject: Project = {
      id: Date.now().toString(),
      code: `2XX${String(Math.floor(Math.random() * 100000)).padStart(5, "0")}`,
      name: "New Project",
      portfolio: "New Portfolio",
      active: true,
    }
    setProjects((prev) => [...prev, newProject])
  }

  const removeSelectedProjects = () => {
    setProjects((prev) => prev.filter((project) => !selectedProjects.includes(project.id)))
    setSelectedProjects([])
  }

  const toggleProjectSelection = (projectId: string) => {
    setSelectedProjects((prev) =>
      prev.includes(projectId) ? prev.filter((id) => id !== projectId) : [...prev, projectId],
    )
  }

  const toggleSelectAll = () => {
    if (selectedProjects.length === filteredProjects.length && filteredProjects.length > 0) {
      setSelectedProjects([])
    } else {
      setSelectedProjects(filteredProjects.map((p) => p.id))
    }
  }

  const handleExcelUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      console.log("Excel file uploaded:", file.name)
      alert(`${file.name} ${t("uploadSuccess")}`)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  const triggerFileUpload = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <FolderCog className="w-8 h-8" />
          {t("projectManagementTitle")}
        </h1>
        <div className="flex items-center gap-3">
          <Button
            onClick={triggerFileUpload}
            className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            size="lg"
          >
            <Upload className="w-4 h-4 mr-2" />
            {t("uploadExcel")}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls,.csv"
            onChange={handleExcelUpload}
            className="hidden"
          />
          <Button
            onClick={addNewProject}
            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            size="lg"
          >
            <Plus className="w-4 h-4 mr-2" />
            {t("addProject")}
          </Button>
          <Button
            onClick={removeSelectedProjects}
            disabled={selectedProjects.length === 0}
            variant="destructive"
            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:transform-none disabled:shadow-none"
            size="lg"
          >
            <Minus className="w-4 h-4 mr-2" />
            {t("removeSelected")} ({selectedProjects.length})
          </Button>
        </div>
      </div>

      <Card className="border-2 border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-xl text-primary">{t("searchAndFilter")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder={t("searchPlaceholder")}
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="active-only"
                checked={showActiveOnly}
                onCheckedChange={(checked) => setShowActiveOnly(checked as boolean)}
              />
              <label
                htmlFor="active-only"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-black dark:text-white"
              >
                {t("showActiveOnly")}
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedProjects.length === filteredProjects.length && filteredProjects.length > 0}
                      onCheckedChange={toggleSelectAll}
                    />
                  </TableHead>
                  <TableHead>{t("projectCode")}</TableHead>
                  <TableHead>{t("projectName")}</TableHead>
                  <TableHead>{t("portfolioCluster")}</TableHead>
                  <TableHead className="text-center">{t("status")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProjects.map((project) => (
                  <TableRow key={project.id} className="hover:bg-muted/50">
                    <TableCell>
                      <Checkbox
                        checked={selectedProjects.includes(project.id)}
                        onCheckedChange={() => toggleProjectSelection(project.id)}
                      />
                    </TableCell>
                    <TableCell className="font-mono text-sm">{project.code}</TableCell>
                    <TableCell className="font-medium">{project.name}</TableCell>
                    <TableCell>{project.portfolio}</TableCell>
                    <TableCell className="text-center">
                      <Button
                        onClick={() => toggleProjectStatus(project.id)}
                        variant="ghost"
                        size="sm"
                        className={`px-4 py-2 rounded-full font-medium transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg ${
                          project.active
                            ? "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white"
                            : "bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white"
                        }`}
                      >
                        {project.active ? (
                          <>
                            <Check className="w-3 h-3 mr-1" />
                            {t("active")}
                          </>
                        ) : (
                          <>
                            <X className="w-3 h-3 mr-1" />
                            {t("inactive")}
                          </>
                        )}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {filteredProjects.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">{t("noProjectsFound")}</div>
          )}

          <div className="mt-4 text-sm text-muted-foreground">
            {t("showing")} {filteredProjects.length} {t("of")} {projects.length} {t("projects")}
            {selectedProjects.length > 0 && ` • ${selectedProjects.length} ${t("selected")}`}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
