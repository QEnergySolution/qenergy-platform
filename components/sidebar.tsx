"use client"

import type React from "react"

import { useState, useEffect } from "react"
import {
  ChevronDown,
  ChevronRight,
  Moon,
  Sun,
  Settings,
  BarChart3,
  FileText,
  Shield,
  Globe,
  Upload,
  FolderCog,
  Eye,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "next-themes"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { useLanguage } from "@/hooks/use-language"
import Image from "next/image"

interface MenuItem {
  id: string
  labelKey: string
  icon: React.ReactNode
  children?: MenuItem[]
}

interface SidebarProps {
  onMenuClick?: (menuId: string) => void
}

const languages = [
  { code: "en", name: "English", flag: "🇺🇸" },
  { code: "fr", name: "Français", flag: "🇫🇷" },
  { code: "de", name: "Deutsch", flag: "🇩🇪" },
  { code: "es", name: "Español", flag: "🇪🇸" },
  { code: "pt", name: "Português", flag: "🇵🇹" },
  { code: "ko", name: "한국어", flag: "🇰🇷" },
]

export function Sidebar({ onMenuClick }: SidebarProps) {
  const [expandedItems, setExpandedItems] = useState<string[]>(["admin", "analysis"])
  const [activeItem, setActiveItem] = useState<string>("weekly-report")
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const { language, changeLanguage, t } = useLanguage()

  const menuItems: MenuItem[] = [
    {
      id: "admin",
      labelKey: "admin",
      icon: <Settings className="w-4 h-4" />,
      children: [
        {
          id: "project-management",
          labelKey: "projectManagement",
          icon: <FolderCog className="w-4 h-4" />, // 관리 관련 아이콘으로 변경
        },
        {
          id: "report-upload",
          labelKey: "reportUpload",
          icon: <Upload className="w-4 h-4" />, // 업로드 아이콘으로 변경
        },
        {
          id: "authorization",
          labelKey: "authorization",
          icon: <Shield className="w-4 h-4" />,
        },
      ],
    },
    {
      id: "analysis",
      labelKey: "analysis",
      icon: <BarChart3 className="w-4 h-4" />,
      children: [
        {
          id: "weekly-report",
          labelKey: "weeklyReport",
          icon: <FileText className="w-4 h-4" />, // 리포트 아이콘으로 변경
        },
        {
          id: "project-history",
          labelKey: "projectDetail",
          icon: <Eye className="w-4 h-4" />, // 상세보기 아이콘으로 변경
        },
      ],
    },
  ]

  useEffect(() => {
    setMounted(true)
  }, [])

  const toggleExpanded = (itemId: string) => {
    setExpandedItems((prev) => (prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]))
  }

  const handleItemClick = (itemId: string) => {
    setActiveItem(itemId)
    onMenuClick?.(itemId)
  }

  const toggleTheme = () => {
    console.log("Current theme:", theme)
    const newTheme = theme === "dark" ? "light" : "dark"
    console.log("Switching to theme:", newTheme)
    setTheme(newTheme)
  }

  const handleLanguageChange = (languageCode: string) => {
    changeLanguage(languageCode as any)
    console.log("Language changed to:", languageCode)
  }

  if (!mounted) {
    return null
  }

  const currentLanguage = languages.find((lang) => lang.code === language) || languages[0]

  return (
    <div className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border">
        <Button
          variant="ghost"
          className="w-full justify-center text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground p-2"
          onClick={() => handleItemClick("weekly-report")}
        >
          <Image src="/images/qenergy-logo.png" alt="QENERGY" width={120} height={32} className="h-8 w-auto" priority />
        </Button>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => (
          <div key={item.id}>
            <Button
              variant="ghost"
              className={`w-full justify-between text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground ${
                activeItem === item.id ? "bg-sidebar-primary text-sidebar-primary-foreground" : ""
              }`}
              onClick={() => {
                toggleExpanded(item.id)
                handleItemClick(item.id)
              }}
            >
              <div className="flex items-center">
                {item.icon}
                <span className="ml-3">{t(item.labelKey as any)}</span>
              </div>
              {item.children &&
                (expandedItems.includes(item.id) ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                ))}
            </Button>

            {/* Submenu */}
            {item.children && expandedItems.includes(item.id) && (
              <div className="ml-4 mt-2 space-y-1">
                {item.children.map((child) => (
                  <Button
                    key={child.id}
                    variant="ghost"
                    className={`w-full justify-start text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground ${
                      activeItem === child.id ? "bg-sidebar-primary text-sidebar-primary-foreground" : ""
                    }`}
                    onClick={() => handleItemClick(child.id)}
                  >
                    {child.icon}
                    <span className="ml-3">{t(child.labelKey as any)}</span>
                  </Button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Language Selector and Theme Toggle */}
      <div className="p-4 border-t border-sidebar-border space-y-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            >
              <Globe className="w-4 h-4 mr-3" />
              <span className="flex items-center gap-2">
                <span className="text-lg">{currentLanguage.flag}</span>
                <span>{currentLanguage.name}</span>
              </span>
              <ChevronDown className="w-4 h-4 ml-auto" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            {languages.map((lang) => (
              <DropdownMenuItem
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`flex items-center gap-3 ${language === lang.code ? "bg-accent" : ""}`}
              >
                <span className="text-lg">{lang.flag}</span>
                <span>{lang.name}</span>
                {language === lang.code && <div className="w-2 h-2 bg-primary rounded-full ml-auto" />}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="ghost"
          className="w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          onClick={toggleTheme}
        >
          {theme === "dark" ? (
            <>
              <Sun className="w-4 h-4 mr-3" />
              <span>{t("lightMode")}</span>
            </>
          ) : (
            <>
              <Moon className="w-4 h-4 mr-3" />
              <span>{t("darkMode")}</span>
            </>
          )}
        </Button>
        <div className="text-xs text-muted-foreground mt-2 text-center">
          {t("current")}: {theme || "loading..."}
        </div>
      </div>
    </div>
  )
}
