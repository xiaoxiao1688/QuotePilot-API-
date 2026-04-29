import hashlib
import secrets


def hash_password(password: str, salt: str | None = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    password_salt = f"{password}{salt}"
    password_hash = hashlib.sha256(password_salt.encode("utf-8")).hexdigest()
    return f"sha256:{salt}:{password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash.startswith("sha256:"):
        return False

    parts = stored_hash.split(":")
    if len(parts) != 3:
        return False

    _, salt, _ = parts
    expected_hash = hash_password(password, salt)
    return secrets.compare_digest(stored_hash, expected_hash)
