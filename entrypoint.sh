#!/bin/bash
set -e
cd /workspace
uvicorn app.main:app --host 0.0.0.0 --port 8000 &   
python gradio_app.py                                  
