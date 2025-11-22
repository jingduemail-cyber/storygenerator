"""
Streamlit app: Personalized Children's Storybook -> PDF (2-page landscape spreads) -> Send via SendGrid

Features:
- Text generation with OpenAI ChatCompletion
- Per-scene image generation with OpenAI Image API
- Cover page with title + author + illustration
- Landscape "2-page spread" layout (each PDF page contains up to 2 scenes side-by-side)
- Automatic font scaling to avoid overflow
- Page numbers footer
- Send resulting PDF as an email attachment via SendGrid

Usage:
streamlit run app.py

"""

import os
import base64
import io
from typing import List, Tuple, Optional
from dotenv import find_dotenv, load_dotenv
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from openai import OpenAI
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Image as RLImage,
    Spacer,
    PageBreak,
    Flowable,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.utils import ImageReader
from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
import qrcode 
from PIL import Image as PILImage
from cloudflare_r2_upload import upload_audio_to_r2
from reportlab.pdfgen import canvas as canvas_module


# ------------------ Configuration & Helpers ------------------

# Running on streamlit cloud
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"] 
SENDGRID_API_KEY = st.secrets["SENDGRID_API_KEY"]
FROM_EMAIL = st.secrets["FROM_EMAIL"]

# # Initialize environment variables
# load_dotenv(find_dotenv())

# # Running locally to retrieve keys
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
# SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
# FROM_EMAIL = os.getenv("FROM_EMAIL")

# # Use environment variables or Streamlit secrets
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else None
# SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY") or st.secrets["SENDGRID_API_KEY"] if "SENDGRID_API_KEY" in st.secrets else None
# FROM_EMAIL = os.getenv("FROM_EMAIL") or st.secrets["FROM_EMAIL"] if "FROM_EMAIL" in st.secrets else None

if not OPENAI_API_KEY:
    st.warning("OpenAI API key not found. Please set OPENAI_API_KEY in env or Streamlit secrets.")
if not SENDGRID_API_KEY:
    st.warning("SendGrid API key not found. Please set SENDGRID_API_KEY in env or Streamlit secrets.")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# PDF layout constants
PAGE_SIZE = landscape(letter)
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE
MARGIN = 0.5 * inch
SPREAD_INNER_WIDTH = PAGE_WIDTH - 2 * MARGIN # PAGE_WIDTH - 2 * MARGIN
SPREAD_HEIGHT = PAGE_HEIGHT - 2 * MARGIN # PAGE_HEIGHT - 2 * MARGIN

# Each spread shows up to 2 scenes side-by-side. Each scene area width:
SCENE_WIDTH = SPREAD_INNER_WIDTH / 2 - 0.25 * inch  # small gutter
IMAGE_MAX_HEIGHT = SPREAD_HEIGHT * 0.55
TEXT_AREA_HEIGHT = SPREAD_HEIGHT * 0.35

# Styles
styles = getSampleStyleSheet()

# Default paragraph style; will be adjusted with font sizing when needed
BASE_PAR_STYLE = ParagraphStyle(
    "BaseScene",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=16, #14
    leading=18,
    alignment=TA_LEFT,
)

COVER_TITLE_STYLE = ParagraphStyle(
    "CoverTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=36,
    alignment=TA_CENTER,
    leading=42,
)

COVER_AUTHOR_STYLE = ParagraphStyle(
    "CoverAuthor",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=18,
    alignment=TA_CENTER,
)

AUTHOR_NOTE_STYLE = getSampleStyleSheet()["Normal"]
AUDIO_LINK_STYLE = getSampleStyleSheet()["Normal"]


# ------------------ OpenAI prompts & generation ------------------

