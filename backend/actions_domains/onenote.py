from __future__ import annotations

import html
from collections.abc import Callable
from typing import Any

from actions_core import ActionContext, ActionResult

JsonObject = dict[str, Any]


async def onenote_status(
    params: JsonObject,
    ctx: ActionContext,
    *,
    onenote_initialize_cache: Callable[[], None],
    onenote_api_request: Callable[..., tuple[JsonObject | list[Any] | str | None, ActionResult | None]],
) -> ActionResult:
    _ = params, ctx
    onenote_initialize_cache()
    me_payload, me_error = onenote_api_request("GET", "me")
    if me_error is not None:
        return me_error

    notebooks_payload, notebooks_error = onenote_api_request("GET", "me/onenote/notebooks", params={"$top": 20})
    if notebooks_error is not None:
        return notebooks_error

    notebooks: list[JsonObject] = []
    if isinstance(notebooks_payload, dict):
        values = notebooks_payload.get("value", [])
        if isinstance(values, list):
            notebooks = [item for item in values if isinstance(item, dict)]

    return ActionResult(
        success=True,
        message="OneNote conectado e pronto para uso.",
        data={
            "onenote_connected": True,
            "display_name": me_payload.get("displayName") if isinstance(me_payload, dict) else None,
            "user_principal_name": me_payload.get("userPrincipalName") if isinstance(me_payload, dict) else None,
            "notebooks_count": len(notebooks),
            "notebooks": [
                {"id": str(nb.get("id", "")), "displayName": str(nb.get("displayName", ""))}
                for nb in notebooks[:10]
            ],
        },
    )


async def onenote_list_notebooks(
    params: JsonObject,
    ctx: ActionContext,
    *,
    onenote_api_request: Callable[..., tuple[JsonObject | list[Any] | str | None, ActionResult | None]],
) -> ActionResult:
    _ = ctx
    payload, error = onenote_api_request("GET", "me/onenote/notebooks", params={"$top": 100})
    if error is not None:
        return error
    notebooks = payload.get("value", []) if isinstance(payload, dict) else []
    if not isinstance(notebooks, list):
        notebooks = []

    query = str(params.get("query", "")).strip().casefold()
    mapped: list[JsonObject] = []
    for notebook in notebooks:
        if not isinstance(notebook, dict):
            continue
        display_name = str(notebook.get("displayName", "")).strip()
        if query and query not in display_name.casefold():
            continue
        mapped.append(
            {
                "id": str(notebook.get("id", "")),
                "displayName": display_name,
                "createdDateTime": notebook.get("createdDateTime"),
                "lastModifiedDateTime": notebook.get("lastModifiedDateTime"),
                "isDefault": bool(notebook.get("isDefault")),
            }
        )
    limited = mapped[:20]
    return ActionResult(
        success=True,
        message=f"{len(mapped)} caderno(s) OneNote encontrado(s).",
        data={
            "notebooks": limited,
            "total_found": len(mapped),
            "truncated": len(mapped) > len(limited),
        },
    )


async def onenote_list_sections(
    params: JsonObject,
    ctx: ActionContext,
    *,
    onenote_api_request: Callable[..., tuple[JsonObject | list[Any] | str | None, ActionResult | None]],
) -> ActionResult:
    _ = ctx
    payload, error = onenote_api_request("GET", "me/onenote/sections", params={"$top": 100})
    if error is not None:
        return error
    sections = payload.get("value", []) if isinstance(payload, dict) else []
    if not isinstance(sections, list):
        sections = []

    notebook_name = str(params.get("notebook_name", "")).strip().casefold()
    notebook_id = str(params.get("notebook_id", "")).strip()
    mapped: list[JsonObject] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        parent_name = ""
        parent_id = ""
        parent = section.get("parentNotebook")
        if isinstance(parent, dict):
            parent_name = str(parent.get("displayName", ""))
            parent_id = str(parent.get("id", ""))
        if notebook_name and notebook_name not in parent_name.casefold():
            continue
        if notebook_id and notebook_id != parent_id:
            continue
        mapped.append(
            {
                "id": str(section.get("id", "")),
                "displayName": str(section.get("displayName", "")),
                "createdDateTime": section.get("createdDateTime"),
                "lastModifiedDateTime": section.get("lastModifiedDateTime"),
                "parentNotebook": parent_name,
                "parentNotebookId": parent_id,
            }
        )
    limited = mapped[:20]
    return ActionResult(
        success=True,
        message=f"{len(mapped)} secao(oes) OneNote encontradas.",
        data={
            "sections": limited,
            "total_found": len(mapped),
            "truncated": len(mapped) > len(limited),
        },
    )


