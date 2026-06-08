"""Settings routes: read, write, test LLM connection, list models."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from core.database import db_manager, JSONFileBackend
from config import settings as app_settings
from services.llm_service import test_connection as llm_test_connection
import json

router = APIRouter()


def _ensure_settings_backend():
    """Lazily register the settings backend if not already present."""
    if "settings" not in db_manager._backends:
        data_path = app_settings.config_dir
        data_path.mkdir(parents=True, exist_ok=True)
        db_manager.register_backend(
            "settings",
            JSONFileBackend("settings", dict, data_path / "web_config.json"),
        )


async def _get_settings() -> dict:
    _ensure_settings_backend()
    result = await db_manager.get("settings", "default")
    return result or {}


async def _save_settings(data: dict):
    _ensure_settings_backend()
    await db_manager.set("settings", "default", data)


def _mask_settings(data: dict) -> dict:
    """Mask sensitive fields in settings."""
    if not data:
        return data
    if data.get("llm", {}).get("api_key"):
        key = data["llm"]["api_key"]
        if len(key) > 8:
            data["llm"]["api_key"] = key[:4] + "****" + key[-4:]
        else:
            data["llm"]["api_key"] = "****"
    if data.get("langsmith", {}).get("api_key"):
        key = data["langsmith"]["api_key"]
        if len(key) > 8:
            data["langsmith"]["api_key"] = key[:4] + "****" + key[-4:]
        else:
            data["langsmith"]["api_key"] = "****"
    return data


# ==================== Settings CRUD ====================

@router.get("/api/settings")
async def get_settings():
    data = await _get_settings()
    return JSONResponse(_mask_settings(data))


@router.post("/api/settings")
async def update_settings(request: Request):
    data = await request.json()
    await _save_settings(data)
    return JSONResponse({"success": True, "settings": data})


# ==================== Schema ====================

_VALID_SCHEMAS = {"settings", "llm", "knowledge", "agent", "skill", "database"}

@router.get("/api/schema/{schema_type}")
async def get_schema(schema_type: str):
    if schema_type not in _VALID_SCHEMAS:
        raise HTTPException(status_code=400, detail=f"Unknown schema type: {schema_type}")
    schema_file = app_settings.config_dir / "schema" / f"{schema_type}_schema.json"
    if not schema_file.exists():
        raise HTTPException(status_code=404, detail="Schema not found")
    with open(schema_file, 'r', encoding='utf-8') as f:
        return JSONResponse(json.load(f))


# ==================== Validate / Test / Import-Export / Model List ====================

@router.post("/api/settings/validate")
async def validate_settings(request: Request):
    data = await request.json()
    errors = []
    llm = data.get("llm", {})
    provider = llm.get("provider", "")

    if not llm.get("api_key"):
        if provider != "ollama":
            errors.append({"field": "llm.api_key", "message": "API Key is required"})

    if llm.get("max_tokens") and llm["max_tokens"] < 1:
        errors.append({"field": "llm.max_tokens", "message": "max_tokens must be > 0"})

    if llm.get("temperature") is not None:
        temp = llm["temperature"]
        if temp < 0 or temp > 2:
            errors.append({"field": "llm.temperature", "message": "temperature must be 0-2"})

    if llm.get("top_p") is not None:
        top_p = llm["top_p"]
        if top_p < 0 or top_p > 1:
            errors.append({"field": "llm.top_p", "message": "top_p must be 0-1"})

    if provider == "azure":
        if not llm.get("api_version"):
            errors.append({"field": "llm.api_version", "message": "Azure requires api_version"})
        if not llm.get("deployment_name"):
            errors.append({"field": "llm.deployment_name", "message": "Azure requires deployment_name"})

    return JSONResponse({"valid": len(errors) == 0, "errors": errors})


@router.post("/api/settings/test-connection")
async def test_api_connection(request: Request):
    result = await llm_test_connection()
    return JSONResponse(result)


@router.post("/api/settings/verify-model")
async def verify_model(request: Request):
    data = await request.json()
    model = data.get("llm", {}).get("model", "")
    if not model:
        return JSONResponse({"success": False, "message": "Model name is required", "error_type": "missing_model"})
    from services.llm_service import verify_model_exists
    ok = await verify_model_exists(model)
    return JSONResponse({"success": ok, "model": model})


@router.post("/api/settings/list-models")
async def list_models(request: Request):
    from services.llm_service import list_available_models
    models = await list_available_models()
    return JSONResponse({"models": models})


@router.post("/api/settings/account-info")
async def get_account_info_endpoint(request: Request):
    from services.llm_service import get_account_info
    info = await get_account_info()
    return JSONResponse(info)


@router.get("/api/settings/export")
async def export_settings():
    data = await _get_settings()
    return JSONResponse(_mask_settings(data))


@router.post("/api/settings/import")
async def import_settings(request: Request):
    data = await request.json()
    try:
        await _save_settings(data)
        return JSONResponse({"success": True, "message": "Settings imported"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid settings format: {str(e)}")


# ==================== Model Providers and Configurations ====================

@router.get("/api/settings/providers")
async def get_providers():
    providers = [
        {
            "id": "openai",
            "name": "OpenAI",
            "default_base_url": "https://api.openai.com/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000},
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_window": 128000},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_window": 128000},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_window": 16384},
            ],
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "default_base_url": "https://api.anthropic.com/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "models": [
                {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context_window": 200000},
                {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_window": 200000},
                {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context_window": 200000},
                {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_window": 200000},
            ],
        },
        {
            "id": "ollama",
            "name": "Ollama",
            "default_base_url": "http://localhost:11434/v1",
            "requires_api_key": False,
            "required_fields": ["model"],
            "models": [
                {"id": "llama3", "name": "LLaMA 3", "context_window": 8192},
                {"id": "llama3.1", "name": "LLaMA 3.1", "context_window": 128000},
                {"id": "mistral", "name": "Mistral", "context_window": 8192},
                {"id": "qwen", "name": "Qwen", "context_window": 8192},
            ],
        },
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "default_base_url": "https://api.deepseek.com/v1",
            "requires_api_key": True,
            "required_fields": ["api_key", "model"],
            "models": [
                {"id": "deepseek-chat", "name": "DeepSeek Chat", "context_window": 8192},
                {"id": "deepseek-coder", "name": "DeepSeek Coder", "context_window": 16384},
                {"id": "deepseek-r1", "name": "DeepSeek R1", "context_window": 128000},
            ],
        },
    ]
    return JSONResponse(providers)


@router.get("/api/settings/models")
async def get_available_models():
    models = [
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "context_window": 128000},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai", "context_window": 128000},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "openai", "context_window": 128000},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai", "context_window": 16384},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic", "context_window": 200000},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic", "context_window": 200000},
        {"id": "llama3", "name": "LLaMA 3", "provider": "ollama", "context_window": 8192},
        {"id": "llama3.1", "name": "LLaMA 3.1", "provider": "ollama", "context_window": 128000},
        {"id": "deepseek-chat", "name": "DeepSeek Chat", "provider": "deepseek", "context_window": 8192},
        {"id": "deepseek-coder", "name": "DeepSeek Coder", "provider": "deepseek", "context_window": 16384},
        {"id": "deepseek-r1", "name": "DeepSeek R1", "provider": "deepseek", "context_window": 128000},
    ]
    return JSONResponse(models)
