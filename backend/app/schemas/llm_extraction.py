from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class CategoryEnum(str, Enum):
    """Project categories for report entries"""
    DEVELOPMENT = "Development"
    EPC = "EPC" 
    FINANCE = "Finance"
    INVESTMENT = "Investment"


class ProjectEntry(BaseModel):
    """Schema for a single project entry extracted from reports"""
    project_name: str = Field(..., description="Name of the project")
    title: Optional[str] = Field(None, description="Title or heading of the entry")
    summary: str = Field(default="", description="Summary of the project status")
    next_actions: Optional[str] = Field(None, description="Planned next actions")
    owner: Optional[str] = Field(None, description="Person or team responsible")
    category: Optional[CategoryEnum] = Field(None, description="Project category")
    source_text: Optional[str] = Field(None, description="Original text from document")
    
    @field_validator('project_name', 'summary')
    @classmethod
    def strip_whitespace(cls, v):
        """Strip whitespace from required string fields"""
        if isinstance(v, str):
            return v.strip()
        return v
    
    @field_validator('project_name')
    @classmethod
    def project_name_not_empty(cls, v):
        """Ensure project name is not empty after stripping"""
        if not v or not v.strip():
            raise ValueError('project_name cannot be empty')
        return v
    
    @field_validator('summary')
    @classmethod
    def ensure_summary_exists(cls, v):
        """Provide default summary if missing"""
        if not v or not v.strip():
            return "No summary provided"
        return v
    
    @field_validator('category', mode='before')
    @classmethod
    def convert_empty_category_to_none(cls, v):
        """Convert empty string category to None"""
        if v == "":
            return None
        return v


class ExtractionResponse(BaseModel):
    """Schema for the complete LLM response"""
    rows: List[ProjectEntry] = Field(..., description="List of extracted project entries")
    
    @field_validator('rows')
    @classmethod
    def validate_rows(cls, v):
        """Ensure we have at least some valid entries"""
        if not isinstance(v, list):
            raise ValueError('rows must be a list')
        return v


# JSON Schema for Azure OpenAI function calling (alternative to response_format)
EXTRACTION_FUNCTION_SCHEMA = {
    "name": "extract_project_entries",
    "description": "Extract project entries from a weekly report document",
    "parameters": {
        "type": "object",
        "properties": {
            "rows": {
                "type": "array",
                "description": "List of project entries found in the document",
                "items": {
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "Name of the project"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title or heading of the entry"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Summary of the project status"
                        },
                        "next_actions": {
                            "type": "string", 
                            "description": "Planned next actions"
                        },
                        "owner": {
                            "type": "string",
                            "description": "Person or team responsible"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["Development", "EPC", "Finance", "Investment"],
                            "description": "Project category"
                        },
                        "source_text": {
                            "type": "string",
                            "description": "Original text from document"
                        }
                    },
                    "required": ["project_name", "summary"]
                }
            }
        },
        "required": ["rows"]
    }
}


# Optimized system prompt for strict JSON output
SYSTEM_PROMPT_V2 = """You are a precise information extraction assistant. Extract project entries from weekly reports and return them as valid JSON.

CRITICAL: Your response must be valid JSON only. No markdown, no explanations, no code blocks.

Return a JSON object with this exact structure:
{
  "rows": [
    {
      "project_name": "string (required)",
      "title": "string or null", 
      "summary": "string (required, min 1 char)",
      "next_actions": "string or null",
      "owner": "string or null", 
      "category": "Development|EPC|Finance|Investment or null",
      "source_text": "string or null"
    }
  ]
}

Rules:
- Only include projects actually mentioned in the document
- Keep summaries concise but informative
- Use exact category names: Development, EPC, Finance, Investment
- If unsure about category, use null
- Extract key information, don't hallucinate details"""
