import streamlit as st
import pandas as pd

from core.llm_factory import create_llm, PROVIDERS, PROVIDER_DEFAULTS
from agents.parser_agent import parse_statement
from agents.categorizer_agent import categorize_transactions
from agents.analysis_agent import analyze_transactions
from agents.advisor_agent import advise
from utils.file_handler import save_uploaded_file


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Statement to Insights",
    page_icon="💰",
    layout="wide",
)


# ── Session state ─────────────────────────────────────────────────────────────

for key in ("llm", "provider", "model_name", "transactions", "analysis", "insight"):
    if key not in st.session_state:
        st.session_state[key] = None


# ── Header ────────────────────────────────────────────────────────────────────

st.title("💰 Statement-to-Insights Finance Agent")
st.write(
    "Upload a bank or UPI statement, then let the AI categorise your spending "
    "and generate actionable financial insights."
)
st.divider()


# ── Sidebar: AI configuration ─────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ AI Configuration")

    # Provider picker (outside the form so defaults update instantly)
    selected_provider = st.selectbox(
        "AI Provider",
        PROVIDERS,
        index=0,
        help="Gemini = Google cloud · Grok = xAI cloud · Ollama = local",
    )

    pdef = PROVIDER_DEFAULTS[selected_provider]

    with st.form("ai_configuration"):

        # API key — only shown when the provider needs one
        if pdef["needs_api_key"]:
            api_key = st.text_input(pdef["api_key_label"], type="password")
        else:
            api_key = ""

        # Ollama server URL
        if pdef["needs_base_url"]:
            base_url = st.text_input(
                "Ollama Server URL",
                value=pdef["base_url"],
                help="URL of your running Ollama instance.",
            )
        else:
            base_url = pdef["base_url"]

        # Model name with provider-specific default
        model_name = st.text_input(
            "Model Name",
            value=pdef["model"],
            help={
                "Gemini": "e.g. gemini-3.8-flash, gemini-3.1-pro-preview",
                "Grok":   "e.g. grok-3-mini, grok-3, grok-3-fast",
                "Ollama": "e.g. qwen3:4b, llama3:8b, mistral",
            }.get(selected_provider, ""),
        )

        connect_button = st.form_submit_button(
            "Connect & Test", use_container_width=True
        )

    if connect_button:
        needs_key = pdef["needs_api_key"]
        if needs_key and not api_key.strip():
            st.error(f"Please enter your {pdef['api_key_label']}.")
        elif not model_name.strip():
            st.error("Please enter a model name.")
        else:
            with st.spinner(f"Connecting to {selected_provider}…"):
                try:
                    client = create_llm(
                        provider=selected_provider,
                        model_name=model_name.strip(),
                        api_key=api_key.strip(),
                        base_url=base_url.strip(),
                    )
                    reply = client.test_connection()

                    # Persist to session
                    st.session_state.llm = client
                    st.session_state.provider = selected_provider
                    st.session_state.model_name = model_name.strip()
                    # Clear old results when provider changes
                    st.session_state.insight = None

                    st.success("Connected!")
                    st.caption(f"Model reply: {reply}")

                except Exception as e:
                    st.session_state.llm = None
                    st.error(f"Connection failed — {type(e).__name__}: {e}")
                    print(f"[{selected_provider} error] {type(e).__name__}: {e}")

    # Connection status
    st.divider()
    if st.session_state.llm:
        icon = {"Gemini": "🌐", "Grok": "🤖", "Ollama": "🏠"}.get(
            st.session_state.provider, "✅"
        )
        st.success(
            f"{icon} {st.session_state.provider} — `{st.session_state.model_name}`"
        )
        if st.button("Disconnect", use_container_width=True):
            for k in ("llm", "provider", "model_name", "transactions", "analysis", "insight"):
                st.session_state[k] = None
            st.rerun()
    else:
        st.warning("No AI model connected.")

    # Provider quick-ref
    st.divider()
    with st.expander("ℹ️ Provider help"):
        st.markdown(
            "**Gemini** · [Get key](https://aistudio.google.com/apikey)  \n"
            "Models: `gemini-3.8-flash`, `gemini-3.1-pro-preview`\n\n"
            "**Grok (xAI)** · [Get key](https://console.x.ai)  \n"
            "Models: `grok-3-mini`, `grok-3`, `grok-3-fast`\n\n"
            "**Ollama** · [Install](https://ollama.com)  \n"
            "Start: `ollama serve`  \n"
            "Pull: `ollama pull qwen3:4b`"
        )


