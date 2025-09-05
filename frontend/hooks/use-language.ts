"use client"

import { useState, useEffect } from "react"
import { translations, type Language, type TranslationKey } from "@/lib/translations"

export function useLanguage() {
  const [language, setLanguage] = useState<Language>("en")

  useEffect(() => {
    const savedLanguage = localStorage.getItem("qenergy-language") as Language
    if (savedLanguage && savedLanguage in translations) {
      setLanguage(savedLanguage)
    }
  }, [])

  const changeLanguage = (newLanguage: Language) => {
    setLanguage(newLanguage)
    localStorage.setItem("qenergy-language", newLanguage)
  }

  const t = (key: TranslationKey, params?: { count?: number; year?: string; week?: string }): string => {
    const template = translations[language][key] || translations.en[key] || key
    
    // Handle template string interpolation for showingReports
    if (key === "showingReports" && params) {
      return template
        .replace("{{count}}", String(params.count || 0))
        .replace("{{year}}", String(params.year || ""))
        .replace("{{week}}", String(params.week || ""))
    }
    
    return template
  }

  return { language, changeLanguage, t }
}
