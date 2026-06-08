"""Skills routes: list, CRUD, generate, import/export."""
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from core.database import db_manager, JSONFileBackend
from config import settings as app_settings
from services.llm_service import call_llm, call_llm_json
import json, uuid, datetime

logger = logging.getLogger(__name__)

router = APIRouter()


def _ensure_skills_backend():
    """Lazily register the skills backend if not already present."""
    if "skills" not in db_manager._backends:
        data_path = app_settings.data_dir
        data_path.mkdir(parents=True, exist_ok=True)
        db_manager.register_backend(
            "skills",
            JSONFileBackend("skills", dict, data_path / "skills.json"),
        )


# ==================== Skill Templates ====================

@router.get("/api/skills")
async def list_skills():
    _ensure_skills_backend()
    all_skills = await db_manager.get_all("skills")
    return JSONResponse(list(all_skills.values()))


@router.get("/api/skills/templates")
async def get_skill_templates():
    templates = [
        {
            "id": "code-review",
            "name": "Code Review",
            "description": "Code review and quality analysis",
            "category": "code",
            "prompts": {
                "system_prompt": "You are a code reviewer. Find bugs, style issues, and suggest improvements.",
                "user_prompt_template": "Review the following code:\n\n{{input}}"
            }
        },
        {
            "id": "data-analyst",
            "name": "Data Analyst",
            "description": "Data analysis and visualization",
            "category": "data",
            "prompts": {
                "system_prompt": "You are a data analyst. Clean, summarize, and visualize data.",
                "user_prompt_template": "Analyze the following data:\n\n{{input}}"
            }
        },
        {
            "id": "translator",
            "name": "Translator",
            "description": "Multi-language translation",
            "category": "translation",
            "prompts": {
                "system_prompt": "You are a professional translator. Translate accurately and naturally.",
                "user_prompt_template": "Translate the following into {{target_language}}:\n\n{{input}}"
            },
            "parameters": [
                {"name": "target_language", "type": "string", "default": "English", "description": "Target language"}
            ]
        },
        {
            "id": "writer",
            "name": "Writer",
            "description": "Copy writing and editing",
            "category": "writing",
            "prompts": {
                "system_prompt": "You are a writing assistant. Help with drafting, editing, and polishing text.",
                "user_prompt_template": "{{action}} the following:\n\n{{input}}"
            },
            "parameters": [
                {"name": "action", "type": "select", "options": ["polish", "expand", "summarize", "rewrite"], "default": "polish"}
            ]
        },
        {
            "id": "summarizer",
            "name": "Summarizer",
            "description": "Content summarization and key-point extraction",
            "category": "document",
            "prompts": {
                "system_prompt": "You are a summarizer. Extract key points and produce concise summaries.",
                "user_prompt_template": "Summarize the following:\n\n{{input}}"
            }
        }
    ]
    return JSONResponse(templates)


# ==================== Skill CRUD ====================

