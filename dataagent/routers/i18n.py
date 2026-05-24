"""
DataAgent - i18n 国际化 API
"""
from fastapi import APIRouter, Query
from typing import Dict, List
from core.i18n import get_i18n_manager, I18nManager
from core.logging import get_logger

logger = get_logger("i18n_api")

router = APIRouter()


@router.get("/languages")
def get_supported_languages() -> Dict:
    """获取支持的语言列表"""
    manager = get_i18n_manager()
    return {
        "success": True,
        "data": {
            "languages": manager.get_supported_languages(),
            "current": manager.get_lang(),
            "default": manager.DEFAULT_LANG
        }
    }


@router.get("/language")
def get_current_language() -> Dict:
    """获取当前语言"""
    manager = get_i18n_manager()
    return {
        "success": True,
        "data": {
            "lang": manager.get_lang()
        }
    }


@router.post("/language")
def set_language(lang: str = Query(..., description="语言代码")) -> Dict:
    """设置语言"""
    manager = get_i18n_manager()
    success = manager.set_lang(lang)
    
    return {
        "success": success,
        "message": f"Language set to {lang}" if success else "Failed to set language"
    }


@router.get("/translations")
def get_translations(lang: str = Query(None, description="语言代码，默认当前语言")) -> Dict:
    """获取翻译内容"""
    manager = get_i18n_manager()
    
    if lang is None:
        lang = manager.get_lang()
    
    translation = manager._translations.get(lang)
    if translation:
        return {
            "success": True,
            "data": {
                "lang": lang,
                "translations": translation.data
            }
        }
    
    return {
        "success": False,
        "message": f"Translations not found for {lang}"
    }


@router.post("/translations")
def add_translation(lang: str, key: str, value: str) -> Dict:
    """添加翻译"""
    manager = get_i18n_manager()
    manager.add_translation(lang, key, value)
    
    return {
        "success": True,
        "message": f"Translation added for {lang}.{key}"
    }


@router.post("/translations/batch")
def add_translations(lang: str, translations: Dict[str, str]) -> Dict:
    """批量添加翻译"""
    manager = get_i18n_manager()
    manager.add_translations(lang, translations)
    
    return {
        "success": True,
        "message": f"{len(translations)} translations added for {lang}"
    }


@router.get("/translate")
def translate(key: str, lang: str = Query(None)) -> Dict:
    """翻译文本"""
    manager = get_i18n_manager()
    
    if lang:
        text = manager.get_translation(lang, key)
    else:
        text = manager.t(key)
    
    return {
        "success": True,
        "data": {
            "key": key,
            "lang": lang or manager.get_lang(),
            "translation": text
        }
    }
