# DATA 品牌替换 — 第 2 轮完成报告

**日期**: 2026-06-15

## 本轮完成工作

### 1. 🔧 遗留品牌引用修复
- **`api/core/workflow/node_factory.py`** — 全部 `Dify*` 类名 → `Data*`
  - `DifyNodeFactory`, `DifyGraphInitContext`, `DifyToolFileManager`, `DifyFileReferenceFactory`, `DifyPromptMessageSerializer`, `DifyRetrieverAttachmentLoader`, `DifyPreparedLLM`, `DifyHumanInputNodeRuntime`, `DifyToolNodeRuntime`, `DifyAgentNode` 等 15+ 个类
  - 内部方法名: `dify_context` → `data_context`, `build_dify_model_access` → `build_data_model_access`
- **`api/core/app/entities/app_invoke_entities.py`** — `DIFY_RUN_CONTEXT_KEY` → `DATA_RUN_CONTEXT_KEY`, `DifyRunContext` → `DataRunContext`, `_dify` → `_data`
- **`api/core/app/workflow/file_runtime.py`** — `DifyWorkflowFileRuntime` → `DataWorkflowFileRuntime`, `bind_dify_workflow_file_runtime` → `bind_data_workflow_file_runtime`
- **`api/tests/conftest.py`** — 同步更新导入引用
- **`docker/docker-compose.yaml`** — `PLUGIN_DIFY_INNER_API_KEY` → `PLUGIN_DATA_INNER_API_KEY`, `difyai` → `data`

### 2. 🎨 DATA 品牌 Logo 设计
- **`web/public/logo/logo.svg`** — 全新 DATA 品牌 SVG Logo
  - 符号: 几何数据节点 (外圆 + 三角箭头 + 中心点)
  - 字标: D A T A 粗体字，第二、四个 A 用品牌蓝 #0033FF
- **`web/public/logo/logo-monochrome-white.svg`** — 暗色主题版本（全白）
- **`web/public/favicon.svg`** — 蓝底白图 favicon
- **`web/app/components/base/logo/data-logo.tsx`** — 组件名更新: `DifyLogo` → `DataLogo`，Logo 尺寸适配新 SVG
- **`web/app/components/base/logo/index.stories.tsx`** — Storybook 组件更新
- **`web/app/components/base/logo/__tests__/data-logo.spec.tsx`** — `DifyLogo` → `DataLogo`，测试尺寸同步
- **`web/app/layout.tsx`** — favicon 指向 `/favicon.svg`，theme-color → `#0033FF`

### 3. 📝 README 更新
- **`README.md`** — 全量重写为 DATA 品牌描述
  - 产品定位、功能特性、架构图（ASCII）、数据流图
  - 快速启动、配置指南、测试说明
  - 贡献指南

### 4. ✅ 验证结果
| 扫描范围 | 结果 |
|---------|------|
| `api/` Python 文件 | ✅ 零 Dify/dify 引用 |
| `web/app/` TypeScript 文件 | ✅ 零 Dify 引用 |
| Docker 配置 (docker/*) | ✅ 干净 |
| Logo/Public 文件 | ✅ 全部更新 |
| Python 语法检查 (api/core) | ✅ 全部通过 |
| 依赖安装 (uv sync) | ✅ 838 包已安装 |
| `graphon` 依赖 | ✅ 已在 `.venv` 中 (v0.5.1) |

### 5. ⚠️ 已知事项
- **LiteLLM 兼容性警告**: `LiteLLM: Failed to fetch remote model cost map` — 上游包兼容问题，不影响运行
- **单元测试依赖**: 部分测试需要完整环境（DB/Redis），无法在无容器环境下运行
- **旧版二进制图标**: `favicon.ico` 及 `icon-*.png` 文件仍保留，建议后续替换为 DATA 品牌图标

## 文件变更统计
- 修改文件: ~40+ 个
- 覆盖范围: Python (api/), TypeScript (web/), Docker, SVG, Markdown, YAML

## 待做事项（下次）
- [ ] `git add -A && git commit -m "feat: rebrand Dify → DATA (phase 2)"`
- [ ] 本地 build Docker 镜像
- [ ] 推送至新的 GitHub 远程仓库
- [ ] 替换 `@langgenius/data-ui` npm 包名
