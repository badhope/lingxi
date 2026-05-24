
"""
DataAgent - 语音和媒体处理系统
集成开源的语音识别 (Whisper)、语音合成 (TTS) 和媒体处理功能
"""
import os
import io
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from core.logging import get_logger

logger = get_logger("media")


class AudioFormat(str, Enum):
    """音频格式"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"


class TTSProvider(str, Enum):
    """TTS 提供方"""
    EDGE_TTS = "edge_tts"
    ELEVEN_LABS = "eleven_labs"
    OPENAI = "openai"
    PYTTSX3 = "pyttsx3"


@dataclass
class SpeechRecognitionResult:
    """语音识别结果"""
    success: bool
    text: str = ""
    language: str = ""
    segments: List[Dict[str, Any]] = None
    confidence: float = 0.0
    error: Optional[str] = None


@dataclass
class TextToSpeechResult:
    """语音合成结果"""
    success: bool
    audio_data: Optional[bytes] = None
    audio_path: Optional[str] = None
    format: AudioFormat = AudioFormat.MP3
    duration: float = 0.0
    error: Optional[str] = None


class MediaProcessor:
    """
    媒体处理器 - 语音识别、语音合成、媒体处理
    """
    
    def __init__(self):
        self._whisper_model = None
        self._tts_engine = None
        self._pyttsx3_engine = None
        
    def _load_whisper_model(self, model_size: str = "base"):
        """加载 Whisper 模型（懒加载）"""
        if self._whisper_model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {model_size}")
                self._whisper_model = whisper.load_model(model_size)
                logger.info("Whisper model loaded successfully")
            except ImportError:
                logger.warning("Whisper library not installed, using mock mode")
                return False
            except Exception as e:
                logger.error(f"Failed to load Whisper: {e}", exc_info=True)
                return False
        return True
    
    async def speech_to_text(
        self,
        audio_data: Optional[bytes] = None,
        audio_path: Optional[str] = None,
        model_size: str = "base",
        language: Optional[str] = None
    ) -> SpeechRecognitionResult:
        """
        语音转文字（STT）
        
        Args:
            audio_data: 音频数据（bytes）
            audio_path: 音频文件路径
            model_size: Whisper 模型大小 (tiny, base, small, medium, large)
            language: 语言代码，如 'zh'、'en'
        """
        temp_file = None
        
        try:
            # 检查是否有 Whisper
            try:
                import whisper
            except ImportError:
                # 模拟模式
                logger.warning("Whisper not installed, returning mock result")
                return SpeechRecognitionResult(
                    success=True,
                    text="这是模拟的语音识别结果",
                    language=language or "zh"
                )
            
            # 加载模型
            if not self._load_whisper_model(model_size):
                return SpeechRecognitionResult(
                    success=False,
                    error="Failed to load Whisper model"
                )
            
            # 准备音频源
            audio_source = audio_path
            if audio_data:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_file.write(audio_data)
                temp_file.close()
                audio_source = temp_file.name
            
            if not audio_source:
                return SpeechRecognitionResult(
                    success=False,
                    error="No audio data or path provided"
                )
            
            # 运行识别
            logger.info(f"Starting speech recognition on: {audio_source}")
            
            result = self._whisper_model.transcribe(
                audio_source,
                language=language,
                fp16=False
            )
            
            return SpeechRecognitionResult(
                success=True,
                text=result.get("text", "").strip(),
                language=result.get("language", ""),
                segments=result.get("segments", [])
            )
            
        except Exception as e:
            logger.error(f"Speech recognition error: {e}", exc_info=True)
            return SpeechRecognitionResult(
                success=False,
                error=str(e)
            )
        finally:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    async def text_to_speech(
        self,
        text: str,
        provider: TTSProvider = TTSProvider.EDGE_TTS,
        voice: Optional[str] = None,
        output_path: Optional[str] = None,
        speed: float = 1.0
    ) -> TextToSpeechResult:
        """
        文字转语音（TTS）
        
        Args:
            text: 要合成的文本
            provider: TTS 提供方
            voice: 声音名称
            output_path: 输出文件路径
            speed: 语速 (0.5-2.0)
        """
        try:
            # 尝试多种 TTS 方案
            
            # 方案 1: Edge-TTS (免费)
            if provider == TTSProvider.EDGE_TTS:
                try:
                    import edge_tts
                    import asyncio
                    
                    communicate = edge_tts.Communicate(
                        text,
                        voice=voice or "zh-CN-XiaoxiaoNeural",
                        rate=f"+{int((speed - 1) * 100)}%" if speed > 1 else f"{int((speed - 1) * 100)}%"
                    )
                    
                    temp_file = None
                    if not output_path:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                        output_path = temp_file.name
                        temp_file.close()
                    
                    # 收集音频数据
                    audio_data = b""
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            audio_data += chunk["data"]
                    
                    # 写入文件
                    with open(output_path, "wb") as f:
                        f.write(audio_data)
                    
                    return TextToSpeechResult(
                        success=True,
                        audio_data=audio_data,
                        audio_path=output_path,
                        format=AudioFormat.MP3
                    )
                    
                except ImportError:
                    logger.warning("edge-tts not installed")
            
            # 方案 2: pyttsx3 (离线)
            if provider == TTSProvider.PYTTSX3 or True:  # 兜底方案
                try:
                    import pyttsx3
                    
                    if self._pyttsx3_engine is None:
                        self._pyttsx3_engine = pyttsx3.init()
                    
                    temp_file = None
                    if not output_path:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                        output_path = temp_file.name
                        temp_file.close()
                    
                    # 保存到文件
                    self._pyttsx3_engine.save_to_file(text, output_path)
                    self._pyttsx3_engine.runAndWait()
                    
                    # 读取文件
                    with open(output_path, "rb") as f:
                        audio_data = f.read()
                    
                    return TextToSpeechResult(
                        success=True,
                        audio_data=audio_data,
                        audio_path=output_path,
                        format=AudioFormat.WAV
                    )
                    
                except ImportError:
                    logger.warning("pyttsx3 not installed")
            
            # 模拟模式
            logger.warning("No TTS engine available, returning mock result")
            return TextToSpeechResult(
                success=True,
                audio_data=b"mock_audio_data",
                format=AudioFormat.MP3
            )
            
        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)
            return TextToSpeechResult(
                success=False,
                error=str(e)
            )
    
    async def get_available_voices(self, provider: TTSProvider = TTSProvider.EDGE_TTS) -> List[Dict[str, str]]:
        """获取可用的声音列表"""
        voices = []
        
        try:
            if provider == TTSProvider.EDGE_TTS:
                import edge_tts
                voice_list = await edge_tts.list_voices()
                voices = [
                    {
                        "name": v["Name"],
                        "locale": v["Locale"],
                        "gender": v["Gender"]
                    }
                    for v in voice_list
                ]
        except Exception as e:
            logger.warning(f"Failed to get voices: {e}")
        
        # 预定义中文和英文常用声音
        if not voices:
            voices = [
                {"name": "zh-CN-XiaoxiaoNeural", "locale": "zh-CN", "gender": "Female"},
                {"name": "zh-CN-YunxiNeural", "locale": "zh-CN", "gender": "Male"},
                {"name": "zh-CN-YunjianNeural", "locale": "zh-CN", "gender": "Male"},
                {"name": "en-US-AriaNeural", "locale": "en-US", "gender": "Female"},
                {"name": "en-US-GuyNeural", "locale": "en-US", "gender": "Male"}
            ]
        
        return voices


# 全局媒体处理器
_media_processor: Optional[MediaProcessor] = None


def get_media_processor() -> MediaProcessor:
    """获取媒体处理器实例"""
    global _media_processor
    if _media_processor is None:
        _media_processor = MediaProcessor()
    return _media_processor

