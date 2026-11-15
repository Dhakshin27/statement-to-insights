"""Exact, pandas-backed financial calculations and forensic analysis."""

from __future__ import annotations

import re
from typing import Dict, List
import pandas as pd


# Known keywords for recurring subscription/utility providers
_RECURRING_KEYWORDS = [
    "netflix", "spotify", "prime", "hotstar", "disney", "youtube",
    "apple.com", "google storage", "icloud", "chatgpt", "openai",
    "broadband", "wifi", "airtel", "jio", "bsnl", "vodafone", "vi ",
    "electricity", "water bill", "gas", "bescom", "tneb", "adani",
    "gym", "fitness", "cult.fit", "rent", "maintenance", "emi",
    "loan", "insurance", "lic", "hdfc life", "sbi life", "sip", "zerodha"
]


def _detect_recurring(expenses_df: pd.DataFrame) -> List[Dict]:
    """Identify repeating transactions or known subscription/bill merchants."""
    if expenses_df.empty:
        return []

    recurring = []
    # 1. Check known subscription/bill patterns
    for kw in _RECURRING_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b" if len(kw) > 3 else re.escape(kw)
        matches = expenses_df[expenses_df["description"].str.contains(pattern, case=False, na=False)]
        if not matches.empty:
            count = len(matches)
            total = float(matches["spend"].sum())
            recurring.append({
                "merchant": kw.title(),
                "count": count,
                "total_spend": round(total, 2),
                "avg_amount": round(total / count, 2),
                "category": matches["category"].iloc[0] if "category" in matches else "Bills",
                "sample_desc": matches["description"].iloc[0][:35],
            })

    # 2. Check identical description & amount occurrences (>=2 occurrences)
    grouped = expenses_df.groupby(["description", "spend"]).size().reset_index(name="count")
    repeats = grouped[grouped["count"] >= 2].sort_values("spend", ascending=False)
    seen_merchants = {r["merchant"].lower() for r in recurring}

    for _, row in repeats.head(8).iterrows():
        desc = str(row["description"])
        amount = float(row["spend"])
        count = int(row["count"])
        # Check if already covered
        if not any(sm in desc.lower() for sm in seen_merchants):
            recurring.append({
                "merchant": desc[:25].strip(),
                "count": count,
                "total_spend": round(amount * count, 2),
                "avg_amount": round(amount, 2),
                "category": "Recurring",
                "sample_desc": desc[:35],
            })
            seen_merchants.add(desc[:15].lower())

    # Sort recurring items by total spend descending
    recurring.sort(key=lambda x: x["total_spend"], reverse=True)
    return recurring[:10]


def _calculate_health_score(total_income: float, total_spent: float, savings_rate: float | None, category_spend: Dict[str, float]) -> tuple[int, str]:
    """Compute a 0-100 Financial Health Score based on cashflow stability and spending discipline."""
    score = 50  # Baseline neutral

    if total_income > 0:
        # Savings rate weight (up to +35 / -25)
        if savings_rate is not None:
            if savings_rate >= 30:
                score += 35
            elif savings_rate >= 20:
                score += 25
            elif savings_rate >= 10:
                score += 15
            elif savings_rate >= 0:
                score += 5
            elif savings_rate >= -20:
                score -= 15
            else:
                score -= 30
        
        # Expense concentration risk
        max_cat_pct = max(category_spend.values()) / total_income if category_spend else 0
        if max_cat_pct > 0.40:
            score -= 15
        elif max_cat_pct > 0.25:
            score -= 5
        else:
            score += 10
    else:
        # No recognized income in statement: evaluate based on expense discipline
        score = 60 if total_spent < 50000 else 45

    score = max(5, min(98, score))

    if score >= 80:
        label = "Exceptional"
    elif score >= 65:
        label = "Healthy"
    elif score >= 50:
        label = "Fair / Moderate"
    else:
        label = "Needs Attention"

    return score, label


