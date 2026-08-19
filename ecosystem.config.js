// PM2 config file: defines BOTH the FastAPI server and the Gradio app
// as separate managed processes, so both can be started/stopped/
// monitored together instead of running two terminals manually.
//
// Usage (from the project root):
//   pm2 start ecosystem.config.js   -- starts both processes
//   pm2 list                        -- see status of both
//   pm2 logs                        -- see live output from both
//   pm2 stop all                    -- stop both
//   pm2 restart all                 -- restart both

module.exports = {
  apps: [
    {
      name: "rag-api",
      // path to the python.exe INSIDE your virtual environment -- this
      // matters: using the venv's python ensures PM2 uses the same
      // installed packages (fastapi, pymilvus, etc.) you've been testing
      // with, not whatever "python" resolves to system-wide.
      script: "venv/Scripts/python.exe",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",
      cwd: __dirname, // run from wherever this config file lives (project root)
    },
    {
      name: "rag-gradio",
      script: "venv/Scripts/python.exe",
      args: "gradio_app.py",
      cwd: __dirname,
    },
  ],
};