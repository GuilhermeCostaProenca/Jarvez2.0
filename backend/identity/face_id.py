from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .identity_store import IdentityStore

try:
    import cv2
except Exception:  # pragma: no cover - optional runtime dependency
    cv2 = None

try:
    from insightface.app import FaceAnalysis
except Exception:  # pragma: no cover - optional runtime dependency
    FaceAnalysis = None

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover - optional runtime dependency
    ort = None


_FACE_ENGINE: Any | None = None
_FACE_ENGINE_FAILED = False


def _face_threshold() -> float:
    raw = os.getenv("JARVEZ_FACE_ID_THRESHOLD", "0.55").strip()
    try:
        return max(0.0, min(float(raw), 1.0))
    except ValueError:
        return 0.55


def _identity_model_root() -> Path:
    raw = os.getenv("JARVEZ_FACE_ID_MODEL_ROOT", "data/identity").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _largest_face(faces: list[Any]) -> Any | None:
    if not faces:
        return None

    def _area(face: Any) -> float:
        bbox = getattr(face, "bbox", None)
        if bbox is None and isinstance(face, dict):
            bbox = face.get("bbox")
        if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
            try:
                return max(0.0, float(bbox[2]) - float(bbox[0])) * max(0.0, float(bbox[3]) - float(bbox[1]))
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    return max(faces, key=_area)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    lhs = np.asarray(left, dtype=np.float32)
    rhs = np.asarray(right, dtype=np.float32)
    if lhs.size == 0 or rhs.size == 0:
        return 0.0
    lhs_norm = float(np.linalg.norm(lhs))
    rhs_norm = float(np.linalg.norm(rhs))
    if lhs_norm <= 1e-8 or rhs_norm <= 1e-8:
        return 0.0
    score = float(np.dot(lhs / lhs_norm, rhs / rhs_norm))
    return max(0.0, min(score, 1.0))


def _load_face_engine() -> Any | None:
    global _FACE_ENGINE
    global _FACE_ENGINE_FAILED
    if _FACE_ENGINE is not None:
        return _FACE_ENGINE
    if _FACE_ENGINE_FAILED or FaceAnalysis is None:
        return None
    model_name = os.getenv("JARVEZ_FACE_ID_MODEL_NAME", "buffalo_l").strip() or "buffalo_l"
    providers = ["CPUExecutionProvider"]
    gpu_enabled = os.getenv("JARVEZ_FACE_ID_ENABLE_GPU", "").strip().lower() in {"1", "true", "yes", "on"}
    if gpu_enabled and ort is not None:
        try:
            available = list(ort.get_available_providers())
        except Exception:
            available = []
        if "CUDAExecutionProvider" in available:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    try:
        app = FaceAnalysis(name=model_name, root=str(_identity_model_root()), providers=providers)
        app.prepare(ctx_id=0 if providers[0] == "CUDAExecutionProvider" else -1, det_size=(640, 640))
        _FACE_ENGINE = app
    except Exception:
        _FACE_ENGINE_FAILED = True
        return None
    return _FACE_ENGINE


@dataclass(slots=True)
class FaceIdentificationResult:
    name: str
    confidence: float
    matched: bool
    face_detected: bool
    source: str = "face"
    compared_profiles: int = 0
    method: str = "face_context"


def capture_webcam_frame(camera_index: int = 0, *, cv2_module: Any = cv2) -> Any:
    if cv2_module is None:
        raise RuntimeError("OpenCV not available")
    camera = cv2_module.VideoCapture(int(camera_index))
    if not camera.isOpened():
        camera.release()
        raise RuntimeError("Unable to open webcam")
    ok, frame = camera.read()
    camera.release()
    if not ok or frame is None:
        raise RuntimeError("Unable to capture webcam frame")
    return frame


def extract_face_embedding(frame: Any, *, engine: Any | None = None) -> list[float] | None:
    resolved_engine = engine or _load_face_engine()
    if resolved_engine is None:
        return None
    try:
        faces = resolved_engine.get(frame)
    except Exception:
        return None
    if not isinstance(faces, list) or not faces:
        return None
    face = _largest_face(faces)
    if face is None:
        return None
    embedding = getattr(face, "embedding", None)
    if embedding is None and isinstance(face, dict):
        embedding = face.get("embedding")
    if embedding is None:
        return None
    vector = np.asarray(embedding, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    if norm > 1e-8:
        vector = vector / norm
    return [float(value) for value in vector.tolist()]


def capture_face_embedding(
    *,
    camera_index: int = 0,
    frame_provider: Callable[..., Any] = capture_webcam_frame,
    engine: Any | None = None,
) -> list[float] | None:
    try:
        frame = frame_provider(camera_index)
    except Exception:
        return None
    return extract_face_embedding(frame, engine=engine)


def identify_face(
    store: IdentityStore,
    *,
    frame: Any | None = None,
    embedding: list[float] | None = None,
    camera_index: int = 0,
    threshold: float | None = None,
    frame_provider: Callable[..., Any] = capture_webcam_frame,
    engine: Any | None = None,
) -> FaceIdentificationResult:
    probe = [float(value) for value in embedding] if embedding is not None else None
    method = "provided_embedding" if probe is not None else "face_context"
    if probe is None:
        try:
            resolved_frame = frame if frame is not None else frame_provider(camera_index)
        except Exception:
            return FaceIdentificationResult(
                name="unknown",
                confidence=0.0,
                matched=False,
                face_detected=False,
                method=method,
            )
        probe = extract_face_embedding(resolved_frame, engine=engine)
    if probe is None:
        return FaceIdentificationResult(
            name="unknown",
            confidence=0.0,
            matched=False,
            face_detected=False,
            method=method,
        )

    resolved_threshold = _face_threshold() if threshold is None else max(0.0, min(float(threshold), 1.0))
    best_name = "unknown"
    best_score = 0.0
    compared_profiles = 0
    for profile in store.list_profiles():
        for candidate in profile.face_embeddings:
            compared_profiles += 1
            score = _cosine_similarity(probe, candidate)
            if score > best_score:
                best_score = score
                best_name = profile.name

    if best_score < resolved_threshold:
        return FaceIdentificationResult(
            name="unknown",
            confidence=best_score,
            matched=False,
            face_detected=True,
            compared_profiles=compared_profiles,
            method=method,
        )
    return FaceIdentificationResult(
        name=best_name,
        confidence=best_score,
        matched=True,
        face_detected=True,
        compared_profiles=compared_profiles,
        method=method,
    )