@router.post("/api/skills/generate")
async def generate_skill(request: Request):
    try:
        data = await request.json()
        purpose = data.get("purpose", "")
        logger.info(f"Generating skill for purpose: {purpose}")

        if not purpose:
            raise HTTPException(status_code=400, detail="Purpose description is required")

        prompt = f"""Based on the following requirement, suggest an AI skill as JSON:
Requirement: {purpose}

Return a JSON object with:
- name: skill name (max 30 chars)
- icon: one emoji
- description: description (max 100 chars)
- category: one of: code, data, document, translation, writing, learning, creative, other

Return only JSON, nothing else."""

        result = await call_llm_json(prompt)
        if "error" in result:
            logger.error(f"Error generating skill: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])

        logger.info("Successfully generated skill")
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_skill: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/skills")
async def create_skill(request: Request):
    _ensure_skills_backend()
    data = await request.json()
    skill_id = data.get("id", str(uuid.uuid4()))
    now = datetime.datetime.now().isoformat()
    skill = {
        "id": skill_id,
        "name": data.get("name", "Untitled skill"),
        "description": data.get("description", ""),
        "version": data.get("version", "1.0.0"),
        "author": data.get("author", ""),
        "category": data.get("category", "custom"),
        "type": data.get("type", "custom"),
        "icon": data.get("icon", "zap"),
        "created_at": now,
        "updated_at": now,
        "parameters": data.get("parameters", []),
        "prompts": data.get("prompts", {}),
        "tools": data.get("tools", []),
    }
    await db_manager.set("skills", skill_id, skill)
    return JSONResponse(skill)


@router.get("/api/skills/{skill_id}")
async def get_skill(skill_id: str):
    _ensure_skills_backend()
    skill = await db_manager.get("skills", skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return JSONResponse(skill)


@router.post("/api/skills/{skill_id}/use")
async def use_skill(skill_id: str, request: Request):
    _ensure_skills_backend()
    skill = await db_manager.get("skills", skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    data = await request.json()
    params = data.get("parameters", {})
    prompt = ""
    if skill.get("prompts", {}).get("system_prompt"):
        prompt += skill["prompts"]["system_prompt"] + "\n\n"
    template = skill.get("prompts", {}).get("user_prompt_template", "{{input}}")
    user_input = params.get("input", str(params))
    prompt += template.replace("{{input}}", user_input)
    for key, value in params.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
    response = await call_llm(prompt)
    return JSONResponse({"response": response, "skill": skill.get("name", "")})


@router.put("/api/skills/{skill_id}")
async def update_skill(skill_id: str, request: Request):
    _ensure_skills_backend()
    skill = await db_manager.get("skills", skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    data = await request.json()
    skill["name"] = data.get("name", skill["name"])
    skill["description"] = data.get("description", skill["description"])
    skill["prompts"] = data.get("prompts", skill["prompts"])
    skill["updated_at"] = datetime.datetime.now().isoformat()
    await db_manager.set("skills", skill_id, skill)
    return JSONResponse(skill)


@router.delete("/api/skills/{skill_id}")
async def delete_skill(skill_id: str):
    _ensure_skills_backend()
    exists = await db_manager.exists("skills", skill_id)
    if not exists:
        raise HTTPException(status_code=404, detail="Skill not found")
    await db_manager.delete("skills", skill_id)
    return JSONResponse({"success": True, "message": "Skill deleted"})


# ==================== Import / Export ====================

@router.post("/api/skills/import")
async def import_skill(request: Request):
    _ensure_skills_backend()
    data = await request.json()
    skill_id = data.get("id", str(uuid.uuid4()))
    exists = await db_manager.exists("skills", skill_id)
    if exists:
        skill_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    skill = {
        "id": skill_id,
        "name": data.get("name", "Imported skill"),
        "description": data.get("description", ""),
        "icon": data.get("icon", "wrench"),
        "category": data.get("category", "other"),
        "version": data.get("version", "1.0.0"),
        "parameters": data.get("parameters", []),
        "prompts": data.get("prompts", {}),
        "tools": data.get("tools", []),
        "created_at": data.get("created_at", now),
        "updated_at": now,
    }
    await db_manager.set("skills", skill_id, skill)
    return JSONResponse(skill)


@router.get("/api/skills/{skill_id}/export")
async def export_skill(skill_id: str):
    _ensure_skills_backend()
    skill = await db_manager.get("skills", skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return JSONResponse(skill)


# ==================== Test ====================

@router.post("/api/skills/{skill_id}/test")
async def test_skill(skill_id: str, request: Request):
    _ensure_skills_backend()
    skill = await db_manager.get("skills", skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    data = await request.json()
    test_input = data.get("input", "test input")

    prompt = ""
    if skill.get("prompts", {}).get("system_prompt"):
        prompt += skill["prompts"]["system_prompt"] + "\n\n"
    template = skill.get("prompts", {}).get("user_prompt_template", "{{input}}")
    prompt += template.replace("{{input}}", test_input)

    try:
        response = await call_llm(prompt)
        return JSONResponse({"success": True, "response": response})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