async def onenote_list_pages(
    params: JsonObject,
    ctx: ActionContext,
    *,
    onenote_api_request: Callable[..., tuple[JsonObject | list[Any] | str | None, ActionResult | None]],
    quote_path_segment: Callable[[str], str],
) -> ActionResult:
    _ = ctx
    section_id = str(params.get("section_id", "")).strip()
    section_name = str(params.get("section_name", "")).strip().casefold()
    title_query = str(params.get("query", "")).strip().casefold()

    if not section_id and not section_name:
        return ActionResult(
            success=False,
            message="Informe section_id ou section_name para listar paginas com seguranca.",
            error="missing section",
        )

    sections_payload, sections_error = onenote_api_request("GET", "me/onenote/sections", params={"$top": 100})
    if sections_error is not None:
        return sections_error
    sections = sections_payload.get("value", []) if isinstance(sections_payload, dict) else []
    if not isinstance(sections, list):
        sections = []

    target_section: JsonObject | None = None
    for section in sections:
        if not isinstance(section, dict):
            continue
        current_id = str(section.get("id", "")).strip()
        current_name = str(section.get("displayName", "")).strip()
        if section_id and current_id == section_id:
            target_section = section
            break
        if section_name and section_name in current_name.casefold():
            target_section = section
            break

    if target_section is None:
        return ActionResult(
            success=False,
            message="Nao encontrei a secao OneNote informada.",
            error="section not found",
        )

    target_section_id = str(target_section.get("id", "")).strip()
    target_section_name = str(target_section.get("displayName", "")).strip()
    encoded_section_id = quote_path_segment(target_section_id)
    pages_payload, pages_error = onenote_api_request(
        "GET",
        f"me/onenote/sections/{encoded_section_id}/pages",
        params={"$top": 100},
    )
    if pages_error is not None:
        return pages_error
    pages = pages_payload.get("value", []) if isinstance(pages_payload, dict) else []
    if not isinstance(pages, list):
        pages = []

    mapped: list[JsonObject] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        title = str(page.get("title", "")).strip()
        if title_query and title_query not in title.casefold():
            continue
        mapped.append(
            {
                "id": str(page.get("id", "")),
                "title": title,
                "createdDateTime": page.get("createdDateTime"),
                "lastModifiedDateTime": page.get("lastModifiedDateTime"),
                "contentUrl": page.get("contentUrl"),
                "sectionId": target_section_id,
                "sectionName": target_section_name,
            }
        )

    limited = mapped[:20]
    return ActionResult(
        success=True,
        message=f"{len(mapped)} pagina(s) encontradas na secao {target_section_name}.",
        data={
            "pages": limited,
            "sectionId": target_section_id,
            "sectionName": target_section_name,
            "total_found": len(mapped),
            "truncated": len(mapped) > len(limited),
        },
    )


async def onenote_search_pages(
    params: JsonObject,
    ctx: ActionContext,
    *,
    onenote_api_request: Callable[..., tuple[JsonObject | list[Any] | str | None, ActionResult | None]],
    quote_path_segment: Callable[[str], str],
) -> ActionResult:
    _ = ctx
    query = (
        str(params.get("query", "")).strip()
        or str(params.get("title", "")).strip()
        or str(params.get("name", "")).strip()
    )
    if not query:
        return ActionResult(success=False, message="Informe uma busca para OneNote.", error="missing query")

    section_id = str(params.get("section_id", "")).strip()
    section_name = str(params.get("section_name", "")).strip().casefold()

    sections_payload, sections_error = onenote_api_request("GET", "me/onenote/sections", params={"$top": 100})
    if sections_error is not None:
        return sections_error
    sections = sections_payload.get("value", []) if isinstance(sections_payload, dict) else []
    if not isinstance(sections, list):
        sections = []

    filtered_sections: list[JsonObject] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        current_section_id = str(section.get("id", "")).strip()
        current_section_name = str(section.get("displayName", "")).strip()
        if section_id and section_id != current_section_id:
            continue
        if section_name and section_name not in current_section_name.casefold():
            continue
        filtered_sections.append(section)

    if not filtered_sections:
        return ActionResult(
            success=False,
            message="Nao encontrei secao OneNote compativel para fazer a busca.",
            data={"query": query},
            error="section not found",
        )

    q = query.casefold()
    filtered = []
    for section in filtered_sections[:40]:
        current_section_id = str(section.get("id", "")).strip()
        current_section_name = str(section.get("displayName", "")).strip()
        encoded_section_id = quote_path_segment(current_section_id)
        pages_payload, pages_error = onenote_api_request(
            "GET",
            f"me/onenote/sections/{encoded_section_id}/pages",
            params={"$top": 100},
        )
        if pages_error is not None:
            return pages_error
        pages = pages_payload.get("value", []) if isinstance(pages_payload, dict) else []
        if not isinstance(pages, list):
            continue

        for page in pages:
            if not isinstance(page, dict):
                continue
            title = str(page.get("title", ""))
            if q in title.casefold():
                filtered.append(
                    {
                        "id": str(page.get("id", "")),
                        "title": title,
                        "createdDateTime": page.get("createdDateTime"),
                        "lastModifiedDateTime": page.get("lastModifiedDateTime"),
                        "contentUrl": page.get("contentUrl"),
                        "sectionId": current_section_id,
                        "sectionName": current_section_name,
                    }
                )
        if len(filtered) >= 20:
            break

    limited = filtered[:20]
    return ActionResult(
        success=True,
        message=f"{len(filtered)} pagina(s) encontradas para '{query}'.",
        data={
            "query": query,
            "pages": limited,
            "total_found": len(filtered),
            "truncated": len(filtered) > len(limited),
        },
    )


