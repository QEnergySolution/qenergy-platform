# QEnergy Platform Backend - Environment Configuration Guide

## 📋 Overview

This guide provides complete information about environment configuration for the QEnergy Platform backend application.

## ✅ Configuration Status

**Current Status**: ✅ **CONFIGURED**

All critical environment variables have been set up in `/backend/.env`. The application is ready to run with the current configuration.

## 📁 Configuration Files

- **`.env`** - Main environment configuration file (77 variables configured)
- **`env.example`** - Template file with example values
- **`validate_env.py`** - Validation script to check configuration completeness

## 🔧 Environment Variables

### Core Application Variables ✅
| Variable | Status | Description |
|----------|---------|-------------|
| `DATABASE_URL` | ✅ Configured | PostgreSQL connection string |
| `SECRET_KEY` | ✅ Configured | Application secret key (auto-generated) |
| `ALGORITHM` | ✅ Configured | JWT algorithm (HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ✅ Configured | Token expiration time |

### Database Configuration ✅
| Variable | Status | Description |
|----------|---------|-------------|
| `DB_HOST` | ✅ Configured | Database host (localhost) |
| `DB_PORT` | ✅ Configured | Database port (5432) |
| `DB_NAME` | ✅ Configured | Database name (qenergy_platform) |
| `DB_USER` | ✅ Configured | Database username |
| `DB_PASSWORD` | ✅ Configured | Database password |

### Azure OpenAI Configuration ⚠️
| Variable | Status | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_API_KEY` | ⚠️ Placeholder | **Needs your actual API key** |
| `AZURE_OPENAI_ENDPOINT` | ⚠️ Placeholder | **Needs your actual endpoint** |
| `AZURE_OPENAI_DEPLOYMENT` | ✅ Configured | Model deployment name (gpt-4) |
| `AZURE_OPENAI_API_VERSION` | ✅ Configured | API version (2024-02-15-preview) |

### Token Limits Configuration ✅
| Variable | Status | Value | Description |
|----------|---------|-------|-------------|
| `AZURE_OPENAI_MAX_CONTEXT` | ✅ Configured | 8000 | Maximum context tokens |
| `AZURE_OPENAI_MAX_INPUT` | ✅ Configured | 3500 | Maximum input tokens |
| `AZURE_OPENAI_MAX_OUTPUT` | ✅ Configured | 4000 | Maximum output tokens |
| `AZURE_OPENAI_SAFETY_BUFFER` | ✅ Configured | 500 | Safety buffer tokens |

### File Upload Configuration ✅
| Variable | Status | Description |
|----------|---------|-------------|
| `REPORT_UPLOAD_TMP_DIR` | ✅ Configured | Temporary upload directory |

### Development Settings ✅
| Variable | Status | Description |
|----------|---------|-------------|
| `DEBUG` | ✅ Configured | Debug mode (True) |
| `ENVIRONMENT` | ✅ Configured | Environment type (development) |
| `LOG_LEVEL` | ✅ Configured | Logging level (INFO) |

### Testing Configuration ✅
| Variable | Status | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_INTEGRATION_TEST` | ✅ Configured | Enable integration tests (0) |
| `AZURE_OPENAI_E2E` | ✅ Configured | Enable E2E tests (0) |

## 🚀 Quick Start

### 1. Validate Current Configuration
```bash
cd backend
python validate_env.py
```

### 2. Configure Azure OpenAI (Required for AI Features)
To enable AI/LLM features, you need to:

1. **Create Azure OpenAI Resource**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create an "Azure OpenAI" resource
   - Note the endpoint URL and resource name

2. **Deploy a Model**
   - In your Azure OpenAI resource, go to "Model deployments"
   - Deploy a GPT-4 model
   - Note the deployment name

3. **Get API Key**
   - In your Azure OpenAI resource, go to "Keys and Endpoint"
   - Copy one of the API keys

4. **Update .env File**
   ```bash
   # Replace these placeholder values in .env:
   AZURE_OPENAI_API_KEY=your-actual-api-key-here
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name
   ```

### 3. Test Configuration
```bash
# Test basic environment loading
python -c "from dotenv import load_dotenv; load_dotenv(); print('✅ Environment loaded successfully')"

# Test Azure OpenAI configuration (if configured)
python -m pytest tests/test_azure_openai_env.py -v
```

## 🔍 Configuration Validation

The `validate_env.py` script provides comprehensive validation:

```bash
python validate_env.py
```

**Exit Codes:**
- `0`: All good, ready to run
- `1`: Critical variables missing
- `2`: Azure OpenAI not configured (AI features disabled)

## 📝 Configuration Notes

### Security Considerations
- ✅ **SECRET_KEY**: Auto-generated secure 32-character key
- ⚠️ **API Keys**: Store securely, never commit to version control
- ✅ **Database**: Uses local PostgreSQL with standard credentials

### Token Limits
The current configuration is optimized for **GPT-4 (8K context)**:
- Context: 8,000 tokens
- Input: 3,500 tokens  
- Output: 4,000 tokens
- Buffer: 500 tokens

For different models, adjust these values in `.env`:
- **GPT-4 Turbo (128K)**: Set `AZURE_OPENAI_MAX_CONTEXT=32000`
- **GPT-3.5 Turbo**: Set `AZURE_OPENAI_MAX_CONTEXT=4000`

### File Uploads
- **Temporary Directory**: `/tmp/qenergy_uploads`
- **Auto-cleanup**: Handled by application
- **Permissions**: Ensure write access to temp directory

## 🛠️ Troubleshooting

### Common Issues

1. **"DATABASE_URL is not set" Error**
   ```bash
   # Check if .env file exists and is readable
   ls -la .env
   cat .env | grep DATABASE_URL
   ```

2. **"Azure OpenAI env vars missing" Error**
   ```bash
   # Validate Azure OpenAI configuration
   python validate_env.py
   ```

3. **Token Limit Errors**
   ```bash
   # Check token configuration
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'Context: {os.getenv(\"AZURE_OPENAI_MAX_CONTEXT\")}, Input: {os.getenv(\"AZURE_OPENAI_MAX_INPUT\")}')"
   ```

### Environment Loading Issues
```bash
# Test environment loading
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('DATABASE_URL:', 'SET' if os.getenv('DATABASE_URL') else 'NOT SET')
print('SECRET_KEY:', 'SET' if os.getenv('SECRET_KEY') else 'NOT SET')
"
```

## 📚 Related Files

- **`backend/.env`** - Main configuration (this file)
- **`backend/env.example`** - Configuration template
- **`backend/validate_env.py`** - Validation script
- **`backend/app/database.py`** - Database connection logic
- **`backend/app/llm_parser.py`** - Azure OpenAI integration
- **`backend/Token_Limits_Configuration.md`** - Detailed token configuration guide

## 🔄 Updates

**Last Updated**: September 2024
**Configuration Version**: v1.0
**Total Variables**: 20 core + 57 optional = 77 variables configured

---

✅ **Status**: Ready for development with current configuration
⚠️ **Action Required**: Configure Azure OpenAI credentials for AI features
