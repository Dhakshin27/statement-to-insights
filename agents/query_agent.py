"""Intelligent Query Agent for 'Ask About This Statement'.

Accurately resolves user questions regarding merchants, categories, subscriptions,
largest expenses, and savings strategies, both with an active LLM (Gemini/Grok/Ollama)
and in standalone deterministic mode.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional
import pandas as pd

from core.llm_factory import LLMClient
from rag.retriever import retrieve


def _extract_merchant_query(question: str, df: pd.DataFrame) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """Detect if the user is asking about a specific merchant or entity."""
    words = re.findall(r"[A-Za-z0-9]{3,}", question.lower())
    ignore_words = {
        "how", "much", "did", "spend", "what", "where", "find", "show", "tell",
        "about", "this", "that", "from", "total", "were", "charges", "orders",
        "payments", "bought", "purchase", "purchases", "cost", "money", "paid",
        "statement", "many", "times", "list", "give", "please", "can", "could",
    }
    candidate_terms = [w for w in words if w not in ignore_words]
    
    if df.empty or not candidate_terms:
        return None, None

    for term in candidate_terms:
        # Match against description
        matched = df[df["description"].str.contains(re.escape(term), case=False, na=False)]
        if not matched.empty:
            return matched, term.title()

    return None, None


def _format_deterministic_answer(question: str, analysis: Dict, df: pd.DataFrame) -> str:
    """Provide a direct, exact numerical answer without requiring an LLM."""
    q_lower = question.lower()
    
    # 1. Merchant lookup
    matched_df, merchant_name = _extract_merchant_query(question, df)
    if matched_df is not None and merchant_name:
        expenses = matched_df[matched_df["amount"] < 0]
        total = abs(float(expenses["amount"].sum())) if not expenses.empty else 0.0
        income_match = matched_df[matched_df["amount"] > 0]
        income_total = float(income_match["amount"].sum()) if not income_match.empty else 0.0

        lines = [f"### 🔍 Transactions matching **{merchant_name}**"]
        if total > 0:
            lines.append(f"- **Total Spent:** ₹{total:,.2f} across **{len(expenses)}** transaction(s).")
            lines.append(f"- **Average per transaction:** ₹{(total / len(expenses)):,.2f}")
        if income_total > 0:
            lines.append(f"- **Total Received:** ₹{income_total:,.2f} across **{len(income_match)}** transaction(s).")

        lines.append("\n**Transaction Log:**")
        lines.append("| Date | Description | Amount |")
        lines.append("| :--- | :--- | :--- |")
        for _, row in matched_df.head(10).iterrows():
            amt_str = f"-₹{abs(row['amount']):,.2f}" if row['amount'] < 0 else f"+₹{row['amount']:,.2f}"
            date_str = str(row['date'])[:10] if pd.notna(row['date']) else "N/A"
            lines.append(f"| {date_str} | {str(row['description'])[:35]} | **{amt_str}** |")
        
        if len(matched_df) > 10:
            lines.append(f"\n*(Showing top 10 of {len(matched_df)} matching transactions)*")
        return "\n".join(lines)

    # 2. Category lookup
    cat_totals = analysis.get("category_totals", {})
    for cat, amt in cat_totals.items():
        if cat.lower() in q_lower:
            total_spent = analysis.get("total_spent", 1) or 1
            pct = (amt / total_spent) * 100
            matched_cat_df = df[(df["category"].str.lower() == cat.lower()) & (df["amount"] < 0)]
            
            lines = [
                f"### 📂 Spending on **{cat}**",
                f"- **Total Spent:** **₹{amt:,.2f}** ({pct:.1f}% of total expenditures)",
                f"- **Transactions recorded:** {len(matched_cat_df)}",
            ]
            if len(matched_cat_df) > 0:
                lines.append("\n**Recent items in this category:**")
                lines.append("| Date | Description | Amount |")
                lines.append("| :--- | :--- | :--- |")
                for _, row in matched_cat_df.head(5).iterrows():
                    amt_str = f"₹{abs(row['amount']):,.2f}"
                    date_str = str(row['date'])[:10] if pd.notna(row['date']) else "N/A"
                    lines.append(f"| {date_str} | {str(row['description'])[:35]} | {amt_str} |")
            return "\n".join(lines)

    # 3. Subscriptions / recurring
    if any(k in q_lower for k in ("recurring", "subscription", "bill", "monthly charges", "utility")):
        recurring = analysis.get("recurring_charges", [])
        if recurring:
            lines = [
                "### 🔄 Detected Subscriptions & Recurring Bills",
                f"Estimated recurring monthly commitment: **₹{analysis.get('recurring_monthly_estimate', 0):,.2f}**\n",
                "| Service / Merchant | Occurrences | Approx. Amount | Category |",
                "| :--- | :--- | :--- | :--- |"
            ]
            for r in recurring:
                lines.append(f"| **{r['merchant']}** | {r['count']}x | ₹{r['avg_amount']:,.2f} | {r.get('category', 'Bills')} |")
            return "\n".join(lines)
        return "No recurring subscription charges or fixed bills were automatically identified in this statement."

    # 4. Highest / Largest purchases
    if any(k in q_lower for k in ("highest", "largest", "biggest", "max", "top expense", "most expensive")):
        largest = analysis.get("largest_expenses", [])
        if largest:
            lines = [
                "### ⚡ Highest Single Expenses",
                "| Date | Description | Category | Amount |",
                "| :--- | :--- | :--- | :--- |"
            ]
            for exp in largest:
                lines.append(f"| {exp['date']} | {exp['description']} | {exp['category']} | **₹{exp['amount']:,.2f}** |")
            return "\n".join(lines)

    # 5. General summary / How to save
    income = analysis.get("total_income", 0.0)
    spent = analysis.get("total_spent", 0.0)
    net = analysis.get("net_cash_flow", 0.0)
    savings_rate = analysis.get("savings_rate", 0)

    lines = [
        "### 📊 Statement Quick Summary",
        f"- **Total Recognized Income:** ₹{income:,.2f}",
        f"- **Total Expenditures:** ₹{spent:,.2f}",
        f"- **Net Cash Flow:** {'+' if net >= 0 else ''}₹{net:,.2f} ({savings_rate or 0:.1f}% savings rate)",
        f"- **Daily Burn Rate:** ₹{analysis.get('daily_burn_rate', 0):,.2f} / day",
        f"- **Financial Health:** {analysis.get('health_score', 50)}/100 ({analysis.get('health_label', 'Fair')})",
    ]
    if analysis.get("top_expense_categories"):
        top_str = ", ".join(f"**{c}** (₹{a:,.0f})" for c, a in analysis["top_expense_categories"][:3])
        lines.append(f"- **Top Spending Areas:** {top_str}")

    lines.append("\n*Tip: Connect an AI model (Gemini, Grok, or local Ollama) in the sidebar for personalized, conversational financial advice!*")
    return "\n".join(lines)


def answer_question(
    question: str,
    analysis: Dict,
    transactions: Iterable[Dict],
    client: Optional[LLMClient] = None,
    statement_id: str = "",
) -> str:
    """Answer questions regarding statement transactions with grounded accuracy."""
    if not transactions:
        return "Please upload a statement to ask questions about your transactions."

    df = pd.DataFrame(transactions).copy()
    df["amount"] = pd.to_numeric(df.get("amount"), errors="coerce").fillna(0.0)
    df["description"] = df.get("description", "").fillna("").astype(str)
    df["category"] = df.get("category", "Miscellaneous").fillna("Miscellaneous")

    # If no LLM client is connected, provide deterministic data answer
    if client is None:
        return _format_deterministic_answer(question, analysis, df)

    # If LLM client is connected, prepare relevant context and calculate exact numbers
    context_chunks = retrieve(question, transactions, statement_id=statement_id, limit=8)
    matched_df, merchant_name = _extract_merchant_query(question, df)
    
    exact_data_context = []
    if matched_df is not None and merchant_name:
        expenses = matched_df[matched_df["amount"] < 0]
        exact_spent = abs(float(expenses["amount"].sum())) if not expenses.empty else 0.0
        exact_data_context.append(
            f"EXACT DATA for '{merchant_name}': {len(matched_df)} transactions totaling ₹{exact_spent:,.2f} spent."
        )

    # Top stats
    summary_stats = (
        f"Total Income: ₹{analysis.get('total_income', 0):,.2f}, "
        f"Total Spent: ₹{analysis.get('total_spent', 0):,.2f}, "
        f"Net Cashflow: ₹{analysis.get('net_cash_flow', 0):,.2f}, "
        f"Health Score: {analysis.get('health_score', 50)}/100, "
        f"Daily Burn Rate: ₹{analysis.get('daily_burn_rate', 0):,.2f}."
    )

    prompt_lines = [
        "You are an expert personal finance copilot.",
        "Answer the user's specific question using the exact statement data provided below.",
        "Be concise, direct, helpful, and use rupee amounts (₹) formatted cleanly.",
        "",
        f"USER QUESTION: {question}",
        "",
        f"FINANCIAL SUMMARY: {summary_stats}",
    ]

    if exact_data_context:
        prompt_lines.append(f"PRE-CALCULATED FIGURES: {'; '.join(exact_data_context)}")

    if analysis.get("recurring_charges"):
        rec_list = ", ".join(f"{r['merchant']} (₹{r['avg_amount']:,.0f})" for r in analysis["recurring_charges"][:5])
        prompt_lines.append(f"DETECTED RECURRING CHARGES: {rec_list}")

    if context_chunks:
        prompt_lines.append("\nRELEVANT STATEMENT TRANSACTIONS:")
        for chunk in context_chunks:
            prompt_lines.append(f"- {chunk}")

    prompt = "\n".join(prompt_lines)

    try:
        reply = client.generate(prompt, timeout=60)
        if reply and reply.strip():
            return reply.strip()
    except Exception as exc:
        print(f"[QueryAgent LLM Error] {exc}")

    # Fallback to deterministic answer if LLM fails
    return _format_deterministic_answer(question, analysis, df)
