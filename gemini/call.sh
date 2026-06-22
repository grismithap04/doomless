#!/bin/bash

# Load env
if [ -f ".env" ]; then
    source .env
fi

TIME_AVAILABLE="${1:-10}"
BREAK_PATTERN="${2:-false}"
USER_INTERESTS="${3:-general}"

PROMPT=$(cat gemini/prompt.txt)

PAYLOAD=$(cat << JSONEOF
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "$PROMPT"
    },
    {
      "role": "user",
      "content": "time_available: $TIME_AVAILABLE minutes, break_pattern_mode: $BREAK_PATTERN, interests: $USER_INTERESTS"
    }
  ],
  "max_tokens": 300,
  "temperature": 0.7
}
JSONEOF
)

curl -s -X POST "https://api.groq.com/openai/v1/chat/completions" \
    -H "Authorization: Bearer $GROQ_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD"