def build_story_prompt(child_name: str, child_age: str, child_interest: str, story_objective: str, your_name: str) -> str:
    prompt = f"""
        You are a children's storybook generator. Create a personalized, age-appropriate, multi-scene illustrated storybook based on the input parameters below.
        
        Child name: {child_name}
        Child age: {child_age}
        Child interests: {child_interest}
        Story objective: {story_objective}
        
        For total scene count and word count, strictly follow these guidelines based on the child's age {child_age}:
        - For child's age from 0 - 2 years old, total scene count should be exactly 2 pages with total word count as close to 60 words as possible. 
        - For child's age from 2 - 4 years old, total scene count should be exactly 4 pages with total word count as close to 120 words as possible.
        - For child's age from 4 - 6 years old, total scene count should be exactly 6 pages with total word count as close to 180 words as possible.
        
        For each scene separated by a line containing only '---'. For each scene:
        - Provide 2-5 sentences of narrative tailored to {child_age}-old children, incorporating {child_interest} and aligned with the story objective of {story_objective}.
        - Each scene has maximum 5 lines in the page.
        - Include one short illustration prompt in parentheses on its own line immediately after the scene text. 
        
        For illustration prompts, follow these guidelines:
        - Each illustration prompt should describe only what each scene appears visually. No text inside the images.
        - Illustration prompts must always replaces “baby” with “gentle cartoon figure”.
        - Do NOT depict a real person or baby or include the child's name in the illustration prompt.
        - Illustrations of the fictional characters must be consistent throughout the entire scenes.

        Follow these for the story guidelines:
        - Scenes should begin with a captivating hook. 
        - Include a gentle problem and a positive resolution. 
        - Make sure the child interests shape the story world and plot.

        Adhere to these writing style guidelines:
        - Use clear language suitable for {child_age} children. Keep language simple, warm, and imaginative. 
        - Keep tone warm, soothing, and encouraging.
        - No scary or age-inappropriate content. 
        - No typos and smooth flows.
        
        Importantly, keep the scene count and word count exactly as specified above. USe simple words and short sentences suitable for {child_age} children.
        Lastly and very importantly again, strictly follow illustration prompt guidelines mentioned above. 
        
        Story starts now:
    """
    return prompt


def generate_story_text(child_name, child_age, child_interest, story_objective, your_name):
    prompt = build_story_prompt(child_name, child_age, child_interest, story_objective, your_name)

    response = openai_client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": "You are an artful and masterful expert specializing for children storytelling."},
            {"role": "user", "content": prompt}
           ],
        max_completion_tokens=3000,
        temperature=0.7,
    )
    text = response.choices[0].message.content
    return text

def generate_story_title(text: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": "You generate short, creative and catchy titles for children's storybook."},
            {"role": "user", "content": f"Please generate one short storybook title, remember only one title, for this story:\n\n{text}"}
        ],
        max_completion_tokens=50,
        temperature=0.7,
    )
    # title = response.choices[0].message.content.strip().strip('"')
    title = response.choices[0].message.content.strip()
    return title

def extract_scenes_and_prompts(story_text: str) -> Tuple[List[str], List[str]]:
    """Return (scene_texts, illustration_prompts) in order."""
    raw_scenes = [s.strip() for s in story_text.split('---') if s.strip()]
    scene_texts = []
    prompts = []
    for s in raw_scenes:
        # find last parentheses block as illustration prompt
        if '(' in s and ')' in s:
            before = s.rsplit('(', 1)[0].strip()
            prompt = s.rsplit('(', 1)[1].rsplit(')', 1)[0].strip()
            scene_texts.append(before)
            prompts.append(prompt)
        else:
            scene_texts.append(s)
            prompts.append('')
    return scene_texts, prompts

# ------------------ Image generation ------------------

def generate_image_for_prompt(prompt: str, size: str = "auto") -> str:
    """Return base64 PNG string from OpenAI image generation."""
    if not prompt:
        # return a tiny blank png base64 as fallback
        blank_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIW2NgYGD4DwABBAEA"
            "AqF5/AAAAABJRU5ErkJggg=="
        )
        return blank_png

    prompt  = (
        "Soft watercolor children-book illustration. Gentle pastel colors, round shapes, dreamy warm mood."
        "Create fully fictional, stylized cartoon characters with no realistic human features."
        "Do not depict any real or identifiable person, nor mention any children name in the prompt."
        + prompt
    )
    
    resp = openai_client.images.generate(
        model="gpt-image-1-mini",
        prompt=prompt,
        size=size,
        n=1,
        background="transparent",
    )
    b64 = resp.data[0].b64_json
    return b64

# ------------------ Audio generation ------------------
def generate_audio_from_text(story_chunk: str) -> str:
    audio_resp = openai_client.audio.speech.create(
        model="tts-1",
        input=story_chunk,
        voice="fable",  # or any of the preset voices you choose
    )
    audio_bytes = audio_resp.read()  # audio binary    
    return audio_bytes

# ------------------ PDF generation (2-page landscape spreads) ------------------

class PageNumCanvas(Flowable):
    """Utility flowable to draw page numbers in footer via build() callback."""
    def __init__(self, doc):
        super().__init__()
        self.doc = doc

    def draw(self):
        pass  # not used; page numbers are added via onPage callback

