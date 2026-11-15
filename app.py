"""Statement-to-Insights: Modern Neo-Glassmorphic Personal Finance Assistant."""

from __future__ import annotations

import hashlib
import io
import pandas as pd
import streamlit as st

from agents.advisor_agent import advise
from agents.analysis_agent import analyze_transactions
from agents.categorizer_agent import categorize_transactions
from agents.parser_agent import parse_statement
from agents.query_agent import answer_question
from core.llm_factory import PROVIDERS, PROVIDER_DEFAULTS, create_llm
from core.ui_theme import CUSTOM_CSS, get_health_score_badge
from rag.retriever import persist_to_chroma
from utils.file_handler import save_uploaded_file
from utils.sample_data import get_sample_transactions


# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Statement to Insights · Financial Copilot",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Adaptive Neo-Glassmorphism CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Session State Initialization ──────────────────────────────────────────────
defaults = {
    "llm": None,
    "provider": None,
    "model_name": None,
    "transactions": None,
    "analysis": None,
    "insight": None,
    "file_id": None,
    "chat_history": [],
    "active_prompt": None,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)


def clear_statement() -> None:
    for k in ("transactions", "analysis", "insight", "file_id", "chat_history", "active_prompt"):
        st.session_state[k] = None if k != "chat_history" else []


# ── Sidebar: Model Connection ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ AI Model Engine")
    st.caption("Connect your preferred cloud or local model for deep reasoning.")

    selected_provider = st.selectbox(
        "Provider",
        PROVIDERS,
        help="Gemini = Google Cloud · Grok = xAI Cloud · Ollama = Local server",
    )
    pdef = PROVIDER_DEFAULTS[selected_provider]

    with st.form("ai_configuration"):
        api_key = (
            st.text_input(pdef["api_key_label"], type="password")
            if pdef["needs_api_key"]
            else ""
        )
        base_url = (
            st.text_input("Ollama Server URL", value=pdef["base_url"])
            if pdef["needs_base_url"]
            else pdef["base_url"]
        )
        model_name = st.text_input(
            "Model Name",
            value=pdef["model"],
            help="Model identifier to complete your prompt.",
        )
        connect = st.form_submit_button("Connect & Test Model", use_container_width=True)

    if connect:
        try:
            if pdef["needs_api_key"] and not api_key.strip():
                raise ValueError(f"Please enter your {pdef['api_key_label']}.")
            client = create_llm(selected_provider, model_name.strip(), api_key.strip(), base_url.strip())
            with st.spinner(f"Verifying {selected_provider} connection…"):
                client.test_connection()
            st.session_state.llm = client
            st.session_state.provider = selected_provider
            st.session_state.model_name = model_name.strip()
            st.success(f"Connected to {selected_provider}!")
        except Exception as exc:
            st.session_state.llm = None
            st.error(f"Connection failed: {exc}")

    if st.session_state.llm:
        st.markdown(
            f'<div class="score-pill score-excellent">● {st.session_state.provider} · <code>{st.session_state.model_name}</code></div>',
            unsafe_allow_html=True,
        )
        if st.button("Disconnect Model", use_container_width=True):
            st.session_state.llm = None
            st.session_state.provider = None
            st.session_state.model_name = None
            st.rerun()
    else:
        st.caption("💡 Local deterministic analytics and query engine active. Connect an AI model for conversational advice.")

    st.divider()
    st.markdown("#### 🔒 Privacy & Local Processing")
    st.caption(
        "Statements are parsed and indexed locally on your device. Only aggregated summaries and specific query contexts are shared with your connected model."
    )



# ── Executive Hero ────────────────────────────────────────
analysis = st.session_state.analysis or {}
health_score = analysis.get("health_score", 50)
health_label = analysis.get("health_label", "Moderate")

st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-badge">✦ PERSONAL FINANCIAL INTELLIGENCE</div>
        <div class="hero-title">Your money.<br>Understood.</div>
        <div class="hero-subtitle">
            A clearer picture of your financial life.
            Discover spending patterns, recurring payments,
            cash flow trends, and opportunities to save.
        </div>
        <div style="margin-top:22px;">
            {get_health_score_badge(health_score, health_label)
                if st.session_state.transactions else
                '<span class="score-pill">● AWAITING STATEMENT</span>'}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)



# ── File Ingestion & Demo Loader ──────────────────────────────────────────────
upload_col, action_col = st.columns([3, 1])