async def onenote_get_page_content(
    params: JsonObject,
    ctx: ActionContext,
    *,
    onenote_api_request: Callable[..., tuple[JsonObject | list[Any] | str | None, ActionResult | None]],
    quote_path_segment: Callable[[str], str],
    strip_html_for_preview: Callable[[str], str],
) -> ActionResult:
    _ = ctx
    page_id = str(params.get("page_id", "")).strip()
    if not page_id:
        return ActionResult(success=False, message="Informe o page_id do OneNote.", error="missing page_id")
    encoded_page_id = quote_path_segment(page_id)

    content, error = onenote_api_request(
        "GET",
        f"me/onenote/pages/{encoded_page_id}/content",
        extra_headers={"Accept": "text/html"},
    )
    if error is not None:
        return error
    html_content = str(content or "")
    return ActionResult(
        success=True,
        message="Conteudo da pagina OneNote carregado.",
        data={
            "page_id": page_id,
            "content_html": html_content,
            "content_preview": strip_html_for_preview(html_content),
        },
    )


async def onenote_create_character_page(
    params: JsonObject,
    ctx: ActionContext,
    *,
    onenote_api_request: Callable[..., tuple[JsonObject | list[Any] | str | None, ActionResult | None]],
    quote_path_segment: Callable[[str], str],
) -> ActionResult:
    _ = ctx
    section_id = str(params.get("section_id", "")).strip()
    title = str(params.get("title", "")).strip()
    body = str(params.get("body", "")).strip()
    if not section_id or not title:
        return ActionResult(success=False, message="section_id e title sao obrigatorios.", error="missing params")

    safe_title = html.escape(title)
    safe_body = html.escape(body) if body else "Sem descricao inicial."
    encoded_section_id = quote_path_segment(section_id)
    html_doc = (
        "<!DOCTYPE html><html><head><title>"
        f"{safe_title}"
        "</title></head><body>"
        f"<h1>{safe_title}</h1><p>{safe_body}</p>"
        "</body></html>"
    )
    payload, error = onenote_api_request(
        "POST",
        f"me/onenote/sections/{encoded_section_id}/pages",
        raw_body=html_doc,
        extra_headers={"Content-Type": "text/html"},
    )
    if error is not None:
        return error

    page_id = str(payload.get("id", "")).strip() if isinstance(payload, dict) else ""
    links = payload.get("links", {}) if isinstance(payload, dict) else {}
    one_note_url = ""
    if isinstance(links, dict):
        one_note = links.get("oneNoteClientUrl")
        if isinstance(one_note, dict):
            one_note_url = str(one_note.get("href", ""))

    return ActionResult(
        success=True,
        message=f"Pagina de personagem '{title}' criada no OneNote.",
        data={"page_id": page_id, "title": title, "one_note_url": one_note_url},
    )


async def onenote_append_to_page(
    params: JsonObject,
    ctx: ActionContext,
    *,
    onenote_api_request: Callable[..., tuple[JsonObject | list[Any] | str | None, ActionResult | None]],
    quote_path_segment: Callable[[str], str],
) -> ActionResult:
    _ = ctx
    page_id = str(params.get("page_id", "")).strip()
    content = str(params.get("content", "")).strip()
    if not page_id or not content:
        return ActionResult(success=False, message="page_id e content sao obrigatorios.", error="missing params")

    encoded_page_id = quote_path_segment(page_id)
    commands = [
        {
            "target": "body",
            "action": "append",
            "content": f"<p>{html.escape(content)}</p>",
        }
    ]
    _, error = onenote_api_request(
        "PATCH",
        f"me/onenote/pages/{encoded_page_id}/content",
        body=commands,
        extra_headers={"Content-Type": "application/json"},
    )
    if error is not None:
        return error
    return ActionResult(
        success=True,
        message="Conteudo anexado na pagina OneNote com sucesso.",
        data={"page_id": page_id},
    )
