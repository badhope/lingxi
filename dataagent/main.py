"""
DataAgent - 万能智能助手
模块化 Web 应用入口
"""
import sys
import os
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from core import config_manager, get_logger

# 初始化日志
logger = get_logger(__name__)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import HTMLResponse

# 导入润色处理函数
from services.polish_service import handle_polish_request

# 初始化数据库（使用新的核心数据库模块）
from core.database import init_database
init_database()

# 创建 FastAPI 应用
app = FastAPI(title="DataAgent", description="万能智能助手")

# 从核心配置获取 CORS 配置
allowed_origins = config_manager.security.cors_origins

# CORS 中间件 - 改进的安全配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 鲁棒性中间件
from middleware.error_handler import ErrorHandlerMiddleware
from middleware.rate_limiter import RateLimitMiddleware

app.add_middleware(ErrorHandlerMiddleware)
# 从核心配置获取速率限制配置
max_requests = config_manager.security.rate_limit_max_requests
window_seconds = config_manager.security.rate_limit_window
app.add_middleware(RateLimitMiddleware, max_requests=max_requests, window_seconds=window_seconds)

# WebSocket 端点 - 必须在其他路由之前定义
from services.agent_service import run_universal_agent
from services.input_sanitizer import validate_message
from services.intent_router import route_intent

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = id(websocket)
    logger.info(f"WebSocket [{connection_id}] Connection started")
    
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "message")
            
            logger.debug(f"WebSocket [{connection_id}] Received message type: {message_type}")
            
            message = data.get("content", "")
            options = data.get("options", {})
            files = data.get("files", [])
            client_settings = data.get("settings", {})

            # 从核心配置获取默认值
            default_llm = config_manager.llm.get("default", {})
            default_api_key = default_llm.api_key if hasattr(default_llm, 'api_key') else ''
            default_base_url = default_llm.base_url if hasattr(default_llm, 'base_url') else 'https://dashscope.aliyuncs.com/compatible-mode/v1'
            default_model = default_llm.model if hasattr(default_llm, 'model') else 'qwen-plus-latest'
            default_temperature = default_llm.temperature if hasattr(default_llm, 'temperature') else 0.7
            default_max_tokens = default_llm.max_tokens if hasattr(default_llm, 'max_tokens') else 8192
            
            settings = {
                "llm": {
                    "provider": client_settings.get("provider", default_llm.provider if hasattr(default_llm, 'provider') else "aliyun"),
                    "api_key": client_settings.get("apiKey", client_settings.get("api_key", default_api_key)),
                    "base_url": client_settings.get("apiUrl", client_settings.get("api_url", default_base_url)),
                    "model": client_settings.get("model", default_model),
                    "temperature": client_settings.get("temperature", default_temperature),
                    "max_tokens": client_settings.get("maxTokens", client_settings.get("max_tokens", default_max_tokens)),
                    "top_p": 0.9
                },
                "sandbox": {
                    "enabled": config_manager.sandbox.use_sandbox,
                    "timeout": config_manager.sandbox.timeout
                }
            }

            # 处理润色请求
            if message_type == "polish":
                logger.info(f"WebSocket [{connection_id}] Handling polish request")
                text = data.get("content", "")
                style = data.get("style", "academic")
                await handle_polish_request(text, style, websocket, settings)
                continue

            # 输入验证
            validation = validate_message(message)
            if not validation["valid"]:
                logger.warning(f"WebSocket [{connection_id}] Message validation failed: {validation['error']}")
                await websocket.send_json({"type": "error", "content": validation["error"]})
                continue

            # 使用净化后的输入
            if validation.get("sanitized") != message:
                message = validation["sanitized"]
                if validation.get("warning"):
                    await websocket.send_json({
                        "type": "thinking",
                        "title": "⚠️ 安全提示",
                        "content": validation["warning"]
                    })

            # 意图识别：检查是否匹配特定功能
            intent_result = await route_intent(message, files, websocket, settings)
            if intent_result:
                # 已由意图路由处理，跳过通用Agent
                continue

            # 通用Agent处理
            logger.info(f"WebSocket [{connection_id}] Running universal agent")
            await run_universal_agent(websocket, message, settings=settings, options=options)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket [{connection_id}] Connection closed by client")
    except Exception as e:
        logger.error(f"WebSocket [{connection_id}] Error: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "content": "发生了一个错误，请稍后重试"
            })
        except:
            pass

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(config_manager.paths.base_dir / "static")), name="static")

