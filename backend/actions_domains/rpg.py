from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def rpg_reindex_sources(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_rpg_index: Any,
    rpg_sources: Any,
) -> ActionResult:
    _ = ctx
    index = get_rpg_index()
    configured = rpg_sources()
    extra_paths_raw = params.get("paths", [])
    extra_paths: list[Path] = []
    if isinstance(extra_paths_raw, list):
        for item in extra_paths_raw:
            if isinstance(item, str) and item.strip():
                extra_paths.append(Path(item.strip()))

    sources = configured + extra_paths
    if not sources:
        return ActionResult(
            success=False,
            message="Nenhuma fonte RPG configurada para indexar.",
            error="missing RPG_SOURCE_PATHS",
        )

    summary = index.ingest_paths(sources)
    stats = index.stats()
    return ActionResult(
        success=True,
        message="Base RPG reindexada com sucesso.",
        data={"ingest_summary": summary, "knowledge_stats": stats},
    )


async def rpg_search_knowledge(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_rpg_index: Any,
) -> ActionResult:
    _ = ctx
    query = str(params.get("query", "")).strip()
    limit = int(params.get("limit", 5))
    if not query:
        return ActionResult(success=False, message="Informe uma consulta RPG.", error="missing query")

    index = get_rpg_index()
    results = index.search(query, limit=limit)
    if not results:
        return ActionResult(
            success=False,
            message="Nao encontrei trechos na base RPG para essa pergunta.",
            data={"query": query},
            error="not found",
        )
    return ActionResult(
        success=True,
        message=f"Encontrei {len(results)} trecho(s) da base RPG.",
        data={"query": query, "results": results},
    )


async def rpg_get_knowledge_stats(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_rpg_index: Any,
) -> ActionResult:
    _ = params
    _ = ctx
    index = get_rpg_index()
    return ActionResult(success=True, message="Estatisticas da base RPG.", data={"knowledge_stats": index.stats()})


async def rpg_save_lore_note(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_rpg_index: Any,
    rpg_notes_dir: Any,
) -> ActionResult:
    _ = ctx
    title = str(params.get("title", "")).strip()
    content = str(params.get("content", "")).strip()
    world = str(params.get("world", "geral")).strip() or "geral"
    if not content:
        return ActionResult(success=False, message="Conteudo vazio para nota de lore.", error="missing content")

    index = get_rpg_index()
    try:
        saved = index.save_note(title=title or "nota_rpg", content=content, world=world, notes_dir=rpg_notes_dir())
    except ValueError as error:
        return ActionResult(success=False, message="Nao consegui salvar a nota RPG.", error=str(error))

    reindex_summary = index.ingest_paths([Path(saved["file_path"])])
    return ActionResult(
        success=True,
        message=f"Nota de lore salva em {saved['world']} e indexada.",
        data={"saved_note": saved, "ingest_summary": reindex_summary, "knowledge_stats": index.stats()},
    )


async def rpg_get_character_mode(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_active_character: Any,
    active_character_payload: Any,
) -> ActionResult:
    _ = params
    active = get_active_character(ctx.participant_identity, ctx.room)
    if active is None:
        return ActionResult(
            success=True,
            message="Nenhum personagem ativo no momento.",
            data=active_character_payload(ctx.participant_identity, ctx.room),
        )
    return ActionResult(
        success=True,
        message=f"Personagem ativo: {active.name}.",
        data=active_character_payload(ctx.participant_identity, ctx.room),
    )


