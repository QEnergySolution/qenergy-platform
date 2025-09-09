"use client"

import React from "react"
import { useState, useMemo, useEffect } from "react"
import { Search, Plus, Minus, Check, X, Upload, FolderCog, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useLanguage } from "@/hooks/use-language"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { useToast } from "@/components/ui/use-toast"
import { ProjectAddDialog } from "./project-add-dialog"
import { ProjectExcelUploadDialog } from "./project-excel-upload-dialog"
import { UiProject } from "@/lib/services/projects"
import { 
  fetchProjectsFromApi, 
  createProject, 
  updateProject, 
  deleteProject,
  bulkUpsertProjects
} from "@/lib/services/projects-api"

export function ProjectManagement() {
  const [projects, setProjects] = useState<UiProject[]>([])
  const [searchKeyword, setSearchKeyword] = useState("")
  const [showActiveOnly, setShowActiveOnly] = useState(true)
  const [selectedProjects, setSelectedProjects] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const { t } = useLanguage()
  const { toast } = useToast()

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const data = await fetchProjectsFromApi()
      setProjects(data)
    } catch (error) {
      console.error("Failed to fetch projects:", error)
      setError(t("failedToLoadProjects"))
      setProjects([])
    } finally {
      setIsLoading(false)
    }
  }

  const filteredProjects = useMemo(() => {
    return projects.filter((project) => {
      const matchesSearch =
        project.code.toLowerCase().includes(searchKeyword.toLowerCase()) ||
        project.name.toLowerCase().includes(searchKeyword.toLowerCase()) ||
        (project.portfolio || "").toLowerCase().includes(searchKeyword.toLowerCase())

      const matchesActiveFilter = showActiveOnly ? project.active : true

      return matchesSearch && matchesActiveFilter
    })
  }, [projects, searchKeyword, showActiveOnly])

  const toggleProjectStatus = async (projectId: string) => {
    const project = projects.find(p => p.id === projectId)
    if (!project) return
    
    try {
      const updatedProject = await updateProject(project.code, { active: !project.active })
      
      if (updatedProject) {
        setProjects(prev => 
          prev.map(p => p.id === projectId ? { ...p, active: !p.active } : p)
        )
        
        toast({
          title: t("statusUpdated"),
          description: project.active 
            ? t("projectMarkedInactive", { code: project.code }) 
            : t("projectMarkedActive", { code: project.code })
        })
      }
    } catch (error) {
      console.error("Failed to update project status:", error)
      toast({
        variant: "destructive",
        title: t("error"),
        description: t("failedToUpdateStatus")
      })
    }
  }

  const handleAddProject = async (project: UiProject) => {
    try {
      const newProject = await createProject(project)
      
      if (newProject) {
        setProjects(prev => [...prev, newProject])
        
        toast({
          title: t("projectAdded"),
          description: t("projectAddedSuccess", { code: newProject.code })
        })
      }
    } catch (error) {
      console.error("Failed to add project:", error)
      toast({
        variant: "destructive",
        title: t("error"),
        description: t("failedToAddProject")
      })
      throw error
    }
  }

  const removeSelectedProjects = async () => {
    if (!selectedProjects.length) return
    
    const selectedProjectDetails = projects.filter(p => selectedProjects.includes(p.id))
    let successCount = 0
    let failCount = 0
    
    for (const project of selectedProjectDetails) {
      try {
        const success = await deleteProject(project.code)
        
        if (success) {
          successCount++
        } else {
          failCount++
        }
      } catch (error) {
        console.error(`Failed to delete project ${project.code}:`, error)
        failCount++
      }
    }
    
    if (successCount > 0) {
      // Refresh projects after deletion
      await loadProjects()
      
      toast({
        title: t("projectsRemoved"),
        description: t("projectsRemovedSuccess", { count: successCount })
      })
    }
    
    if (failCount > 0) {
      toast({
        variant: "destructive",
        title: t("error"),
        description: t("failedToRemoveProjects", { count: failCount })
      })
    }
    
    setSelectedProjects([])
  }

  const handleBulkUpsert = async (projects: UiProject[], markMissingAsInactive: boolean) => {
    try {
      const result = await bulkUpsertProjects(projects, markMissingAsInactive)
      
      if (result.success) {
        // Refresh projects after bulk upsert
        await loadProjects()
      }
      
      return result
    } catch (error) {
      console.error("Failed to bulk upsert projects:", error)
      return { success: false }
    }
  }

  const toggleProjectSelection = (projectId: string) => {
    setSelectedProjects(prev =>
      prev.includes(projectId) ? prev.filter(id => id !== projectId) : [...prev, projectId]
    )
  }

  const toggleSelectAll = () => {
    if (selectedProjects.length === filteredProjects.length && filteredProjects.length > 0) {
      setSelectedProjects([])
    } else {
      setSelectedProjects(filteredProjects.map(p => p.id))
    }
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
            onClick={() => setUploadDialogOpen(true)}
            className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            size="lg"
          >
            <Upload className="w-4 h-4 mr-2" />
            {t("uploadExcel")}
          </Button>
          <Button
            onClick={() => setAddDialogOpen(true)}
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
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">{t("loading")}...</div>
          ) : error ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>{t("error")}</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : (
            <>
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
            </>
          )}
        </CardContent>
      </Card>

      <ProjectAddDialog 
        open={addDialogOpen} 
        onOpenChange={setAddDialogOpen} 
        onAddProject={handleAddProject}
        existingProjectCodes={projects.map(p => p.code)}
      />

      <ProjectExcelUploadDialog
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
        onUpload={handleBulkUpsert}
      />
    </div>
  )
}
