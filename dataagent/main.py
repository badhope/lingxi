"""
DATA-Agent - 基于 CrewAI 的智能数据助手
统一API入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from pathlib import Path

from config import settings

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="基于 CrewAI 的智能数据助手",
    version=settings.app_version
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from routers.api import router as api_router
app.include_router(api_router)

# 保留原有核心路由（可选）
try:
    from routers.auth import router as auth_router
    app.include_router(auth_router)
except Exception:
    pass

try:
    from routers.settings import router as settings_router
    app.include_router(settings_router)
except Exception:
    pass

try:
    from routers.knowledge import router as knowledge_router
    app.include_router(knowledge_router)
except Exception:
    pass


@app.get("/")
async def root():
    """首页"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "description": "基于 CrewAI 的智能数据助手",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health():
    """API健康检查"""
    return {"status": "ok", "service": settings.app_name}


@app.get("/docs_ui")
async def docs_ui():
    """简单文档页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DATA-Agent API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #2e86de; }
            .api-item { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
            .api-method { font-weight: bold; color: #27ae60; }
            .api-path { font-family: monospace; background: #f0f0f0; padding: 5px 10px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>DATA-Agent API</h1>
        <p>基于 CrewAI 的智能数据助手</p>
        
        <div class="api-item">
            <span class="api-method">POST</span>
            <span class="api-path">/api/analyze</span>
            <p>数据分析接口 - 使用 CrewAI 团队执行数据分析</p>
        </div>
        
        <div class="api-item">
            <span class="api-method">POST</span>
            <span class="api-path">/api/knowledge/query</span>
            <p>知识库查询接口 - 使用 CrewAI 团队查询知识库</p>
        </div>
        
        <div class="api-item">
            <span class="api-method">GET</span>
            <span class="api-path">/docs</span>
            <p>Swagger UI - 完整的API文档</p>
        </div>
        
        <div class="api-item">
            <span class="api-method">GET</span>
            <span class="api-path">/health</span>
            <p>健康检查接口</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="DATA-Agent API Server")
    parser.add_argument("--port", type=int, default=settings.api_port, help="Port to run the server on")
    parser.add_argument("--host", type=str, default=settings.api_host, help="Host to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )
