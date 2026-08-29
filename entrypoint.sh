bash
#!/bin/bash
set -e
cd /workspace
pm2-runtime start ecosystem.config.js