async def rpg_assume_character(
    params: JsonObject,
    ctx: ActionContext,
    *,
    find_existing_character_sheet_by_name: Any,
    rpg_character_pdfs_dir: Any,
    summarize_character_text: Any,
    find_onenote_character_page: Any,
    quote_path_segment: Any,
    onenote_api_request: Any,
    extract_onenote_character_profile: Any,
    strip_html_for_preview: Any,
    get_rpg_index: Any,
    ensure_onenote_character_page: Any,
    build_character_prompt_hint: Any,
    active_character_mode_cls: Any,
    now_iso: Any,
    set_active_character: Any,
    active_character_payload: Any,
) -> ActionResult:
    name = str(params.get("name", "")).strip()
    source = str(params.get("source", "auto")).strip().lower() or "auto"
    section_name = str(params.get("section_name", "")).strip() or None
    visual_reference_url = str(params.get("referencia_visual_url", "")).strip() or None
    pinterest_pin_url = str(params.get("pinterest_pin_url", "")).strip() or None
    visual_description = str(params.get("descricao_visual", "")).strip() or None
    if not name:
        return ActionResult(success=False, message="Informe o nome do personagem.", error="missing name")

    resolved_source = source if source in {"auto", "onenote", "pdf", "manual"} else "auto"
    summary = ""
    profile: JsonObject = {}
    page_id: str | None = None
    page_title: str | None = None
    resolved_section_name: str | None = None
    one_note_url: str | None = None
    used_source = "manual"
    one_note_sync_status = "skipped"
    one_note_sync_error: str | None = None
    existing_sheet, existing_sheet_path = find_existing_character_sheet_by_name(name)
    sheet_json_path: str | None = str(existing_sheet_path.resolve()) if existing_sheet_path else None
    sheet_markdown_path: str | None = None
    sheet_pdf_path: str | None = None
    if existing_sheet_path:
        md_candidate = existing_sheet_path.with_suffix(".md")
        if md_candidate.exists():
            sheet_markdown_path = str(md_candidate.resolve())
        pdf_candidate = rpg_character_pdfs_dir() / existing_sheet_path.parent.name / f"{existing_sheet_path.stem}.pdf"
        if pdf_candidate.exists():
            sheet_pdf_path = str(pdf_candidate.resolve())
    if existing_sheet and not summary:
        derived = existing_sheet.get("derived", {}) if isinstance(existing_sheet.get("derived"), dict) else {}
        class_label = str(existing_sheet.get("class_name", "")).strip()
        race_label = str(existing_sheet.get("race", "")).strip()
        summary = summarize_character_text(
            " ".join(
                part
                for part in [
                    f"{name}.",
                    f"Raca {race_label}." if race_label else "",
                    f"Classe {class_label}." if class_label else "",
                    f"Nivel {existing_sheet.get('level')}." if existing_sheet.get("level") else "",
                    f"Conceito: {existing_sheet.get('concept')}." if existing_sheet.get("concept") else "",
                    f"Defesa {derived.get('defense')}." if derived.get("defense") is not None else "",
                ]
                if part
            )
        )
        profile = {
            "summary": summary,
            "sheet_reference": {
                "sheet_json_path": sheet_json_path,
                "sheet_markdown_path": sheet_markdown_path,
                "sheet_pdf_path": sheet_pdf_path,
                "sheet_builder_source": existing_sheet.get("builder"),
            },
        }
        used_source = "sheet"

    if resolved_source in {"auto", "onenote"}:
        match = find_onenote_character_page(name, section_name)
        if match and isinstance(match, dict):
            page = match.get("page")
            if isinstance(page, dict):
                page_id = str(page.get("id", "")).strip() or None
                page_title = str(page.get("title", "")).strip() or None
                resolved_section_name = str(match.get("section_name", "")).strip() or None
                links = page.get("links", {})
                if isinstance(links, dict):
                    one_note = links.get("oneNoteClientUrl")
                    if isinstance(one_note, dict):
                        one_note_url = str(one_note.get("href", "")).strip() or None
                if page_id:
                    encoded_page_id = quote_path_segment(page_id)
                    content, error = onenote_api_request(
                        "GET",
                        f"me/onenote/pages/{encoded_page_id}/content",
                        extra_headers={"Accept": "text/html"},
                    )
                    if error is None:
                        html_content = str(content or "")
                        profile = extract_onenote_character_profile(html_content)
                        summary = str(profile.get("summary", "")).strip() or summarize_character_text(
                            strip_html_for_preview(html_content)
                        )
                        if not visual_reference_url:
                            visual_reference_url = str(profile.get("visual_reference_url", "")).strip() or None
                        if not pinterest_pin_url:
                            pinterest_pin_url = str(profile.get("pinterest_pin_url", "")).strip() or None
                        if not visual_description:
                            visual_description = str(profile.get("visual_description", "")).strip() or None
                        used_source = "onenote"

    if not summary and resolved_source in {"auto", "pdf"}:
        results = get_rpg_index().search(name, limit=3)
        if results:
            first = results[0]
            summary = summarize_character_text(str(first.get("content", "")))
            profile = {
                "summary": summary,
                "knowledge_limits": "Baseado em trechos indexados de PDFs e lore local. Se faltar informacao, assuma incerteza.",
            }
            used_source = "pdf"

    if not summary:
        summary = (
            f"Assuma o papel de {name}. Mantenha consistencia de personalidade, voz e objetivos. "
            "Se faltar contexto, improvise com coerencia e confirme lacunas quando necessario."
        )
        used_source = "manual" if resolved_source == "manual" else resolved_source
        profile = {
            "summary": summary,
            "knowledge_limits": "Contexto manual e incompleto. Nao invente fatos canonicos sem marcar como improviso.",
        }

    page_sync_payload, page_sync_error = ensure_onenote_character_page(
        title=name,
        summary=summary,
        source=used_source,
        preferred_section_name=resolved_section_name or section_name,
        visual_reference_url=visual_reference_url,
        pinterest_pin_url=pinterest_pin_url,
        visual_description=visual_description,
    )
    if page_sync_error is None and isinstance(page_sync_payload, dict):
        page_id = str(page_sync_payload.get("page_id", "")).strip() or page_id
        page_title = str(page_sync_payload.get("title", "")).strip() or page_title or name
        resolved_section_name = str(page_sync_payload.get("section_name", "")).strip() or resolved_section_name
        one_note_url = str(page_sync_payload.get("one_note_url", "")).strip() or one_note_url
        one_note_sync_status = "created" if page_sync_payload.get("created") else "reused"
    elif page_sync_error is not None:
        one_note_sync_status = "failed"
        one_note_sync_error = page_sync_error.message

    if visual_reference_url and not profile.get("visual_reference_url"):
        profile["visual_reference_url"] = visual_reference_url
    if pinterest_pin_url and not profile.get("pinterest_pin_url"):
        profile["pinterest_pin_url"] = pinterest_pin_url
    if visual_description and not profile.get("visual_description"):
        profile["visual_description"] = visual_description
    if summary and not profile.get("summary"):
        profile["summary"] = summary
    prompt_hint = build_character_prompt_hint(name, summary, profile)

    active = active_character_mode_cls(
        name=name,
        source=used_source,
        summary=summary,
        activated_at=now_iso(),
        page_id=page_id,
        page_title=page_title,
        section_name=resolved_section_name,
        one_note_url=one_note_url,
        visual_reference_url=visual_reference_url,
        pinterest_pin_url=pinterest_pin_url,
        visual_description=visual_description,
        profile=profile,
        prompt_hint=prompt_hint,
        sheet_json_path=sheet_json_path,
        sheet_markdown_path=sheet_markdown_path,
        sheet_pdf_path=sheet_pdf_path,
    )
    set_active_character(ctx.participant_identity, ctx.room, active)
    return ActionResult(
        success=True,
        message=(
            f"Modo personagem ativado para {name}."
            if one_note_sync_status != "failed"
            else f"Modo personagem ativado para {name}, mas a pagina dedicada no OneNote nao foi sincronizada."
        ),
        data={
            **active_character_payload(ctx.participant_identity, ctx.room),
            "character_prompt_hint": prompt_hint,
            "one_note_character_page_sync": one_note_sync_status,
            "one_note_character_page_error": one_note_sync_error,
        },
    )


