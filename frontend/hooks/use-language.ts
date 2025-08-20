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

  const t = (key: TranslationKey): string => {
    return translations[language][key] || translations.en[key] || key
  }

  return { language, changeLanguage, t }
}
