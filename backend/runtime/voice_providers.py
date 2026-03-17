from __future__ import annotations

import asyncio
import importlib
import inspect
import io
import logging
import os
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_GOOGLE_VOICE = "Charon"
DEFAULT_OPENAI_VOICE = "alloy"
DEFAULT_ELEVENLABS_VOICE = "EXAVITQu4vr4xnSDxMaL"
DEFAULT_KOKORO_VOICE = "af_heart"


class VoiceProviderError(RuntimeError):
    """Raised when a configured voice provider cannot be loaded or used."""


@dataclass(slots=True)
class VoiceProviderConfig:
    provider_name: str
    voice_name: str
    kokoro_model_path: str
    kokoro_device: str


class VoiceProvider(ABC):
    provider_name = "unknown"
    default_voice_name = DEFAULT_GOOGLE_VOICE
    sample_rate = 24_000
    mime_type = "audio/mpeg"

    def __init__(self, config: VoiceProviderConfig) -> None:
        self.config = config
        self.voice_name = config.voice_name

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Return the synthesized audio bytes for a text segment."""

    async def stream(self, text: str) -> AsyncIterator[bytes]:
        yield await self.synthesize(text)

    def build_livekit_tts(self) -> Any:
        try:
            from livekit.agents import tts
            from livekit.agents._exceptions import APIConnectionError
        except Exception as exc:  # noqa: BLE001
            raise VoiceProviderError(
                "LiveKit Agents com suporte a TTS e necessario para usar providers de voz nao realtime."
            ) from exc

        provider = self

        class _ProviderChunkedStream(tts.ChunkedStream):
            def __init__(self, *, input_text: str, conn_options: Any) -> None:
                super().__init__(tts=provider_tts, input_text=input_text, conn_options=conn_options)

            async def _run(self, output_emitter: Any) -> None:
                try:
                    audio_bytes = await provider.synthesize(self._input_text)
                except VoiceProviderError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    raise APIConnectionError(f"Falha ao sintetizar audio com {provider.provider_name}.") from exc

                output_emitter.initialize(
                    request_id=uuid.uuid4().hex,
                    sample_rate=provider.sample_rate,
                    num_channels=1,
                    mime_type=provider.mime_type,
                )
                output_emitter.push(audio_bytes)

        class _ProviderTTS(tts.TTS):
            def __init__(self) -> None:
                super().__init__(
                    capabilities=tts.TTSCapabilities(streaming=False, aligned_transcript=False),
                    sample_rate=provider.sample_rate,
                    num_channels=1,
                )

            def synthesize(self, text: str, *, conn_options: Any = tts.DEFAULT_API_CONNECT_OPTIONS) -> Any:
                return _ProviderChunkedStream(input_text=text, conn_options=conn_options)

        provider_tts = _ProviderTTS()
        return provider_tts


class GoogleRealtimeProvider(VoiceProvider):
    provider_name = "google"
    default_voice_name = DEFAULT_GOOGLE_VOICE

    async def synthesize(self, text: str) -> bytes:  # noqa: ARG002
        raise VoiceProviderError(
            "Google realtime continua sendo gerenciado pelo RealtimeModel e nao expone synthesize() em bytes."
        )

    def build_livekit_tts(self) -> Any:
        return None


class OpenAIVoiceProvider(VoiceProvider):
    provider_name = "openai"
    default_voice_name = DEFAULT_OPENAI_VOICE
    sample_rate = 24_000
    mime_type = "audio/mpeg"

    def __init__(self, config: VoiceProviderConfig) -> None:
        super().__init__(config)
        self._model_name = os.getenv("JARVEZ_OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip() or "gpt-4o-mini-tts"

    async def synthesize(self, text: str) -> bytes:
        module = _lazy_import("openai", "pip install openai")
        client_cls = getattr(module, "AsyncOpenAI", None)
        if client_cls is None:
            raise VoiceProviderError("O pacote openai instalado nao expoe AsyncOpenAI para TTS.")
        client = client_cls()
        response = await client.audio.speech.create(
            model=self._model_name,
            voice=self.voice_name,
            input=text,
            format="mp3",
        )
        try:
            return await _coerce_audio_bytes(response)
        finally:
            await _close_client(client)


class ElevenLabsProvider(VoiceProvider):
    provider_name = "elevenlabs"
    default_voice_name = DEFAULT_ELEVENLABS_VOICE
    sample_rate = 44_100
    mime_type = "audio/mpeg"

    def __init__(self, config: VoiceProviderConfig) -> None:
        super().__init__(config)
        self._model_name = (
            os.getenv("JARVEZ_ELEVENLABS_MODEL", "eleven_flash_v2_5").strip() or "eleven_flash_v2_5"
        )
        self._output_format = (
            os.getenv("JARVEZ_ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128").strip() or "mp3_44100_128"
        )

    async def synthesize(self, text: str) -> bytes:
        module = _lazy_import("elevenlabs", "pip install elevenlabs")
        client_cls = getattr(module, "AsyncElevenLabs", None) or getattr(module, "ElevenLabs", None)
        if client_cls is None:
            raise VoiceProviderError("O pacote elevenlabs instalado nao expoe um cliente compativel.")
        api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        client = client_cls(api_key=api_key or None)
        tts_api = getattr(client, "text_to_speech", None)
        if tts_api is None:
            raise VoiceProviderError("Cliente ElevenLabs sem text_to_speech configurado.")
        convert = getattr(tts_api, "convert", None) or getattr(tts_api, "generate", None)
        if convert is None:
            raise VoiceProviderError("Cliente ElevenLabs sem metodo convert/generate para TTS.")
        response = convert(
            voice_id=self.voice_name,
            model_id=self._model_name,
            output_format=self._output_format,
            text=text,
        )
        try:
            return await _coerce_audio_bytes(response)
        finally:
            await _close_client(client)


class KokoroProvider(VoiceProvider):
    provider_name = "kokoro"
    default_voice_name = DEFAULT_KOKORO_VOICE
    sample_rate = 24_000
    mime_type = "audio/wav"

    async def synthesize(self, text: str) -> bytes:
        module = _lazy_import(
            "kokoro_onnx",
            "pip install kokoro-onnx soundfile",
        )
        soundfile = _lazy_import("soundfile", "pip install soundfile")
        kokoro_cls = getattr(module, "Kokoro", None)
        if kokoro_cls is None:
            raise VoiceProviderError("O pacote kokoro-onnx nao expoe a classe Kokoro esperada.")

        def _generate() -> bytes:
            model_path, voices_path = self._resolve_assets()
            init_signature = inspect.signature(kokoro_cls)
            init_kwargs: dict[str, object] = {}
            if "device" in init_signature.parameters:
                init_kwargs["device"] = self.config.kokoro_device

            kokoro = kokoro_cls(model_path, voices_path, **init_kwargs)
            create_signature = inspect.signature(kokoro.create)
            create_kwargs: dict[str, object] = {"speed": 1.0}
            if "lang" in create_signature.parameters:
                create_kwargs["lang"] = os.getenv("KOKORO_LANGUAGE", "pt")
            samples, sample_rate = kokoro.create(text, **create_kwargs)
            buffer = io.BytesIO()
            soundfile.write(
                buffer,
                samples,
                sample_rate,
                format="WAV",
            )
            return buffer.getvalue()

        return await asyncio.to_thread(_generate)

    def _resolve_assets(self) -> tuple[str, str]:
        base_path = Path(self.config.kokoro_model_path).expanduser()
        if base_path.is_dir():
            model_file = next(base_path.glob("*.onnx"), None)
            voices_file = next(base_path.glob("*.bin"), None)
        else:
            model_file = base_path if base_path.suffix.lower() == ".onnx" else None
            voices_file = next(base_path.parent.glob("*.bin"), None) if model_file else None

        if model_file is None or voices_file is None:
            raise VoiceProviderError(
                "Kokoro requer um diretorio com arquivos .onnx e .bin ou um caminho .onnx acompanhado do voices .bin."
            )

        return str(model_file), str(voices_file)


def resolve_voice_provider_config() -> VoiceProviderConfig:
    raw_provider = str(os.getenv("JARVEZ_VOICE_PROVIDER", "google")).strip().lower() or "google"
    provider_name = raw_provider
    valid_providers = {"google", "openai", "elevenlabs", "kokoro"}
    if provider_name not in valid_providers:
        logger.warning(
            "JARVEZ_VOICE_PROVIDER=%s invalido; usando google como fallback.",
            raw_provider,
        )
        provider_name = "google"

    default_voice_name = {
        "google": DEFAULT_GOOGLE_VOICE,
        "openai": DEFAULT_OPENAI_VOICE,
        "elevenlabs": DEFAULT_ELEVENLABS_VOICE,
        "kokoro": DEFAULT_KOKORO_VOICE,
    }[provider_name]

    voice_name = str(os.getenv("JARVEZ_VOICE_NAME", "")).strip() or default_voice_name
    return VoiceProviderConfig(
        provider_name=provider_name,
        voice_name=voice_name,
        kokoro_model_path=str(os.getenv("KOKORO_MODEL_PATH", "./models/kokoro")).strip() or "./models/kokoro",
        kokoro_device=str(os.getenv("KOKORO_DEVICE", "cuda")).strip() or "cuda",
    )


def build_voice_provider_from_env() -> VoiceProvider:
    config = resolve_voice_provider_config()
    provider_cls = {
        "google": GoogleRealtimeProvider,
        "openai": OpenAIVoiceProvider,
        "elevenlabs": ElevenLabsProvider,
        "kokoro": KokoroProvider,
    }[config.provider_name]
    return provider_cls(config)


def _lazy_import(module_name: str, install_hint: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise VoiceProviderError(
            f"Provider de voz requer o pacote '{module_name}'. Instale com `{install_hint}`."
        ) from exc


async def _coerce_audio_bytes(value: Any) -> bytes:
    current = value
    if inspect.isawaitable(current):
        current = await current
    if current is None:
        raise VoiceProviderError("Provider de voz retornou payload vazio.")

    read = getattr(current, "read", None)
    if callable(read):
        read_result = read()
        if inspect.isawaitable(read_result):
            read_result = await read_result
        if isinstance(read_result, (bytes, bytearray)):
            return bytes(read_result)

    iter_bytes = getattr(current, "iter_bytes", None)
    if callable(iter_bytes):
        iterator = iter_bytes()
        return await _collect_binary_chunks(iterator)

    if isinstance(current, (bytes, bytearray)):
        return bytes(current)
    if isinstance(current, str):
        return current.encode("utf-8")

    content = getattr(current, "content", None)
    if isinstance(content, (bytes, bytearray)):
        return bytes(content)

    if hasattr(current, "__aiter__"):
        return await _collect_binary_chunks(current)
    if isinstance(current, Iterable):
        chunks: list[bytes] = []
        for chunk in current:
            if isinstance(chunk, str):
                chunks.append(chunk.encode("utf-8"))
            else:
                chunks.append(bytes(chunk))
        if chunks:
            return b"".join(chunks)

    raise VoiceProviderError("Nao foi possivel converter o retorno do provider de voz em bytes.")


async def _collect_binary_chunks(iterator: Any) -> bytes:
    chunks: list[bytes] = []
    if hasattr(iterator, "__aiter__"):
        async for chunk in iterator:
            chunks.append(_normalize_binary_chunk(chunk))
    else:
        for chunk in iterator:
            chunks.append(_normalize_binary_chunk(chunk))
    if not chunks:
        raise VoiceProviderError("Provider de voz nao retornou audio.")
    return b"".join(chunks)


def _normalize_binary_chunk(chunk: Any) -> bytes:
    if isinstance(chunk, str):
        return chunk.encode("utf-8")
    if isinstance(chunk, bytearray):
        return bytes(chunk)
    if isinstance(chunk, bytes):
        return chunk
    return bytes(chunk)


async def _close_client(client: Any) -> None:
    for attr_name in ("aclose", "close"):
        closer = getattr(client, attr_name, None)
        if not callable(closer):
            continue
        result = closer()
        if inspect.isawaitable(result):
            await result
        return