with upload_col:
    uploaded_file = st.file_uploader(
        "Upload Bank or UPI Statement",
        type=["csv", "pdf"],
        help="Supports CSV and PDF bank statements with date, description, and amount columns.",
    )

with action_col:
    st.write("") # spacing
    st.write("")
    if not st.session_state.transactions:
        if st.button("⚡ Load Demo Statement", use_container_width=True, type="primary"):
            sample_txs = get_sample_transactions()
            categorized = categorize_transactions(sample_txs)
            st.session_state.transactions = categorized
            st.session_state.analysis = analyze_transactions(categorized)
            st.session_state.file_id = "demo_statement_001"
            st.session_state.insight = None
            st.session_state.chat_history = []
            st.rerun()
    else:
        if st.button("✕ Clear Statement", use_container_width=True):
            clear_statement()
            st.rerun()

# Handle File Ingestion
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_id = hashlib.sha256(file_bytes).hexdigest()
    if file_id != st.session_state.file_id:
        with st.spinner("Extracting, categorizing, and indexing your statement…"):
            try:
                path = save_uploaded_file(uploaded_file)
                parsed = parse_statement(path)
                categorized = categorize_transactions(parsed)
                st.session_state.transactions = categorized
                st.session_state.analysis = analyze_transactions(categorized)
                st.session_state.file_id = file_id
                st.session_state.insight = None
                st.session_state.chat_history = []
                persist_to_chroma(categorized, file_id[:12])
                st.success("Statement successfully analyzed!")
                st.rerun()
            except Exception as exc:
                st.error(f"Error parsing statement: {exc}")

if not st.session_state.transactions:
    st.info("👋 Upload a CSV/PDF statement above or click **'⚡ Load Demo Statement'** to explore the command center immediately.")
    st.stop()

transactions = st.session_state.transactions or []
analysis = st.session_state.analysis or {}

# ── Telemetry KPI Grid ────────────────────────────────────────────────────────
net_flow = analysis.get("net_cash_flow", 0.0)
savings_rate = analysis.get("savings_rate")
savings_sub = f"{savings_rate:.1f}% savings rate" if savings_rate is not None else "N/A"
burn_rate = analysis.get("daily_burn_rate", 0.0)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(
    "Net Cash Flow",
    f"{'+' if net_flow >= 0 else ''}₹{net_flow:,.2f}",
    savings_sub,
)
kpi2.metric(
    "Total Expenditures",
    f"₹{analysis.get('total_spent', 0.0):,.2f}",
    f"₹{burn_rate:,.0f} / day velocity",
    delta_color="inverse",
)
kpi3.metric(
    "Total Recognized Income",
    f"₹{analysis.get('total_income', 0.0):,.2f}",
    f"{analysis.get('income_count', 0)} credit event(s)",
)
kpi4.metric(
    "Financial Health Score",
    f"{analysis.get('health_score', 50)}/100",
    analysis.get("health_label", "Moderate"),
)

# ── Safe DataFrame Construction ───────────────────────────────────────────────
st.divider()
df = pd.DataFrame(transactions)
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
else:
    df["date"] = pd.Series(dtype="datetime64[ns]")

if "amount" in df.columns:
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
else:
    df["amount"] = pd.Series(dtype="float64")

if "category" in df.columns:
    df["category"] = df["category"].fillna("Miscellaneous")
else:
    df["category"] = pd.Series(dtype="object")

if "description" not in df.columns:
    df["description"] = pd.Series(dtype="object")

df["type"] = df["amount"].ge(0).map({True: "Income", False: "Expense"})

with st.expander("🔍 Interactive Filters & Search", expanded=False):
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 3])
    
    # Category Filter
    all_cats = sorted(df["category"].unique().tolist())
    selected_cats = f_col1.multiselect("Filter by Category", all_cats, default=[])
    
    # Type Filter
    selected_type = f_col2.selectbox("Transaction Type", ["All", "Expense", "Income"])
    
    # Amount Slider
    max_val = float(abs(df["amount"]).max()) if not df.empty else 1000.0
    amount_range = f_col3.slider("Max Amount (₹)", 0.0, max_val, max_val)
    
    # Search
    search_query = f_col4.text_input("Live Description Search", placeholder="e.g. Swiggy, Netflix, Amazon, Salary...")

# Apply Filters
filtered_df = df.copy()
if selected_cats:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_cats)]
if selected_type != "All":
    filtered_df = filtered_df[filtered_df["type"] == selected_type]
