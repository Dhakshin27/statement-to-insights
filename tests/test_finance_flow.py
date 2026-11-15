from agents.advisor_agent import advise
from agents.analysis_agent import analyze_transactions
from agents.query_agent import answer_question


TRANSACTIONS = [
    {"date": "2026-01-01", "description": "Salary credit", "amount": 10000, "category": "Salary"},
    {"date": "2026-01-02", "description": "Swiggy dinner", "amount": -2500, "category": "Food"},
    {"date": "2026-01-03", "description": "Uber ride", "amount": -400, "category": "Transport"},
]


def test_analysis_uses_positive_spending_totals():
    analysis = analyze_transactions(TRANSACTIONS)
    assert analysis["total_spent"] == 2900
    assert analysis["total_income"] == 10000
    assert analysis["category_totals"]["Food"] == 2500
    assert analysis["net_cash_flow"] == 7100


def test_local_insights_work_without_an_llm():
    result = advise(analyze_transactions(TRANSACTIONS))
    assert "Watch list" in result
    assert "Food" in result


def test_transaction_lookup_returns_relevant_statement_context():
    result = answer_question("Find my Uber transaction", analyze_transactions(TRANSACTIONS), TRANSACTIONS)
    assert "Uber ride" in result
