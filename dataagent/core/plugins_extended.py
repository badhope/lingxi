"""
DataAgent - 扩展插件集合
提供额外的实用插件功能
"""
import random
import re
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List

from core.logging import get_logger
from core.plugins import (
    PluginMetadata,
    PluginType,
    ToolPlugin,
    AnalyticsPlugin,
    plugin_manager,
    plugins_logger,
)


class NetworkToolsPlugin(ToolPlugin):
    """网络工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="network_tools",
            name="Network Tools",
            description="HTTP请求、IP查询、网络诊断工具",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["network", "http", "api", "ip"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("http_get", self._http_get)
        self.register_tool("http_post", self._http_post)
        self.register_tool("check_url_status", self._check_url_status)
        self.register_tool("get_ip_info", self._get_ip_info)
        self.register_tool("check_dns", self._check_dns)
        self.register_tool("parse_url", self._parse_url)
        self.register_tool("build_url", self._build_url)
        plugins_logger.info("Network Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _http_get(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """HTTP GET请求"""
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(url, headers={'User-Agent': 'DataAgent/1.0'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8')
                return {
                    "success": True,
                    "status_code": response.status,
                    "content": content[:1000],
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _http_post(self, url: str, data: str = "", headers: Dict[str, str] = None, timeout: int = 10) -> Dict[str, Any]:
        """HTTP POST请求"""
        try:
            import urllib.request
            import urllib.error
            import json
            
            headers = headers or {'User-Agent': 'DataAgent/1.0', 'Content-Type': 'application/json'}
            body = json.dumps(data).encode('utf-8') if isinstance(data, dict) else data.encode('utf-8')
            
            req = urllib.request.Request(url, data=body, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8')
                return {
                    "success": True,
                    "status_code": response.status,
                    "content": content[:1000],
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_url_status(self, url: str, timeout: int = 5) -> Dict[str, Any]:
        """检查URL状态"""
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return {
                    "success": True,
                    "url": url,
                    "status_code": response.status,
                    "reachable": True
                }
        except urllib.error.HTTPError as e:
            return {
                "success": True,
                "url": url,
                "status_code": e.code,
                "reachable": True
            }
        except Exception as e:
            return {
                "success": True,
                "url": url,
                "reachable": False,
                "error": str(e)
            }
    
    def _get_ip_info(self, ip: str = "") -> Dict[str, Any]:
        """查询IP信息"""
        try:
            import urllib.request
            import json
            
            if not ip:
                url = "http://httpbin.org/ip"
            else:
                url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,query"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'DataAgent/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_dns(self, domain: str) -> Dict[str, Any]:
        """DNS查询"""
        try:
            import socket
            
            try:
                ipv4 = socket.gethostbyname(domain)
                return {
                    "success": True,
                    "domain": domain,
                    "ipv4": ipv4,
                    "ipv6": None
                }
            except socket.gaierror:
                return {
                    "success": False,
                    "error": f"Cannot resolve domain: {domain}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_url(self, url: str) -> Dict[str, Any]:
        """解析URL"""
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            return {
                "success": True,
                "scheme": parsed.scheme,
                "netloc": parsed.netloc,
                "hostname": parsed.hostname,
                "port": parsed.port,
                "path": parsed.path,
                "params": parsed.params,
                "query": parsed.query,
                "fragment": parsed.fragment
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _build_url(self, scheme: str = "https", hostname: str = "", path: str = "/", params: str = "", query: str = "") -> Dict[str, Any]:
        """构建URL"""
        try:
            from urllib.parse import urlencode, urlunparse
            
            query_dict = {}
            if query:
                for item in query.split('&'):
                    if '=' in item:
                        k, v = item.split('=', 1)
                        query_dict[k] = v
            
            netloc = hostname
            url = urlunparse((scheme, netloc, path, params, urlencode(query_dict), ''))
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}


class ImageToolsPlugin(ToolPlugin):
    """图片处理工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="image_tools",
            name="Image Tools",
            description="图片处理工具（缩放、格式转换、占位图生成）",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["image", "resize", "convert", "thumbnail"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("create_thumbnail_info", self._create_thumbnail_info)
        self.register_tool("get_image_info", self._get_image_info)
        self.register_tool("generate_image_placeholder", self._generate_image_placeholder)
        self.register_tool("calculate_aspect_ratio", self._calculate_aspect_ratio)
        self.register_tool("validate_image_dimensions", self._validate_image_dimensions)
        plugins_logger.info("Image Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _create_thumbnail_info(self, width: int, height: int, max_size: int = 200) -> Dict[str, Any]:
        """生成缩略图尺寸信息"""
        try:
            aspect_ratio = width / height if height > 0 else 1
            
            if width > height:
                new_width = min(max_size, width)
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = min(max_size, height)
                new_width = int(new_height * aspect_ratio)
            
            return {
                "success": True,
                "original": {"width": width, "height": height},
                "thumbnail": {"width": new_width, "height": new_height},
                "aspect_ratio": aspect_ratio
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_image_info(self, width: int, height: int, format: str = "JPEG") -> Dict[str, Any]:
        """获取图片信息"""
        try:
            aspect_ratio = width / height if height > 0 else 1
            megapixels = (width * height) / 1000000
            estimated_size_kb = (width * height * 3) / 1024 / 10
            
            return {
                "success": True,
                "dimensions": {"width": width, "height": height},
                "format": format,
                "aspect_ratio": round(aspect_ratio, 2),
                "megapixels": round(megapixels, 2),
                "estimated_size_kb": round(estimated_size_kb, 2)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_image_placeholder(self, width: int, height: int, bg_color: str = "#cccccc", text: str = "") -> Dict[str, Any]:
        """生成占位图片信息"""
        try:
            aspect_ratio = width / height if height > 0 else 1
            
            svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="{bg_color}"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#666666" font-family="Arial" font-size="14">{text or f"{width} × {height}"}</text></svg>'
            
            return {
                "success": True,
                "width": width,
                "height": height,
                "bg_color": bg_color,
                "svg_data": svg,
                "aspect_ratio": aspect_ratio
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_aspect_ratio(self, width: int, height: int) -> Dict[str, Any]:
        """计算宽高比"""
        try:
            if height == 0:
                return {"success": False, "error": "Height cannot be zero"}
            
            ratio = width / height
            
            def gcd(a, b):
                while b:
                    a, b = b, a % b
                return a
            
            divisor = gcd(width, height)
            ratio_w = width // divisor
            ratio_h = height // divisor
            
            return {
                "success": True,
                "ratio_decimal": round(ratio, 4),
                "ratio_fraction": f"{ratio_w}:{ratio_h}",
                "is_landscape": width > height,
                "is_portrait": width < height,
                "is_square": width == height
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _validate_image_dimensions(self, width: int, height: int, max_width: int = 4096, max_height: int = 4096) -> Dict[str, Any]:
        """验证图片尺寸"""
        try:
            valid = 0 < width <= max_width and 0 < height <= max_height
            megapixels = (width * height) / 1000000
            
            warnings = []
            if width > max_width:
                warnings.append(f"宽度超过最大值: {width} > {max_width}")
            if height > max_height:
                warnings.append(f"高度超过最大值: {height} > {max_height}")
            if megapixels > 8:
                warnings.append(f"分辨率过高: {megapixels:.1f}MP")
            
            return {
                "success": True,
                "valid": valid,
                "dimensions": {"width": width, "height": height},
                "megapixels": round(megapixels, 2),
                "warnings": warnings
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ValidatorPlugin(ToolPlugin):
    """数据验证工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="validator_tools",
            name="Validator Tools",
            description="数据验证工具（邮箱、手机、身份证等）",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["validator", "email", "phone", "id_card"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("validate_email", self._validate_email)
        self.register_tool("validate_phone_cn", self._validate_phone_cn)
        self.register_tool("validate_id_card_cn", self._validate_id_card_cn)
        self.register_tool("validate_url", self._validate_url)
        self.register_tool("validate_ipv4", self._validate_ipv4)
        self.register_tool("validate_postal_code_cn", self._validate_postal_code_cn)
        self.register_tool("validate_credit_card", self._validate_credit_card)
        plugins_logger.info("Validator Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _validate_email(self, email: str) -> Dict[str, Any]:
        """验证邮箱"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        return {
            "success": True,
            "valid": is_valid,
            "email": email
        }
    
    def _validate_phone_cn(self, phone: str) -> Dict[str, Any]:
        """验证中国手机号"""
        pattern = r'^1[3-9]\d{9}$'
        is_valid = bool(re.match(pattern, phone))
        
        carriers = {
            '130': '中国移动', '131': '中国移动', '134': '中国移动', '135': '中国移动',
            '136': '中国移动', '137': '中国移动', '138': '中国移动', '139': '中国移动',
            '145': '中国联通', '147': '中国移动', '150': '中国移动', '151': '中国移动',
            '152': '中国移动', '157': '中国移动', '158': '中国移动', '159': '中国移动',
            '166': '中国联通', '1709': '中国电信', '171': '中国联通', '173': '中国电信',
            '175': '中国联通', '176': '中国联通', '177': '中国电信', '178': '中国移动',
            '180': '中国电信', '181': '中国电信', '182': '中国移动', '183': '中国移动',
            '184': '中国移动', '185': '中国联通', '186': '中国联通', '187': '中国移动',
            '188': '中国移动', '189': '中国电信', '190': '中国电信', '191': '中国电信',
            '193': '中国电信', '195': '中国移动', '197': '中国移动', '198': '中国移动',
            '199': '中国电信'
        }
        
        carrier = None
        if is_valid:
            prefix = phone[:3]
            carrier = carriers.get(prefix, '未知运营商')
        
        return {
            "success": True,
            "valid": is_valid,
            "phone": phone,
            "carrier": carrier
        }
    
    def _validate_id_card_cn(self, id_card: str) -> Dict[str, Any]:
        """验证中国身份证"""
        if not re.match(r'^\d{17}[\dXx]$', id_card):
            return {"success": True, "valid": False, "error": "格式错误"}
        
        factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        
        total = sum(int(id_card[i]) * factors[i] for i in range(17))
        check_digit = check_codes[total % 11]
        
        is_valid = id_card[-1].upper() == check_digit
        
        birth_year = int(id_card[6:10])
        birth_month = int(id_card[10:12])
        birth_day = int(id_card[12:14])
        gender_digit = int(id_card[16])
        
        province_codes = {
            '11': '北京市', '12': '天津市', '13': '河北省', '14': '山西省',
            '15': '内蒙古', '21': '辽宁省', '22': '吉林省', '23': '黑龙江省',
            '31': '上海市', '32': '江苏省', '33': '浙江省', '34': '安徽省',
            '35': '福建省', '36': '江西省', '37': '山东省', '41': '河南省',
            '42': '湖北省', '43': '湖南省', '44': '广东省', '45': '广西壮族自治区',
            '46': '海南省', '50': '重庆市', '51': '四川省', '52': '贵州省',
            '53': '云南省', '54': '西藏自治区', '61': '陕西省', '62': '甘肃省',
            '63': '青海省', '64