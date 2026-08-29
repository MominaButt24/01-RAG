module.exports = {
  apps: [
    {
      name: "rag-api",
      script: "venv/bin/python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",
      cwd: __dirname,
    },
    {
      name: "rag-gradio",
      script: "venv/bin/python",
      args: "gradio_app.py",
      cwd: __dirname,
    },
  ],
};