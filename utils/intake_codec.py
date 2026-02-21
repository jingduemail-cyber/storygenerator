import json, base64

def encode_intake(intake: dict) -> str:
    raw = json.dumps(intake, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

def decode_intake(token: str) -> dict:
    pad = "=" * (-len(token) % 4)
    raw = base64.urlsafe_b64decode((token + pad).encode("ascii")).decode("utf-8")
    return json.loads(raw)