filtered_df = filtered_df[abs(filtered_df["amount"]) <= amount_range]
if search_query.strip():
    filtered_df = filtered_df[filtered_df["description"].str.contains(search_query.strip(), case=False, na=False)]


# ── Modular Command Center Tabs ───────────────────────────────────────────────
tab_pulse, tab_forensics, tab_explorer, tab_copilot = st.tabs([
    "📊 Executive Pulse & Cash Flow",
    "🔬 Smart Forensics & Risk Radar",
    "📑 Transaction Explorer",
    "🤖 AI Statement Copilot",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: EXECUTIVE PULSE & CASH FLOW
# ══════════════════════════════════════════════════════════════════════════════
with tab_pulse:
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📂 Spending by Category")
        category_totals = analysis.get("category_totals", {})
        if category_totals:
            cat_df = pd.DataFrame(
                category_totals.items(), columns=["Category", "Amount"]
            ).sort_values("Amount", ascending=False).set_index("Category")
            st.bar_chart(cat_df, color="#10b981", use_container_width=True)
            
            # Category share breakdown table
            cat_pcts = analysis.get("category_percentages", {})
            st.markdown("**Top Category Shares:**")
            summary_cols = st.columns(min(4, len(cat_pcts)))
            for idx, (cat, pct) in enumerate(list(cat_pcts.items())[:4]):
                summary_cols[idx].metric(cat, f"₹{category_totals[cat]:,.0f}", f"{pct}% of spend")
        else:
            st.info("No expense categories found.")

    with col_right:
        st.markdown("#### 📈 Cash Flow Velocity & Trends")
        monthly_spend = analysis.get("monthly_spend", {})
        monthly_income = analysis.get("monthly_income", {})
        
        if monthly_spend or monthly_income:
            months = sorted(set(list(monthly_spend.keys()) + list(monthly_income.keys())))
            trend_df = pd.DataFrame({
                "Month": months,
                "Spend": [monthly_spend.get(m, 0.0) for m in months],
                "Income": [monthly_income.get(m, 0.0) for m in months],
            }).set_index("Month")
            st.line_chart(trend_df, color=["#ef4444", "#10b981"], use_container_width=True)
        else:
            st.info("Insufficient monthly date series to chart timeline.")

        # Weekend vs Weekday analysis
        st.markdown("#### ⚡ Spend Velocity: Weekday vs Weekend")
        wk_col1, wk_col2 = st.columns(2)
        wk_col1.metric("Weekday Spend", f"₹{analysis.get('weekday_spend', 0.0):,.2f}")
        wk_col2.metric("Weekend Spend", f"₹{analysis.get('weekend_spend', 0.0):,.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: SMART FORENSICS & RISK RADAR
# ══════════════════════════════════════════════════════════════════════════════
with tab_forensics:
    col_rec, col_outliers = st.columns(2)

    with col_rec:
        st.markdown("#### 🔄 Detected Subscriptions & Recurring Bills")
        recurring = analysis.get("recurring_charges", [])
        if recurring:
            st.caption(
                f"Projected Monthly Fixed Commitment: **₹{analysis.get('recurring_monthly_estimate', 0):,.2f}**"
            )
            rec_df = pd.DataFrame(recurring)[["merchant", "count", "avg_amount", "category"]]
            rec_df.columns = ["Merchant / Service", "Frequency", "Average (₹)", "Category"]
            st.dataframe(rec_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recurring subscriptions or repeat bills detected.")

    with col_outliers:
        st.markdown("#### ⚡ Top 5 Largest Expenses")
        largest = analysis.get("largest_expenses", [])
        if largest:
            st.caption("Review high-ticket transactions for potential one-time budget spikes.")
            outlier_df = pd.DataFrame(largest)
            outlier_df.columns = ["Date", "Description", "Category", "Amount (₹)"]
            st.dataframe(outlier_df, use_container_width=True, hide_index=True)
        else:
            st.info("No major outlier expenses identified.")

    st.divider()
    st.markdown("#### ⚠️ Overspending Watch Radar (>20% of Income)")
    threshold = analysis.get("total_income", 0.0) * 0.20
    category_totals = analysis.get("category_totals", {})
    alerts = [(cat, amt) for cat, amt in category_totals.items() if threshold > 0 and amt > threshold]
    if alerts:
        for cat, amt in sorted(alerts, key=lambda x: x[1], reverse=True):
            pct_inc = (amt / analysis["total_income"]) * 100
            st.warning(f"**{cat}**: ₹{amt:,.2f} accounts for **{pct_inc:.1f}%** of your total recognized income (watch threshold: 20%).")
    else:
        st.success("All spending categories are currently within healthy income allocation ratios.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: TRANSACTION EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
with tab_explorer:
    exp_header_col, export_col1, export_col2 = st.columns([3, 1, 1])
    exp_header_col.markdown(f"#### 📑 Filtered Transactions ({len(filtered_df):,} of {len(df):,})")
    
    # Export CSV
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    export_col1.download_button(
        "📥 Export CSV",
        data=csv_buffer.getvalue(),
        file_name="transactions_export.csv",
        mime="text/csv",
        use_container_width=True,
    )
    
    # Export JSON
    json_str = filtered_df.to_json(orient="records", date_format="iso")
    export_col2.download_button(
        "📥 Export JSON",
        data=json_str,
        file_name="transactions_export.json",
        mime="application/json",
        use_container_width=True,
    )

    display_df = filtered_df.copy()
    display_df["formatted_amount"] = display_df["amount"].map(
        lambda x: f"-₹{abs(x):,.2f}" if x < 0 else f"+₹{x:,.2f}"
    )
    
    st.dataframe(
        display_df[["date", "description", "category", "type", "formatted_amount"]],
        column_config={
            "date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
            "description": st.column_config.TextColumn("Description"),
            "category": st.column_config.TextColumn("Category"),
            "type": st.column_config.TextColumn("Type"),
            "formatted_amount": st.column_config.TextColumn("Amount (₹)"),
        },
        use_container_width=True,
        hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: AI STATEMENT COPILOT ("ASK ABOUT THIS STATEMENT")
# ══════════════════════════════════════════════════════════════════════════════
with tab_copilot:
    st.markdown("### 🤖 Statement Copilot")
    st.caption("Ask questions about any merchant, inspect subscriptions, or request personalized savings advice.")

    # 1. High-Level AI Insights Generator
    with st.expander("✦ Executive AI Financial Review", expanded=(st.session_state.insight is not None)):
        ai_provider_tag = f"via {st.session_state.provider}" if st.session_state.llm else "(Deterministic Mode)"
        if st.session_state.insight is None:
            if st.button(f"✨ Generate Strategic Financial Insights {ai_provider_tag}", type="primary"):
                with st.spinner("Analyzing financial patterns…"):
                    st.session_state.insight = advise(analysis, st.session_state.llm)
                    st.rerun()
        else:
            st.markdown(st.session_state.insight)
            if st.button("🔄 Refresh Insights"):
                st.session_state.insight = None
                st.rerun()

    st.divider()

    # 2. Interactive Prompt Suggestion Chips
    st.markdown("#### 💡 Quick Questions (Click to Ask)")
    chip_cols = st.columns(4)
    if chip_cols[0].button("🍔 How much on Food & Dining?", use_container_width=True):
        st.session_state.active_prompt = "How much did I spend on Food?"
    if chip_cols[1].button("🔄 List my subscriptions", use_container_width=True):
        st.session_state.active_prompt = "What are my recurring subscriptions?"
    if chip_cols[2].button("⚡ What was my biggest expense?", use_container_width=True):
        st.session_state.active_prompt = "What was my highest single expense?"
    if chip_cols[3].button("💰 How can I save more?", use_container_width=True):
        st.session_state.active_prompt = "Give me 3 practical ways to save money."

    # 3. Chat History Stream
    if st.session_state.chat_history:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble-user"><strong>You:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble-bot"><strong>Copilot:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("✕ Clear Conversation History"):
            st.session_state.chat_history = []
            st.rerun()

    # 4. Input Form for Statement Copilot
    user_query = st.chat_input("Ask anything about this statement (e.g. Swiggy charges, Amazon orders, fuel spend)...")
    prompt_to_run = user_query or st.session_state.active_prompt

    if prompt_to_run:
        # Clear active prompt latch
        st.session_state.active_prompt = None

        # Add user query to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt_to_run})

        with st.spinner("Analyzing statement records…"):
            answer = answer_question(
                prompt_to_run,
                analysis,
                transactions,
                client=st.session_state.llm,
                statement_id=(st.session_state.file_id or "")[:12],
            )
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()
