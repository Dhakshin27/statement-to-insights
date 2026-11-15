from typing import Dict
from core.llm_factory import LLMClient


def _build_prompt(analysis: Dict) -> str:
    """Build a natural-language prompt from the analysis dictionary."""
    total_spent = analysis.get("total_spent", 0)
    total_income = analysis.get("total_income", 0)
    monthly = analysis.get("monthly_totals", {})
    cat_totals = analysis.get("category_totals", {})
    top_cats = analysis.get("top_expense_categories", [])

    lines = [
        "You are a friendly personal-finance assistant.",
        "Based on the financial summary below, provide:",
        "1. Plain-language insights about spending patterns.",
        "2. Overspending alerts for any category exceeding 20% of total income.",
        "3. Practical, actionable suggestions to save money.",
        "",
        "Keep your response concise, structured with bullet points, and focused on key takeaways.",
        "",
        f"Total income : ₹{total_income:,.2f}",
        f"Total spent  : ₹{total_spent:,.2f}",
    ]

    if monthly:
        lines.append("")
        lines.append("Monthly net amounts:")
        for month in sorted(monthly.keys()):
            lines.append(f"  {month}: ₹{monthly[month]:,.2f}")

    if cat_totals:
        lines.append("")
        lines.append("Spending by category:")
        for cat, amt in sorted(cat_totals.items(), key=lambda x: x[1]):
            lines.append(f"  {cat}: ₹{amt:,.2f}")

    if top_cats:
        lines.append("")
        lines.append("Top 3 expense categories:")
        for cat, amt in top_cats:
            lines.append(f"  {cat}: ₹{amt:,.2f}")

    return "\n".join(lines)


def advise(analysis: Dict, client: LLMClient, model_name: str = "") -> str:
    """Generate plain-language financial insights.

    Parameters
    ----------
    analysis   : dict returned by analyze_transactions()
    client     : LLMClient instance (provider-agnostic wrapper)
    model_name : ignored — model is already baked into LLMClient; kept for
                 backward-compat with old callers that pass it.

    Returns
    -------
    str  – the model's insight text
    """
    if not analysis:
        return "No transaction data found. Please upload a valid statement."

    prompt = _build_prompt(analysis)
    return client.generate(prompt, timeout=90) or "No response from the model."
