import streamlit as st
from utils.language import get_language
from pathlib import Path

def get_app_title(LANG: dict, page_id: str) -> str:
    return (
        LANG.get("pages", {})
            .get(page_id, {})
            .get("title")
        or LANG.get("pages", {})
               .get("home", {})
               .get("title", "")
    )


def render_top_bar(LANG, page_id: str):    
    app_title = get_app_title(LANG, page_id)

    # ---- Layout ----
    left, right = st.columns([8.5, 1.5])

    # ---- Title ----
    with left:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;height:48px;">
                <h1 style="margin:0;">{app_title}</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---- Inline language links ----
    with right:
        current = st.session_state.lang

        en_style = "font-weight:700;" if current == "en" else ""
        zh_style = "font-weight:700;" if current == "zh" else ""

        st.markdown(
            f"""
            <div style="
                display:flex;
                justify-content:flex-end;
                align-items:center;
                height:48px;
                white-space:nowrap;
                font-size:0.95rem;
            ">
                <a href="?lang=en" style="{en_style} text-decoration:none;">EN</a>
                <span style="margin:0 6px;">|</span>
                <a href="?lang=zh" style="{zh_style} text-decoration:none;">中文</a>
            </div>
            """,
            unsafe_allow_html=True
        )

    return LANG
