import os
import pathlib

UPLOAD_DIR = pathlib.Path(__file__).resolve().parents[1] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_uploaded_file(uploaded_file) -> str:
    """Save a Streamlit UploadedFile to the uploads directory.
    Returns the absolute path to the saved file.
    """
    # Ensure a safe filename
    filename = os.path.basename(uploaded_file.name)
    dest_path = UPLOAD_DIR / filename
    # Write bytes
    with open(dest_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest_path)
