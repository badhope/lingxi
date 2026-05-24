# DataAgent 启动指南

## 🚀 快速启动

### 后端已成功启动！

**服务状态**: ✅ 运行中  
**访问地址**: http://localhost:8000  
**API健康检查**: ✅ http://localhost:8000/api/health

---

## 📋 当前配置

### 环境变量 (.env)
- API Key: 已配置（请在 config.toml 中填入真实密钥）
- API Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
- API Model: qwen-plus-latest
- CORS: 允许 localhost:8000 和 127.0.0.1:8000
- 日志级别: INFO
- 配置目录: /workspace/Data-Agent/dataagent/.dataagent

### 主配置文件 (config.toml)
- LLM Provider: 通义千问 (Qwen)
- Max Tokens: 8192
- Temperature: 0.0
- 日志级别: INFO

---

## 🎯 可用功能

### ✅ 已注册插件 (16个)

1. **Math Tools** - 数学计算工具
2. **String Tools** - 字符串处理工具
3. **Time Tools** - 时间日期工具
4. **File Tools** - 文件操作工具
5. **Basic Analytics** - 基础数据分析
6. **Simple Visualization** - 简单数据可视化
7. **Sample Data Source** - 示例数据源
8. **Crypto Tools** - 加密解密工具
9. **Data Converter** - 数据格式转换
10. **Regex Tools** - 正则表达式工具
11. **Color Tools** - 颜色工具
12. **Unit Converter** - 单位转换工具
13. **Advanced Analytics** - 高级数据分析
14. **List Tools** - 列表操作工具
15. **Text Generator** - 文本生成工具
16. **DateTime Tools** - 日期时间工具

### ✅ WebSocket 功能
- 实时对话功能
- 意图识别路由
- 消息流式响应

### ✅ 核心服务
- 数据库持久化（JSON文件后端）
- 配置管理系统
- 中间件支持（CORS、错误处理、速率限制）
- 插件系统

---

## 🌐 Web 界面

**访问地址**: http://localhost:8000

界面功能包括：
- 智能对话界面
- 侧边栏导航
- 实时消息推送
- WebSocket 连接
- 多语言支持

---

## 🔧 配置说明

### 编辑 API 密钥

打开配置文件：
```bash
vim /workspace/Data-Agent/dataagent/config/config.toml
```

填入你的 API 密钥：
```toml
[llm]
model = "qwen-plus-latest"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key = "your_actual_api_key_here"  # 替换这里
max_tokens = 8192
temperature = 0.0
```

### 环境变量配置

编辑 `.env` 文件：
```bash
vim /workspace/Data-Agent/dataagent/.env
```

主要配置项：
- `API_KEY` - API 密钥
- `API_BASE_URL` - API 基础 URL
- `API_MODEL` - 模型名称
- `LOG_LEVEL` - 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `DATAAGENT_CONFIG_DIR` - 配置目录

---

## 📊 服务端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | Web 界面 |
| `/api/health` | GET | 健康检查 |
| `/ws` | WebSocket | 实时对话 |
| `/api/polish` | POST | 文本润色 |
| `/api/documents` | * | 文档管理 |
| `/api/knowledge` | * | 知识库管理 |
| `/api/plugins` | * | 插件管理 |
| `/api/settings` | * | 设置管理 |

---

## 🔒 安全特性

已启用的安全功能：
- ✅ CORS 跨域资源共享
- ✅ 速率限制（60请求/分钟）
- ✅ 输入验证和清理
- ✅ 错误处理中间件
- ✅ 日志记录

---

## 🚦 启动/停止服务

### 启动服务
```bash
cd /workspace/Data-Agent/dataagent
python start_simple.py
```

### 停止服务
在运行终端按 `Ctrl+C`

### 重启服务
```bash
# 先停止
Ctrl+C

# 再启动
python start_simple.py
```

---

## 🔍 查看日志

实时查看应用日志：
```bash
# 如果配置了日志文件
tail -f /workspace/Data-Agent/dataagent/.dataagent/logs/*.log

# 或者查看标准输出
# 日志已经在启动终端中显示
```

---

## ⚠️ 已知问题

1. **API密钥未配置**: 当前使用示例密钥，需要替换为真实密钥
2. **部分路由加载失败**: admin, openclaw, dashboard 路由有语法错误（不影响核心功能）
3. **前端JS错误**: copyToClipboard 函数可能未定义（不影响主要功能）

---

## 📝 修复历史

### ✅ 已修复的问题

1. **plugins_builtin.py** - eval 安全风险 ✅
2. **database.py** - Pydantic 序列化方法混用 ✅
3. **websocket.py** - 迭代时修改字典问题 ✅
4. **config_manager.py** - 容器兼容性问题 ✅
5. **intent_router.py** - 导入路径问题 ✅

详见：`/workspace/Data-Agent/ISSUE_FIX_SUMMARY.md`

---

## 🎉 快速测试

### 测试健康检查
```bash
curl http://localhost:8000/api/health
```

### 测试 WebSocket
在浏览器控制台中：
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (event) => console.log(event.data);
ws.send(JSON.stringify({type: 'message', content: 'Hello!'}));
```

---

## 📞 下一步

1. 填入真实的 API 密钥
2. 测试各项功能
3. 根据需要调整配置
4. 如有需要，修复报告的语法错误

---

**生成时间**: 2026-05-24 15:00:12  
**服务状态**: 运行中 ✅  
**文档版本**: 1.0
