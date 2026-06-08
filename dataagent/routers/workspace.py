"""Workspace routes: SOUL/AGENTS/HEARTBEAT/MEMORY read/write."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json

from core.workspace import (
    get_workspace_manager,
    WorkspaceFileType,
    AgentConfig,
    HeartbeatTask,
    MemoryEntry,
)

router = APIRouter()


# ========== SOUL.md API ==========

@router.get("/soul/current")
async def get_current_soul():
    """Read current SOUL.md content."""
    wm = get_workspace_manager()
    content = wm.read_file(WorkspaceFileType.SOUL)
    return {"success": True, "content": content}


class UpdateSoulRequest(BaseModel):
    content: str


@router.put("/soul/current")
async def update_soul(request: UpdateSoulRequest):
    """Write SOUL.md content."""
    wm = get_workspace_manager()
    wm.write_file(WorkspaceFileType.SOUL, request.content)
    return {"success": True, "message": "SOUL.md updated"}


# ========== Workspace Files API ==========

@router.get("/workspace/files")
async def list_workspace_files():
    """List all workspace files."""
    wm = get_workspace_manager()
    files = wm.list_workspace_files()
    return {"success": True, "files": files}


@router.get("/workspace/files/{file_type}")
async def get_workspace_file(file_type: str):
    """Read a workspace file by type (SOUL.md, AGENTS.md, HEARTBEAT.md, MEMORY.md, config.yaml)."""
    try:
        file_enum = WorkspaceFileType(file_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Invalid file type: {file_type}")
    wm = get_workspace_manager()
    content = wm.read_file(file_enum)
    return {"success": True, "file_type": file_type, "content": content}


class WriteFileRequest(BaseModel):
    content: str


@router.put("/workspace/files/{file_type}")
async def update_workspace_file(file_type: str, request: WriteFileRequest):
    """Write a workspace file by type."""
    try:
        file_enum = WorkspaceFileType(file_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Invalid file type: {file_type}")
    wm = get_workspace_manager()
    wm.write_file(file_enum, request.content)
    return {"success": True, "message": f"{file_type} updated"}


# ========== AGENTS.md API ==========

@router.get("/workspace/agents")
async def get_agents():
    """Parse and return agent configs from AGENTS.md."""
    wm = get_workspace_manager()
    agents = wm.parse_agents_md()
    return {
        "success": True,
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "model": agent.model,
                "personality": agent.personality,
                "skills": agent.skills,
                "channels": agent.channels,
                "enabled": agent.enabled,
            }
            for agent in agents
        ],
    }


# ========== HEARTBEAT.md API ==========

@router.get("/workspace/heartbeat")
async def get_heartbeat_tasks():
    """Parse and return heartbeat tasks from HEARTBEAT.md."""
    wm = get_workspace_manager()
    tasks = wm.parse_heartbeat_md()
    return {
        "success": True,
        "tasks": [
            {
                "name": task.name,
                "description": task.description,
                "schedule": task.schedule,
                "time": task.time,
                "enabled": task.enabled,
                "type": task.task_type,
                "message": task.message,
            }
            for task in tasks
        ],
    }


# ========== MEMORY.md API ==========

class AddMemoryRequest(BaseModel):
    content: str
    memory_type: str = "note"
    tags: Optional[List[str]] = None
    importance: int = 5


@router.post("/workspace/memory")
async def add_memory(request: AddMemoryRequest):
    """Append a memory entry to MEMORY.md."""
    wm = get_workspace_manager()
    entry = wm.add_memory(
        content=request.content,
        memory_type=request.memory_type,
        tags=request.tags,
        importance=request.importance,
    )
    return {
        "success": True,
        "message": "Memory added",
        "memory": {
            "id": entry.id,
            "date": entry.date,
            "type": entry.type,
            "content": entry.content,
            "tags": entry.tags,
            "importance": entry.importance,
        },
    }


# ========== Dashboard ==========

@router.get("/dashboard")
async def dashboard():
    """Aggregate workspace info for the dashboard."""
    wm = get_workspace_manager()
    workspace_files = wm.list_workspace_files()
    agents = wm.parse_agents_md()
    heartbeat_tasks = wm.parse_heartbeat_md()

    return {
        "success": True,
        "workspace": {
            "file_count": len(workspace_files),
            "files": [{"name": f["name"], "size": f["size"]} for f in workspace_files],
        },
        "agents": {
            "count": len(agents),
            "enabled": sum(1 for a in agents if a.enabled),
        },
        "heartbeat": {
            "count": len(heartbeat_tasks),
            "enabled": sum(1 for t in heartbeat_tasks if t.enabled),
        },
    }
