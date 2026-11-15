# Statement to Insights

A personal-finance assistant for bank and UPI statements. Upload a CSV or table-based PDF to extract transactions, categorise them, calculate spending trends, surface overspending alerts, and ask plain-language questions about the statement.

## What it does

- **Parser agent** normalises CSV/PDF transaction data into date, description, amount, and balance fields.
- **Categoriser agent** assigns deterministic spending categories from merchant and narration keywords.
- **Analysis agent** uses pandas for exact income, spend, category, monthly, and cash-flow calculations.
- **Advisor agent** produces practical overspending alerts and savings actions. It has a local deterministic fallback, so the core insights button works without an LLM connection.
- **Intent routing and retrieval** routes questions to transaction lookup, spending analysis, or savings guidance. Relevant statement descriptions are retrieved locally; statements are also persisted to ChromaDB on a best-effort basis when Chroma is available.

## Run locally

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

CSV files should include a date column, a description/narration column, and either an amount column or debit and credit columns. Expenses are represented as negative amounts internally.

## AI providers

Gemini, Grok, and Ollama are optional. Connect one from the sidebar for richer generated advice. The dashboard, transaction explorer, calculator-backed totals, alerts, lookup, and starter insights work without a provider.

## Privacy

Uploaded statements are saved in `data/uploads` for parsing. If an AI provider is connected, only the financial summary and context needed for the requested advice are sent to that provider.
