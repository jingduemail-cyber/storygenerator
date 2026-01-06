# --- Set up global page formatting and styles ---
import streamlit as st
from utils.ui import render_top_bar, get_app_title
from utils.language.loader import get_language
from pathlib import Path

PAGE_ID = "about_and_support"

if "lang" not in st.session_state:
    st.session_state.lang = "en"

params = st.query_params

if "lang" in params:
    st.session_state.lang = params["lang"]

T = get_language(st.session_state.lang)

st.set_page_config(
    page_title=get_app_title(T, PAGE_ID),
    layout="centered"
)

render_top_bar(T, PAGE_ID)

# Global CSS for clean, modern UI
st.markdown("""
<style>
    .main-title {
        font-size: 40px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 20px;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 24px;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Create About and Support page ---
st.write("---")
st.header(T["ui"]["about_subheader"])
st.markdown(T["ui"]["about_description"])

st.write("---")
st.header(T["ui"]["support_subheader"])
st.markdown(T["ui"]["support_description"])

st.write("---")
st.header(T["ui"]["contact_subheader"])
st.markdown(T["ui"]["contact_description"])
