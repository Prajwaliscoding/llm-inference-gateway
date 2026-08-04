import secrets
import hashlib

def generate_api_key() -> str:
    return secrets.token_urlsafe(32)

def hash_api_key(raw_key:str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()