def _on_page(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.saveState()
    # --- GLOBAL PASTEL BACKGROUND (applies to ALL pages) ---
    canvas.setFillColorRGB(0.96, 0.98, 1.0)   # pastel blue
    # Examples:
    #   Pink:  c.setFillColorRGB(1.0, 0.95, 0.97)
    #   Mint:  c.setFillColorRGB(0.94, 1.0, 0.96)
    #   Cream: c.setFillColorRGB(1.0, 0.99, 0.94)
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    canvas.setFont('Helvetica', 10)
    canvas.drawCentredString(PAGE_WIDTH / 2.0, 0.3 * inch, text)
    canvas.restoreState()


def fit_paragraph_to_box(text: str, box_width: float, box_height: float, style: ParagraphStyle, min_font: int = 8, max_font: int = 18) -> Paragraph:
    """Return a Paragraph instance sized so that it fits inside box_width x box_height by adjusting font size."""
    # Try decreasing font size until it fits
    for fs in range(max_font, min_font - 1, -1):
        test_style = ParagraphStyle(
            name=f"tmp_{fs}",
            parent=style,
            fontSize=fs,
            leading=int(fs * 1.2),
        )
        para = Paragraph(text.replace('\n', '<br/>'), test_style)
        avail_w = box_width
        avail_h = box_height
        w, h = para.wrap(avail_w, avail_h)
        if h <= avail_h:
            return para
    # if nothing fits, return with min_font and rely on clipping/wrapping
    final_style = ParagraphStyle(name=f"tmp_min", parent=style, fontSize=min_font, leading=int(min_font * 1.2))
    return Paragraph(text.replace('\n', '<br/>'), final_style)

# QR code generation function
def generate_qr_code(url: str):
    """
    Convert URL into a QR code ReportLab Image().
    """
    qr = qrcode.QRCode(box_size=8, border=1)
    qr.add_data(url)
    qr.make(fit=True)

    qr_pil = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img_buffer = io.BytesIO()
    qr_pil.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # Convert into ReportLab Image
    qr_rl = RLImage(img_buffer, width=150, height=150)
    return qr_rl

# Compress base64 image
def compress_image(image_b64, quality=70):
    img_bytes = io.BytesIO(base64.b64decode(image_b64))
    img = PILImage.open(img_bytes)
    
    # If PNG has alpha channel (RGBA), convert safely
    if img.mode == "RGBA":
        background = PILImage.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # apply alpha channel
        img = background
    else:
        img = img.convert("RGB")

    compressed = io.BytesIO()
    img.save(compressed, format="JPEG", optimize=True, quality=quality)
    return compressed.getvalue()

# Create PDF with full-spread artwork
def create_storybook_pdf_bytes(
    title: str,
    author: str,
    cover_image_b64: str,
    scenes: List[str],
    images_b64: List[str],
    story_audio_url: str,
    page_size=PAGE_SIZE,
) -> bytes:
    """
    Final corrected full-spread generator.
    Important: SpreadFlowable.wrap uses the availWidth/availHeight ReportLab passes.
    """

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    story = []
    
    # -------------------------
    # SpreadFlowable (fixed)
    # -------------------------
    class SpreadFlowable(Flowable):
        """
        Full-page flowable that:
         - uses availWidth/availHeight provided by wrap()
         - scales & centers image inside the top portion
         - places scene text centered at bottom (or centered full-page if center_text=True)
        """

        def __init__(self, img_b64: Optional[str] = None, text: Optional[str] = None, center_text: bool = False):
            super().__init__()
            self.img_b64 = img_b64
            self.text = text
            self.center_text = center_text
            # will be set in wrap()
            self.width = None
            self.height = None

        def wrap(self, availWidth, availHeight):
            # CRITICAL: use the exact available size ReportLab provides.
            self.width = availWidth
            self.height = availHeight
            return (self.width, self.height)

        def _draw_scaled_image_in_box(self, c, image_b64: str, box_w: float, box_h: float):
            """
            Draw image centered inside a box of size box_w x box_h.
            Coordinates are relative to (0,0) bottom-left of the flowable.
            Returns (draw_w, draw_h, draw_x, draw_y).
            """
            if not image_b64:
                return 0, 0, 0, 0
            try:
                img_buf = io.BytesIO(base64.b64decode(image_b64))
                rlimg = RLImage(img_buf)
                iw, ih = rlimg.imageWidth, rlimg.imageHeight
                if iw <= 0 or ih <= 0:
                    return 0, 0, 0, 0
                scale = min(box_w / iw, box_h / ih, 1.0)
                draw_w = iw * scale
                draw_h = ih * scale
                draw_x = (self.width - draw_w) / 2.0
                # box origin assumed at y = (self.height - box_h) (top area)
                box_origin_y = self.height - box_h
                # center vertically within the box
                draw_y = box_origin_y + (box_h - draw_h) / 2.0
                rlimg.drawWidth = draw_w
                rlimg.drawHeight = draw_h
                rlimg.drawOn(c, draw_x, draw_y)
                return draw_w, draw_h, draw_x, draw_y
            except Exception:
                return 0, 0, 0, 0

        def draw(self):
            c = self.canv

            # avail dims (already set in wrap)
            avail_w = self.width
            avail_h = self.height

            # Reserve part of the flowable for image vs text:
            # image_area_h uses most of the height; leave room for bottom text
            image_area_h = avail_h * 0.78  # 78% top for image (tunable)
            text_area_h = avail_h - image_area_h

            # ---- Draw image (centered inside the top image_area) ----
            if self.img_b64:
                self._draw_scaled_image_in_box(c, self.img_b64, avail_w, image_area_h)

            # ---- Centered text (author note spread) ----
            if self.text and self.center_text:
                style = ParagraphStyle(
                    "AuthorNoteCentered",
                    parent=BASE_PAR_STYLE,
                    fontSize=20,
                    leading=26,
                    alignment=1,  # center
                )
                para = Paragraph(self.text.replace("\n", "<br/>"), style)
                max_w = avail_w * 0.9
                max_h = avail_h * 0.9
                tw, th = para.wrap(max_w, max_h)
                x = (avail_w - tw) / 2.0
                y = (avail_h - th) / 2.0
                para.drawOn(c, x, y)
                return

            # ---- Scene bottom text (non-centered) ----
            if self.text and not self.center_text:
                style = ParagraphStyle(
                    "SceneTextBottom",
                    parent=BASE_PAR_STYLE,
                    fontSize=16, #18
                    leading=22,
                    alignment=1,  # center horizontally
                )
                para = Paragraph(self.text.replace("\n", "<br/>"), style)
                max_text_w = avail_w * 0.9
                max_text_h = text_area_h * 0.95
                tw, th = para.wrap(max_text_w, max_text_h)

                # bottom margin inside flowable — draw just above bottom edge
                bottom_margin = avail_h * 0.05
                x = (avail_w - tw) / 2.0
                y = bottom_margin

                # Draw a light background for readability
                c.saveState()
                # c.setFillColorRGB(1, 1, 1, alpha=0.8)
                c.setFillColorRGB(0.96, 0.98, 1.0)   # Light pastel blue
                c.rect(x - 6, y - 6, tw + 12, th + 12, stroke=0, fill=1)
                c.restoreState()

                para.drawOn(c, x, y)

    # -----------------------------------------------------------------
    # Build the flow: cover -> scenes 
    # -----------------------------------------------------------------

    # --- Cover: full-spread cover image plus title + author    
    # Add cover page title + author
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(title, COVER_TITLE_STYLE))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"By {author}", COVER_AUTHOR_STYLE))
    story.append(PageBreak())
    
    # Add cover image spread
    story.append(SpreadFlowable(img_b64=cover_image_b64, text=None)) # Previous version
    # story.append(RLImage("cover_image.png", width=600, height=400)) # Testing this using RLImage
    story.append(PageBreak())

    # --- Scenes: use images_b64 and scenes lists (iterate by index)
    # We'll display one spread per image/text pair; be tolerant of unequal lengths.
    n_pairs = max(len(images_b64), len(scenes))
    for i in range(n_pairs):
        img_b64 = images_b64[i] if i < len(images_b64) else None
        txt = scenes[i] if i < len(scenes) else None
        story.append(SpreadFlowable(img_b64=img_b64, text=txt, center_text=False))
        story.append(PageBreak())

    # Build PDF (use your onPage callbacks as before)
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ------------------ SendGrid email ------------------