# 注册路由 - 使用 try-except 避免单个依赖问题阻止启动
def safe_register_router(router_name, import_path, prefix=None):
    try:
        module = __import__(import_path, fromlist=['router'])
        router = module.router
        if prefix:
            app.include_router(router, prefix=prefix)
        else:
            app.include_router(router)
        logger.info(f"✅ 加载路由成功: {router_name}")
    except Exception as e:
        logger.warning(f"⚠️ 加载路由失败: {router_name} - {str(e)}")

# 基础路由（这些应该总是可用）
safe_register_router("auth", "routers.auth")
safe_register_router("settings", "routers.settings")
safe_register_router("knowledge", "routers.knowledge")
safe_register_router("skills", "routers.skills")
safe_register_router("mcp", "routers.mcp")
safe_register_router("conversations", "routers.conversations")

# 可选路由（需要额外依赖）
safe_register_router("databases", "routers.databases")
safe_register_router("financial", "routers.financial")
safe_register_router("nl2sql", "routers.nl2sql")
safe_register_router("visualization", "routers.visualization")
safe_register_router("agent", "routers.agent")
safe_register_router("feedback", "routers.feedback")
safe_register_router("documents", "routers.documents")  # 需要 pdfplumber
safe_register_router("logs", "routers.logs")
safe_register_router("vector_stores", "routers.vector_stores")
safe_register_router("data_analysis", "routers.data_analysis")
safe_register_router("agent_market", "routers.agent_market")
safe_register_router("plugins", "routers.plugins")
safe_register_router("workflows", "routers.workflows")
safe_register_router("llm_ops", "routers.llm_ops")
safe_register_router("openclaw", "routers.openclaw")
safe_register_router("workspace", "routers.workspace", prefix="/api/workspace")
safe_register_router("media", "routers.media", prefix="/api/media")
safe_register_router("advanced", "routers.advanced", prefix="/api/advanced")
safe_register_router("skillhub", "routers.skillhub", prefix="/api/skillhub")
safe_register_router("dashboard", "routers.dashboard", prefix="/api/dashboard")
safe_register_router("admin", "routers.admin", prefix="/api/admin")
safe_register_router("websocket", "routers.websocket")
safe_register_router("i18n", "routers.i18n", prefix="/api/i18n")
safe_register_router("exporter", "routers.exporter", prefix="/api/exporter")

# 注册内置插件
try:
    from core.plugins_builtin import register_builtin_plugins
    _has_plugins = True
except Exception as e:
    logger.warning(f"⚠️ 插件模块加载失败: {str(e)}")
    _has_plugins = False


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化内置插件"""
    if _has_plugins:
        try:
            await register_builtin_plugins()
            logger.info("✅ Built-in plugins registered successfully")
        except Exception as e:
            logger.error(f"❌ Failed to register built-in plugins: {e}", exc_info=True)
    else:
        logger.info("⏭️ 插件注册跳过（模块未加载）")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "DataAgent"}

@app.post("/api/test-connection")
async def test_connection(request: dict):
    """测试LLM连接"""
    from openai import AsyncOpenAI
    try:
        client = AsyncOpenAI(
            api_key=request.get("apiKey", request.get("api_key", "")),
            base_url=request.get("apiUrl", request.get("api_url", ""))
        )
        await client.chat.completions.create(
            model=request.get("model", "qwen-plus-latest"),
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return {"success": True, "message": "连接成功"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/install-package")
async def install_package(request: dict):
    """安装Python包"""
    import subprocess
    package = request.get("package", "")
    if not package:
        return {"success": False, "error": "请提供包名"}

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return {"success": True, "message": f"{package} 安装成功"}
        else:
            return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "安装超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 首页路由 - 聊天界面
@app.get("/")
async def get():
    html_path = config_manager.paths.base_dir / "templates" / "index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# 日志查看器页面路由
@app.get("/logs")
async def logs():
    html_path = config_manager.paths.base_dir / "templates" / "logs.html"
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/plugins")
async def plugins():
    html_path = config_manager.paths.base_dir / "templates" / "plugins.html"
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# 管理界面路由 - 暂时移除（web/ 已归档）
# @app.get("/agents")
# @app.get("/skills")
# @app.get("/mcp")

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="DataAgent Web Interface")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    logger.info("Starting DataAgent Web Interface...")
    uvicorn.run(app, host=args.host, port=args.port)
