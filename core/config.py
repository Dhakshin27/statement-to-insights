# core/config.py
"""Configuration constants for the Statement‑to‑Insights finance assistant.

This module centralises settings that are referenced throughout the code‑base.
"""

# Supported transaction categories. Adjust as needed.
CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Entertainment",
    "Shopping",
    "Healthcare",
    "Salary",
    "Investment",
    "Miscellaneous",
]

# Default LLM model name (used if the user does not supply one).
DEFAULT_MODEL = "gemini-4-hydrogen"

# PDF parser implementation – one of "pdfplumber" or "tabula".
PDF_PARSER = "pdfplumber"

# Overspending threshold (percentage of monthly budget). For demo we'll use 20%.
OVERSPENDING_THRESHOLD = 0.20

# Path for the Chroma vector store (relative to the project root).
CHROMA_DB_PATH = "data/chroma_db"
