"""Advisor agent: turn exact calculations into practical financial guidance."""

from __future__ import annotations

from typing import Dict, Optional

from core.config import OVERSPENDING_THRESHOLD
from core.llm_factory import LLMClient


def deterministic_advice(analysis: Dict) -> str:
    """Produce useful guidance when an LLM is not configured or unavailable."""
    spent, income = analysis.get("total_spent", 0.0), analysis.get("total_income", 0.0)
    net = analysis.get("net_cash_flow", income - spent)
    lines = ["### Snapshot", f"- You spent **₹{spent:,.0f}** and received **₹{income:,.0f}** in this statement period.", f"- Your net cash flow is **{'+' if net >= 0 else ''}₹{net:,.0f}**."]
    if income:
        lines.append(f"- Your estimated savings rate is **{analysis.get('savings_rate', 0):.1f}%**.")
    alerts = []
    if income:
        for category, amount in analysis.get("category_totals", {}).items():
            share = amount / income
            if share > OVERSPENDING_THRESHOLD:
                alerts.append(f"- **{category}** is ₹{amount:,.0f} ({share:.0%} of income), above the 20% watch level.")
    if alerts:
        lines.extend(["\n### Watch list", *alerts])
    elif analysis.get("top_expense_categories"):
        category, amount = analysis["top_expense_categories"][0]
        lines.extend(["\n### Focus", f"- Your biggest spending area is **{category}** at ₹{amount:,.0f}; review its recurring purchases first."])
    lines.extend(["\n### One practical next step", "- Set a weekly cap for your largest discretionary category and check it against this dashboard before the next statement cycle."])
    return "\n".join(lines)


def _build_prompt(analysis: Dict, context: str = "") -> str:
    category_totals = analysis.get("category_totals", {})
    lines = ["You are a friendly personal-finance assistant. Use only the supplied numbers.", "Give a short Markdown answer with patterns, any 20%-of-income alerts, and 2 practical savings actions.", f"Income: ₹{analysis.get('total_income', 0):,.2f}; Spending: ₹{analysis.get('total_spent', 0):,.2f}; Net: ₹{analysis.get('net_cash_flow', 0):,.2f}", "Spending by category (positive expense totals):", *[f"- {category}: ₹{amount:,.2f}" for category, amount in sorted(category_totals.items(), key=lambda item: item[1], reverse=True)]]
    if context:
        lines.extend(["Relevant transaction descriptions:", context])
    return "\n".join(lines)


def advise(analysis: Dict, client: Optional[LLMClient] = None, model_name: str = "", context: str = "") -> str:  # noqa: ARG001
    """Generate advice, with a deterministic fallback if the model fails."""
    if not analysis:
        return "No transaction data found. Please upload a valid statement."
    if client is None:
        return deterministic_advice(analysis)
    try:
        reply = client.generate(_build_prompt(analysis, context), timeout=90)
        return reply.strip() if reply and reply.strip() else deterministic_advice(analysis)
    except Exception:
        return deterministic_advice(analysis)
