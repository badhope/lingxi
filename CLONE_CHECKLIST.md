# 项目克隆检查清单

此文档列出了克隆项目后需要执行的步骤，确保项目可以正常运行。

## 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/badhope/Data-Agent.git
cd Data-Agent
```

### 2. 配置环境

#### 方式一：使用 .env 文件（推荐）
```bash
# 复制 .env 模板
cp .env.example dataagent/.env

# 编辑 .env 文件，填入您的 API 密钥
cd dataagent
nano .env  # 或使用您喜欢的编辑器
```

#### 方式二：使用 config.toml 文件
```bash
cd dataagent
cp config/config.example.toml config/config.toml

# 编辑 config/config.toml，填入您的 API 密钥
nano config/config.toml
```

### 3. 安装依赖

#### 最小依赖（快速启动）
```bash
cd dataagent
pip install -r requirements-minimal.txt
```

#### 完整依赖（全部功能）
```bash
cd dataagent
pip install -r requirements.txt
```

### 4. 启动应用
```bash
cd dataagent
python main.py
```

然后在浏览器中访问：`http://localhost:8000`

## 使用 Docker

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

## 项目结构

```
Data-Agent/
├── dataagent/              # 主项目目录
│   ├── main.py            # 统一入口文件 ✅
│   ├── core/              # 核心模块
│   ├── routers/           # API 路由
│   ├── services/          # 业务逻辑
│   ├── static/            # 静态资源（CSS/JS）
│   ├── templates/         # HTML 模板
│   ├── config/            # 配置文件
│   │   └── config.example.toml  # 配置模板
│   ├── requirements.txt   # 完整依赖
│   └── requirements-minimal.txt  # 最小依赖
├── .env.example          # 环境变量模板
├── docker-compose.yml    # Docker 配置
├── README.md             # 主文档
└── UNIFIED_ARCHITECTURE.md  # 架构说明
```

## 常见问题

### Q: 提示缺少某个 Python 包？
A: 运行 `pip install -r requirements.txt` 安装所有依赖，或根据提示安装单个包。

### Q: API Key 在哪里配置？
A: 有两种方式：
1. 在 `dataagent/.env` 文件中配置
2. 在 `dataagent/config/config.toml` 文件中配置

推荐使用 config.toml 方式，功能更完整。

### Q: 如何修改端口？
A: 编辑 `main.py` 文件，修改底部的端口配置，或启动时指定：
```bash
python main.py --port 8080
```

### Q: 如何升级项目？
A:
```bash
git pull origin main
cd dataagent
pip install -r requirements.txt  # 如果依赖有变化
```

## 技术支持

- 查看项目文档：README.md
- 查看架构说明：UNIFIED_ARCHITECTURE.md
- 提交 Issue：GitHub Issues
