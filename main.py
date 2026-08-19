import os
import shutil

from src.pipeline import ingest_file, ask, list_uploaded_files, delete_uploaded_files, reset_everything
from src.config import UPLOAD_DIR

def do_ingest():
    source_path = input("Enter the path to the file you want to ingest: ").strip()

    if not os.path.exists(source_path):
        print(f"File not found: {source_path}")
        return

    # copy the file into data/uploads/ so the project keeps a consistent,
    # known location for anything it has ingested
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = os.path.basename(source_path)
    dest_path = os.path.join(UPLOAD_DIR, filename)
    shutil.copy(source_path, dest_path)

    count = ingest_file(dest_path)
    print(f"Ingested '{filename}': {count} chunks stored.")


def do_ask():
    query = input("Enter your question: ").strip()
    result = ask(query)

    print("=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(result["answer"])

    print("\n" + "=" * 60)
    print("CHUNKS USED (for verification)")
    print("=" * 60)
    for i, ch in enumerate(result["chunks_used"], 1):
        print(f"\n--- Chunk #{i} [{ch['source']}] (score: {ch['score']:.4f}) ---")
        preview = ch["text"][:300] + ("..." if len(ch["text"]) > 300 else "")
        print(preview)


def do_reset():
    reset_everything()
    print("Collection reset and data/uploads/ cleared -- ready for clean ingestion --")


def do_list():
    files = list_uploaded_files()
    if not files:
        print("No files currently stored.")
        return
    print(f"{len(files)} file(s) currently stored:")
    for f in files:
        print(f"  - {f}")

def do_delete():
    files = list_uploaded_files()
    if not files:
        print("No files currently stored — nothing to delete.")
        return
 
    print("Currently stored files:")
    for f in files:
        print(f"  - {f}")
 
    raw = input("Enter filename(s) to delete (comma-separated for multiple): ").strip()
    filenames_to_delete = [name.strip() for name in raw.split(",") if name.strip()]
 
    deleted = delete_uploaded_files(filenames_to_delete)
    if deleted:
        print(f"Deleted: {', '.join(deleted)}")
    not_found = set(filenames_to_delete) - set(deleted)
    if not_found:
        print(f"Not found (skipped): {', '.join(not_found)}")



def main():
    while 1:
        print("What would you like to do?")
        print("  1. Ingest a file")
        print("  2. Ask a question")
        print("  3. Reset the collection")
        print("  4. List uploaded files")
        print("  5. Delete file(s)")
    
        choice = input("Enter 1-5 or exit by -1: ").strip()
        
        if choice == "1":
            do_ingest()
        elif choice == "2":
            do_ask()
        elif choice == "3":
            do_reset()
        elif choice == "4":
            do_list()
        elif choice == "5":
            do_delete()
        elif choice == "-1":
            break
        else:
            print("Invalid choice — enter 1-5.")
    

if __name__ == "__main__":
    main()