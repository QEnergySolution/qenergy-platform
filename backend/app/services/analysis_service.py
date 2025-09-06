from typing import List, Dict, Any, Optional, Tuple
import os
import json
import logging
import hashlib
from datetime import datetime
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text

from ..models.project_history import ProjectHistory
from ..models.weekly_report_analysis import WeeklyReportAnalysis
from ..models.project import Project
from ..schemas.analysis import WeeklyReportAnalysisCreate, WeeklyReportAnalysisRead, Language, Category

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self):
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        
        if not all([self.azure_api_key, self.azure_endpoint]):
            logger.warning("Azure OpenAI credentials not fully configured")

    def get_projects_by_cw_pair(
        self, 
        db: Session, 
        past_cw: str, 
        latest_cw: str,
        category: Optional[Category] = None
    ) -> List[Dict[str, Any]]:
        """Get candidate projects present in either past_cw or latest_cw"""
        query = db.query(ProjectHistory).filter(
            or_(
                ProjectHistory.cw_label == past_cw,
                ProjectHistory.cw_label == latest_cw
            )
        )
        
        if category:
            query = query.filter(ProjectHistory.category == category)
        
        # Group by project_code and collect metadata
        project_data = {}
        for record in query.all():
            if record.project_code not in project_data:
                project_data[record.project_code] = {
                    "project_code": record.project_code,
                    "project_name": None,
                    "categories": set(),
                    "cw_labels": set()
                }
            
            project_data[record.project_code]["categories"].add(record.category or "Unknown")
            project_data[record.project_code]["cw_labels"].add(record.cw_label)
        
        # Get project names from projects table
        project_codes = list(project_data.keys())
        if project_codes:
            projects = db.query(Project).filter(Project.project_code.in_(project_codes)).all()
            for project in projects:
                if project.project_code in project_data:
                    project_data[project.project_code]["project_name"] = project.project_name
        
        # Convert sets to lists for JSON serialization
        result = []
        for data in project_data.values():
            result.append({
                "project_code": data["project_code"],
                "project_name": data["project_name"],
                "categories": list(data["categories"]),
                "cw_labels": list(data["cw_labels"])
            })
        
        return result

    def get_project_content_for_cw(
        self,
        db: Session,
        project_code: str,
        cw_label: str,
        category: Optional[Category] = None
    ) -> Optional[str]:
        """Get aggregated content for a project in a specific calendar week"""
        query = db.query(ProjectHistory).filter(
            and_(
                ProjectHistory.project_code == project_code,
                ProjectHistory.cw_label == cw_label
            )
        )
        
        if category:
            query = query.filter(ProjectHistory.category == category)
        
        records = query.all()
        if not records:
            return None
        
        # Aggregate content from all records for this project/CW
        content_parts = []
        for record in records:
            parts = [record.summary]
            if record.title:
                parts.insert(0, f"Title: {record.title}")
            if record.next_actions:
                parts.append(f"Next Actions: {record.next_actions}")
            content_parts.append(" | ".join(parts))
        
        return "\n\n".join(content_parts)

    def detect_language(self, text: str) -> Language:
        """Simple language detection - can be enhanced later"""
        if not text:
            return "EN"
        
        # Simple heuristic - check for Korean characters
        korean_chars = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
        if korean_chars > len(text) * 0.1:  # More than 10% Korean characters
            return "KO"
        
        return "EN"

    def extract_negative_words(self, text: str, language: Language) -> List[str]:
        """Extract negative sentiment words from text"""
        # Simple negative word detection - can be enhanced with proper NLP
        negative_patterns = {
            "EN": [
                "delay", "delays", "delayed", "problem", "problems", "issue", "issues",
                "risk", "risks", "concern", "concerns", "failure", "failed", "error",
                "errors", "critical", "urgent", "behind", "overrun", "deficit",
                "shortage", "lack", "insufficient", "poor", "bad", "worse", "worst",
                "cancel", "cancelled", "stop", "stopped", "pause", "paused"
            ],
            "KO": [
                "지연", "문제", "위험", "실패", "오류", "긴급", "부족", "중단", "취소"
            ]
        }
        
        words = negative_patterns.get(language, negative_patterns["EN"])
        found_words = []
        
        text_lower = text.lower()
        for word in words:
            if word.lower() in text_lower:
                found_words.append(word)
        
        return list(set(found_words))  # Remove duplicates

    def calculate_similarity(self, past_content: str, latest_content: str) -> float:
        """Calculate content similarity using simple word overlap"""
        if not past_content or not latest_content:
            return 0.0
        
        # Simple word-based similarity
        past_words = set(past_content.lower().split())
        latest_words = set(latest_content.lower().split())
        
        if not past_words and not latest_words:
            return 100.0
        if not past_words or not latest_words:
            return 0.0
        
        intersection = past_words.intersection(latest_words)
        union = past_words.union(latest_words)
        
        return (len(intersection) / len(union)) * 100 if union else 0.0

    async def get_llm_analysis(
        self,
        past_content: str,
        latest_content: str,
        language: Language,
        project_code: str
    ) -> Dict[str, Any]:
        """Get risk and similarity analysis from LLM"""
        if not all([self.azure_api_key, self.azure_endpoint]):
            logger.warning("Azure OpenAI not configured, using fallback analysis")
            return self._fallback_analysis(past_content, latest_content)
        
        try:
            prompt = self._build_analysis_prompt(past_content, latest_content, language, project_code)
            
            headers = {
                "api-key": self.azure_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {"role": "system", "content": "You are an expert project analyst. Analyze the provided project reports and respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            
            url = f"{self.azure_endpoint}/openai/deployments/{self.azure_deployment}/chat/completions?api-version=2024-02-15-preview"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                return json.loads(content)
                
        except Exception as e:
            logger.error(f"LLM analysis failed for {project_code}: {e}")
            return self._fallback_analysis(past_content, latest_content)

    def _build_analysis_prompt(self, past_content: str, latest_content: str, language: Language, project_code: str) -> str:
        """Build analysis prompt for LLM"""
        return f"""Analyze these two project reports for project {project_code}:

PAST REPORT:
{past_content[:1000]}

LATEST REPORT:
{latest_content[:1000]}

Provide analysis as JSON with exactly these fields:
{{
    "risk_lvl": <number 0-100>,
    "risk_desc": "<brief risk assessment>",
    "similarity_lvl": <number 0-100>,
    "similarity_desc": "<brief similarity assessment>"
}}

Risk level: 0=no risk, 100=critical risk
Similarity level: 0=completely different, 100=identical content
Language: {language}
Respond with valid JSON only."""

    def _fallback_analysis(self, past_content: str, latest_content: str) -> Dict[str, Any]:
        """Fallback analysis when LLM is not available"""
        similarity = self.calculate_similarity(past_content, latest_content)
        
        # Simple heuristic for risk based on negative words and content changes
        combined_content = f"{past_content} {latest_content}"
        negative_words = self.extract_negative_words(combined_content, "EN")
        
        risk_level = min(len(negative_words) * 15 + (100 - similarity) * 0.3, 100)
        
        return {
            "risk_lvl": round(risk_level, 2),
            "risk_desc": f"Risk assessment based on {len(negative_words)} negative indicators and {100-similarity:.1f}% content change",
            "similarity_lvl": round(similarity, 2),
            "similarity_desc": f"Content similarity: {similarity:.1f}% word overlap"
        }

    def _generate_content_hash(self, past_content: str, latest_content: str) -> str:
        """Generate hash for content to detect changes"""
        combined = f"{past_content}|{latest_content}"
        return hashlib.md5(combined.encode()).hexdigest()

    async def analyze_project_pair(
        self,
        db: Session,
        project_code: str,
        past_cw: str,
        latest_cw: str,
        language: Language,
        category: Optional[Category],
        created_by: str
    ) -> Tuple[WeeklyReportAnalysisRead, bool]:  # Returns (analysis, was_created)
        """Analyze a single project pair, with caching"""
        
        # Check if analysis already exists
        existing = db.query(WeeklyReportAnalysis).filter(
            and_(
                WeeklyReportAnalysis.project_code == project_code,
                WeeklyReportAnalysis.cw_label == latest_cw,
                WeeklyReportAnalysis.language == language,
                WeeklyReportAnalysis.category == category
            )
        ).first()
        
        # Get content for both periods
        past_content = self.get_project_content_for_cw(db, project_code, past_cw, category) or ""
        latest_content = self.get_project_content_for_cw(db, project_code, latest_cw, category) or ""
        
        # Generate content hash for cache invalidation
        content_hash = self._generate_content_hash(past_content, latest_content)
        
        # If exists and content hasn't changed, return existing
        if existing and existing.content_hash == content_hash:
            logger.info(f"Using cached analysis for {project_code} {latest_cw}")
            return self._convert_to_read_schema(existing), False
        
        # Perform new analysis
        logger.info(f"Analyzing {project_code} for {past_cw} -> {latest_cw}")
        
        # Language detection
        detected_language = self.detect_language(f"{past_content} {latest_content}")
        if language != detected_language:
            logger.info(f"Language override: requested {language}, detected {detected_language}")
        
        # Extract features
        negative_words = self.extract_negative_words(f"{past_content} {latest_content}", language)
        
        # Get LLM analysis
        llm_result = await self.get_llm_analysis(past_content, latest_content, language, project_code)
        
        # Create analysis record
        analysis_data = WeeklyReportAnalysisCreate(
            project_code=project_code,
            cw_label=latest_cw,
            language=language,
            category=category,
            risk_lvl=llm_result.get("risk_lvl"),
            risk_desc=llm_result.get("risk_desc"),
            similarity_lvl=llm_result.get("similarity_lvl"),
            similarity_desc=llm_result.get("similarity_desc"),
            negative_words={"words": negative_words, "count": len(negative_words)},
            created_by=created_by
        )
        
        # Upsert to database
        if existing:
            # Update existing
            for key, value in analysis_data.model_dump().items():
                if key != "created_by":  # Don't update created_by
                    setattr(existing, key, value)
            existing.content_hash = content_hash  # Update content hash
            db.commit()
            db.refresh(existing)
            return self._convert_to_read_schema(existing), False
        else:
            # Create new
            analysis_dict = analysis_data.model_dump()
            analysis_dict['content_hash'] = content_hash  # Add content hash
            new_analysis = WeeklyReportAnalysis(**analysis_dict)
            db.add(new_analysis)
            db.commit()
            db.refresh(new_analysis)
            return self._convert_to_read_schema(new_analysis), True

    def _convert_to_read_schema(self, analysis: WeeklyReportAnalysis) -> WeeklyReportAnalysisRead:
        """Convert SQLAlchemy model to Pydantic read schema"""
        return WeeklyReportAnalysisRead(
            id=str(analysis.id),
            project_code=analysis.project_code,
            cw_label=analysis.cw_label,
            language=analysis.language,
            category=analysis.category,
            risk_lvl=analysis.risk_lvl,
            risk_desc=analysis.risk_desc,
            similarity_lvl=analysis.similarity_lvl,
            similarity_desc=analysis.similarity_desc,
            negative_words=analysis.negative_words,
            created_at=str(analysis.created_at),
            created_by=analysis.created_by
        )

    def get_analysis_results(
        self,
        db: Session,
        past_cw: str,
        latest_cw: str,
        language: Optional[Language] = None,
        category: Optional[Category] = None
    ) -> List[WeeklyReportAnalysisRead]:
        """Get existing analysis results"""
        query = db.query(WeeklyReportAnalysis).filter(
            WeeklyReportAnalysis.cw_label == latest_cw
        )
        
        if language:
            query = query.filter(WeeklyReportAnalysis.language == language)
        if category:
            query = query.filter(WeeklyReportAnalysis.category == category)
        
        results = query.all()
        return [self._convert_to_read_schema(analysis) for analysis in results]
