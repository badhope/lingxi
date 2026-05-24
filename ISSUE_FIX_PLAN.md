# DataAgent 问题修复计划表

## 问题清单

### 🔴 高优先级 (High Priority)

| ID | 问题描述 | 严重程度 | 文件位置 | 状态 |
|----|---------|---------|---------|------|
| 1 | plugins_builtin.py 中使用 eval() 存在安全风险 | 高 | core/plugins_builtin.py:78 | ✅ 已修复 |
| 2 | config.py 中使用 threading.Lock 但在 async 上下文中应该用 asyncio.Lock | 高 | core/config.py:248 | ✅ 无需修复（锁在同步方法中使用） |
| 3 | database.py 中使用 threading.RLock 但在 async 上下文中应该用 asyncio.Lock | 高 | core/database.py:24 | ✅ 无需修复（锁在同步方法中使用） |
| 4 | websocket.py 在迭代时可能修改字典导致问题 | 高 | core/websocket.py:381 | ✅ 已修复 |
| 5 | config_manager.py 中 Path.home() 在容器环境中可能有问题 | 高 | core/config_manager.py:52 | ✅ 已修复 |
| 6 | database.py 中 Pydantic 序列化方法混用 (model_dump 和 dict) | 高 | core/database.py:99-104 | ✅ 已修复 |
| 7 | intent_router.py 导入路径问题 | 高 | services/intent_router.py:多处 | ✅ 已修复 |

### 🟡 中优先级 (Medium Priority)

| ID | 问题描述 | 严重程度 | 文件位置 | 状态 |
|----|---------|---------|---------|------|
| 8 | 缺少异常处理和日志记录的一致性 | 中 | 多文件 | 待修复 |
| 9 | 配置验证可以更严格 | 中 | core/config.py | 待修复 |
| 10 | WebSocket 消息队列没有错误处理 | 中 | core/websocket.py | 待修复 |

### 🟢 低优先级 (Low Priority)

| ID | 问题描述 | 严重程度 | 文件位置 | 状态 |
|----|---------|---------|---------|------|
| 11 | 代码注释可以更完善 | 低 | 多文件 | 待修复 |
| 12 | 类型提示可以更全面 | 低 | 多文件 | 待修复 |

---

## 修复计划

### 阶段 1: 修复高优先级问题
1. 修复问题 1 - plugins_builtin.py eval 安全问题
2. 修复问题 2 - config.py 异步锁问题
3. 修复问题 3 - database.py 异步锁问题
4. 修复问题 4 - websocket.py 迭代问题
5. 修复问题 5 - 容器兼容性问题
6. 修复问题 6 - Pydantic 序列化问题

### 阶段 2: 修复中优先级问题
7. 增强异常处理和日志
8. 加强配置验证
9. WebSocket 错误处理

### 阶段 3: 优化低优先级问题
10. 完善代码注释
11. 增强类型提示

---

## 修复详情

### 问题 1: plugins_builtin.py eval 安全风险
**位置**: `core/plugins_builtin.py:78`
**问题**: 使用 `eval(expression)` 执行用户输入的数学表达式存在安全风险
**修复方案**: 改用 `ast.literal_eval()` 或安全的数学表达式解析器

### 问题 2-3: 同步锁在 async 上下文问题
**位置**: `core/config.py:248`, `core/database.py:24`
**问题**: 在异步方法中使用 `threading.Lock/RLock` 会阻塞事件循环
**修复方案**: 改用 `asyncio.Lock`

### 问题 4: websocket 迭代时修改字典
**位置**: `core/websocket.py:381`
**问题**: 迭代 `self.connections.items()` 时可能同时有连接被移除
**修复方案**: 迭代前创建字典的副本

### 问题 5: 容器环境 Path.home() 问题
**问题**: 在容器中 `Path.home()` 可能返回不期望的路径
**修复方案**: 使用环境变量或相对路径替代

### 问题 6: Pydantic 序列化方法混用
**位置**: `core/database.py:99-104`
**问题**: 同时使用 `model_dump()` (v2) 和 `dict()` (v1)
**修复方案**: 统一使用 Pydantic v2 的 `model_dump()`

### 问题 7: intent_router.py 导入路径问题
**状态**: ✅ 已修复
**修复**: 将 `from app.services.document_service` 改为 `from services.document_service`
