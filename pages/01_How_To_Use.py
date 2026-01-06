# --- Set up global page formatting and styles ---
import streamlit as st
from utils.ui import render_top_bar, get_app_title
from utils.language.loader import get_language
from pathlib import Path

PAGE_ID = "how_to_use"

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

# --- Set up the how to use and faq page ---
st.write("---")
st.header(T["ui"]["how_subtitle"])
st.markdown(T["ui"]["how_steps"])

st.write("---")
st.header(T["ui"]["faq_subtitle"])

with st.expander(T["ui"]["faq_cost_question"]):
    st.write(T["ui"]["faq_cost_answer"])

with st.expander(T["ui"]["faq_time_question"]):
    st.write(T["ui"]["faq_time_answer"])

with st.expander(T["ui"]["faq_delivery_question"]):
    st.write(T["ui"]["faq_delivery_answer"])

with st.expander(T["ui"]["faq_delivery_error_question"]):
    st.write(T["ui"]["faq_delivery_error_answer"])

with st.expander(T["ui"]["faq_data_question"]):
    st.write(T["ui"]["faq_data_answer"])

with st.expander(T["ui"]["faq_volume_question"]):
    st.write(T["ui"]["faq_volume_answer"])