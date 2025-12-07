# --- Store all backend functions here ---

"""
Streamlit app: Personalized Children's Storybook -> PDF (2-page landscape spreads) -> Send via SendGrid

Features:
- Text generation with OpenAI ChatCompletion
- Per-scene image generation with OpenAI Image API
- Cover page with title + author + illustration
- Landscape "2-page spread" layout (each PDF page contains up to 2 scenes side-by-side)
- Automatic font scaling to avoid overflow
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
from reportlab.pdfgen import canvas as canvas_module
import boto3
import uuid
import time
import logging
from multiprocessing import Process, Queue
import replicate






# --- Import API keys ---
# Initialize environment variables
load_dotenv(find_dotenv())
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Use environment variables or Streamlit secrets
OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY") or 
    (st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else st.warning("OpenAI API key not found."))
)

SENDGRID_API_KEY = (
    os.getenv("SENDGRID_API_KEY") or 
    (st.secrets["SENDGRID_API_KEY"] if "SENDGRID_API_KEY" in st.secrets else st.warning("SendGrid API key not found."))
)

FROM_EMAIL = (
    os.getenv("FROM_EMAIL") or 
    (st.secrets["FROM_EMAIL"] if "FROM_EMAIL" in st.secrets else st.warning("Email distributor key key not found."))
)

# -------------------------------------------------------------
# Config & defaults
# -------------------------------------------------------------
IMAGE_PROVIDER = (
    os.getenv("IMAGE_PROVIDER") or
    (st.secrets["IMAGE_PROVIDER"] if "IMAGE_PROVIDER" in st.secrets else st.warning("Image provider setting not found."))
)

REPLICATE_API_TOKEN = (
    os.getenv("REPLICATE_API_TOKEN") or
    (st.secrets["REPLICATE_API_TOKEN"] if "REPLICATE_API_TOKEN" in st.secrets else st.warning("Replicate API key not found."))
)

LOCAL_MODEL_ID = os.getenv("LOCAL_MODEL_ID", "stabilityai/sdxl-turbo")

REPLICATE_MODEL_ID = (
    os.getenv("REPLICATE_MODEL_ID") or
    (st.secrets["REPLICATE_MODEL_ID"] if "REPLICATE_MODEL_ID" in st.secrets else st.warning("Replicate image model id not found."))
)

REPLICATE_TEXT_MODEL_ID = (
    os.getenv("REPLICATE_TEXT_MODEL_ID") or
    (st.secrets["REPLICATE_TEXT_MODEL_ID"] if "REPLICATE_TEXT_MODEL_ID" in st.secrets else st.warning("Replicate text model id not found."))
)

LOCAL_MAX_SECONDS = float(os.getenv("LOCAL_MAX_SECONDS", "25.0"))
HARD_TIMEOUT_SECONDS = int(os.getenv("HARD_TIMEOUT_SECONDS", "300"))   # hard kill: 5 minutes

DEFAULT_SIZE = (768, 768)
FALLBACK_SIZE = (512, 512)
DEFAULT_STEPS = 4
FALLBACK_STEPS = 2
DEFAULT_PROMPT_STRENGTH = 1.2

# blank PNG base64 (1x1 transparent)
_BLANK_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIW2NgYGD4DwABBAEA"
    "AqF5/AAAAABJRU5ErkJggg=="
)

_local_pipe = None
_replicate_client = None




# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------ Configuration & Helpers ------------------
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
        - For child's age from 0 - 2 years old, total scene count should be exactly 2 pages with total word count as close to 50 words as possible. 
        - For child's age from 2 - 4 years old, total scene count should be exactly 3 pages with total word count as close to 75 words as possible.
        - For child's age from 4 - 6 years old, total scene count should be exactly 4 pages with total word count as close to 100 words as possible.
        
        For each scene separated by a line containing only '---'. For each scene:
        - Provide 2-5 sentences of narrative tailored to {child_age}-old children, incorporating {child_interest} and aligned with the story objective of {story_objective}.
        - Each scene has preferably 3 lines and maximum 5 lines in the page.
        - Include one short illustration prompt in parentheses on its own line immediately after the scene text. 
        
        For illustration prompts, follow these guidelines:
        - Each illustration prompt should describe only what each scene appears visually. No text inside the images.
        - Illustration prompts must always replaces “baby” with “gentle cartoon figure”.
        - Do NOT depict a real person or baby or include the child's name in the illustration prompt.
        - Illustrations of the fictional characters must be consistent throughout the entire scenes.
        - Use soft watercolor children-book illustration style. Gentle pastel colors, round shapes, dreamy warm mood, friendly, safe for children, whimsical, cartoon for all images.

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
        Lastly and very importantly again, strictly follow illustration prompt guidelines mentioned above. Use soft watercolor children-book illustration style. Gentle pastel colors, round shapes, dreamy warm mood, friendly, safe for children, whimsical, cartoon for all images.
        
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

# Generate text using Replicate model REPLICATE_TEXT_MODEL_ID
def generate_story_text_replicate(child_name, child_age, child_interest, story_objective, your_name):
    user_prompt = build_story_prompt(child_name, child_age, child_interest, story_objective, your_name)
    
    system_prompt = (
        "You are a children's storybook writer. Your job is to write warm, gentle, "
        "imaginative stories suitable for young children. Use soft pacing, simple vocabulary, "
        "and emotional clarity. Avoid scary elements, violence, or complex plots. "
        "Use pastel, dreamlike imagery. Keep tone uplifting and magical."
    )
    
    try:
        output = replicate.run(
            REPLICATE_TEXT_MODEL_ID,
            input={
                "prompt": f"<s>[INST]<<SYS>>{system_prompt}<</SYS>>{user_prompt}[/INST]",
                "max_new_tokens": 600,
                "temperature": 0.8,
                "top_p": 0.9,
                "presence_penalty": 0.2,
                "frequency_penalty": 0.2,
                "min_tokens": 100,
            },
        )

        # replicate returns a generator of text chunks → join them
        if isinstance(output, list):
            return "".join(output).strip()
        elif isinstance(output, str):
            return output.strip()
        else:
            return str(output)

    except Exception as e:
        return f"ERROR generating story: {e}"


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
    title = response.choices[0].message.content.strip()
    return title

def generate_story_title_replicate(text: str) -> str:
    title_user_prompt = f"Please generate one short catchy storybook title, remember only one title, for this story:\n\n{text}"
    
    title_system_prompt = (
        "You are a children's storybook writer. Your job is to generate short, "
        "creative and catchy titles for children's storybook. Use soft pacing, simple vocabulary."
    )
    
    try:
        title_output = replicate.run(
            REPLICATE_TEXT_MODEL_ID,
            input={
                "prompt": f"<s>[INST]<<SYS>>{title_system_prompt}<</SYS>>{title_user_prompt}[/INST]",
                "max_new_tokens": 60,
                "temperature": 0.8,
            },
        )

        # replicate returns a generator of text chunks → join them
        if isinstance(title_output, list):
            return "".join(title_output).strip()
        elif isinstance(title_output, str):
            return title_output.strip()
        else:
            return str(title_output)

    except Exception as e:
        return f"ERROR generating story: {e}"



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

# ------------------ Audio generation & storage ------------------
def generate_audio_from_text(story_chunk: str) -> str:
    audio_resp = openai_client.audio.speech.create(
        model="tts-1",
        input=story_chunk,
        voice="fable",  # or any of the preset voices you choose
    )
    audio_bytes = audio_resp.read()  # audio binary    
    return audio_bytes

def get_r2_client():
    """Create boto3 client for Cloudflare R2 using Streamlit secrets."""
    account_id = st.secrets["r2"]["account_id"]
    access_key = st.secrets["r2"]["access_key"]
    secret_key = st.secrets["r2"]["secret_key"]

    session = boto3.session.Session()
    client = session.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    return client


def upload_audio_to_r2(audio_bytes: bytes, filename: str = None) -> str:
    """
    Uploads audio bytes to Cloudflare R2 and returns a public URL.
    """
    bucket_name = st.secrets["r2"]["bucket_name"]
    public_base_url = st.secrets["r2"]["public_base_url"]

    # Auto-generate filename if not provided
    if filename is None:
        filename = f"{uuid.uuid4()}.mp3"

    client = get_r2_client()

    # Upload audio
    client.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=audio_bytes,
        ContentType="audio/mpeg"
    )

    # Public, direct access URL
    public_url = f"{public_base_url}/{filename}"

    return public_url

# ------------------ Image generation ------------------



# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------
def _pil_to_b64(img: PILImage.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _strengthen_prompt(prompt: str, strength: float) -> str:
    if strength <= 1.0:
        return prompt
    anchor = (
        "Soft watercolor children-book illustration. Gentle pastel colors, "
        "round shapes, dreamy warm mood."
    )
    repeats = min(3, int(round((strength - 1.0) * 2)))
    return f"{anchor} " + " ".join([anchor] * repeats) + " " + prompt


# -------------------------------------------------------------
# LOCAL SDXL-TURBO PIPELINE
# -------------------------------------------------------------
def _load_local_pipe():
    global _local_pipe
    if _local_pipe is not None:
        return _local_pipe

    from diffusers import AutoPipelineForText2Image
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    logging.info(f"Loading SDXL-Turbo locally ({LOCAL_MODEL_ID})…")
    pipe = AutoPipelineForText2Image.from_pretrained(
        LOCAL_MODEL_ID,
        use_safetensors=True,
    )

    try:
        pipe = pipe.to(device, dtype=dtype)
    except:
        pipe = pipe.to(device)

    _local_pipe = pipe
    return pipe


# -------------------------------------------------------------
# LOCAL GENERATION (with timeout wrapper)
# -------------------------------------------------------------
def _local_generate_worker(prompts, width, height, steps, strength, out_q):
    """Executed inside subprocess. Produces list of PIL images."""
    try:
        pipe = _load_local_pipe()
        prompts_prepped = [_strengthen_prompt(p, strength) for p in prompts]

        try:
            result = pipe(
                prompts_prepped,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=0.0,
            )
            imgs = result.images
        except TypeError:
            # fallback sequential
            imgs = []
            for pp in prompts_prepped:
                r = pipe(pp, width=width, height=height,
                         num_inference_steps=steps, guidance_scale=0.0)
                imgs.append(r.images[0])

        out_q.put(imgs)
    except Exception as e:
        out_q.put(e)


def _generate_local_with_timeout(prompts, width, height, steps, strength):
    """
    Spawns a subprocess to allow safe timeout+kill.
    """
    q = Queue()
    p = Process(
        target=_local_generate_worker,
        args=(prompts, width, height, steps, strength, q),
    )

    p.start()
    p.join(HARD_TIMEOUT_SECONDS)

    if p.is_alive():
        logging.error("Local SDXL process stuck → FORCE TERMINATING.")
        p.terminate()
        p.join()
        return None  # main code will fallback

    result = q.get()
    if isinstance(result, Exception):
        raise result
    return result  # list of PIL images


# -------------------------------------------------------------
# REPLICATE PROVIDER
# -------------------------------------------------------------
def _get_replicate_client():
    global _replicate_client
    if _replicate_client:
        return _replicate_client

    import replicate
    if not REPLICATE_API_TOKEN:
        raise RuntimeError("REPLICATE_API_TOKEN missing")
    _replicate_client = replicate
    _replicate_client.Client(api_token=REPLICATE_API_TOKEN)
    return _replicate_client


def _generate_replicate(prompt, width, height, strength):
    import requests

    client = _get_replicate_client()
    pp = _strengthen_prompt(prompt, strength)

    output = client.run(
        REPLICATE_MODEL_ID,
        input={"prompt": pp, "width": width, "height": height},
    )

    url = output[0] if isinstance(output, list) else output
    img = PILImage.open(io.BytesIO(requests.get(url).content)).convert("RGBA")
    return img


# -------------------------------------------------------------
# PUBLIC BATCH API
# -------------------------------------------------------------
def generate_images_for_prompts(
    prompts: List[str],
    prompt_strength: float = DEFAULT_PROMPT_STRENGTH,
    prefer_size: Optional[tuple] = None,
    prefer_steps: Optional[int] = None,
) -> List[str]:

    if not prompts:
        return []

    width, height = prefer_size if prefer_size else DEFAULT_SIZE
    steps = prefer_steps if prefer_steps is not None else DEFAULT_STEPS

    # ---------------------------------------------------------
    # LOCAL MODE
    # ---------------------------------------------------------
    if IMAGE_PROVIDER == "local":
        start = time.time()
        imgs = _generate_local_with_timeout(
            prompts, width, height, steps, prompt_strength
        )
        elapsed = time.time() - start

        # hard timeout => None returned => fallback
        if imgs is None:
            logging.error("Hard timeout triggered — using fallback size.")
            imgs = _generate_local_with_timeout(
                prompts, FALLBACK_SIZE[0], FALLBACK_SIZE[1], FALLBACK_STEPS, prompt_strength
            )

        # soft fallback if slow
        if elapsed > LOCAL_MAX_SECONDS:
            logging.warning("Slow local generation — retrying with smaller parameters.")
            imgs = _generate_local_with_timeout(
                prompts, FALLBACK_SIZE[0], FALLBACK_SIZE[1], FALLBACK_STEPS, prompt_strength
            )

        if imgs is None:
            return [_BLANK_PNG_B64 for _ in prompts]

        return [_pil_to_b64(img) for img in imgs]

    # ---------------------------------------------------------
    # REPLICATE MODE (local or cloud)
    # ---------------------------------------------------------
    elif IMAGE_PROVIDER == "replicate":
        out = []
        for p in prompts:
            try:
                print(f"Generating image for prompt: {p}")
                img = _generate_replicate(p, width, height, prompt_strength)
                out.append(_pil_to_b64(img))
                time.sleep(10)  # to avoid rate limits
                
            except:
                out.append(_BLANK_PNG_B64)
                print(f"Failed to generate image for prompt: {p} and returned blank image.")
        return out

    else:
        raise ValueError(f"Unknown IMAGE_PROVIDER: {IMAGE_PROVIDER}")


# -------------------------------------------------------------
# SINGLE IMAGE (backwards compatible)
# -------------------------------------------------------------
def generate_image_for_prompt(prompt: str, size: str = "small") -> str:
    if not prompt:
        print("No prompt provided, returning blank image.")
        return _BLANK_PNG_B64

    size_map = {
        # "auto": DEFAULT_SIZE,
        "auto": (768, 768),
        "small": FALLBACK_SIZE,
        # "medium": DEFAULT_SIZE,
        "large": (1024, 1024),
    }
    width, height = size_map.get(size, DEFAULT_SIZE)
    print(f"Selected size: {size} ({width}x{height})")
    print(f"Generating single image with size: {size} ({width}x{height})")

    result = generate_images_for_prompts(
        [prompt],
        prompt_strength=DEFAULT_PROMPT_STRENGTH,
        prefer_size=(width, height),
    )
    return result[0]





# ------------------ PDF generation (2-page landscape spreads) ------------------
# Utility flowable to draw page numbers in footer - not used currently
class PageNumCanvas(Flowable):
    """Utility flowable to draw page numbers in footer via build() callback."""
    def __init__(self, doc):
        super().__init__()
        self.doc = doc

    def draw(self):
        pass  # not used; page numbers are added via onPage callback

# onPage callback to add page numbers and background - not used currently
def _on_page(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.saveState()
    # --- GLOBAL PASTEL BACKGROUND (applies to ALL pages) ---
    canvas.setFillColorRGB(0.96, 0.98, 1.0)   # pastel blue
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    canvas.setFont('Helvetica', 10)
    canvas.drawCentredString(PAGE_WIDTH / 2.0, 0.3 * inch, text)
    canvas.restoreState()

# Utility to fit paragraph text into a box by adjusting font size - not used currently
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

# QR code generation function - not used currently
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

# Compress base64 image - not used currently
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

def send_email_with_attachment(send_to: str, subject: str, body: str, attachment_bytes: bytes, filename: str, from_email=None):
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