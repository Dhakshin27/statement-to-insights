
import os
import re
from typing import List, Dict, Optional

import pandas as pd
import pdfplumber


def _normalize_header(header) -> str:
    """Convert column names into consistent identifiers."""
    if header is None:
        return ""

    return re.sub(r"[^a-z0-9]", "", str(header).lower())


def _parse_money(value) -> Optional[float]:
    """Convert formatted monetary values into floats."""

    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    if not text or text in {"-", "—", "–"}:
        return None

    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")

    text = re.sub(r"[₹$€£,\s]", "", text, flags=re.UNICODE)
    text = re.sub(r"(?i)INR", "", text)

    if text.upper().endswith("DR"):
        negative = True
        text = text[:-2]

    elif text.upper().endswith("CR"):
        text = text[:-2]

    try:
        amount = float(text)
        return -abs(amount) if negative else amount
    except ValueError:
        return None


def _get_column(row, aliases):
    """Find a value using possible column names."""
    for alias in aliases:
        if alias in row:
            return row[alias]

    return None


def _convert_row(row: Dict) -> Optional[Dict]:
    """Convert one statement row into a standard transaction."""

    date = _get_column(row, ["date", "transactiondate", "valuedate"])

    description = _get_column(
        row,
        ["description", "narration", "particulars", "details", "remarks"]
    )

    if date is None or description is None:
        return None

    if pd.isna(date) or pd.isna(description):
        return None

    description = str(description).strip()

    if not description:
        return None

    # Prefer debit/credit columns when both are present.
    debit_value = _get_column(
        row, ["debit", "withdrawal", "withdrawals", "debitinr"]
    )

    credit_value = _get_column(
        row, ["credit", "deposit", "deposits", "creditinr"]
    )

    if debit_value is not None or credit_value is not None:
        debit = _parse_money(debit_value) or 0.0
        credit = _parse_money(credit_value) or 0.0

        # Expenses are negative; income is positive.
        amount = credit - debit

    else:
        amount_value = _get_column(
            row, ["amount", "transactionamount", "withdrawalamount"]
        )

        amount = _parse_money(amount_value)

        if amount is None:
            return None

    # Skip rows without an actual transaction amount.
    if amount == 0:
        return None

    currency = _get_column(row, ["currency"])

    if currency is None:
        currency = (
            "INR"
            if any("inr" in key for key in row)
            else ""
        )

    balance_value = _get_column(
        row, ["balance", "closingbalance", "runningbalance", "balanceinr"]
    )

    balance = _parse_money(balance_value)

    transaction = {
        "date": str(date).strip(),
        "description": description,
        "amount": amount,
        "currency": str(currency).strip(),
    }

    if balance is not None:
        transaction["balance"] = balance

    return transaction


def _normalize_row(raw_row, headers):
    """Map raw values to normalized column names."""

    if len(raw_row) != len(headers):
        return {}

    return {
        _normalize_header(headers[i]): raw_row[i]
        for i in range(len(headers))
        if headers[i]
    }


def parse_statement(file_path: str) -> List[Dict]:
    """Parse CSV or PDF bank statements into standard transactions."""

    _, ext = os.path.splitext(file_path.lower())

    transactions = []

    if ext == ".csv":

        df = pd.read_csv(file_path)
        df.columns = [_normalize_header(c) for c in df.columns]

        for _, row in df.iterrows():
            transaction = _convert_row(row.to_dict())

            if transaction:
                transactions.append(transaction)

    elif ext == ".pdf":

        with pdfplumber.open(file_path) as pdf:

            for page in pdf.pages:

                for table in page.extract_tables() or []:

                    if not table or len(table) < 2:
                        continue

                    headers = table[0]

                    for raw_row in table[1:]:

                        row = _normalize_row(raw_row, headers)

                        if not row:
                            continue

                        transaction = _convert_row(row)

                        if transaction:
                            transactions.append(transaction)

    else:
        raise ValueError(
            "Unsupported file type. Upload a CSV or PDF statement."
        )

    if not transactions:
        raise ValueError(
            "No valid transactions found. "
            "Check the statement's column names and format."
        )

    return transactions
