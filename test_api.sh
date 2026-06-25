#!/usr/bin/env bash
# Test the Vercel-deployed AI API
curl -s -X POST https://al-ma-swpi-github-io.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"say hello briefly","context":"","history":[]}'
echo