def analyze_transactions(transactions: List[Dict]) -> Dict:
    """Return an extensive financial summary for normalized transactions."""
    if not transactions:
        return {}

    df = pd.DataFrame(transactions).copy()
    df["amount"] = pd.to_numeric(df.get("amount"), errors="coerce").fillna(0.0)
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    df["category"] = df.get("category", "Uncategorized").fillna("Uncategorized")
    df["description"] = df.get("description", "").fillna("").astype(str)

    expenses = df.loc[df["amount"] < 0].copy()
    expenses["spend"] = -expenses["amount"]
    income = df.loc[df["amount"] > 0, "amount"]
    
    total_spent = float(expenses["spend"].sum())
    total_income = float(income.sum())
    net_cash_flow = total_income - total_spent

    monthly_totals: Dict[str, float] = {}
    monthly_spend: Dict[str, float] = {}
    monthly_income: Dict[str, float] = {}

    if df["date"].notna().any():
        dated = df.loc[df["date"].notna()].copy()
        dated["year_month"] = dated["date"].dt.to_period("M").astype(str)
        monthly_totals = {str(k): round(float(v), 2) for k, v in dated.groupby("year_month")["amount"].sum().items()}
        
        dated_expenses = expenses.loc[expenses["date"].notna()].copy()
        dated_expenses["year_month"] = dated_expenses["date"].dt.to_period("M").astype(str)
        monthly_spend = {str(k): round(float(v), 2) for k, v in dated_expenses.groupby("year_month")["spend"].sum().items()}
        
        dated_income = df.loc[(df["amount"] > 0) & df["date"].notna()].copy()
        dated_income["year_month"] = dated_income["date"].dt.to_period("M").astype(str)
        monthly_income = {str(k): round(float(v), 2) for k, v in dated_income.groupby("year_month")["amount"].sum().items()}

    category_spend = {str(k): round(float(v), 2) for k, v in expenses.groupby("category")["spend"].sum().items()}
    top_expense_categories = sorted(category_spend.items(), key=lambda item: item[1], reverse=True)[:5]
    
    category_percentages = {}
    if total_spent > 0:
        category_percentages = {cat: round((amt / total_spent) * 100, 1) for cat, amt in category_spend.items()}

    savings_rate = (net_cash_flow / total_income * 100) if total_income else None

    # Daily burn rate & Active date range
    active_days = 1
    daily_burn_rate = total_spent
    start_date = None
    end_date = None
    weekend_spend = 0.0
    weekday_spend = 0.0

    if not expenses.empty and expenses["date"].notna().any():
        valid_dates = expenses.loc[expenses["date"].notna(), "date"]
        start_date = valid_dates.min().strftime("%d %b %Y")
        end_date = valid_dates.max().strftime("%d %b %Y")
        delta_days = (valid_dates.max() - valid_dates.min()).days + 1
        active_days = max(1, delta_days)
        daily_burn_rate = round(total_spent / active_days, 2)

        # Weekend vs Weekday analysis
        is_weekend = valid_dates.dt.dayofweek.isin([5, 6])
        weekend_spend = round(float(expenses.loc[is_weekend, "spend"].sum()), 2)
        weekday_spend = round(float(expenses.loc[~is_weekend, "spend"].sum()), 2)

    # Top 5 single outlier expense transactions
    largest_expenses = []
    if not expenses.empty:
        sorted_exp = expenses.sort_values("spend", ascending=False).head(5)
        for _, row in sorted_exp.iterrows():
            largest_expenses.append({
                "date": row["date"].strftime("%d %b %Y") if pd.notna(row["date"]) else "N/A",
                "description": row["description"][:40],
                "category": row["category"],
                "amount": round(float(row["spend"]), 2),
            })

    # Recurring subscriptions & fixed bills detection
    recurring_charges = _detect_recurring(expenses)
    recurring_monthly_estimate = round(sum(item["avg_amount"] for item in recurring_charges), 2)

    # Health score
    health_score, health_label = _calculate_health_score(total_income, total_spent, savings_rate, category_spend)

    return {
        "transaction_count": int(len(df)),
        "expense_count": int(len(expenses)),
        "income_count": int(len(income)),
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "net_cash_flow": round(net_cash_flow, 2),
        "savings_rate": round(savings_rate, 1) if savings_rate is not None else None,
        "health_score": health_score,
        "health_label": health_label,
        "daily_burn_rate": daily_burn_rate,
        "active_days": active_days,
        "start_date": start_date,
        "end_date": end_date,
        "weekend_spend": weekend_spend,
        "weekday_spend": weekday_spend,
        "monthly_totals": monthly_totals,
        "monthly_spend": monthly_spend,
        "monthly_income": monthly_income,
        "category_totals": category_spend,
        "category_percentages": category_percentages,
        "top_expense_categories": top_expense_categories,
        "largest_expenses": largest_expenses,
        "recurring_charges": recurring_charges,
        "recurring_monthly_estimate": recurring_monthly_estimate,
    }
