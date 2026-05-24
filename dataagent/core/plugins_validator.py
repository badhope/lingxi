"""
DataAgent - Validator插件部分
"""
import re
from typing import Any, Dict

class ValidatorPluginPart:
    """数据验证工具插件 - 剩余方法"""
    
    @staticmethod
    def _validate_id_card_cn_impl(id_card: str) -> Dict[str, Any]:
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
            '63': '青海省', '64': '宁夏回族自治区', '65': '新疆维吾尔自治区',
            '71': '台湾省', '81': '香港特别行政区', '82': '澳门特别行政区'
        }
        
        province = province_codes.get(id_card[0:2], '未知')
        gender = '男性' if gender_digit % 2 == 1 else '女性'
        
        return {
            "success": True,
            "valid": is_valid,
            "province": province,
            "birth_date": f"{birth_year}-{birth_month:02d}-{birth_day:02d}",
            "gender": gender,
            "age": 2024 - birth_year
        }
    
    @staticmethod
    def _validate_url_impl(url: str) -> Dict[str, Any]:
        """验证URL"""
        pattern = r'^https?://[^\s<>"]+$'
        is_valid = bool(re.match(pattern, url))
        return {
            "success": True,
            "valid": is_valid,
            "url": url
        }
    
    @staticmethod
    def _validate_ipv4_impl(ip: str) -> Dict[str, Any]:
        """验证IPv4地址"""
        parts = ip.split('.')
        is_valid = len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)
        return {
            "success": True,
            "valid": is_valid,
            "ip": ip
        }
    
    @staticmethod
    def _validate_postal_code_cn_impl(postal_code: str) -> Dict[str, Any]:
        """验证中国邮政编码"""
        pattern = r'^\d{6}$'
        is_valid = bool(re.match(pattern, postal_code))
        return {
            "success": True,
            "valid": is_valid,
            "postal_code": postal_code
        }
    
    @staticmethod
    def _validate_credit_card_impl(card_number: str) -> Dict[str, Any]:
        """验证信用卡号（Luhn算法）"""
        digits = [int(d) for d in card_number if d.isdigit()]
        
        if len(digits) < 13 or len(digits) > 19:
            return {"success": True, "valid": False, "error": "Invalid length"}
        
        checksum = 0
        reverse_digits = digits[::-1]
        
        for i, digit in enumerate(reverse_digits):
            if i % 2 == 1:
                doubled = digit * 2
                checksum += doubled - 9 if doubled > 9 else doubled
            else:
                checksum += digit
        
        is_valid = checksum % 10 == 0
        
        card_types = {
            '4': 'Visa',
            '51': 'Mastercard', '52': 'Mastercard', '53': 'Mastercard',
            '54': 'Mastercard', '55': 'Mastercard',
            '34': 'Amex', '37': 'Amex',
            '6011': 'Discover'
        }
        
        card_type = None
        for prefix, name in card_types.items():
            if card_number.startswith(prefix):
                card_type = name
                break
        
        return {
            "success": True,
            "valid": is_valid,
            "card_number": card_number[-4:].rjust(len(card_number), '*'),
            "card_type": card_type
        }
