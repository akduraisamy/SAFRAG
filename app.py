# SAFRAG — SAF + RAG Pipeline
# Author: Dr. Amudha Kumari Duraisamy
# Entry point: Streamlit UI
# Usage: streamlit run app.py

import os
import streamlit as st
from dotenv import load_dotenv
from scripts.query import ask, get_collection

load_dotenv()

st.set_page_config(
    page_title="SAFRAG — CE Literature Q&A",
    page_icon="🧫",
    layout="wide",
)

st.title("🧫✈️ SAFRAG")
st.caption("Chain Elongation Fermentation Literature Q&A | Dr. Amudha Kumari Duraisamy")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")

    backend = st.radio(
        "LLM Backend",
        options=["ollama", "anthropic"],
        format_func=lambda x: "🟢 Ollama (Free, Local)" if x == "ollama" else "🔑 Anthropic (Paid)",
        index=0,
        help="Ollama runs fully on your machine — no API key, no cost. Anthropic is cloud-based.",
    )

    if backend == "ollama":
        ollama_model = st.selectbox(
            "Ollama model",
            options=["mistral", "llama3.1", "llama3.2", "gemma2", "phi3"],
            index=0,
            help=(
                "Best for scientific Q&A:\n"
                "• mistral — best balance of speed + accuracy\n"
                "• llama3.1 — strong reasoning, needs ~8GB RAM\n"
                "• llama3.2 — fastest but weaker on dense science\n\n"
                "Pull a model first: ollama pull mistral"
            ),
        )
        selected_model = ollama_model
        st.info("Ollama must be running locally.\n`ollama serve` or open the Ollama app.", icon="ℹ️")
    else:
        api_key = st.text_input(
            "Anthropic API Key",
            value=os.environ.get("ANTHROPIC_API_KEY", ""),
            type="password",
            help="Stored only in session memory, never saved to disk.",
        )
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        selected_model = "claude-sonnet-4-6"
        st.caption(f"Model: `{selected_model}`")

    n_chunks = st.slider(
        "Chunks retrieved", min_value=4, max_value=16, value=8,
        help="More chunks = broader context but slower response."
    )

    st.divider()
    st.subheader("Example questions")
    examples = [
        "Which papers reported MCCA > 8 g/L and what HRT did they use?",
        "Which feedstocks appeared in semi-continuous setups?",
        "What genera were dominant in Tonanzi 2020?",
        "Compare ethanol-to-acetate ratios used across studies.",
        "What pH conditions were used in continuous reactor experiments?",
        "Which studies used food waste as feedstock?",
        "What were the main MCCA products reported across all papers?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["question_input"] = ex

    st.divider()
    try:
        col = get_collection()
        st.metric("Indexed chunks", col.count())
        st.caption("Re-index: `python scripts/ingest.py`")
    except Exception:
        st.warning("No index found.\nRun: `python scripts/ingest.py`")

# ── Main area ─────────────────────────────────────────────────────────────────
question = st.text_area(
    "Ask a question about your CE fermentation literature:",
    height=100,
    placeholder="e.g. Which papers reported MCCA > 8 g/L and what HRT did they use?",
    key="question_input",
)

col1, col2 = st.columns([1, 5])
with col1:
    submit = st.button("Ask", type="primary", use_container_width=True)
with col2:
    show_chunks = st.checkbox("Show retrieved chunks", value=False)

if submit:
    if not question.strip():
        st.warning("Please enter a question.")
    elif backend == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        st.error("Add your Anthropic API key in the sidebar.")
    else:
        with st.spinner(f"Retrieving and reasoning via {selected_model}..."):
            try:
                result = ask(
                    question,
                    n_results=n_chunks,
                    backend=backend,
                    model=selected_model,
                )
            except Exception as e:
                if "connection" in str(e).lower() or "connect" in str(e).lower():
                    st.error(
                        "Cannot connect to Ollama. Make sure it is running:\n"
                        "- Open the Ollama app, or\n"
                        "- Run `ollama serve` in a terminal"
                    )
                else:
                    st.error(f"Error: {e}")
                st.stop()

        # Show paper-filter notice if active
        if result.get("paper_filter"):
            st.info(
                f"🔍 Searched within: **{', '.join(result['paper_filter'])}**",
                icon="📄",
            )

        st.subheader("Answer")
        st.markdown(result["answer"])

        st.caption(f"Backend: `{result['backend']}` | Model: `{result['model']}`")

        st.subheader("Sources consulted")
        src_cols = st.columns(min(len(result["sources"]), 4))
        for i, src in enumerate(result["sources"]):
            src_cols[i % 4].success(src)

        if show_chunks:
            st.subheader("Retrieved chunks")
            for i, chunk in enumerate(result["chunks"]):
                with st.expander(
                    f"[{i + 1}] {chunk['source']} — chunk {chunk['chunk_index']} "
                    f"(distance: {chunk['distance']})"
                ):
                    st.text(chunk["text"])
