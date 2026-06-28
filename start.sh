#!/bin/bash
# start.sh
export $(cat .env | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000