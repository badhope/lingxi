# DataAgent Docker 部署指南

本文档提供使用 Docker 部署 DataAgent 的完整指南。

## 📋 前提条件

- Docker 20.10+
- Docker Compose 2.0+ (可选)

## 🚀 快速开始

### 方式一：使用 Docker Compose（推荐）

```bash
# 1. 进入项目目录
cd /workspace/Data-Agent

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 访问应用
# http://localhost:8000
```

### 方式二：使用 Docker 命令

```bash
# 1. 构建镜像
docker build -t dataagent:latest -f Dockerfile .

# 2. 运行容器
docker run -d \
  --name dataagent \
  -p 8000:8000 \
  -v ~/.dataagent:/root/.dataagent \
  dataagent:latest
```

## 🐳 构建多阶段镜像

DataAgent 支持三种构建目标：

### 开发环境
```bash
docker build --target dev -t dataagent:dev .
```

### 生产环境
```bash
docker build --target prod -t dataagent:prod .
```

### 测试环境
```bash
docker build --target test -t dataagent:test .
```

## 📦 Docker Compose 服务说明

### 主要服务

| 服务 | 端口 | 说明 |
|------|------|------|
| dataagent | 8000 | 主应用（开发模式） |
| dataagent-prod | 8001 | 主应用（生产模式） |

### 可选服务

| 服务 | 说明 | 启用方式 |
|------|------|---------|
| db | PostgreSQL 数据库 | `docker-compose --profile db up -d` |
| redis | Redis 缓存 | `docker-compose --profile redis up -d` |
| nginx | Nginx 反向代理 | `docker-compose --profile nginx up -d` |

## 🔧 环境变量配置

创建 `.env` 文件：

```bash
# 应用配置
DEBUG=False
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO

# 数据库配置
DATABASE_TYPE=sqlite
DATABASE_PATH=/app/data/dataagent.db

# 或使用 PostgreSQL
DATABASE_TYPE=postgresql
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_USER=dataagent
DATABASE_PASSWORD=your_password
DATABASE_NAME=dataagent

# LLM 配置
LLM_PROVIDER=aliyun
LLM_API_KEY=your_api_key
LLM_MODEL=qwen-plus-latest

# 安全配置
SECRET_KEY=your_secret_key
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# 功能开关
WEBHOOK_ENABLED=True
CACHE_ENABLED=True
```

## 🔒 生产环境最佳实践

### 1. 使用环境变量

```bash
docker run -d \
  --name dataagent \
  -p 8000:8000 \
  -e DEBUG=False \
  -e LLM_API_KEY=your_api_key \
  -e SECRET_KEY=your_secret_key \
  -v dataagent_data:/app/data \
  dataagent:prod
```

### 2. 使用 Docker Secrets

```bash
# 创建 secret
echo "your_api_key" | docker secret create dataagent_api_key -
echo "your_password" | docker secret create dataagent_db_password -

# 使用 secret
docker-compose.prod.yml
```

### 3. 启用 HTTPS

使用 Nginx + Let's Encrypt：

```bash
# 启动 Nginx 反向代理
docker-compose --profile nginx up -d
```

## 📊 数据持久化

### 默认数据目录

| 主机路径 | 容器路径 | 说明 |
|---------|---------|------|
| `~/.dataagent` | `/root/.dataagent` | 用户配置和数据 |
| `./data` | `/app/data` | 应用数据 |
| `./logs` | `/app/logs` | 日志文件 |
| `./workspace` | `/app/workspace` | 工作区文件 |

### 备份数据

```bash
# 备份整个数据目录
tar -czf dataagent_backup_$(date +%Y%m%d).tar.gz ~/.dataagent

# 恢复数据
tar -xzf dataagent_backup_20240101.tar.gz -C ~
```

## 🔍 故障排查

### 查看日志

```bash
# 查看应用日志
docker-compose logs -f dataagent

# 查看所有服务日志
docker-compose logs -f
```

### 进入容器

```bash
# 进入容器 shell
docker exec -it dataagent /bin/bash

# 查看运行中的进程
docker exec dataagent ps aux
```

### 检查健康状态

```bash
# 检查容器健康
docker inspect dataagent | grep -A 10 "Health"

# API 健康检查
curl http://localhost:8000/api/health
```

### 常见问题

#### 1. 端口冲突

如果 8000 端口被占用：

```bash
# 修改 docker-compose.yml 中的端口映射
ports:
  - "8080:8000"  # 改为你想要的端口
```

#### 2. 权限问题

```bash
# 设置数据目录权限
sudo chown -R 1000:1000 ~/.dataagent

# 或使用卷
volumes:
  - /path/to/data:/app/data
```

#### 3. 内存不足

```bash
# 增加 Docker 内存限制
# Docker Desktop -> Settings -> Resources -> Memory: 4GB+
```

## 🧹 清理

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 删除镜像

```bash
# 删除构建的镜像
docker rmi dataagent:latest
docker rmi dataagent:dev
docker rmi dataagent:prod
```

## 📝 完整示例：生产环境部署

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/Data-Agent.git
cd Data-Agent

# 2. 创建环境配置文件
cat > .env << EOF
DEBUG=False
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO
DATABASE_TYPE=postgresql
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_USER=dataagent
DATABASE_PASSWORD=secure_password
DATABASE_NAME=dataagent
LLM_PROVIDER=aliyun
LLM_API_KEY=your_api_key
SECRET_KEY=your_very_secure_secret_key
CORS_ORIGINS=https://your-domain.com
WEBHOOK_ENABLED=True
CACHE_ENABLED=True
EOF

# 3. 启动数据库和服务
docker-compose --profile db up -d

# 4. 等待数据库就绪
sleep 10

# 5. 启动应用
docker-compose up -d

# 6. 检查状态
docker-compose ps
docker-compose logs -f dataagent
```

## 🎯 下一步

- 访问 API 文档：http://localhost:8000/docs
- 配置 LLM 提供方
- 上传知识库文档
- 创建第一个 Agent
- 配置技能和工作流

## 📚 相关资源

- [项目主 README](../README.md)
- [API 文档](../docs/api.md)
- [部署指南](../docs/deployment.md)
