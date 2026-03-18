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


def resolve_kokoro_assets(base_dir: Path) -> tuple[Path, Path]:
    configured = os.getenv("KOKORO_MODEL_PATH", "./models/kokoro").strip() or "./models/kokoro"
    model_root = (base_dir / configured).resolve()
    if model_root.is_file():
        model_file = model_root
        voices_file = next(model_root.parent.glob("*.bin"), None)
    else:
        model_file = next(model_root.glob("*.onnx"), None)
        voices_file = next(model_root.glob("*.bin"), None)
    if model_file is None or voices_file is None:
        raise FileNotFoundError(
            f"Kokoro assets nao encontrados em {model_root}. Esperado .onnx e .bin."
        )
    return model_file, voices_file


def main() -> int:
    backend_dir = Path(__file__).resolve().parent
    load_env_file(backend_dir / ".env")

    import onnxruntime as ort
    import soundfile as sf
    from kokoro_onnx import Kokoro

    requested_device = (os.getenv("KOKORO_DEVICE", "cuda").strip() or "cuda").lower()
    requested_provider = (
        "CUDAExecutionProvider" if requested_device == "cuda" else "CPUExecutionProvider"
    )

    ort.preload_dlls(directory="")
    os.environ["ONNX_PROVIDER"] = requested_provider

    model_path, voices_path = resolve_kokoro_assets(backend_dir)
    kokoro = Kokoro(str(model_path), str(voices_path))
    providers = kokoro.sess.get_providers()
    active_provider = providers[0] if providers else "unknown"

    available_voices = sorted(list(kokoro.voices.files))
    preferred_voice = "bf_emma" if "bf_emma" in available_voices else available_voices[0]

    if requested_device == "cuda" and active_provider != "CUDAExecutionProvider":
        raise RuntimeError(
            f"Kokoro carregou em {active_provider}, nao em CUDA. Providers: {providers}"
        )

    text = "Ola. Eu sou o Jarvez falando em portugues do Brasil pela voz local Kokoro."
    samples, sample_rate = kokoro.create(
        text,
        voice=preferred_voice,
        lang="pt-br",
        speed=1.0,
    )
    output_path = backend_dir / "test_kokoro_output.wav"
    sf.write(output_path, samples, sample_rate, format="WAV")

    print(f"Kokoro provider ativo: {active_provider}")
    print(f"Kokoro voice usada: {preferred_voice}")
    print(f"Kokoro sample_rate: {sample_rate}")
    print(f"Kokoro audio salvo em: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
