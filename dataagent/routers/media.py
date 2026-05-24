
"""
DataAgent - 语音和媒体 API 路由
集成语音识别 (STT)、语音合成 (TTS) 和媒体处理功能
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import io

from core.logging import get_logger
from core.media import (
    get_media_processor,
    TTSProvider,
    AudioFormat
)

logger = get_logger("media_api")

router = APIRouter()


class STTRequest(BaseModel):
    """语音识别请求（备用方案）"""
    model: Optional[str] = "base"
    language: Optional[str] = None


class TTSRequest(BaseModel):
    """语音合成请求"""
    text: str
    provider: Optional[TTSProvider] = TTSProvider.EDGE_TTS
    voice: Optional[str] = "zh-CN-XiaoxiaoNeural"
    speed: Optional[float] = 1.0


@router.post("/speech-to-text", summary="语音识别 (STT)")
async def speech_to_text(
    audio_file: UploadFile = File(...),
    model: str = Query("base", description="Whisper 模型大小: tiny, base, small, medium, large"),
    language: Optional[str] = Query(None, description="语言代码: zh, en, ja, etc.")
):
    """
    上传音频文件，转换为文字
    
    支持的格式: wav, mp3, flac, ogg, m4a
    """
    try:
        # 读取音频文件
        audio_data = await audio_file.read()
        logger.info(f"Processing audio file: {audio_file.filename}, size: {len(audio_data)} bytes")
        
        # 调用媒体处理器
        processor = get_media_processor()
        result = await processor.speech_to_text(
            audio_data=audio_data,
            model_size=model,
            language=language
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return {
            "success": True,
            "text": result.text,
            "language": result.language,
            "segments": result.segments
        }
        
    except Exception as e:
        logger.error(f"STT error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-to-speech", summary="语音合成 (TTS)")
async def text_to_speech(request: TTSRequest):
    """
    将文字转换为语音
    
    支持多种 TTS 引擎和声音选择
    """
    try:
        processor = get_media_processor()
        result = await processor.text_to_speech(
            text=request.text,
            provider=request.provider,
            voice=request.voice,
            speed=request.speed
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        # 返回音频流
        if result.audio_data:
            return StreamingResponse(
                io.BytesIO(result.audio_data),
                media_type=f"audio/{result.format}",
                headers={
                    "Content-Disposition": f"attachment; filename=speech.{result.format}"
                }
            )
        elif result.audio_path and os.path.exists(result.audio_path):
            return FileResponse(
                result.audio_path,
                media_type=f"audio/{result.format}",
                filename=f"speech.{result.format}"
            )
        else:
            raise HTTPException(status_code=500, detail="No audio data generated")
            
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices", summary="获取可用声音列表")
async def get_voices(
    provider: TTSProvider = Query(TTSProvider.EDGE_TTS, description="TTS 提供方")
):
    """获取可用的声音列表"""
    try:
        processor = get_media_processor()
        voices = await processor.get_available_voices(provider)
        return {
            "success": True,
            "provider": provider,
            "voices": voices
        }
    except Exception as e:
        logger.error(f"Get voices error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", summary="媒体处理系统状态")
async def media_status():
    """
    检查媒体处理系统的状态和可用的库
    """
    status = {
        "success": True,
        "libraries": {},
        "features": {}
    }
    
    # 检查可用的库
    try:
        import whisper
        status["libraries"]["whisper"] = {"available": True}
        status["features"]["speech_to_text"] = True
    except ImportError:
        status["libraries"]["whisper"] = {"available": False, "note": "Install: pip install openai-whisper"}
        status["features"]["speech_to_text"] = False
    
    try:
        import edge_tts
        status["libraries"]["edge_tts"] = {"available": True}
        status["features"]["text_to_speech"] = True
    except ImportError:
        status["libraries"]["edge_tts"] = {"available": False, "note": "Install: pip install edge-tts"}
    
    try:
        import pyttsx3
        status["libraries"]["pyttsx3"] = {"available": True}
        if "text_to_speech" not in status["features"]:
            status["features"]["text_to_speech"] = True
    except ImportError:
        status["libraries"]["pyttsx3"] = {"available": False, "note": "Install: pip install pyttsx3"}
    
    return status


@router.get("/libraries/requirements", summary="推荐安装的库")
async def get_library_requirements():
    """获取推荐的安装库列表"""
    return {
        "success": True,
        "recommended": [
            {
                "name": "openai-whisper",
                "description": "OpenAI 的语音识别库",
                "install": "pip install openai-whisper",
                "optional": True,
                "note": "需要 ffmpeg: brew install ffmpeg (macOS) 或 apt install ffmpeg (Linux)"
            },
            {
                "name": "edge-tts",
                "description": "微软 Edge 的免费 TTS 库",
                "install": "pip install edge-tts",
                "optional": True,
                "note": "需要网络连接"
            },
            {
                "name": "pyttsx3",
                "description": "离线 TTS 库",
                "install": "pip install pyttsx3",
                "optional": True,
                "note": "离线使用，但质量较低"
            },
            {
                "name": "torch",
                "description": "PyTorch (Whisper 需要)",
                "install": "pip install torch",
                "optional": True,
                "note": "openai-whisper 会自动安装"
            }
        ]
    }

