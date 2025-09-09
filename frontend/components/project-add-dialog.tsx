"use client"

import React, { useState } from "react"
import { useLanguage } from "@/hooks/use-language"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { UiProject } from "@/lib/services/projects"

interface ProjectAddDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAddProject: (project: UiProject) => Promise<void>
  existingProjectCodes?: string[]
}

export function ProjectAddDialog({ open, onOpenChange, onAddProject, existingProjectCodes = [] }: ProjectAddDialogProps) {
  const { t } = useLanguage()
  const [projectCode, setProjectCode] = useState("")
  const [projectName, setProjectName] = useState("")
  const [portfolio, setPortfolio] = useState("")
  const [active, setActive] = useState(true)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<{ [key: string]: string }>({})

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {}

    if (!projectCode.trim()) {
      newErrors.projectCode = t("fieldRequired")
    } else if (projectCode.length > 32) {
      newErrors.projectCode = t("maxLength").replace("{0}", "32")
    } else if (existingProjectCodes.includes(projectCode)) {
      newErrors.projectCode = t("projectCodeExists")
    }

    if (!projectName.trim()) {
      newErrors.projectName = t("fieldRequired")
    } else if (projectName.length > 255) {
      newErrors.projectName = t("maxLength").replace("{0}", "255")
    }

    if (portfolio && portfolio.length > 128) {
      newErrors.portfolio = t("maxLength").replace("{0}", "128")
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsLoading(true)

    try {
      const newProject: UiProject = {
        id: Date.now().toString(), // Temporary ID, will be replaced by the server
        code: projectCode,
        name: projectName,
        portfolio,
        active,
      }

      await onAddProject(newProject)
      resetForm()
      onOpenChange(false)
    } catch (error) {
      console.error("Error adding project:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const resetForm = () => {
    setProjectCode("")
    setProjectName("")
    setPortfolio("")
    setActive(true)
    setErrors({})
  }

  const handleCancel = () => {
    resetForm()
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-xl">{t("addProject")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="projectCode" className="text-right">
                {t("projectCode")} <span className="text-red-500">*</span>
              </Label>
              <Input
                id="projectCode"
                value={projectCode}
                onChange={(e) => setProjectCode(e.target.value)}
                placeholder="e.g., 2ES00001"
                className={errors.projectCode ? "border-red-500" : ""}
              />
              {errors.projectCode && <p className="text-sm text-red-500">{errors.projectCode}</p>}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="projectName" className="text-right">
                {t("projectName")} <span className="text-red-500">*</span>
              </Label>
              <Input
                id="projectName"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g., Project Alpha"
                className={errors.projectName ? "border-red-500" : ""}
              />
              {errors.projectName && <p className="text-sm text-red-500">{errors.projectName}</p>}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="portfolio" className="text-right">
                {t("portfolioCluster")}
              </Label>
              <Input
                id="portfolio"
                value={portfolio}
                onChange={(e) => setPortfolio(e.target.value)}
                placeholder="e.g., Portfolio A"
                className={errors.portfolio ? "border-red-500" : ""}
              />
              {errors.portfolio && <p className="text-sm text-red-500">{errors.portfolio}</p>}
            </div>
            <div className="flex items-center gap-2">
              <Switch id="active" checked={active} onCheckedChange={setActive} />
              <Label htmlFor="active">{t("active")}</Label>
            </div>
          </div>
          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={handleCancel} disabled={isLoading}>
              {t("cancel")}
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? t("saving") : t("add")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
