"""Provides realistic sample statement datasets for demonstration."""

from __future__ import annotations
from typing import List, Dict


def get_sample_transactions() -> List[Dict]:
    """Return a realistic mix of salary, food, bills, shopping, and entertainment transactions."""
    return [
        {"date": "2026-03-01", "description": "Salary Credit - Acme Corp Tech", "amount": 95000.0, "category": "Salary"},
        {"date": "2026-03-02", "description": "Swiggy Biryani House Order", "amount": -680.0, "category": "Food"},
        {"date": "2026-03-03", "description": "Uber Ride to Tech Park", "amount": -320.0, "category": "Transport"},
        {"date": "2026-03-04", "description": "Amazon India - Wireless Mouse", "amount": -1499.0, "category": "Shopping"},
        {"date": "2026-03-05", "description": "Netflix 4K Premium Plan", "amount": -649.0, "category": "Entertainment"},
        {"date": "2026-03-07", "description": "Electricity Bill Payment BESCOM", "amount": -2450.0, "category": "Bills"},
        {"date": "2026-03-09", "description": "Cult.Fit Gym Monthly Membership", "amount": -2200.0, "category": "Bills"},
        {"date": "2026-03-10", "description": "Swiggy Quick Gourmet Dinner", "amount": -540.0, "category": "Food"},
        {"date": "2026-03-12", "description": "Shell Petrol Pump Fuel", "amount": -1500.0, "category": "Transport"},
        {"date": "2026-03-14", "description": "Zomato Sunday Brunch with Friends", "amount": -1850.0, "category": "Food"},
        {"date": "2026-03-15", "description": "Spotify Family Subscription", "amount": -179.0, "category": "Entertainment"},
        {"date": "2026-03-16", "description": "Zerodha Coin Mutual Fund SIP", "amount": -10000.0, "category": "Investment"},
        {"date": "2026-03-18", "description": "Airtel Fiber Broadband Bill", "amount": -1179.0, "category": "Bills"},
        {"date": "2026-03-20", "description": "Apollo Pharmacy Wellness & Medicine", "amount": -890.0, "category": "Healthcare"},
        {"date": "2026-03-22", "description": "Myntra Fashion Shopping Weekend", "amount": -3499.0, "category": "Shopping"},
        {"date": "2026-03-24", "description": "Swiggy Office Lunch Box", "amount": -380.0, "category": "Food"},
        {"date": "2026-03-25", "description": "Uber Commute Trip", "amount": -285.0, "category": "Transport"},
        {"date": "2026-03-27", "description": "Freelance Design Retainer Payment", "amount": 25000.0, "category": "Salary"},
        {"date": "2026-03-28", "description": "Starbucks Coffee & Snacks", "amount": -620.0, "category": "Food"},
        {"date": "2026-03-30", "description": "Apartment Maintenance Society", "amount": -4500.0, "category": "Bills"},
    ]
