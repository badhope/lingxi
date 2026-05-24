# DataAgent

## 项目说明

此为 DataAgent 核心目录。请查看根目录的 [README.md](../README.md) 获取完整的项目说明和使用指南。

## 快速开始

```bash
# 启动应用
python main.py
```

访问 http://localhost:8000

## 配置

请编辑 `config/config.toml` 文件来配置你的 API 密钥和其他设置。

## 项目结构

```
dataagent/
├── main.py              # 统一入口
├── core/                # 核心模块
├── routers/             # API路由
├── services/            # 业务逻辑
├── static/              # 静态资源
├── templates/           # HTML模板
├── config/              # 配置文件
└── requirements.txt     # 依赖
```