# ── Main area ─────────────────────────────────────────────────────────────────

if st.session_state.llm is None:
    prov_hint = " · ".join(
        f"**{p}**" for p in PROVIDERS
    )
    st.info(f"👈 Connect an AI model in the sidebar to get started.  \nSupported: {prov_hint}")
    st.stop()

# ── Step 1: Upload ────────────────────────────────────────────────────────────

st.subheader("Step 1 · Upload your bank statement")
st.caption("Supported formats: CSV (date, description, amount) · PDF with a transaction table")

uploaded_file = st.file_uploader(
    "Drop your statement here",
    type=["csv", "pdf"],
    label_visibility="collapsed",
)

if uploaded_file is not None:
    with st.spinner("Parsing statement…"):
        try:
            file_path = save_uploaded_file(uploaded_file)
            transactions = parse_statement(file_path)
            transactions = categorize_transactions(transactions)
            st.session_state.transactions = transactions
            st.session_state.analysis = analyze_transactions(transactions)
            st.session_state.insight = None   # reset on new upload
        except Exception as e:
            st.error(f"Could not parse file: {e}")
            st.stop()

if st.session_state.transactions is None:
    st.info("Upload a statement above to continue.")
    st.stop()

transactions = st.session_state.transactions
analysis = st.session_state.analysis or {}

# ── Step 2: Transactions table ────────────────────────────────────────────────

st.divider()
st.subheader("Step 2 · Review transactions")

df = pd.DataFrame(transactions)
col1, col2, col3 = st.columns(3)
col1.metric("Transactions", len(df))
col2.metric("Total Spent", f"₹{analysis.get('total_spent', 0):,.2f}")
col3.metric("Total Income", f"₹{analysis.get('total_income', 0):,.2f}")

st.dataframe(df, use_container_width=True)

# ── Step 3: Charts ────────────────────────────────────────────────────────────

st.divider()
st.subheader("Step 3 · Spending breakdown")

cat_totals = analysis.get("category_totals", {})
monthly_totals = analysis.get("monthly_totals", {})

chart_col, monthly_col = st.columns(2)

if cat_totals:
    expense_df = pd.DataFrame(
        [(cat, -amt) for cat, amt in cat_totals.items() if amt < 0],
        columns=["Category", "Amount"],
    ).set_index("Category").sort_values("Amount", ascending=False)
    if not expense_df.empty:
        chart_col.bar_chart(expense_df)
        chart_col.caption("Expenses by category (₹)")

if monthly_totals:
    monthly_df = pd.DataFrame(
        sorted(monthly_totals.items()), columns=["Month", "Net"]
    ).set_index("Month")
    monthly_col.line_chart(monthly_df)
    monthly_col.caption("Monthly net cash flow (₹)")

# ── Step 4: AI insights ───────────────────────────────────────────────────────

st.divider()
st.subheader("Step 4 · AI-generated insights")

provider_label = st.session_state.provider or "AI"

if st.session_state.llm is None:
    st.warning("⚠️ Please configure and connect an AI provider in the sidebar (Gemini, Grok, or Ollama) to generate insights.")
elif st.session_state.insight is None:
    if st.button(
        f"✨ Generate Insights via {provider_label}",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner(f"Asking {provider_label} for financial insights…"):
            try:
                insight = advise(
                    analysis,
                    st.session_state.llm,
                    st.session_state.model_name,
                )
                st.session_state.insight = insight
                st.rerun()
            except Exception as e:
                st.error(f"Insight generation failed — {type(e).__name__}: {e}")
                print(f"[Advisor/{provider_label}] {type(e).__name__}: {e}")
else:
    st.markdown(st.session_state.insight)
    if st.button("🔄 Regenerate Insights"):
        st.session_state.insight = None
        st.rerun()
