"""
DataAgent - i18n 国际化模块
支持多种语言切换
"""
import json
from pathlib import Path
from typing import Dict, Optional, List, Callable
from functools import lru_cache
from core.logging import get_logger

logger = get_logger("i18n")


class Translation:
    """翻译类"""
    
    def __init__(self, lang: str, data: Dict[str, str]):
        self.lang = lang
        self.data = data
    
    def get(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """获取翻译文本"""
        text = self.data.get(key, default or key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text
    
    def __call__(self, key: str, **kwargs) -> str:
        """快捷调用"""
        return self.get(key, **kwargs)


class I18nManager:
    """
    i18n 管理器
    支持多种语言切换
    """
    
    DEFAULT_LANG = "zh"
    SUPPORTED_LANGS = ["zh", "en", "ja", "ko"]
    
    def __init__(self, translations_dir: Optional[Path] = None):
        if translations_dir is None:
            translations_dir = Path.home() / ".dataagent" / "translations"
        
        self.translations_dir = translations_dir
        self.translations_dir.mkdir(parents=True, exist_ok=True)
        
        self._translations: Dict[str, Translation] = {}
        self._current_lang: str = self.DEFAULT_LANG
        
        # 初始化默认翻译
        self._init_default_translations()
        
        # 加载翻译文件
        self._load_translations()
        
        logger.info(f"I18n manager initialized (default: {self.DEFAULT_LANG})")
    
    def _init_default_translations(self):
        """初始化默认翻译"""
        # 中文
        self._translations["zh"] = Translation("zh", {
            "app.title": "DataAgent - AI 助手",
            "app.welcome": "欢迎使用 DataAgent!",
            "chat.typing": "正在输入...",
            "chat.send": "发送",
            "skills.title": "技能",
            "knowledge.title": "知识库",
            "settings.title": "设置",
            "btn.save": "保存",
            "btn.cancel": "取消",
            "btn.ok": "确定",
            "btn.delete": "删除",
            "msg.success": "操作成功",
            "msg.error": "操作失败",
            "msg.loading": "加载中...",
            "msg.not_found": "资源未找到",
            "soul.title": "人格配置",
            "workspace.title": "工作区",
            "notifications.title": "通知",
            "health.healthy": "系统健康",
            "cache.hit_rate": "缓存命中率",
            "memory.added": "记忆已添加",
            "task.created": "任务已创建",
            "task.completed": "任务已完成",
            "task.failed": "任务失败",
            "common.error": "错误",
            "common.info": "信息",
            "common.warning": "警告",
            "common.confirm": "确认",
            "common.back": "返回",
            "common.next": "下一步",
            "common.previous": "上一步",
            "common.close": "关闭",
            "common.search": "搜索",
            "common.filter": "筛选",
            "common.all": "全部",
            "admin.title": "管理面板",
            "admin.config": "配置管理",
            "admin.plugins": "插件管理",
            "admin.logs": "日志查看",
            "admin.health": "健康检查"
        })
        
        # 英文
        self._translations["en"] = Translation("en", {
            "app.title": "DataAgent - AI Assistant",
            "app.welcome": "Welcome to DataAgent!",
            "chat.typing": "Typing...",
            "chat.send": "Send",
            "skills.title": "Skills",
            "knowledge.title": "Knowledge Base",
            "settings.title": "Settings",
            "btn.save": "Save",
            "btn.cancel": "Cancel",
            "btn.ok": "OK",
            "btn.delete": "Delete",
            "msg.success": "Success",
            "msg.error": "Error",
            "msg.loading": "Loading...",
            "msg.not_found": "Not Found",
            "soul.title": "SOUL Configuration",
            "workspace.title": "Workspace",
            "notifications.title": "Notifications",
            "health.healthy": "System Healthy",
            "cache.hit_rate": "Cache Hit Rate",
            "memory.added": "Memory Added",
            "task.created": "Task Created",
            "task.completed": "Task Completed",
            "task.failed": "Task Failed",
            "common.error": "Error",
            "common.info": "Info",
            "common.warning": "Warning",
            "common.confirm": "Confirm",
            "common.back": "Back",
            "common.next": "Next",
            "common.previous": "Previous",
            "common.close": "Close",
            "common.search": "Search",
            "common.filter": "Filter",
            "common.all": "All",
            "admin.title": "Admin Panel",
            "admin.config": "Config Management",
            "admin.plugins": "Plugins",
            "admin.logs": "Logs",
            "admin.health": "Health Check"
        })
        
        # 日文
        self._translations["ja"] = Translation("ja", {
            "app.title": "DataAgent - AI アシスタント",
            "app.welcome": "DataAgent へようこそ！",
            "chat.typing": "入力中...",
            "chat.send": "送信",
            "skills.title": "スキル",
            "knowledge.title": "ナレッジベース",
            "settings.title": "設定",
            "btn.save": "保存",
            "btn.cancel": "キャンセル",
            "btn.ok": "OK",
            "btn.delete": "削除",
            "msg.success": "成功",
            "msg.error": "エラー",
            "msg.loading": "読み込み中...",
            "msg.not_found": "見つかりません"
        })
        
        # 韩文
        self._translations["ko"] = Translation("ko", {
            "app.title": "DataAgent - AI 어시스턴트",
            "app.welcome": "DataAgent에 오신 것을 환영합니다!",
            "chat.typing": "입력 중...",
            "chat.send": "전송"
        })
    
    def _load_translations(self):
        """加载翻译文件"""
        for lang_file in self.translations_dir.glob("*.json"):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                lang = lang_file.stem
                if lang in self._translations:
                    # 合并翻译
                    self._translations[lang].data.update(data)
                else:
                    self._translations[lang] = Translation(lang, data)
                
                logger.debug(f"Loaded translations: {lang}")
            except Exception as e:
                logger.warning(f"Failed to load {lang_file}: {e}")
    
    def set_lang(self, lang: str) -> bool:
        """设置语言"""
        if lang not in self.SUPPORTED_LANGS and lang not in self._translations:
            logger.warning(f"Unsupported language: {lang}")
            return False
        
        self._current_lang = lang
        logger.info(f"Language changed to: {lang}")
        return True
    
    def get_lang(self) -> str:
        """获取当前语言"""
        return self._current_lang
    
    def t(self, key: str, **kwargs) -> str:
        """获取翻译（简写）"""
        return self.translate(key, **kwargs)
    
    def translate(self, key: str, **kwargs) -> str:
        """获取翻译"""
        if self._current_lang in self._translations:
            return self._translations[self._current_lang].get(key, **kwargs)
        return key
    
    def get_translation(self, lang: str, key: str, **kwargs) -> Optional[str]:
        """获取指定语言的翻译"""
        if lang in self._translations:
            return self._translations[lang].get(key, **kwargs)
        return None
    
    def add_translation(self, lang: str, key: str, value: str):
        """添加翻译"""
        if lang not in self._translations:
            self._translations[lang] = Translation(lang, {})
        
        self._translations[lang].data[key] = value
        self._save_translation_file(lang)
    
    def add_translations(self, lang: str, translations: Dict[str, str]):
        """批量添加翻译"""
        if lang not in self._translations:
            self._translations[lang] = Translation(lang, {})
        
        self._translations[lang].data.update(translations)
        self._save_translation_file(lang)
    
    def _save_translation_file(self, lang: str):
        """保存翻译文件"""
        if lang not in self._translations:
            return
        
        try:
            file_path = self.translations_dir / f"{lang}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._translations[lang].data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save translation file: {e}")
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return list(self._translations.keys())
    
    def get_current_translation(self) -> Translation:
        """获取当前翻译对象"""
        return self._translations.get(self._current_lang, self._translations[self.DEFAULT_LANG])


# 全局 i18n 管理器
_i18n_manager: Optional[I18nManager] = None


def get_i18n_manager() -> I18nManager:
    """获取 i18n 管理器"""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager


def t(key: str, **kwargs) -> str:
    """快捷翻译函数"""
    return get_i18n_manager().t(key, **kwargs)
