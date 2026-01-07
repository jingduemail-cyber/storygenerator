# --- Import modules ---
import streamlit as st
from utils.processor import (
    build_story_prompt, 
    generate_story_text,
    generate_story_text_lang,
    generate_story_text_replicate, 
    generate_story_title, 
    generate_story_title_lang,
    generate_story_title_replicate,
    generate_story_text_openrouter,
    extract_scenes_and_prompts,
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
import time
from utils.ui import render_top_bar, get_app_title
from utils.language.loader import get_language
from pathlib import Path

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

with st.form(key="story_form"):
    child_name = st.text_input(T["ui"]["child_name"])
    child_age = st.text_input(T["ui"]["child_age"])
    child_interest = st.text_input(T["ui"]["interests"])
    story_objective = st.text_area(T["ui"]["objective"])
    your_name = st.text_input(T["ui"]["author_name"])
    recipient_email = st.text_input(T["ui"]["email"])
    submitted = st.form_submit_button(T["ui"]["generate"])

if submitted:
    if not recipient_email or not child_name:
        st.error(T["ui"]["error_missing_fields"])
    else:
        st.success(T["ui"]["submit_success"])
        
        intake = {
        "child_name": child_name,
        "child_age": child_age,
        "child_interest": child_interest,
        "story_objective": story_objective,
        "your_name": your_name,
        "recipient_email": recipient_email,
        "language": st.session_state.lang
        }
        
        lang = intake.get("language", "en")
        
        with st.spinner(T["ui"]["spinner"]):
            # Build story and title
            story_text = generate_story_text(child_name, child_age, child_interest, story_objective, your_name)
            story_title = generate_story_title(text = story_text)
            
            # # Test with multiple language support for prompting
            # story_text = generate_story_text_lang(intake)
            # story_title = generate_story_title_lang(text = story_text, language=lang)
            
            story_title = story_title.strip()
            scenes, prompts = extract_scenes_and_prompts(story_text)
            
            # Generate audio
            story_chunk = "\n\n".join(scenes)
            # story_chunk = sanitize_text_for_tts(story_chunk)

            story_audio = generate_audio_from_text_replicate(story_chunk = story_chunk)
            story_audio_url = upload_audio_to_r2(audio_bytes = story_audio, filename=f"{story_title.replace(' ', '_')}_audio.mp3")
            
            # Genarate cover image
            cover_prompt = f"Do not include any text in the image. Design a children's storybook cover illustration related to the topic of '{child_interest}'. Do not include any text or human-like characters in the image."
            cover_b64 = generate_image_for_prompt_openai(cover_prompt)

            # Generate scene images
            images_b64 = []
            for p in prompts:
                img_b64 = generate_image_for_prompt_openai(p)
                images_b64.append(img_b64)

            # Create PDF bytes
            pdf_bytes = create_storybook_pdf_bytes(
                title=story_title,
                author=your_name,
                cover_image_b64=cover_b64,
                scenes=scenes,
                images_b64=images_b64,
                story_audio_url=story_audio_url,
            )

            # Send via SendGrid
            if recipient_email:
                subject = T["email"]["subject"]
                audio_link_html = build_audio_link(story_audio_url=story_audio_url, lang=intake["language"])
                
                if lang == "zh":
                    body = T["email"]["body"]
                else:
                    body = T["email"]["body"].format(audio_link=audio_link_html)

                try:
                    resp = send_email_with_attachment(
                        send_to=recipient_email,
                        subject=subject,
                        body=body,
                        attachment_bytes=pdf_bytes,
                        filename=T["email"]["file_name"],
                    )
                    st.success(T["ui"]["success"])
                    
                except Exception as e:
                    print(T["email"]["send_failure"].format(e=e))
            

st.write("---")
st.markdown(T["ui"]["home_help"])

# End of file