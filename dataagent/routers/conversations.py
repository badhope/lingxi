"""Conversation routes: CRUD + search + export + share."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from core.database import db_manager
from config import settings
import json, uuid, datetime, re
from pathlib import Path

router = APIRouter()


def _ensure_conversations_backend():
    """Lazily register the conversations backend if not already present."""
    from core.database import JSONFileBackend
    if "conversations" not in db_manager._backends:
        data_path = settings.data_dir
        data_path.mkdir(parents=True, exist_ok=True)
        db_manager.register_backend(
            "conversations",
            JSONFileBackend("conversations", dict, data_path / "conversations.json"),
        )


# ==================== Conversation CRUD ====================

@router.get("/api/conversations")
async def list_conversations():
    _ensure_conversations_backend()
    all_convs = await db_manager.get_all("conversations")
    return JSONResponse(list(all_convs.values()))


@router.post("/api/conversations")
async def create_conversation(request: Request):
    _ensure_conversations_backend()
    data = await request.json()
    conv_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    conversation = {
        "id": conv_id,
        "title": data.get("title", "New conversation"),
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }
    await db_manager.set("conversations", conv_id, conversation)
    return JSONResponse(conversation)


@router.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    _ensure_conversations_backend()
    conv = await db_manager.get("conversations", conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return JSONResponse(conv)


@router.put("/api/conversations/{conv_id}")
async def update_conversation(conv_id: str, request: Request):
    _ensure_conversations_backend()
    conv = await db_manager.get("conversations", conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    data = await request.json()
    conv["title"] = data.get("title", conv["title"])
    conv["messages"] = data.get("messages", conv["messages"])
    conv["updated_at"] = datetime.datetime.now().isoformat()
    await db_manager.set("conversations", conv_id, conv)
    return JSONResponse(conv)


@router.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    _ensure_conversations_backend()
    exists = await db_manager.exists("conversations", conv_id)
    if not exists:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db_manager.delete("conversations", conv_id)
    return JSONResponse({"success": True, "message": "Conversation deleted"})


# ==================== Search ====================

@router.get("/api/conversations/search")
async def search_conversations(q: str = ""):
    _ensure_conversations_backend()
    if not q:
        return JSONResponse([])
    all_convs = await db_manager.get_all("conversations")
    results = []
    for conv_id, conv in all_convs.items():
        title_match = q.lower() in conv.get("title", "").lower()
        content_match = False
        for msg in conv.get("messages", []):
            if q.lower() in msg.get("content", "").lower():
                content_match = True
                break
        if title_match or content_match:
            results.append({
                "id": conv_id,
                "title": conv.get("title", ""),
                "updated_at": conv.get("updated_at", ""),
                "match_type": "title" if title_match else "content",
            })
    results.sort(key=lambda x: x["updated_at"], reverse=True)
    return JSONResponse(results)


# ==================== Export ====================

@router.get("/api/conversations/{conv_id}/export")
async def export_conversation(conv_id: str, format: str = "json"):
    _ensure_conversations_backend()
    conv = await db_manager.get("conversations", conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if format in ("markdown", "md"):
        lines = [f"# {conv.get('title', 'Conversation')}\n"]
        lines.append(f"Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        lines.append("---\n\n")
        for msg in conv.get("messages", []):
            role = "User" if msg.get("type") == "user" else "Assistant" if msg.get("type") == "assistant" else "System"
            lines.append(f"**{role}**:\n\n{msg.get('content', '')}\n\n")
        content = "\n".join(lines)
        return JSONResponse({"format": "markdown", "content": content})
    return JSONResponse({"format": "json", "content": conv})


# ==================== Share ====================

@router.post("/api/conversations/{conv_id}/share")
async def share_conversation(conv_id: str):
    _ensure_conversations_backend()
    conv = await db_manager.get("conversations", conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    share_id = str(uuid.uuid4())[:8]
    if not re.match(r'^[a-zA-Z0-9]+$', share_id):
        raise HTTPException(status_code=400, detail="Invalid share ID")
    share_dir = settings.data_dir / "shares"
    share_dir.mkdir(parents=True, exist_ok=True)
    share_file = share_dir / f"{share_id}.json"
    with open(share_file, 'w', encoding='utf-8') as f:
        json.dump({
            "id": share_id,
            "conversation": conv,
            "created_at": datetime.datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)
    return JSONResponse({"share_id": share_id, "share_url": f"/api/conversations/shared/{share_id}"})


@router.get("/api/conversations/shared/{share_id}")
async def get_shared_conversation(share_id: str):
    if not re.match(r'^[a-zA-Z0-9]+$', share_id):
        raise HTTPException(status_code=400, detail="Invalid share ID")
    share_file = settings.data_dir / "shares" / f"{share_id}.json"
    if not share_file.exists():
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    with open(share_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return JSONResponse(data)
