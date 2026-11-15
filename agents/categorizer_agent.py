from typing import List, Dict

# Keyword-based mapping – covers common Indian & international transaction descriptions.
_CATEGORY_KEYWORDS: dict = {
    "Food": [
        "restaurant", "cafe", "coffee", "meal", "dining", "swiggy", "zomato",
        "burger", "pizza", "hotel", "bakery", "biryani", "food",
    ],
    "Transport": [
        "uber", "ola", "lyft", "taxi", "cab", "bus", "metro", "train", "rapido",
        "fuel", "petrol", "diesel", "toll", "parking", "auto",
    ],
    "Bills": [
        "electricity", "electric", "water bill", "gas bill", "utility",
        "internet", "broadband", "jio", "airtel", "bsnl", "phone", "mobile",
        "credit card", "emi", "loan", "insurance",
    ],
    "Entertainment": [
        "netflix", "prime", "hotstar", "disney", "spotify", "youtube",
        "movie", "cinema", "pvr", "inox", "concert", "theatre", "gaming",
        "steam", "playstation", "xbox",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho",
        "store", "mall", "shop", "purchase", "clothing", "apparel", "fashion",
        "electronics", "gadget",
    ],
    "Healthcare": [
        "pharmacy", "medical", "hospital", "clinic", "medicine", "doctor",
        "health", "apollo", "1mg", "netmeds", "diagnostic", "lab test",
    ],
    "Salary": [
        "salary", "payroll", "remuneration", "pay credit", "neft cr",
        "salary credit", "income", "stipend",
    ],
    "Investment": [
        "stock", "mutual fund", "mf", "brokerage", "investment", "dividend",
        "zerodha", "groww", "upstox", "nse", "bse", "sip", "fd", "ppf",
    ],
}


def _match_category(description: str) -> str:
    """Return a spending category based on description keywords.
    Falls back to 'Miscellaneous' when no keyword matches.
    """
    desc = description.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in desc:
                return category
    return "Miscellaneous"


def categorize_transactions(transactions: List[Dict]) -> List[Dict]:
    """Mutate each transaction dict in-place to add a ``category`` key.

    This is deterministic and does not call the LLM.
    """
    for txn in transactions:
        txn["category"] = _match_category(txn.get("description", ""))
    return transactions
