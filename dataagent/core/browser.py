
"""
DataAgent - 浏览器自动化工具
借鉴 OpenClaw 的浏览器自动化能力，支持网页导航、数据提取、表单填写等
"""
import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from core.logging import get_logger

logger = get_logger("browser")


class BrowserEngine(str, Enum):
    """浏览器引擎类型"""
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    PUPPETEER = "puppeteer"


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = True
    slow_mo: float = 0.0
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    timeout: int = 30000
    engine: BrowserEngine = BrowserEngine.PLAYWRIGHT
    
    # 代理配置
    proxy_server: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None


@dataclass
class ScreenshotResult:
    """截图结果"""
    success: bool
    image_data: Optional[bytes] = None
    image_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ExtractionResult:
    """数据提取结果"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    html: Optional[str] = None
    text: Optional[str] = None
    error: Optional[str] = None


class BrowserTool:
    """
    浏览器自动化工具
    提供网页浏览、数据提取、截图等功能
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._page = None
        self._playwright = None
        self._context = None
    
    async def start(self):
        """启动浏览器"""
        try:
            # 尝试使用 Playwright
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            launch_options = {
                "headless": self.config.headless,
                "slow_mo": self.config.slow_mo,
            }
            
            if self.config.proxy_server:
                launch_options["proxy"] = {
                    "server": self.config.proxy_server,
                }
                if self.config.proxy_username and self.config.proxy_password:
                    launch_options["proxy"]["username"] = self.config.proxy_username
                    launch_options["proxy"]["password"] = self.config.proxy_password
            
            self._browser = await self._playwright.chromium.launch(**launch_options)
            self._context = await self._browser.new_context(
                viewport={
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                },
                user_agent=self.config.user_agent
            )
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.config.timeout)
            
            logger.info("浏览器启动成功")
            return True
            
        except ImportError:
            logger.warning("Playwright 未安装，使用模拟模式")
            self._page = MockBrowserPage()
            return True
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}", exc_info=True)
            return False
    
    async def stop(self):
        """停止浏览器"""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}", exc_info=True)
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -&gt; bool:
        """导航到指定 URL"""
        try:
            if self._page is None:
                await self.start()
            
            if hasattr(self._page, 'goto'):
                await self._page.goto(url, wait_until=wait_until)
                logger.info(f"成功导航到: {url}")
                return True
            else:
                # 模拟模式
                logger.info(f"[模拟] 导航到: {url}")
                return True
                
        except Exception as e:
            logger.error(f"导航失败 {url}: {e}", exc_info=True)
            return False
    
    async def get_url(self) -&gt; Optional[str]:
        """获取当前 URL"""
        if self._page and hasattr(self._page, 'url'):
            return self._page.url
        return None
    
    async def get_title(self) -&gt; Optional[str]:
        """获取页面标题"""
        try:
            if self._page and hasattr(self._page, 'title'):
                return await self._page.title()
        except Exception as e:
            logger.error(f"获取标题失败: {e}", exc_info=True)
        return None
    
    async def screenshot(self, full_page: bool = False, save_path: Optional[str] = None) -&gt; ScreenshotResult:
        """截图"""
        try:
            if self._page is None:
                await self.start()
            
            if hasattr(self._page, 'screenshot'):
                image_data = await self._page.screenshot(full_page=full_page)
                
                if save_path:
                    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(image_data)
                    logger.info(f"截图已保存到: {save_path}")
                
                return ScreenshotResult(
                    success=True,
                    image_data=image_data,
                    image_path=save_path
                )
            else:
                # 模拟模式
                return ScreenshotResult(
                    success=True,
                    image_path=save_path
                )
                
        except Exception as e:
            logger.error(f"截图失败: {e}", exc_info=True)
            return ScreenshotResult(success=False, error=str(e))
    
    async def click(self, selector: str, timeout: Optional[int] = None) -&gt; bool:
        """点击元素"""
        try:
            if self._page and hasattr(self._page, 'click'):
                await self._page.click(selector, timeout=timeout or self.config.timeout)
                logger.info(f"点击元素: {selector}")
                return True
            else:
                logger.info(f"[模拟] 点击元素: {selector}")
                return True
        except Exception as e:
            logger.error(f"点击失败 {selector}: {e}", exc_info=True)
            return False
    
    async def fill(self, selector: str, value: str) -&gt; bool:
        """填充表单"""
        try:
            if self._page and hasattr(self._page, 'fill'):
                await self._page.fill(selector, value)
                logger.info(f"填充表单 {selector}")
                return True
            else:
                logger.info(f"[模拟] 填充表单 {selector}: {value}")
                return True
        except Exception as e:
            logger.error(f"填充失败 {selector}: {e}", exc_info=True)
            return False
    
    async def type_text(self, selector: str, text: str, delay: float = 0.0) -&gt; bool:
        """输入文本"""
        try:
            if self._page and hasattr(self._page, 'type'):
                await self._page.type(selector, text, delay=delay)
                logger.info(f"输入文本到 {selector}")
                return True
            else:
                logger.info(f"[模拟] 输入文本到 {selector}")
                return True
        except Exception as e:
            logger.error(f"输入失败 {selector}: {e}", exc_info=True)
            return False
    
    async def extract_text(self, selector: Optional[str] = None) -&gt; ExtractionResult:
        """提取文本"""
        try:
            if self._page is None:
                await self.start()
            
            if hasattr(self._page, 'content'):
                if selector:
                    try:
                        text = await self._page.text_content(selector)
                    except Exception:
                        text = None
                else:
                    text = await self._page.content()
                
                return ExtractionResult(
                    success=True,
                    text=text,
                    html=await self._page.content() if not selector else None
                )
            else:
                return ExtractionResult(
                    success=True,
                    text=f"[模拟] 从 {selector or '页面'} 提取的文本"
                )
                
        except Exception as e:
            logger.error(f"文本提取失败: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))
    
    async def extract_data(self, selector: str, attribute: Optional[str] = None) -&gt; ExtractionResult:
        """提取数据"""
        try:
            if self._page and hasattr(self._page, 'evaluate'):
                script = f"""
                () =&gt; {{
                    const elements = document.querySelectorAll('{selector}');
                    const data = Array.from(elements).map(el =&gt; {{
                        if ('{attribute}') {{
                            return el.getAttribute('{attribute}');
                        }}
                        return el.textContent?.trim();
                    }});
                    return data;
                }}
                """
                result = await self._page.evaluate(script)
                
                return ExtractionResult(
                    success=True,
                    data={"results": result}
                )
            else:
                return ExtractionResult(
                    success=True,
                    data={"results": [f"[模拟] {selector} 数据"]}
                )
                
        except Exception as e:
            logger.error(f"数据提取失败: {e}", exc_info=True)
            return ExtractionResult(success=False, error=str(e))
    
    async def execute_script(self, script: str) -&gt; Any:
        """执行 JavaScript"""
        try:
            if self._page and hasattr(self._page, 'evaluate'):
                return await self._page.evaluate(script)
            return None
        except Exception as e:
            logger.error(f"脚本执行失败: {e}", exc_info=True)
            return None
    
    async def scroll(self, direction: str = "down", amount: int = 500) -&gt; bool:
        """滚动页面"""
        try:
            script = ""
            if direction == "down":
                script = f"window.scrollBy(0, {amount})"
            elif direction == "up":
                script = f"window.scrollBy(0, -{amount})"
            elif direction == "bottom":
                script = "window.scrollTo(0, document.body.scrollHeight)"
            elif direction == "top":
                script = "window.scrollTo(0, 0)"
            
            if script:
                await self.execute_script(script)
                logger.info(f"滚动页面: {direction}")
                return True
            return False
        except Exception as e:
            logger.error(f"滚动失败: {e}", exc_info=True)
            return False
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -&gt; bool:
        """等待元素出现"""
        try:
            if self._page and hasattr(self._page, 'wait_for_selector'):
                await self._page.wait_for_selector(
                    selector,
                    timeout=timeout or self.config.timeout
                )
                return True
            return True
        except Exception as e:
            logger.error(f"等待元素超时 {selector}: {e}", exc_info=True)
            return False


class MockBrowserPage:
    """模拟浏览器页面（用于无 Playwright 的环境）"""
    def __init__(self):
        self.url = "about:blank"
    
    async def goto(self, url, **kwargs):
        self.url = url
    
    async def title(self):
        return "Mock Page"
    
    async def content(self):
        return "&lt;html&gt;&lt;body&gt;Mock Content&lt;/body&gt;&lt;/html&gt;"
    
    async def screenshot(self, **kwargs):
        return b"mock_image_data"


# 全局浏览器实例
_browser_tool: Optional[BrowserTool] = None


def get_browser_tool(config: Optional[BrowserConfig] = None) -&gt; BrowserTool:
    """获取浏览器工具实例"""
    global _browser_tool
    if _browser_tool is None:
        _browser_tool = BrowserTool(config)
    return _browser_tool

