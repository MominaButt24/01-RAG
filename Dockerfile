FROM python:3.12-slim

WORKDIR /workspace

# System dependencies: LibreOffice (for docx->pdf), Node.js + PM2, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    curl \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pm2 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Project code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 8000 7860

ENTRYPOINT ["/workspace/entrypoint.sh"]