"""
chat.py — AI Advisor Chat Tab
──────────────────────────────
Conversational interface with financial context injection,
streaming responses, and quick-prompt suggestions.
"""

from __future__ import annotations

import streamlit as st

from penny import ai_advisor


def render_chat(results: dict | None) -> None:
    """Render the AI Advisor chat tab."""
    if not ai_advisor.is_available():
        st.warning(
            "**Gemini API key not configured.**  \n"
            "Add your key to the `.env` file to enable AI-powered advice.  \n"
            "The Dashboard and Goals tabs still work without it."
        )
        return

    # Header with clear button
    hcol1, hcol2 = st.columns([4, 1])
    with hcol1:
        st.markdown(
            '<p style="font-size:16px;font-weight:600;color:#f0f0f5;margin:0">'
            '<i class="lucide-bot" style="margin-right:6px;color:#818cf8"></i>'
            "AI Financial Advisor</p>",
            unsafe_allow_html=True,
        )
    with hcol2:
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Build context from analysis
    financial_context = ""
    if results:
        financial_context = ai_advisor.build_financial_context(results["report"])

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Quick prompts (shown when chat is empty)
    prompt_clicked = None
    if not st.session_state.chat_history:
        st.caption("Try one of these prompts to get started:")
        qp1, qp2, qp3 = st.columns(3)
        quick_prompts = [
            "How can I reduce my debt faster?",
            "Am I saving enough for retirement?",
            "What's the best way to invest my surplus?",
        ]
        with qp1, st.container():
            st.markdown('<div class="quick-prompt-btn">', unsafe_allow_html=True)
            if st.button(quick_prompts[0], key="qp0"):
                prompt_clicked = quick_prompts[0]
            st.markdown("</div>", unsafe_allow_html=True)
        with qp2, st.container():
            st.markdown('<div class="quick-prompt-btn">', unsafe_allow_html=True)
            if st.button(quick_prompts[1], key="qp1"):
                prompt_clicked = quick_prompts[1]
            st.markdown("</div>", unsafe_allow_html=True)
        with qp3, st.container():
            st.markdown('<div class="quick-prompt-btn">', unsafe_allow_html=True)
            if st.button(quick_prompts[2], key="qp2"):
                prompt_clicked = quick_prompts[2]
            st.markdown("</div>", unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("Ask me anything about your finances…")
    active_prompt = user_input or prompt_clicked

    if active_prompt:
        # Show user message
        st.session_state.chat_history.append({"role": "user", "content": active_prompt})
        with st.chat_message("user"):
            st.markdown(active_prompt)

        # Stream AI response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            for chunk in ai_advisor.generate_advice(
                active_prompt,
                st.session_state.chat_history[:-1],  # exclude current msg
                financial_context,
            ):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
