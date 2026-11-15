import pandas as pd
from collections import defaultdict
from typing import List, Dict


def analyze_transactions(transactions: List[Dict]) -> Dict:
    """Perform basic financial analysis on a list of transaction dictionaries.

    Returns a dictionary with:
    - total_spent: sum of negative amounts (expenses)
    - total_income: sum of positive amounts (income)
    - monthly_totals: mapping of "YYYY-MM" to net amount for that month
    - category_totals: mapping of category to net amount
    - top_expense_categories: list of top 3 expense categories by absolute spend
    """
    if not transactions:
        return {}

    df = pd.DataFrame(transactions)
    # Ensure proper types
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    else:
        df['date'] = pd.NaT
    if 'category' not in df.columns:
        df['category'] = 'Uncategorized'

    total_spent = -df.loc[df['amount'] < 0, 'amount'].sum()
    total_income = df.loc[df['amount'] > 0, 'amount'].sum()

    # Monthly net totals
    monthly_totals = {}
    if df['date'].notna().any():
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        monthly = df.groupby('year_month')['amount'].sum().to_dict()
        monthly_totals = {k: round(v, 2) for k, v in monthly.items()}

    # Category totals
    cat_totals = df.groupby('category')['amount'].sum().to_dict()
    cat_totals = {k: round(v, 2) for k, v in cat_totals.items()}

    # Top expense categories (by absolute spend)
    expense_cats = {k: -v for k, v in cat_totals.items() if v < 0}
    top_expense_categories = sorted(expense_cats.items(), key=lambda x: x[1], reverse=True)[:3]
    top_expense_categories = [(cat, round(val, 2)) for cat, val in top_expense_categories]

    return {
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "monthly_totals": monthly_totals,
        "category_totals": cat_totals,
        "top_expense_categories": top_expense_categories,
    }
