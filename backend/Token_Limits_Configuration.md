# Azure OpenAI Token Limits Configuration

## Environment Variables

Configure Azure OpenAI token limits using these environment variables in your `.env` file:

```bash
# Azure OpenAI Model Context Limit (default: 8000)
AZURE_OPENAI_MAX_CONTEXT=8000

# Maximum Input Tokens for Document Processing (default: 3500)  
AZURE_OPENAI_MAX_INPUT=3500

# Maximum Output Tokens for Response (default: 4000)
AZURE_OPENAI_MAX_OUTPUT=4000

# Safety Buffer for Context Overflow (default: 500)
AZURE_OPENAI_SAFETY_BUFFER=500
```

## How It Works

### 1. **Smart Text Truncation**
- Documents are automatically truncated to fit within `AZURE_OPENAI_MAX_INPUT` token limits
- Preserves sentence and paragraph boundaries when possible
- Falls back to word boundaries to avoid cutting words in half

### 2. **Dynamic Token Allocation**
- Output tokens are calculated dynamically: `max_output = min(context_limit - input_tokens - safety_buffer, max_output)`
- Ensures total token usage stays within model limits
- Provides logging for monitoring: `Smart token allocation: input=X, max_output=Y, context_limit=Z`

### 3. **Truncated Response Recovery**
- Handles cases where Azure OpenAI response is truncated due to token limits
- Extracts complete project entries from partial JSON responses
- Skips incomplete entries to ensure data quality

## Model-Specific Recommendations

### GPT-3.5 Turbo (4K context)
```bash
AZURE_OPENAI_MAX_CONTEXT=4000
AZURE_OPENAI_MAX_INPUT=2000
AZURE_OPENAI_MAX_OUTPUT=1500
AZURE_OPENAI_SAFETY_BUFFER=500
```

### GPT-3.5 Turbo (16K context)
```bash
AZURE_OPENAI_MAX_CONTEXT=16000
AZURE_OPENAI_MAX_INPUT=7000
AZURE_OPENAI_MAX_OUTPUT=8000
AZURE_OPENAI_SAFETY_BUFFER=1000
```

### GPT-4 (8K context) - **Current Default**
```bash
AZURE_OPENAI_MAX_CONTEXT=8000
AZURE_OPENAI_MAX_INPUT=3500
AZURE_OPENAI_MAX_OUTPUT=4000
AZURE_OPENAI_SAFETY_BUFFER=500
```

### GPT-4 (32K context)
```bash
AZURE_OPENAI_MAX_CONTEXT=32000
AZURE_OPENAI_MAX_INPUT=15000
AZURE_OPENAI_MAX_OUTPUT=16000
AZURE_OPENAI_SAFETY_BUFFER=1000
```

## Monitoring & Debugging

### Token Usage Logs
The system logs token usage for each document:
```
Processing /path/to/file.docx: 12711 chars -> 12711 chars, ~3307 input tokens
Smart token allocation: input=3307, max_output=4000, context_limit=8000
```

### Handling Truncation
When JSON responses are truncated, you'll see:
```
JSON parsing failed: Unterminated string starting at: line X column Y
```

The system automatically recovers by parsing complete entries from the truncated response.

## Performance Tips

1. **Larger Models**: Use higher context limits for complex documents
2. **Cost Optimization**: Reduce `MAX_INPUT` and `MAX_OUTPUT` for simpler documents
3. **Reliability**: Increase `SAFETY_BUFFER` if you experience frequent truncation
4. **Processing Speed**: Lower token limits = faster processing but potentially less complete extraction

## Troubleshooting

### "Context length exceeded" Error
- Reduce `AZURE_OPENAI_MAX_INPUT`
- Increase `AZURE_OPENAI_SAFETY_BUFFER`
- Check your deployment's actual context limit

### Missing Project Data
- Increase `AZURE_OPENAI_MAX_INPUT` to include more document content
- Check if important information is being truncated

### High API Costs  
- Reduce `AZURE_OPENAI_MAX_OUTPUT` for shorter responses
- Lower `AZURE_OPENAI_MAX_INPUT` for smaller input chunks
