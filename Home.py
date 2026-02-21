# --- Import modules ---
import streamlit as st
from utils.processor import (
    build_story_prompt, 
    generate_story_text,
    generate_story_text_lang,
    generate_story_text_replicate, 
    generate_story_text_replicate_gpt5nano,
    generate_story_title, 
    generate_story_title_lang,
    generate_story_title_replicate,
    generate_story_title_replicate_gpt5nano,
    generate_story_text_openrouter,
    extract_scenes_and_prompts,
    normalize_prompt,
    generate_audio_from_text,
    sanitize_text_for_tts,
    generate_audio_from_text_replicate,
    get_r2_client, 
    build_audio_link,
    upload_audio_to_r2, 
    generate_image_for_prompt, 
    generate_image_for_prompt_openai,
    create_storybook_pdf_bytes, 
    send_email_with_attachment,
)
from utils.ui_storage import save_intake_to_localstorage
from utils.url_tools import add_query_params
from utils.intake_codec import encode_intake, decode_intake
import time
from utils.ui import render_top_bar, get_app_title
from utils.language.loader import get_language
from pathlib import Path
import secrets

PAGE_ID = "home"

if "lang" not in st.session_state:
    st.session_state.lang = "en"

params = st.query_params

if "lang" in params:
    st.session_state.lang = params["lang"]

T = get_language(st.session_state.lang)

# --- Set up global page formatting and styles ---
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

# Inject CSS to style placeholder + input
st.markdown("""
<style>
/* Placeholder text styling */
input::placeholder {
    font-style: italic;
    color: #888888 !important;
}

/* When typing, override text style */
input {
    font-style: normal !important;
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# --- Set up home and user intake page ---
st.write("---")
st.write(T["ui"]["instructions"])

# Session state init
if "intake" not in st.session_state:
    st.session_state.intake = None
if "page_length" not in st.session_state:
    st.session_state.page_length = 4

PAYPAL_LINKS = {
    4: st.secrets["paypal"]["link_4"],
    8: st.secrets["paypal"]["link_8"],
    12: st.secrets["paypal"]["link_12"],
}

with st.form(key="story_form"):
    child_name = st.text_input(T["ui"]["child_name"])
    child_age = st.text_input(T["ui"]["child_age"])
    child_interest = st.text_input(T["ui"]["interests"])
    story_objective = st.text_area(T["ui"]["objective"])
    your_name = st.text_input(T["ui"]["author_name"])
    recipient_email = st.text_input(T["ui"]["email"])

    # NEW: page length selector
    page_length = st.radio(
        T["ui"]["page_length"],
        options=[4, 8, 12],
        index=[4, 8, 12].index(st.session_state.page_length),
        horizontal=True,
        help=T["ui"]["help"]
    )

    submitted = st.form_submit_button("Continue to Payment")

# Save intake only (no generation here)
if submitted:
    if not recipient_email or not child_name:
        st.error(T["ui"]["error_missing_fields"])
    else:
        st.session_state.page_length = page_length
        st.session_state.intake = {
            "child_name": child_name,
            "child_age": child_age,
            "child_interest": child_interest,
            "story_objective": story_objective,
            "your_name": your_name,
            "recipient_email": recipient_email,
            "language": st.session_state.lang,
            # pass to your pipeline if needed
            "page_length": page_length,
        }
        
        # Build per payment return URL
        intake = st.session_state.intake
        token = encode_intake(intake)
        BASE_URL = st.secrets["app_base_url"]
        download_url = f"{BASE_URL}/Download?intake={token}"
        paypal_url = PAYPAL_LINKS[st.session_state.page_length]
        paypal_url = add_query_params(paypal_url, {"return": download_url})
        st.success("Intake saved. Please proceed to payment.")

# Payment section (only shown after intake saved)
if st.session_state.intake:
    st.write("---")
    st.subheader("Step 2 — Pay with PayPal")
    price_map = {4: "$1.00", 8: "$1.49", 12: "$1.99"}
    st.info(f"You selected **{st.session_state.page_length} pages** ({price_map[st.session_state.page_length]}). After payment, please go to the Download page to generate and download your PDF.")
    paypal_url = PAYPAL_LINKS[st.session_state.page_length]
    st.link_button("Pay", paypal_url)