async def rpg_clear_character_mode(
    params: JsonObject,
    ctx: ActionContext,
    *,
    get_active_character: Any,
    clear_active_character: Any,
    active_character_payload: Any,
) -> ActionResult:
    _ = params
    active = get_active_character(ctx.participant_identity, ctx.room)
    clear_active_character(ctx.participant_identity, ctx.room)
    if active is None:
        return ActionResult(
            success=True,
            message="Nenhum modo personagem estava ativo.",
            data={**active_character_payload(ctx.participant_identity, ctx.room), "active_character_cleared": True},
        )
    return ActionResult(
        success=True,
        message=f"Modo personagem encerrado para {active.name}.",
        data={**active_character_payload(ctx.participant_identity, ctx.room), "active_character_cleared": True},
    )


async def rpg_create_character_sheet(
    params: JsonObject,
    ctx: ActionContext,
    *,
    safe_file_part: Any,
    rpg_characters_dir: Any,
    rpg_character_pdfs_dir: Any,
    generate_character_sheet: Any,
    invalid_character_build_error_cls: Any,
    rpg_pdf_export_enabled: Any,
    export_tormenta20_sheet_pdf: Any,
    get_active_character: Any,
    find_onenote_character_page: Any,
    onenote_append_to_page: Any,
    set_active_character: Any,
    tormenta20_pdf_template_path: Any,
    log_info: Any,
) -> ActionResult:
    name = str(params.get("name", "")).strip()
    if not name:
        return ActionResult(success=False, message="Informe o nome do personagem.", error="missing name")

    world = str(params.get("world", "tormenta20")).strip() or "tormenta20"
    class_name = (
        str(params.get("class_name", "")).strip()
        or str(params.get("class", "")).strip()
        or str(params.get("character_class", "")).strip()
        or "A definir"
    )
    safe_world = safe_file_part(world)
    safe_name = safe_file_part(name)
    target_dir = rpg_characters_dir() / safe_world
    target_dir.mkdir(parents=True, exist_ok=True)
    md_path = target_dir / f"{safe_name}.md"
    json_path = target_dir / f"{safe_name}.json"
    pdf_dir = rpg_character_pdfs_dir() / safe_world
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{safe_name}.pdf"

    try:
        generation = generate_character_sheet(params)
    except invalid_character_build_error_cls as error:
        return ActionResult(success=False, message=str(error), error=str(error))

    sheet_data = generation.normalized_sheet
    sheet_md = generation.markdown
    builder_source = generation.source
    md_path.write_text(sheet_md, encoding="utf-8")
    json_path.write_text(
        json.dumps(sheet_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pdf_exported = False
    pdf_error: str | None = None
    if rpg_pdf_export_enabled():
        pdf_exported, pdf_error = export_tormenta20_sheet_pdf(sheet_data, pdf_path)
    template_paths = [
        item.strip()
        for item in os.getenv("RPG_CHARACTER_TEMPLATE_PDFS", "").split(";")
        if item.strip()
    ]
    existing_templates = [path for path in template_paths if Path(path).exists()]
    one_note_sync_status = "skipped"
    one_note_sync_error: str | None = None
    active_character = get_active_character(ctx.participant_identity, ctx.room)
    target_page_id: str | None = None
    if active_character and active_character.page_id and active_character.name.casefold() == name.casefold():
        target_page_id = active_character.page_id
    else:
        match = find_onenote_character_page(name)
        if match and isinstance(match, dict):
            page = match.get("page")
            if isinstance(page, dict):
                target_page_id = str(page.get("id", "")).strip() or None
    if target_page_id:
        skill_summary = sheet_data.get("recommended_skills")
        if not isinstance(skill_summary, list) or not skill_summary:
            skill_summary = []
        artifact_summary = (
            f"Arquivos locais: JSON {json_path.resolve()} | MD {md_path.resolve()} | "
            f"PDF {pdf_path.resolve() if pdf_exported else 'indisponivel'}."
        )
        append_text = (
            f"Ficha Tormenta20 atualizada. Classe: {class_name}. Nivel: {sheet_data.get('level', 1)}. "
            f"Builder: {builder_source}. Status: {generation.status}. "
            f"PV {sheet_data['derived']['pv']}, PM {sheet_data['derived']['pm']}, Defesa {sheet_data['derived']['defense']}. "
            f"Pericias recomendadas: {', '.join(str(item) for item in skill_summary[:6])}. "
            f"{artifact_summary}"
        )
        append_result = await onenote_append_to_page({"page_id": target_page_id, "content": append_text}, ctx)
        if append_result.success:
            one_note_sync_status = "appended"
        else:
            one_note_sync_status = "failed"
            one_note_sync_error = append_result.message
    if active_character and active_character.name.casefold() == name.casefold():
        active_character.sheet_json_path = str(json_path.resolve())
        active_character.sheet_markdown_path = str(md_path.resolve())
        active_character.sheet_pdf_path = str(pdf_path.resolve()) if pdf_exported else None
        set_active_character(ctx.participant_identity, ctx.room, active_character)

    pdf_status = "created" if pdf_exported else ("skipped" if not rpg_pdf_export_enabled() else "failed")
    log_info(
        "rpg_sheet_pipeline %s",
        json.dumps(
            {
                "character_name": name,
                "world": world,
                "builder_source": builder_source,
                "generation_status": generation.status,
                "pdf_status": pdf_status,
                "pdf_error": pdf_error,
                "one_note_sync_status": one_note_sync_status,
            },
            ensure_ascii=False,
        ),
    )

    return ActionResult(
        success=True,
        message=f"Ficha Tormenta20 base de {name} criada.",
        data={
            "character_name": name,
            "sheet_markdown_path": str(md_path.resolve()),
            "sheet_json_path": str(json_path.resolve()),
            "sheet_pdf_path": str(pdf_path.resolve()) if pdf_exported else None,
            "sheet_pdf_status": pdf_status,
            "sheet_pdf_error": pdf_error,
            "sheet_pdf_template_path": str(tormenta20_pdf_template_path().resolve()) if rpg_pdf_export_enabled() else None,
            "sheet_data": sheet_data,
            "sheet_builder_source": builder_source,
            "sheet_builder_error": "; ".join(generation.errors) if generation.errors else None,
            "sheet_generation_status": generation.status,
            "sheet_generation_warnings": generation.warnings,
            "sheet_applied_choices": generation.applied_choices,
            "sheet_unsupported_fields": generation.unsupported_fields,
            "template_references": existing_templates,
            "one_note_character_page_sync": one_note_sync_status,
            "one_note_character_page_error": one_note_sync_error,
        },
    )


async def rpg_create_threat_sheet(
    params: JsonObject,
    ctx: ActionContext,
    *,
    generate_threat_sheet: Any,
    invalid_threat_definition_error_cls: Any,
    safe_file_part: Any,
    rpg_threats_dir: Any,
    rpg_threat_pdfs_dir: Any,
    export_tormenta20_threat_pdf: Any,
    log_info: Any,
) -> ActionResult:
    _ = ctx
    name = str(params.get("name", "")).strip()
    if not name:
        return ActionResult(success=False, message="Informe o nome da ameaca.", error="missing name")

    try:
        generation = generate_threat_sheet(params)
    except invalid_threat_definition_error_cls as error:
        return ActionResult(success=False, message=str(error), error=str(error))

    threat_data = generation.normalized_threat
    world = str(threat_data.get("world", "tormenta20")).strip() or "tormenta20"
    safe_world = safe_file_part(world)
    safe_name = safe_file_part(name)
    target_dir = rpg_threats_dir() / safe_world
    target_dir.mkdir(parents=True, exist_ok=True)
    md_path = target_dir / f"{safe_name}.md"
    json_path = target_dir / f"{safe_name}.json"
    pdf_dir = rpg_threat_pdfs_dir() / safe_world
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{safe_name}.pdf"

    md_path.write_text(generation.markdown, encoding="utf-8")
    json_path.write_text(json.dumps(threat_data, ensure_ascii=False, indent=2), encoding="utf-8")
    pdf_exported, pdf_error = export_tormenta20_threat_pdf(threat_data, pdf_path)
    pdf_status = "created" if pdf_exported else "failed"

    log_info(
        "rpg_threat_pipeline %s",
        json.dumps(
            {
                "threat_name": name,
                "world": world,
                "challenge_level": threat_data.get("challenge_level"),
                "role": threat_data.get("role"),
                "builder_source": threat_data.get("builder"),
                "generation_status": generation.status,
                "pdf_status": pdf_status,
                "pdf_error": pdf_error,
            },
            ensure_ascii=False,
        ),
    )

    return ActionResult(
        success=True,
        message=f"Ameaca Tormenta20 base de {name} criada.",
        data={
            "threat_name": name,
            "threat_markdown_path": str(md_path.resolve()),
            "threat_json_path": str(json_path.resolve()),
            "threat_pdf_path": str(pdf_path.resolve()) if pdf_exported else None,
            "threat_pdf_status": pdf_status,
            "threat_pdf_error": pdf_error,
            "threat_data": threat_data,
            "threat_builder_source": str(threat_data.get("builder", "jarvez-threat-generator")),
            "threat_generation_status": generation.status,
            "threat_generation_warnings": generation.warnings,
        },
    )


async def rpg_session_recording(
    params: JsonObject,
    ctx: ActionContext,
    *,
    recording_key: Any,
    rpg_active_recordings: dict[str, Any],
    rpg_last_session_files: dict[str, str],
    recording_state_cls: Any,
    extract_history_since: Any,
    safe_file_part: Any,
    rpg_session_logs_dir: Any,
    build_session_markdown: Any,
    get_active_character: Any,
    infer_character_session_notes: Any,
    onenote_append_to_page: Any,
) -> ActionResult:
    mode = str(params.get("mode", "status")).strip().lower()
    world = str(params.get("world", "geral")).strip() or "geral"
    title = str(params.get("title", "")).strip() or f"sessao_{datetime.now().strftime('%Y%m%d_%H%M')}"
    key = recording_key(ctx.participant_identity, ctx.room)
    current = rpg_active_recordings.get(key)

    if mode == "status":
        if current and current.active:
            return ActionResult(
                success=True,
                message="Gravacao de sessao ativa.",
                data={
                    "recording_active": True,
                    "title": current.title,
                    "world": current.world,
                    "started_at": current.started_at.isoformat(),
                },
            )
        return ActionResult(success=True, message="Nenhuma gravacao ativa.", data={"recording_active": False})

    if mode == "start":
        history_items = getattr(getattr(ctx.session, "history", None), "items", None)
        start_index = len(history_items) if isinstance(history_items, list) else 0
        rpg_active_recordings[key] = recording_state_cls(
            participant_identity=ctx.participant_identity,
            room=ctx.room,
            title=title,
            world=world,
            started_at=datetime.now(timezone.utc),
            start_history_index=start_index,
            active=True,
        )
        return ActionResult(
            success=True,
            message=f"Gravacao da sessao '{title}' iniciada.",
            data={"recording_active": True, "title": title, "world": world},
        )

    if mode == "stop":
        if not current or not current.active:
            return ActionResult(success=False, message="Nao ha gravacao ativa para parar.", error="no active recording")
        messages = extract_history_since(ctx.session, current.start_history_index)
        safe_world = safe_file_part(current.world)
        safe_title = safe_file_part(current.title)
        out_dir = rpg_session_logs_dir() / safe_world
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        out_file.write_text(build_session_markdown(state=current, messages=messages), encoding="utf-8")

        current.output_file = str(out_file.resolve())
        current.active = False
        rpg_active_recordings.pop(key, None)
        rpg_last_session_files[key] = str(out_file.resolve())
        active_character = get_active_character(ctx.participant_identity, ctx.room)
        one_note_sync_status = "skipped"
        one_note_sync_error: str | None = None
        if active_character and active_character.page_id:
            session_notes = infer_character_session_notes(messages)
            first_user_lines = [
                item.get("content", "").strip()
                for item in messages
                if item.get("role") == "user" and str(item.get("content", "")).strip()
            ]
            excerpt = " ".join(first_user_lines[:2]).strip()
            if len(excerpt) > 240:
                excerpt = excerpt[:240].rstrip() + "..."
            sync_line = (
                f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Sessao '{current.title}' encerrada. "
                f"Mundo: {current.world}. Falas registradas: {len(messages)}. "
                f"Arquivo local: {out_file.resolve()}."
            )
            if excerpt:
                sync_line += f" Abertura da sessao: {excerpt}"
            inferred_chunks: list[str] = []
            summary = str(session_notes.get("summary", "")).strip()
            if summary:
                inferred_chunks.append(f"Resumo: {summary}")
            objectives = session_notes.get("objectives", [])
            if isinstance(objectives, list) and objectives:
                inferred_chunks.append(f"Objetivos observados: {' | '.join(str(item) for item in objectives)}")
            relations = session_notes.get("relations", [])
            if isinstance(relations, list) and relations:
                inferred_chunks.append(f"Relacoes observadas: {' | '.join(str(item) for item in relations)}")
            secrets = session_notes.get("secrets", [])
            if isinstance(secrets, list) and secrets:
                inferred_chunks.append(f"Segredos citados: {' | '.join(str(item) for item in secrets)}")
            if inferred_chunks:
                sync_line += " " + " ".join(inferred_chunks)
            sync_line += " Revise a ficha do personagem se houve mudanca mecanica nesta sessao."
            append_result = await onenote_append_to_page(
                {"page_id": active_character.page_id, "content": sync_line},
                ctx,
            )
            if append_result.success:
                one_note_sync_status = "appended"
            else:
                one_note_sync_status = "failed"
                one_note_sync_error = append_result.message

        return ActionResult(
            success=True,
            message=f"Gravacao encerrada e salva em {out_file.name}.",
            data={
                "recording_active": False,
                "session_file": str(out_file.resolve()),
                "messages_recorded": len(messages),
                "active_character_name": active_character.name if active_character else None,
                "one_note_character_page_sync": one_note_sync_status,
                "one_note_character_page_error": one_note_sync_error,
            },
        )

    return ActionResult(success=False, message="Modo invalido. Use start, stop ou status.", error="invalid mode")


async def rpg_write_session_summary(
    params: JsonObject,
    ctx: ActionContext,
    *,
    recording_key: Any,
    rpg_last_session_files: dict[str, str],
    build_session_summary: Any,
) -> ActionResult:
    key = recording_key(ctx.participant_identity, ctx.room)
    session_file = str(params.get("session_file", "")).strip() or rpg_last_session_files.get(key, "")
    if not session_file:
        return ActionResult(success=False, message="Nao encontrei sessao para resumir.", error="missing session file")
    path = Path(session_file)
    if not path.exists():
        return ActionResult(success=False, message="Arquivo de sessao nao encontrado.", error="file not found")

    content = path.read_text(encoding="utf-8", errors="ignore")
    messages: list[dict[str, str]] = []
    for line in content.splitlines():
        text = line.strip()
        if text.startswith("**Jogador:**"):
            messages.append({"role": "user", "content": text.replace("**Jogador:**", "", 1).strip()})
        elif text.startswith("**Jarvez:**"):
            messages.append({"role": "assistant", "content": text.replace("**Jarvez:**", "", 1).strip()})

    summary_md = build_session_summary(path.stem, messages)
    summary_file = path.with_name(path.stem + "_resumo.md")
    summary_file.write_text(summary_md, encoding="utf-8")
    return ActionResult(
        success=True,
        message="Resumo da sessao criado com sucesso.",
        data={"summary_file": str(summary_file.resolve()), "session_file": str(path.resolve())},
    )


async def rpg_ideate_next_session(
    params: JsonObject,
    ctx: ActionContext,
    *,
    recording_key: Any,
    rpg_last_session_files: dict[str, str],
    rpg_notes_dir: Any,
) -> ActionResult:
    key = recording_key(ctx.participant_identity, ctx.room)
    session_file = str(params.get("session_file", "")).strip() or rpg_last_session_files.get(key, "")
    if not session_file:
        return ActionResult(success=False, message="Nao encontrei sessao anterior para gerar ideias.", error="missing session file")
    path = Path(session_file)
    if not path.exists():
        return ActionResult(success=False, message="Arquivo de sessao nao encontrado.", error="file not found")

    raw = path.read_text(encoding="utf-8", errors="ignore")
    seed = raw.lower()
    ideas = [
        "Abrir com consequencia direta da ultima decisao do grupo.",
        "Introduzir um NPC com motivacao ambigua e informacao incompleta.",
        "Criar um conflito com limite de tempo para aumentar tensao.",
        "Conectar um gancho pessoal de um personagem ao arco principal.",
    ]
    if "morreu" in seed or "morte" in seed:
        ideas.append("Explorar impacto da perda com chance de vinganca, luto ou legado.")
    if "drag" in seed or "dragao" in seed:
        ideas.append("Escalar para uma ameaca ancestral com pistas progressivas.")

    ideas_dir = rpg_notes_dir() / "next_session_ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    ideas_file = ideas_dir / f"ideias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    ideas_file.write_text("# Ideias para Proxima Sessao\n\n" + "\n".join(f"- {idea}" for idea in ideas) + "\n", encoding="utf-8")
    return ActionResult(
        success=True,
        message="Ideias da proxima sessao geradas.",
        data={"ideas": ideas, "ideas_file": str(ideas_file.resolve()), "session_file": str(path.resolve())},
    )
