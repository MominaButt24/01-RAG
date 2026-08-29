import os
import sentry_sdk
from dotenv import load_dotenv

load_dotenv()

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    environment=os.environ.get("APP_ENV", "development"),
    release=os.environ.get("APP_RELEASE", "rag-pipeline:v1"),
    traces_sample_rate=1.0,
    send_default_pii=False,
)

import gradio as gr
import requests

API_BASE = "http://127.0.0.1:8000/api/v1"


def call_list_files():
    try:
        response = requests.get(f"{API_BASE}/list")
        response.raise_for_status()
        files = response.json()["files"]
        if not files:
            return "No files currently uploaded."
        return "\n".join(f"- {f}" for f in files)
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the API server. Make sure it's running (uvicorn app.main:app --reload)."
    except Exception as e:
        return f"Error: {e}"


def call_upload_file(file):
    if file is None:
        return "Please select a file first.", call_list_files()
    try:
        filename = os.path.basename(file.name)
        with open(file.name, "rb") as f:
            response = requests.post(f"{API_BASE}/upload", files={"file": (filename, f)})
        response.raise_for_status()
        data = response.json()
        status = f"Uploaded '{data['filename']}' — {data['chunks_stored']} chunks stored."
        return status, call_list_files()
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the API server.", call_list_files()
    except Exception as e:
        return f"Error: {e}", call_list_files()


def call_delete_files(filenames_text):
    if not filenames_text.strip():
        return "Enter at least one filename to delete.", call_list_files()
    filenames = [name.strip() for name in filenames_text.split(",") if name.strip()]
    try:
        response = requests.delete(f"{API_BASE}/delete", json={"filenames": filenames})
        response.raise_for_status()
        data = response.json()
        status = f"Deleted: {', '.join(data['deleted']) or 'none'}"
        if data["not_found"]:
            status += f"\nNot found: {', '.join(data['not_found'])}"
        return status, call_list_files()
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the API server.", call_list_files()
    except Exception as e:
        return f"Error: {e}", call_list_files()


def call_chat(query):
    if not query.strip():
        return "Please enter a question.", ""
    try:
        response = requests.post(f"{API_BASE}/chat", json={"query": query})
        response.raise_for_status()
        data = response.json()
        answer = data["answer"]

        chunks_text = ""
        for i, ch in enumerate(data["chunks_used"], 1):
            preview = ch["text"][:300] + ("..." if len(ch["text"]) > 300 else "")
            chunks_text += (
                f"--- Chunk #{i} [{ch['filename']} - {ch['source']}] "
                f"(score: {ch['score']:.4f}) ---\n{preview}\n\n"
            )

        return answer, chunks_text
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the API server.", ""
    except Exception as e:
        return f"Error: {e}", ""


with gr.Blocks(title="RAG Assistant") as demo:
    gr.Markdown("# RAG Document Assistant")
    gr.Markdown("Upload documents, then ask questions grounded in them. Delete files you no longer need.")

    with gr.Tab("Upload"):
        file_input = gr.File(label="Select a file (pdf, docx, pptx, xlsx)")
        upload_button = gr.Button("Upload & Ingest")
        upload_status = gr.Textbox(label="Status", interactive=False)

    with gr.Tab("Chat"):
        query_input = gr.Textbox(label="Ask a question about your uploaded documents")
        chat_button = gr.Button("Ask")
        answer_output = gr.Textbox(label="Answer", interactive=False, lines=4)
        chunks_output = gr.Textbox(label="Chunks used (for verification)", interactive=False, lines=10)

    with gr.Tab("Files"):
        refresh_button = gr.Button("Refresh file list")
        files_output = gr.Textbox(label="Currently uploaded files", interactive=False, lines=8)
        gr.Markdown("---")
        delete_input = gr.Textbox(label="Filename(s) to delete (comma-separated)")
        delete_button = gr.Button("Delete")
        delete_status = gr.Textbox(label="Delete status", interactive=False)

    upload_button.click(fn=call_upload_file, inputs=file_input, outputs=[upload_status, files_output])
    chat_button.click(fn=call_chat, inputs=query_input, outputs=[answer_output, chunks_output])
    refresh_button.click(fn=call_list_files, inputs=None, outputs=files_output)
    delete_button.click(fn=call_delete_files, inputs=delete_input, outputs=[delete_status, files_output])

    demo.load(fn=call_list_files, inputs=None, outputs=files_output)


if __name__ == "__main__":
    demo.launch(share=True)