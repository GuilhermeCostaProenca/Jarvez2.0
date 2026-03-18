from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> int:
    backend_dir = Path(__file__).resolve().parent
    load_env_file(backend_dir / ".env")

    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY ausente. Gere sua key em https://elevenlabs.io e preencha backend/.env."
        )

    from elevenlabs import ElevenLabs

    client = ElevenLabs(api_key=api_key)
    response = client.voices.get_all()
    voices = getattr(response, "voices", None)
    if voices is None:
        raise RuntimeError("Resposta inesperada ao listar vozes da ElevenLabs.")

    print(f"Vozes ElevenLabs encontradas: {len(voices)}")
    for voice in list(voices)[:10]:
        voice_id = getattr(voice, "voice_id", None) or getattr(voice, "id", None)
        name = getattr(voice, "name", None) or "sem-nome"
        print(f"- {name} ({voice_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
