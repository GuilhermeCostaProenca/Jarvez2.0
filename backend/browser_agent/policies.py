from __future__ import annotations

from urllib.parse import urlparse


def normalize_allowed_domains(raw_domains: list[object] | None) -> list[str]:
    if not isinstance(raw_domains, list):
        return []
    normalized: list[str] = []
    for item in raw_domains:
        text = str(item or "").strip().lower()
        if not text:
            continue
        parsed = urlparse(text if "://" in text else f"https://{text}")
        host = (parsed.netloc or parsed.path).strip().lower()
        if not host:
            continue
        if host not in normalized:
            normalized.append(host)
    return normalized


def validate_browser_request(request: str, allowed_domains: list[str]) -> str | None:
    if not request.strip():
        return "Pedido do browser agent ausente."
    if not allowed_domains:
        return "O browser agent exige allowed_domains explicitos."
    return None
