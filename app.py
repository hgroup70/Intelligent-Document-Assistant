"""Entry point. Run with: streamlit run app.py"""

from __future__ import annotations

import logging

import streamlit as st

st.set_page_config(
    page_title="Intelligent Document Assistant",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Document summarizer and Q&A app built with Streamlit and LangChain."},
)

from src.ui import state  # noqa: E402  (set_page_config must run first)
from src.ui.chat_view import render_chat  # noqa: E402
from src.ui.document_view import render_document  # noqa: E402
from src.ui.history_view import render_history  # noqa: E402
from src.ui.home import render_doc_header, render_welcome  # noqa: E402
from src.ui.login import require_login  # noqa: E402
from src.ui.sidebar import render_sidebar  # noqa: E402
from src.ui.styles import inject_css  # noqa: E402
from src.ui.summary_view import render_summary  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> None:
    inject_css()
    state.init_state()

    if state.settings().auth_enabled:
        if not require_login():
            return
    else:
        state.ensure_anonymous_workspace()

    svc = state.service()
    render_sidebar(svc)

    doc = state.active_document(svc)
    if doc is None:
        render_welcome()
        return

    render_doc_header(doc)
    state.apply_navigation()
    view = st.segmented_control("View", state.VIEWS, key="view", label_visibility="collapsed")
    if view is None:  # user clicked the selected option again (deselect)
        view = state.VIEW_SUMMARY

    if view == state.VIEW_SUMMARY:
        render_summary(svc, doc)
    elif view == state.VIEW_CHAT:
        render_chat(svc, doc)
    elif view == state.VIEW_TEXT:
        render_document(svc, doc)
    else:
        render_history(svc)


if __name__ == "__main__":  # `streamlit run` executes this file as __main__
    main()
