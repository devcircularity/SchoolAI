#!/bin/bash

BASE_URL="http://localhost:8000/api/messages"
SCHOOL_CODE="OLJ-001"
CHAT_ID="d1d9df16-7040-47b6-960c-22da8bdebc70"

prompts=(
  "What is the name of our school?"
  "How many classes do we have?"
  "Show me the fee structure."
  "Which students have not paid their fees in full?"
  "List the classes and the number of students in each."
  "Who is the head teacher?"
  "Which classes have the most students?"
  "When is the next fees payment deadline?"
  "Tell me about our school."
  "Show me the term dates for this year."
)

for prompt in "${prompts[@]}"; do
  echo -e "\n--- Prompt: $prompt ---"
  curl -s -X POST "$BASE_URL?school_code=$SCHOOL_CODE" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\": \"$CHAT_ID\", \"text\": \"$prompt\"}"
  echo -e "\n"
done
