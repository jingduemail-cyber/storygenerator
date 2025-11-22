import boto3
import uuid
import streamlit as st

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
