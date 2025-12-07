# --- Import modules ---
import streamlit as st
from utils.processor import (
    build_story_prompt, 
    generate_story_text,
    generate_story_text_replicate, 
    generate_story_title, 
    generate_story_title_replicate,
    extract_scenes_and_prompts,
    generate_audio_from_text,
    get_r2_client, 
    upload_audio_to_r2, 
    generate_image_for_prompt, 
    create_storybook_pdf_bytes, 
    send_email_with_attachment,
)


# --- Set up global page formatting and styles ---
st.set_page_config(
    page_title="Personalized Storybook Generator",
    page_icon="📚",
    layout="centered"
)

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

import streamlit as st

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
st.set_page_config(page_title="Storybook Generator", page_icon="📘")

# Optional global styling
st.markdown("<h1 class='main-title'>📘 Personalized Storybook Generator</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Create a magical, personalized storybook for your child</p>", unsafe_allow_html=True)

st.write("---")

st.header("✨ Create Your Storybook")
st.write("Please fill in ALL details below. You will receive the final storybook by email.")

with st.form(key="story_form"):
    st.header("Story Inputs")
    child_name = st.text_input("Child's Name", placeholder="Enter the child's name...")
    child_age = st.text_input("Child's Age", placeholder="Example - 3 months old...")
    child_interest = st.text_input("Child's Interests", placeholder="Example - space, robots, friendship...")
    story_objective = st.text_area("Story Objective", placeholder="Example - encourage curiosity and kindness...")
    your_name = st.text_input("Author Name", placeholder="Example - Mom & Dad")
    recipient_email = st.text_input("Author Email", placeholder="Enter your email to receive the storybook...")
    submitted = st.form_submit_button("Generate Storybook")

if submitted:
    if not recipient_email or not child_name:
        st.error("Please fill in at least the child's name and your email.")
    else:
        st.success(
            "Thank you! We’re generating your magical story now. This may take a moment and please do not close this page."
            "Please expect an email in about 15 minutes. If it's not in your inbox, kindly check your Spam or Promotions folder."
        )
        
        with st.spinner("Generating story..."):
            # Build story and title
            story_text = generate_story_text(child_name, child_age, child_interest, story_objective, your_name)
            story_title = generate_story_title(text = story_text)
            
            # # Test with Replicate text model
            # story_text = generate_story_text_replicate(child_name, child_age, child_interest, story_objective, your_name) 
            # story_title = generate_story_title_replicate(text = story_text)
            
            
            story_title = story_title.strip()
            print(f"Generated story title: {story_title}")

            # Extract scenes and illustration prompts
            scenes, prompts = extract_scenes_and_prompts(story_text)
            st.success("Text generation complete!")
            print(f"Extracted {len(scenes)} scenes and {len(prompts)} prompts.")
            
        # Audio generation
        with st.spinner("Generating story audio..."):
            # story_audio = generate_audio_from_text(story_chunk = "\n\n".join(scenes))
            # story_audio_url = upload_audio_to_r2(audio_bytes = story_audio, filename=f"{story_title.replace(' ', '_')}_audio.mp3")
            story_audio_url = "www.google.com"  # Temporary for testing
            st.success("Audio generation complete!")
            print(f"Uploaded audio URL: {story_audio_url}")
        
        # Cover illustration generation
        cover_prompt = f"Do not include any text in the image. Design a cover illustration for children's book titled '{story_title}'. Do not include any text in the image."

        with st.spinner("Generating cover image..."):
            cover_b64 = generate_image_for_prompt(cover_prompt, size="small")
            st.success("Cover image generated.")

        # Generate each scene image
        images_b64 = []
        with st.spinner("Generating scene images..."):
            for p in prompts:
                img_b64 = generate_image_for_prompt(p, size="small")            
                images_b64.append(img_b64)
        
        st.success("Scene images generated.")
        print("Scene images generated.")

        # Create PDF bytes
        with st.spinner("Composing PDF..."):
            pdf_bytes = create_storybook_pdf_bytes(
                title=story_title,
                author=your_name,
                cover_image_b64=cover_b64,
                scenes=scenes,
                images_b64=images_b64,
                story_audio_url=story_audio_url,
            )

        st.success("PDF composition complete!")
        print("PDF ready!")

        # Send via SendGrid
        if recipient_email:
            with st.spinner(f"Sending PDF to {recipient_email}"):
                subject = f"Your storybook: {story_title}"
                body = (
                    f"<p>Hello!</p>"
                    f"<p>We have generated the personalized storybook '{story_title}' for {child_name} in the PDF attachment."
                    f"<br/>Click <a href='{story_audio_url}'>HERE</a> to download the audio book.</p>"
                    f"<p>✨ Your personalized children storybook is completely <strong>free to enjoy!</strong> Hope you like it!</p>"
                    f"<p>Best regards,<br/>The StoryGenerator Team</p>"
                )

                try:
                    resp = send_email_with_attachment(
                        send_to=recipient_email,
                        subject=subject,
                        body=body,
                        attachment_bytes=pdf_bytes,
                        filename="storybook.pdf",
                    )
                    st.success(f"Email sent to {recipient_email}! If you don't see it, please check your spam/junk folder.")
                    print(f"Email sent (status {resp.status_code}).")
                except Exception as e:
                    print(f"Failed to send email: {e}")

st.write("---")
st.markdown("👉 Need help? Visit the **How To Use** page in the sidebar.")

# End of file