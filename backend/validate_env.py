#!/usr/bin/env python3
"""
Environment Configuration Validator for QEnergy Platform Backend

This script validates that all required environment variables are properly configured.
Run this script to check if your .env file is complete and correctly formatted.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables only.")

def check_required_vars() -> Tuple[List[str], List[str]]:
    """Check required environment variables"""
    
    # Core required variables (application won't start without these)
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
    ]
    
    # Azure OpenAI variables (required for AI features)
    azure_openai_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "AZURE_OPENAI_DEPLOYMENT",
    ]
    
    # Optional but recommended variables
    optional_vars = [
        "DB_HOST",
        "DB_PORT", 
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "API_V1_STR",
        "PROJECT_NAME",
        "BACKEND_CORS_ORIGINS",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_MAX_CONTEXT",
        "AZURE_OPENAI_MAX_INPUT",
        "AZURE_OPENAI_MAX_OUTPUT", 
        "AZURE_OPENAI_SAFETY_BUFFER",
        "REPORT_UPLOAD_TMP_DIR",
        "DEBUG",
        "ENVIRONMENT",
        "LOG_LEVEL",
        "AZURE_OPENAI_INTEGRATION_TEST",
        "AZURE_OPENAI_E2E",
        "OPENAI_API_KEY",  # Legacy support
    ]
    
    missing_required = []
    missing_azure = []
    missing_optional = []
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing_required.append(var)
    
    # Check Azure OpenAI variables
    for var in azure_openai_vars:
        value = os.getenv(var)
        if not value or value.strip() == "" or "your-" in value.lower():
            missing_azure.append(var)
    
    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing_optional.append(var)
    
    return missing_required, missing_azure, missing_optional

def validate_specific_values() -> List[str]:
    """Validate specific environment variable values"""
    issues = []
    
    # Check DATABASE_URL format
    db_url = os.getenv("DATABASE_URL", "")
    if db_url and not db_url.startswith("postgresql://"):
        issues.append("DATABASE_URL should start with 'postgresql://'")
    
    # Check SECRET_KEY strength
    secret_key = os.getenv("SECRET_KEY", "")
    if secret_key and len(secret_key) < 32:
        issues.append("SECRET_KEY should be at least 32 characters long")
    if "your-" in secret_key.lower() or "change-this" in secret_key.lower():
        issues.append("SECRET_KEY contains placeholder text - please update with a real secret key")
    
    # Check Azure OpenAI endpoint format
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    if endpoint and not endpoint.startswith("https://"):
        issues.append("AZURE_OPENAI_ENDPOINT should start with 'https://'")
    if endpoint and "your-" in endpoint.lower():
        issues.append("AZURE_OPENAI_ENDPOINT contains placeholder text - please update with your actual endpoint")
    
    # Check API key placeholders
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    if api_key and "your-" in api_key.lower():
        issues.append("AZURE_OPENAI_API_KEY contains placeholder text - please update with your actual API key")
    
    # Check token limits are reasonable numbers
    try:
        max_context = int(os.getenv("AZURE_OPENAI_MAX_CONTEXT", "8000"))
        max_input = int(os.getenv("AZURE_OPENAI_MAX_INPUT", "3500"))
        max_output = int(os.getenv("AZURE_OPENAI_MAX_OUTPUT", "4000"))
        
        if max_input + max_output > max_context:
            issues.append(f"Token limits inconsistent: MAX_INPUT({max_input}) + MAX_OUTPUT({max_output}) > MAX_CONTEXT({max_context})")
    except ValueError:
        issues.append("Token limit variables should be valid integers")
    
    return issues

def check_env_file_exists() -> bool:
    """Check if .env file exists"""
    env_file = Path(__file__).parent / ".env"
    return env_file.exists()

def main():
    """Main validation function"""
    print("🔍 QEnergy Platform Backend - Environment Configuration Validator")
    print("=" * 70)
    
    # Check if .env file exists
    if not check_env_file_exists():
        print("❌ ERROR: .env file not found!")
        print("   Please copy env.example to .env and configure the values.")
        sys.exit(1)
    else:
        print("✅ .env file found")
    
    # Check required variables
    missing_required, missing_azure, missing_optional = check_required_vars()
    
    print(f"\n📋 Environment Variables Status:")
    print("-" * 40)
    
    # Report missing required variables
    if missing_required:
        print(f"❌ CRITICAL - Missing required variables ({len(missing_required)}):")
        for var in missing_required:
            print(f"   - {var}")
    else:
        print("✅ All critical variables are set")
    
    # Report missing Azure OpenAI variables
    if missing_azure:
        print(f"\n⚠️  WARNING - Missing Azure OpenAI variables ({len(missing_azure)}):")
        print("   AI/LLM features will not work without these:")
        for var in missing_azure:
            print(f"   - {var}")
    else:
        print("✅ Azure OpenAI configuration is complete")
    
    # Report missing optional variables
    if missing_optional:
        print(f"\n💡 INFO - Missing optional variables ({len(missing_optional)}):")
        print("   These have defaults but you may want to configure them:")
        for var in missing_optional:
            value = os.getenv(var, "")
            if value:
                print(f"   - {var} (current: {value[:20]}...)")
            else:
                print(f"   - {var}")
    
    # Validate specific values
    issues = validate_specific_values()
    if issues:
        print(f"\n⚠️  Configuration Issues Found ({len(issues)}):")
        for issue in issues:
            print(f"   - {issue}")
    
    # Summary
    print(f"\n📊 Summary:")
    print("-" * 20)
    
    total_issues = len(missing_required) + len(issues)
    if total_issues == 0:
        print("🎉 Configuration looks good!")
        if missing_azure:
            print("   Note: Configure Azure OpenAI variables to enable AI features.")
    else:
        print(f"⚠️  {total_issues} critical issue(s) found that need attention.")
        if missing_required:
            print("   Fix required variables before starting the application.")
    
    # Configuration recommendations
    print(f"\n💡 Next Steps:")
    print("-" * 15)
    
    if missing_required:
        print("1. Configure missing required variables in .env file")
    
    if missing_azure:
        print("2. Set up Azure OpenAI service and configure API credentials")
        print("   - Create Azure OpenAI resource in Azure Portal")
        print("   - Deploy a GPT model (e.g., gpt-4)")
        print("   - Get API key and endpoint from Azure Portal")
    
    if "your-" in os.getenv("SECRET_KEY", "").lower():
        print("3. Generate a strong SECRET_KEY (use: python -c 'import secrets; print(secrets.token_urlsafe(32))')")
    
    print("4. Test the configuration by running: python -m pytest tests/test_azure_openai_env.py")
    
    # Exit with appropriate code
    if missing_required:
        sys.exit(1)
    elif missing_azure:
        sys.exit(2)  # Warning level
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
