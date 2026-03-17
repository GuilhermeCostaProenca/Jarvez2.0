from __future__ import annotations

import json
import os
from typing import Any

import requests


def _model_name() -> str:
    return os.getenv("OPENAI_CODEX_MODEL", "").strip() or os.getenv("OPENAI_CODEX_FALLBACK_MODEL", "").strip() or "gpt-4.1"


def _api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def _max_chunks() -> int:
    raw = os.getenv("OPENAI_CODE_MAX_CONTEXT_CHUNKS", "4").strip()
    try:
        return max(1, min(8, int(raw)))
    except ValueError:
        return 4


def _max_tokens() -> int:
    raw = os.getenv("OPENAI_CODE_MAX_OUTPUT_TOKENS", "900").strip()
    try:
        return max(200, min(4000, int(raw)))
    except ValueError:
        return 900


def _truncate(text: str, limit: int = 8000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _heuristic_summary(user_request: str, project: dict[str, Any], snippets: list[dict[str, Any]]) -> dict[str, Any]:
    files = []
    for snippet in snippets[:4]:
        path = str(snippet.get("source_path", "")).strip()
        if path and path not in files:
            files.append(path)
    return {
        "summary": (
            f"Analise heuristica para '{project.get('name', 'projeto')}'. "
            f"Pedido: {user_request.strip() or 'sem descricao adicional'}."
        ),
        "files": files,
        "risks": [
            "Nenhuma chave OPENAI_API_KEY configurada; usando fallback heuristico.",
            "Revise os arquivos sugeridos antes de aplicar mudancas automatizadas.",
        ],
        "validation_commands": [["git", "diff"], ["git", "status"]],
        "patch_preview": None,
    }


def _openai_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    if not _api_key():
        return None

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": _model_name(),
            "temperature": 0.2,
            "max_tokens": _max_tokens(),
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        return None
    parsed = json.loads(content)
    return parsed if isinstance(parsed, dict) else None


def _build_context_block(project: dict[str, Any], snippets: list[dict[str, Any]], extra_files: list[dict[str, Any]]) -> str:
    blocks: list[str] = [
        f"Projeto: {project.get('name', 'desconhecido')}",
        f"Raiz: {project.get('root_path', '')}",
    ]
    for item in snippets[: _max_chunks()]:
        blocks.append(
            "\n".join(
                [
                    f"[Snippet] {item.get('source_path', '')}",
                    _truncate(str(item.get("content", "")), 1200),
                ]
            )
        )
    for item in extra_files[:2]:
        blocks.append(
            "\n".join(
                [
                    f"[File] {item.get('path', '')}",
                    _truncate(str(item.get("content", "")), 1800),
                ]
            )
        )
    return "\n\n".join(block for block in blocks if block.strip())


def analyze_code_issue(
    *,
    user_request: str,
    project: dict[str, Any],
    snippets: list[dict[str, Any]],
    extra_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    extra_files = extra_files or []
    heuristic = _heuristic_summary(user_request, project, snippets)
    system_prompt = (
        "Voce e um analista de codigo. Responda em JSON com as chaves: "
        "summary, files, risks, validation_commands, patch_preview. "
        "Nao invente que leu algo fora do contexto fornecido."
    )
    user_prompt = "\n\n".join(
        [
            f"Pedido do usuario:\n{user_request}",
            _build_context_block(project, snippets, extra_files),
        ]
    )
    try:
        parsed = _openai_json(system_prompt, user_prompt)
    except Exception:
        parsed = None
    return parsed or heuristic


def explain_project_state(
    *,
    user_request: str,
    project: dict[str, Any],
    snippets: list[dict[str, Any]],
    extra_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return analyze_code_issue(
        user_request=user_request,
        project=project,
        snippets=snippets,
        extra_files=extra_files,
    )


def propose_patch_plan(
    *,
    user_request: str,
    project: dict[str, Any],
    snippets: list[dict[str, Any]],
    extra_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    extra_files = extra_files or []
    heuristic = _heuristic_summary(user_request, project, snippets)
    heuristic["risks"] = [
        *heuristic["risks"],
        "A proposta e um plano de mudanca; o patch final ainda precisa ser fornecido para code_apply_patch.",
    ]
    system_prompt = (
        "Voce e um planejador de mudancas de codigo. Responda em JSON com as chaves: "
        "summary, files, risks, validation_commands, patch_preview. "
        "patch_preview deve ser null se voce nao puder propor um diff seguro."
    )
    user_prompt = "\n\n".join(
        [
            f"Pedido do usuario:\n{user_request}",
            _build_context_block(project, snippets, extra_files),
        ]
    )
    try:
        parsed = _openai_json(system_prompt, user_prompt)
    except Exception:
        parsed = None
    return parsed or heuristic


def summarize_diff(
    *,
    project: dict[str, Any],
    diff_text: str,
) -> dict[str, Any]:
    heuristic = {
        "summary": f"Resumo heuristico do diff em {project.get('name', 'projeto')}.",
        "files": [],
        "risks": [],
        "validation_commands": [["git", "diff"]],
        "patch_preview": _truncate(diff_text, 1200) or None,
    }
    system_prompt = (
        "Resuma um diff de codigo em JSON com as chaves: summary, files, risks, validation_commands, patch_preview."
    )
    user_prompt = "\n\n".join(
        [
            f"Projeto: {project.get('name', 'desconhecido')}",
            f"Diff:\n{_truncate(diff_text, 5000)}",
        ]
    )
    try:
        parsed = _openai_json(system_prompt, user_prompt)
    except Exception:
        parsed = None
    return parsed or heuristic
