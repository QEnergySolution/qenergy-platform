"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { ProjectManagement } from "@/components/project-management"
import { ReportUpload } from "@/components/report-upload"
import { WeeklyReport } from "@/components/weekly-report"
import { Authorization } from "@/components/authorization"
import { ProjectDetail } from "@/components/project-detail"

export default function HomePage() {
  const [activeView, setActiveView] = useState("weekly-report")

  const renderContent = () => {
    switch (activeView) {
      case "project-management":
        return <ProjectManagement />
      case "report-upload":
        return <ReportUpload />
      case "weekly-report":
        return <WeeklyReport />
      case "authorization":
        return <Authorization />
      case "project-history":
        return <ProjectDetail />
      default:
        return (
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold mb-6">QENERGY AI Analysis Platform</h1>
            <div className="bg-card border rounded-lg p-6">
              <p className="text-muted-foreground">
                Welcome to the QENERGY AI Analysis Platform. Use the sidebar to navigate through different sections.
              </p>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar onMenuClick={setActiveView} />
      <main className="flex-1 p-8">{renderContent()}</main>
    </div>
  )
}