def send_email_with_attachment(send_to: str, subject: str, body: str, attachment_bytes: bytes, filename: str, from_email: str):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=send_to,
        subject=subject,
        html_content=body,
    )

    encoded = base64.b64encode(attachment_bytes).decode()
    attachedFile = Attachment(
        FileContent(encoded),
        FileName(filename),
        FileType("application/pdf"),
        Disposition("attachment"),
    )
    message.attachment = attachedFile

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    return response

# ------------------ Streamlit UI ------------------

st.set_page_config(page_title="Personalized Storybook Generator", layout="wide")
st.title("Personalized Children's Storybook")

with st.form(key="story_form"):
    st.header("Story Inputs")
    child_name = st.text_input("Child's Name", value="Bond")
    child_age = st.text_input("Child's Age", value="3 months old")
    child_interest = st.text_input("Child's Interests (Comma Separated)", value="Space, robots")
    story_objective = st.text_area("Story Objective / Moral", value="Encourage curiosity and kindness")
    your_name = st.text_input("Author Name", value="Mom & Dad")
    recipient_email = st.text_input("Recipient Email for PDF", value="")
    cover_prompt_override = st.text_input("Optional: Cover Illustration Prompt (Leave Blank to Auto-generate)", value="")
    # with_image_choice = st.radio(
    #     "Choose Storybook Format",
    #     ["Text + Images + Audio", "Text + Audio Only"],
    #     horizontal=True,
    # )
    submitted = st.form_submit_button("Generate Storybook")

