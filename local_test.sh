#!/bin/bash

# podman build -t executor .
# podman run -p 9000:8080 executor

# Base Lambda-compatible URL
BASE_URL="http://localhost:9000/2015-03-31/functions/function/invocations"

# --------------------------------------------------
# TypeScript: Simple console.log
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "typescript",
    "code": "console.log(\"hello world\")"
  }'

echo
echo "--------------------------------"

# --------------------------------------------------
# TypeScript: Returning an object via output variable
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "typescript",
    "code": "const output = { result: 42 };"
  }'

echo
echo "--------------------------------"

# --------------------------------------------------
# TypeScript: Using input variables
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "typescript",
    "input": { "a": 5, "b": 7 },
    "code": "const output = { sum: a + b };"
  }'

echo
echo "--------------------------------"

# --------------------------------------------------
# TypeScript: Using environment variables
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "typescript",
    "env": { "SECRET": "shh" },
    "code": "const output = { envSecret: process.env.SECRET };"
  }'

echo
echo "--------------------------------"

# --------------------------------------------------
# TypeScript: Importing a standard library (fs)
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "typescript",
    "code": "import * as fs from \"fs\"; const output = { tmpExists: fs.existsSync(\"/tmp\") };"
  }'

echo
echo "--------------------------------"

# --------------------------------------------------
# TypeScript: Error case (invalid code)
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "typescript",
    "code": "const output = { broken: doesNotExist(1, 2) };"
  }'

echo
echo "--------------------------------"

# --------------------------------------------------
# Python: Simple execution
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "input": { "a": 1, "b": 2 },
    "code": "print(a + b)"
  }'

echo
echo "--------------------------------"

# --------------------------------------------------
# Python: Structured output
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "input": { "a": 1, "b": 2 },
    "code": "output = {\"result\": a + b}"
  }'

echo
echo "--------------------------------"

# --------------------------------------------------
# Python: Environment variables
curl -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "language":
