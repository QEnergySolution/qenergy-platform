"use client"

import React, { useState, useRef } from "react"
import { useLanguage } from "@/hooks/use-language"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Upload, FileX, CheckCircle, AlertCircle, X, Download } from "lucide-react"
import { UiProject } from "@/lib/services/projects"
import { read, utils } from 'xlsx'

interface ProjectExcelUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpload: (projects: UiProject[], markMissingAsInactive: boolean) => Promise<{
    success: boolean;
    createdCount?: number;
    updatedCount?: number;
    inactivatedCount?: number;
    errors?: Array<{ rowIndex: number; projectCode?: string; errorMessage: string }>;
  }>
}

export function ProjectExcelUploadDialog({ open, onOpenChange, onUpload }: ProjectExcelUploadDialogProps) {
  const { t } = useLanguage()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<{
    success: boolean;
    createdCount?: number;
    updatedCount?: number;
    inactivatedCount?: number;
    errors?: Array<{ rowIndex: number; projectCode?: string; errorMessage: string }>;
  } | null>(null)
  const [markMissingAsInactive, setMarkMissingAsInactive] = useState(false)
  const [parseError, setParseError] = useState<string | null>(null)
  const [parsedProjects, setParsedProjects] = useState<UiProject[]>([])

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      parseFile(selectedFile)
    }
  }

  const parseFile = async (file: File) => {
    setParseError(null)
    setParsedProjects([])
    
    try {
      const buffer = await file.arrayBuffer()
      const workbook = read(buffer)
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      const data = utils.sheet_to_json<any>(worksheet)
      
      if (data.length === 0) {
        setParseError(t("noDataInFile"))
        return
      }
      
      // Check required columns
      const requiredColumns = ["project_code", "project_name"]
      const firstRow = data[0]
      const missingColumns = requiredColumns.filter(col => !(col in firstRow))
      
      if (missingColumns.length > 0) {
        setParseError(t("missingColumns") + ": " + missingColumns.join(", "))
        return
      }
      
      // Map to UiProject format
      const projects: UiProject[] = data.map((row, index) => {
        const status = row.status !== undefined ? Number(row.status) : 1
        
        return {
          id: `temp-${index}`, // Temporary ID
          code: String(row.project_code || ""),
          name: String(row.project_name || ""),
          portfolio: String(row.portfolio_cluster || ""),
          active: status === 1
        }
      })
      
      setParsedProjects(projects)
    } catch (error) {
      console.error("Error parsing Excel file:", error)
      setParseError(t("errorParsingFile"))
    }
  }

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault()
  }

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault()
    const droppedFile = event.dataTransfer.files[0]
    if (droppedFile) {
      setFile(droppedFile)
      parseFile(droppedFile)
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current?.click()
  }

  const handleUpload = async () => {
    if (!file || parsedProjects.length === 0) return
    
    setIsUploading(true)
    
    try {
      const result = await onUpload(parsedProjects, markMissingAsInactive)
      setUploadResult(result)
    } catch (error) {
      console.error("Error uploading projects:", error)
      setUploadResult({
        success: false,
        errors: [{ rowIndex: -1, errorMessage: String(error) }]
      })
    } finally {
      setIsUploading(false)
    }
  }

  const handleClose = () => {
    setFile(null)
    setUploadResult(null)
    setParseError(null)
    setParsedProjects([])
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
    onOpenChange(false)
  }

  const downloadErrorsAsCsv = () => {
    if (!uploadResult?.errors?.length) return
    
    const headers = ["Row", "Project Code", "Error Message"]
    const rows = uploadResult.errors.map(error => [
      error.rowIndex + 1,
      error.projectCode || "",
      error.errorMessage
    ])
    
    const csvContent = [
      headers.join(","),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    ].join("\n")
    
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.setAttribute("href", url)
    link.setAttribute("download", "upload_errors.csv")
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
  
  const downloadSampleExcel = () => {
    const sampleFilePath = "/samples/sample-projects.xlsx"
    const link = document.createElement("a")
    link.setAttribute("href", sampleFilePath)
    link.setAttribute("download", "sample-projects.xlsx")
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="text-xl">{t("uploadExcel")}</DialogTitle>
        </DialogHeader>
        
        <div className="py-4 space-y-4">
          {!uploadResult ? (
            <>
              <div
                className="border-2 border-dashed rounded-md p-6 text-center cursor-pointer hover:bg-muted/50 transition-colors"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={triggerFileInput}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                <p className="mt-2 text-sm font-medium">{t("dragOrClickToUpload")}</p>
                <p className="mt-1 text-xs text-muted-foreground">.xlsx, .xls, .csv</p>
              </div>
              
              {parseError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>{t("error")}</AlertTitle>
                  <AlertDescription>{parseError}</AlertDescription>
                </Alert>
              )}
              
              {file && !parseError && (
                <>
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertTitle>{t("fileSelected")}</AlertTitle>
                    <AlertDescription>{file.name}</AlertDescription>
                  </Alert>
                  
                  <div className="space-y-2">
                    <p className="text-sm font-medium">{t("previewData")}</p>
                    <div className="max-h-40 overflow-y-auto border rounded">
                      <table className="min-w-full divide-y divide-border">
                        <thead>
                          <tr className="bg-muted/50">
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">{t("projectCode")}</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">{t("projectName")}</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">{t("portfolioCluster")}</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">{t("status")}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {parsedProjects.slice(0, 5).map((project, index) => (
                            <tr key={index} className="border-b">
                              <td className="px-4 py-2 text-sm">{project.code}</td>
                              <td className="px-4 py-2 text-sm">{project.name}</td>
                              <td className="px-4 py-2 text-sm">{project.portfolio}</td>
                              <td className="px-4 py-2 text-sm">{project.active ? t("active") : t("inactive")}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {parsedProjects.length > 5 && (
                        <div className="px-4 py-2 text-xs text-muted-foreground">
                          {t("andMoreRows", { count: parsedProjects.length - 5 })}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2 pt-2">
                      <input
                        type="checkbox"
                        id="markMissingAsInactive"
                        checked={markMissingAsInactive}
                        onChange={(e) => setMarkMissingAsInactive(e.target.checked)}
                        className="rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <label htmlFor="markMissingAsInactive" className="text-sm">
                        {t("markMissingAsInactive")}
                      </label>
                    </div>
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="space-y-4">
              {uploadResult.success ? (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertTitle>{t("uploadSuccess")}</AlertTitle>
                  <AlertDescription>
                    <div className="space-y-1 pt-2">
                      <p>{t("createdCount")}: {uploadResult.createdCount || 0}</p>
                      <p>{t("updatedCount")}: {uploadResult.updatedCount || 0}</p>
                      {uploadResult.inactivatedCount !== undefined && (
                        <p>{t("inactivatedCount")}: {uploadResult.inactivatedCount}</p>
                      )}
                    </div>
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>{t("uploadFailed")}</AlertTitle>
                  <AlertDescription>
                    {uploadResult.errors && uploadResult.errors.length > 0 ? (
                      <div className="space-y-2 pt-2">
                        <p>{t("errorsFound", { count: uploadResult.errors.length })}</p>
                        <div className="max-h-40 overflow-y-auto border rounded">
                          <table className="min-w-full divide-y divide-border">
                            <thead>
                              <tr className="bg-muted/50">
                                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">{t("row")}</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">{t("projectCode")}</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">{t("error")}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {uploadResult.errors.slice(0, 5).map((error, index) => (
                                <tr key={index} className="border-b">
                                  <td className="px-4 py-2 text-sm">{error.rowIndex + 1}</td>
                                  <td className="px-4 py-2 text-sm">{error.projectCode || "-"}</td>
                                  <td className="px-4 py-2 text-sm">{error.errorMessage}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {uploadResult.errors.length > 5 && (
                            <div className="px-4 py-2 text-xs text-muted-foreground">
                              {t("andMoreErrors", { count: uploadResult.errors.length - 5 })}
                            </div>
                          )}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-2"
                          onClick={downloadErrorsAsCsv}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          {t("downloadErrors")}
                        </Button>
                      </div>
                    ) : (
                      t("unknownError")
                    )}
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </div>
        
        <DialogFooter className="flex flex-col sm:flex-row sm:justify-between">
          <div className="mb-3 sm:mb-0">
            <Button 
              type="button" 
              variant="outline" 
              size="sm" 
              onClick={downloadSampleExcel}
              className="flex items-center"
            >
              <Download className="h-4 w-4 mr-2" />
              {t("downloadSampleExcel")}
            </Button>
          </div>
          
          <div className="flex gap-2">
            {!uploadResult ? (
              <>
                <Button type="button" variant="outline" onClick={handleClose}>
                  {t("cancel")}
                </Button>
                <Button
                  type="button"
                  disabled={!file || parsedProjects.length === 0 || !!parseError || isUploading}
                  onClick={handleUpload}
                >
                  {isUploading ? t("uploading") : t("upload")}
                </Button>
              </>
            ) : (
              <Button type="button" onClick={handleClose}>
                {t("close")}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
