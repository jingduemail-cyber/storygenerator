# App/pages/03_Generate_&_Download.py
import streamlit as st
import time
from utils.processor import (
    generate_story_text,
    generate_story_title,
    extract_scenes_and_prompts,
    normalize_prompt,
    generate_audio_from_text_replicate,
    upload_audio_to_r2,
    generate_image_for_prompt_openai,
    create_storybook_pdf_bytes,
)
import json
from utils.ui_storage import hydrate_intake_from_localstorage_via_queryparam
import streamlit as st
import json
import streamlit.components.v1 as components
import streamlit as st
from utils.intake_codec import decode_intake

st.set_page_config(page_title="Generate & Download", layout="centered")
st.title("Generate & Download")

# Intake setup: hydrate from localStorage via query param, with fallback to session state
# Try session first
intake = st.session_state.get("intake")

# If missing, try query param
if not intake:
    token = st.query_params.get("intake")
    print("Received token from query params:", token)
    
    if token:
        try:
            intake = decode_intake(token)
            st.session_state.intake = intake
        except Exception:
            intake = None

if not intake:
    st.warning("No intake found. Please go back to Home and submit the form again.")
    st.page_link("Home.py", label="Go to Home", icon="🏠")
    st.stop()

# Display intake summary for confirmation
st.write("✅ Intake found.")
st.write(f"Selected pages: **{intake.get('page_length', 4)}**")
st.info("Click below to generate your storybook PDF. Please do not close this tab while generating.")

# Avoid regen on refresh
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = None

def do_generate():
    child_name = intake["child_name"]
    child_age = intake["child_age"]
    child_interest = intake["child_interest"]
    story_objective = intake["story_objective"]
    your_name = intake["your_name"]
    page_length = intake["page_length"]
    lang = intake.get("language", "en")

    # 1) Generate story + title
    story_text = generate_story_text(
        child_name, child_age, child_interest, story_objective, your_name,
        page_length=intake.get("page_length", 4),
    )
    story_title = generate_story_title(text=story_text).strip()

    # 2) Extract scenes/prompts
    expected = intake.get("page_length", 4)
    scenes, prompts = extract_scenes_and_prompts(story_text, expected_scenes=expected)

    # (Optional) If you want page_length to affect content density, do it inside your processor functions.
    # For now, we just store it in intake.

    # 3) Audio
    story_chunk = "\n\n".join(scenes)
    story_audio = generate_audio_from_text_replicate(story_chunk=story_chunk, lang=lang)
    story_audio_url = upload_audio_to_r2(
        audio_bytes=story_audio,
        filename=f"{story_title.replace(' ', '_')}_audio.mp3"
    )

    # 4) Cover
    cover_prompt = (
        f"Do not include any text in the image. "
        f"Design a children's storybook cover illustration related to the topic of '{child_interest}'. "
        f"Do not include any text or human-like characters in the image."
    )
    cover_b64 = generate_image_for_prompt_openai(cover_prompt)

    # 5) Scene images
    images_b64 = []
    
    for idx, p in enumerate(prompts):
        safe_prompt = normalize_prompt(p)

        try:
            img_b64 = generate_image_for_prompt_openai(p)
        except Exception:
            img_b64 = generate_image_for_prompt_openai(safe_prompt)

        images_b64.append(img_b64)

    # 6) PDF bytes
    pdf_bytes = create_storybook_pdf_bytes(
        title=story_title,
        author=your_name,
        cover_image_b64=cover_b64,
        scenes=scenes,
        images_b64=images_b64,
        story_audio_url=story_audio_url,
    )

    st.session_state.pdf_bytes = pdf_bytes
    st.session_state.pdf_filename = f"{story_title.replace(' ', '_')}.pdf"

# Generate button
if st.session_state.pdf_bytes is None:
    if st.button("Generate storybook"):
        with st.spinner("Generating... please keep this tab open"):
            do_generate()
        st.success("Generation complete. Download below.")

# Download button (enabled when ready)
if st.session_state.pdf_bytes:
    st.download_button(
        label="Download storybook PDF",
        data=st.session_state.pdf_bytes,
        file_name=st.session_state.pdf_filename or "storybook.pdf",
        mime="application/pdf",
    )