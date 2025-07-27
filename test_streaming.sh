#!/bin/bash
curl -X POST http://localhost:5000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Tell me about London", "session_id": "test123", "stream": true}' \
  -N