if submitted:
    with st.spinner("Generating story..."):
        story_text = generate_story_text(child_name, child_age, child_interest, story_objective, your_name)
        story_title = generate_story_title(text = story_text)
    
    # Cover page title generation
    story_title = story_title.strip()
    st.success("Story title generated.")
    # st.write(f"## Story Title: {story_title}")

    # Extract scenes and illustration prompts
    scenes, prompts = extract_scenes_and_prompts(story_text)
    st.success("Story scenes generated.")
    # st.write("### Generated Scenes Preview")
    
    # # Display scenes and prompts - To be commented out later
    # for i, s in enumerate(scenes, start=1):
    #     st.markdown(f"**Scene {i}:** {s}")
    #     st.markdown(f"**Prompt {i}:** {prompts[i-1]}")
    
    # Audio generation
    with st.spinner("Generating story audio..."):
        story_audio = generate_audio_from_text(story_chunk = "\n\n".join(scenes))
        # st.success("Story audio generated.")
        
    # Upload audio to Cloudflare R2
    with st.spinner("Uploading audio to Cloudflare R2..."):
        story_audio_url = upload_audio_to_r2(audio_bytes = story_audio, filename=f"{story_title.replace(' ', '_')}_audio.mp3")
        st.success("Story audio generated.")
        # st.write(f"**Audio URL:** {story_audio_url}")
    
    # COVER illustration
    if cover_prompt_override.strip():
        cover_prompt = cover_prompt_override.strip()
    else:
        # Create a concise cover prompt based on title & author
        cover_prompt = f"Cover illustration for children's book titled '{story_title}'. Do not include any text in the image."
        # st.success("Story cover prompt generated.")
        # st.write(f"**Cover Illustration Prompt:** {cover_prompt}")

    with st.spinner("Generating cover image..."):
        cover_b64 = generate_image_for_prompt(cover_prompt, size="auto")
        # st.success("Cover image generated.")

    # Generate each scene image
    images_b64 = []
    with st.spinner("Generating scene images..."):
        for p in prompts:
            img_b64 = generate_image_for_prompt(p, size="auto")            
            images_b64.append(img_b64)

    st.success("Scene images generated.")

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

    st.success("PDF ready!")

    # st.download_button("Download Storybook PDF", data=pdf_bytes, file_name="storybook.pdf", mime="application/pdf")

    # Send via SendGrid if recipient provided
    if recipient_email:
        if not SENDGRID_API_KEY:
            st.error("SENDGRID_API_KEY not configured. Can't send email.")
        else:
            with st.spinner(f"Sending PDF to {recipient_email}"):
                subject = f"Your storybook: {story_title}"
                body = (
                    f"<p>Hello!</p>"
                    f"<p>We have generated the personalized storybook '{story_title}' for {child_name} in the PDF attachment. "
                    f"<br/>Click <a href='{story_audio_url}'>HERE</a> to download the audio book.</p>"
                    f"<p>✨ Your personalized children storybook is completely <strong>free to enjoy!</strong> "
                    f"<br/>If you love it and want to support the creator, a small donation would help keep the project growing and allow me to build even more magical features for families.</p>"
                    f"<p>💛 Support the project: <a href='https://gofund.me/4bfdc92c1'>HERE</a>. Every gesture counts and thank you!</p>"
                    f"<p>Best regards,<br/>The StoryGenerator Team</p>"
                )

                try:
                    resp = send_email_with_attachment(
                        send_to=recipient_email,
                        subject=subject,
                        body=body,
                        attachment_bytes=pdf_bytes,
                        filename="storybook.pdf",
                        from_email=FROM_EMAIL,
                    )
                    # st.success(f"Email sent (status {resp.status_code}).")
                    st.success(f"Email sent.")
                except Exception as e:
                    st.error(f"Failed to send email: {e}")

# End of file