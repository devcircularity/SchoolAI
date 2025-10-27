#!/usr/bin/env bash
set -euo pipefail

# --- EDIT THESE TWO ONLY ---
TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMmY5OTg0MS1mYjU1LTRkMzMtYTY3Mi1jYzFlN2QyNWRjZTUiLCJyb2xlcyI6WyJQQVJFTlQiXSwiYWN0aXZlX3NjaG9vbF9pZCI6bnVsbCwiaWF0IjoxNzU0ODUwNTMyLCJleHAiOjE3NTQ4NTQxMzJ9._340jicmd9X8erT3v-zf5Jqw2Sum6nVri3lRxOryXww'
SCHOOL_ID='3649fd09-d333-4acb-bf97-daa7b02757d2'

base() { echo "http://localhost:8000$1"; }

echo "== Create class =="
CLASS_ID=$(
  curl -sX POST "$(base /classes)" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-School-ID: $SCHOOL_ID" \
    -H "Content-Type: application/json" \
    -d '{"name":"North","level":"Grade 4","academic_year":"2025","stream":"A"}' \
  | jq -r '.id'
)
echo "CLASS_ID=$CLASS_ID"

echo "== Create guardian =="
G2=$(
  curl -sX POST "$(base /guardians)" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-School-ID: $SCHOOL_ID" \
    -H "Content-Type: application/json" \
    -d '{"first_name":"Peter","last_name":"Otieno","phone":"+254711111111","email":"peter@example.com","relationship":"Parent"}' \
  | jq -r '.id'
)
echo "GUARDIAN_ID=$G2"

echo "== Create student in that class, linked to guardian =="
S2=$(
  curl -sX POST "$(base /students)" \
    -H "Authorization: Bearer $TOKEN" \
    -H "X-School-ID: $SCHOOL_ID" \
    -H "Content-Type: application/json" \
    --data-binary @- <<JSON | jq -r '.id'
{
  "admission_no": "ADM-0003",
  "first_name": "Naila",
  "last_name": "Otieno",
  "gender": "F",
  "class_id": "$CLASS_ID",
  "primary_guardian_id": "$G2"
}
JSON
)
echo "STUDENT2_ID=$S2"

echo "== Generate invoices for the class =="
curl -sX POST "$(base /invoices/generate)" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-School-ID: $SCHOOL_ID" \
  -H "Content-Type: application/json" \
  --data-binary @- <<JSON | jq
{
  "class_id": "$CLASS_ID",
  "term": 1,
  "year": 2025,
  "include_optional": { "Lunch": true }
}
JSON

echo "== List invoices =="
curl -s "$(base /invoices)" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-School-ID: $SCHOOL_ID" | jq
