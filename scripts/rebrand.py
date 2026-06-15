#!/usr/bin/env python3
"""
DATA → DATA 全品牌替换脚本
执行步骤:
  1. 文件内容替换（所有文本文件）
  2. 文件/目录重命名

用法: uv run --project api scripts/rebrand.py
"""

import os
import re
import shutil
from pathlib import Path

BASE = Path(r"C:\Users\X1882\.qclaw\workspace\data")

# ====== 排除目录 ======
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".next", "dist", "build",
    "venv", ".venv", ".idea", ".vscode", "coverage", "migrations",
    "volumes",  # Docker volumes with user data
}

# ====== 排除文件名后缀 ======
BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", 
    ".eot", ".ttf", ".otf", ".pyc", ".gitkeep", ".DS_Store",
    ".pdf", ".zip", ".tar", ".gz", ".mp4", ".mp3", ".wav",
}

# ====== 文件内容替换规则 ======
# 顺序重要！
# 规则一：更长/更具体的模式优先（避免 DataAgent 被 DATA 先匹配）
# 规则二：全名替换优先于部分替换
# 规则三：带 -_ 连接的模式优先于纯单词
CONTENT_RULES = [
    # ========== Layer 1: 最长/最特定的标识符 ==========
    # --- 超长常量 ---
    (r'\bDIFY_DRIVE_LAYER_TYPE_ID\b',  'DATA_DRIVE_LAYER_TYPE_ID'),
    (r'\bDIFY_OUTPUT_LAYER_TYPE_ID\b', 'DATA_OUTPUT_LAYER_TYPE_ID'),
    (r'\bDIFY_SHELL_LAYER_TYPE_ID\b',  'DATA_SHELL_LAYER_TYPE_ID'),
    (r'\bDIFY_INNER_API_URL\b',       'DATA_INNER_API_URL'),
    (r'\bDIFY_INNER_API_KEY\b',       'DATA_INNER_API_KEY'),
    (r'\bDIFY_BIND_ADDRESS\b',       'DATA_BIND_ADDRESS'),
    (r'\bDIFY_PORT\b',               'DATA_PORT'),

    # --- 双层类名 ---
    (r'\bDifyLoginManager\b',          'DataLoginManager'),
    (r'\bDifyOutputLayerConfig\b',     'DataOutputLayerConfig'),
    (r'\bDifyShellLayerConfig\b',      'DataShellLayerConfig'),
    (r'\bDifyDriveLayerConfig\b',      'DataDriveLayerConfig'),
    (r'\bDifyDriveConfig\b',           'DataDriveConfig'),
    (r'\bDifyAgentConfig\b',          'DataAgentConfig'),
    (r'\bDifySandbox\b',              'DataSandbox'),
    (r'\bDifyModel\b',                'DataModel'),

    # ========== Layer 2: 单层类名 ==========
    (r'\bDifyConfig\b',                'DataConfig'),
    (r'\bDifyApp\b',                   'DataApp'),
    (r'\bDifyAgent\b',                 'DataAgent'),
    (r'\bDifyDrive\b',                 'DataDrive'),
    (r'\bDifyUtils\b',                'DataUtils'),
    (r'\bDifyException\b',            'DataException'),
    (r'\bDifyError\b',                'DataError'),

    # ========== Layer 3: 蛇形命名（包含 _ 或 -） ==========
    # 注意：先处理带 - 的，再处理带 _ 的
    (r'\bdify-config\b',               'data-config'),
    (r'\bdify-command\b',              'data-command'),
    (r'\bdify-error\b',               'data-error'),
    (r'\bdify-mock\b',                'data-mock'),
    (r'\bdify-env-sync\b',            'data-env-sync'),
    (r'\bsse-data\b',                  'sse-data'),
    (r'\bdify-ui\b',                  'data-ui'),
    (r'\bdify-logo\b',                'data-logo'),
    (r'\bdify-client\b',              'data-client'),
    (r'\bdify-invariants\b',          'data-invariants'),

    # ---- 带 _ 的蛇形名 ----
    # vdb 和 trace 提供商包名（大量出现）
    # 注意：不使用 \b 边界，因为 _ 是单词字符
    (r'data_vdb_',                       'data_vdb_'),
    (r'data_trace_',                     'data_trace_'),
    (r'\bdify_vdb\b',                  'data_vdb'),
    (r'\bdify_trace\b',                'data_trace'),
    (r'\bdify_config\b',              'data_config'),
    (r'\bdify_app\b',                 'data_app'),
    (r'\bdify_agent\b',               'data_agent'),
    (r'\bdify_test\b',                'data_test'),
    (r'\bdify_secret_key\b',          'data_secret_key'),
    (r'\bdify_plugin\b',               'data_plugin'),
    (r'\bdify_mock\b',                 'data_mock'),
    (r'pytest_data\b',                  'pytest_data'),

    # ========== Layer 4: Docker / 部署相关 ==========
    (r'data-api\b',          'data-api'),
    (r'data-web\b',          'data-web'),
    (r'data-sandbox\b',      'data-sandbox'),
    (r'data-plugin-daemon\b', 'data-plugin-daemon'),
    (r'\bdify-sandbox\b',              'data-sandbox'),
    (r'\bdify_es01_data\b',            'data_es01_data'),
    (r'\bdify-es-cluster\b',           'data-es-cluster'),
    (r'\bdify-es0\b',                  'data-es0'),
    (r'\bdify-ai-seekdb\b',            'data-ai-seekdb'),
    (r'\bdify_search\b',               'data_search'),
    (r'\bdify_plugin\b',               'data_plugin'),
    (r'\bdify\.crt\b',                 'data.crt'),
    (r'\bdify\.key\b',                 'data.key'),
    (r'\bdify\.svg\b',                 'data.svg'),
    (r'\bdify\.json\b',                'data.json'),
    (r'\bdify\.tsx\b',                 'data.tsx'),
    (r'hello@data\.ai\b',              'hello@data.ai'),
    (r'data\.ai',                       'data.ai'),
    (r'data\.app',                      'data.app'),

    # ========== Layer 5: 默认密码 ==========
    (r'\bDify@123\b',                   'Data@123'),
    (r'\bDifyai123456\b',              'Data123456'),
    (r'\bDify123456\b',                'Data123456'),
    (r'\bdifyai123456\b',              'data123456'),
    (r'\bdify-ai-seekdb\b',           'data-ai-seekdb'),

    # ========== Layer 6: 产品名（单独出现，最后处理）==========
    # 在 JSX/HTML/README/注释中的品牌名 DATA → DATA
    # 注意：\b 确保是单词边界，不会匹配 modify、difficulty 等
    # 前面的类名/标识符规则已处理 DifyClass/dify_xx 形式
    (r'\bDify\b',      'DATA'),

    # ========== Layer 7: 小写在文档/路径中 ==========
    # 非代码上下文的 standalone data → data
    (r'\bdify\b',       'data'),
]

print("""
⚠️  重要提示:
  本脚本使用正则替换，包含的风险:
  1. 部分替换可能过度匹配（如 modify → modata）
  2. 如果执行后出现问题，请 git checkout backup-original 恢复
  3. 执行后务必进行人工 review 和测试
""")

# 更精细的产品名处理：只在非代码上下文中替换 DATA → DATA
# 例如 README, 注释, UI 字符串等
# 代码中的 DATA 已经通过上面的类名规则处理了

# ====== 文件名替换规则 ======
FILE_RENAME_RULES = [
    # (old_pattern, new_name)
    # 使用通配，实际处理时用正则
]

def should_skip(path: Path) -> bool:
    """检查文件/目录是否应该跳过"""
    parts = path.parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    ext = path.suffix.lower()
    if ext in BINARY_EXTS:
        return True
    return False

def get_all_text_files(base: Path) -> list[Path]:
    """获取所有需要处理的文本文件"""
    files = []
    for root, dirs, filenames in os.walk(base):
        root_path = Path(root)
        # 修改 dirs in-place 来排除目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        # 跳过整个排除路径
        rel = root_path.relative_to(base).parts
        if any(part in EXCLUDE_DIRS for part in rel):
            dirs.clear()
            continue
        
        for fn in filenames:
            fpath = root_path / fn
            if not should_skip(fpath):
                files.append(fpath)
    
    return files

def replace_in_file(filepath: Path, rules: list[tuple[str, str]]) -> int:
    """在单个文件中执行所有替换，返回替换次数"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"  ⚠ 读取失败: {filepath.relative_to(BASE)} - {e}")
        return 0

    total = 0
    new_content = content
    for pattern, replacement in rules:
        new_content, count = re.subn(pattern, replacement, new_content)
        total += count
    
    if total == 0:
        return 0
    
    # 写回
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        print(f"  ⚠ 写入失败: {filepath.relative_to(BASE)} - {e}")
        return 0
    
    return total

def rename_dify_files(base: Path) -> list[tuple[Path, Path]]:
    """重命名所有含 'data' 的文件和目录（从最深层开始）"""
    # 先收集所有需要重命名的项
    renames = []
    
    # 文件重命名
    for fpath in get_all_text_files(base):
        if 'data' in fpath.stem.lower() and fpath.suffix not in BINARY_EXTS:
            new_stem = fpath.stem
            # 处理各种大小写组合
            new_stem = new_stem.replace('DATA', 'Data')
            new_stem = new_stem.replace('data', 'data')
            if new_stem != fpath.stem:
                new_path = fpath.with_stem(new_stem)
                renames.append((fpath, new_path))
    
    # 目录重命名（从最深到最浅，避免路径失效）
    dir_renames = []
    for root, dirs, _ in os.walk(base):
        root_path = Path(root)
        rel = root_path.relative_to(base).parts
        if any(part in EXCLUDE_DIRS for part in rel):
            continue
        for d in dirs:
            if 'data' in d.lower():
                new_name = d.replace('DATA', 'Data').replace('data', 'data')
                if new_name != d:
                    dir_renames.append((root_path / d, root_path / new_name))
    
    # 目录从最深到最浅排序
    dir_renames.sort(key=lambda x: len(str(x[0])), reverse=True)
    
    return renames + dir_renames

def main():
    print("=" * 60)
    print("  DATA → DATA 全品牌替换")
    print("=" * 60)
    print()
    
    # ====== Phase 1: 文件内容替换 ======
    print("📝 Phase 1: 文件内容替换")
    print(f"   规则数: {len(CONTENT_RULES)}")
    print()
    
    files = get_all_text_files(BASE)
    print(f"   扫描到 {len(files)} 个文本文件")
    
    changed_files = 0
    total_replacements = 0
    
    for i, fpath in enumerate(files):
        count = replace_in_file(fpath, CONTENT_RULES)
        if count > 0:
            rel = fpath.relative_to(BASE)
            print(f"  ✅ {rel}: {count} 处替换")
            changed_files += 1
            total_replacements += count
        
        # 进度汇报
        if (i + 1) % 500 == 0:
            print(f"  ... 已处理 {i+1}/{len(files)} 文件, 已修改 {changed_files} 个")
    
    print()
    print(f"  总计: {changed_files} 个文件, {total_replacements} 处替换")
    
    # ====== Phase 2: 文件/目录重命名 ======
    print()
    print("📁 Phase 2: 文件/目录重命名")
    print()
    
    rename_list = rename_dify_files(BASE)
    rename_list.sort(key=lambda x: len(str(x[0])), reverse=True)
    
    for old_path, new_path in rename_list:
        try:
            if old_path.exists():
                # 检查目标是否已存在
                if new_path.exists():
                    print(f"  ⚠ 目标已存在: {new_path.relative_to(BASE)}")
                    continue
                old_path.rename(new_path)
                print(f"  📄 {old_path.relative_to(BASE)}")
                print(f"     → {new_path.relative_to(BASE)}")
        except Exception as e:
            print(f"  ❌ 重命名失败: {old_path.relative_to(BASE)} - {e}")
    
    print()
    print("=" * 60)
    print("  ✅ 品牌替换完成！")
    print("=" * 60)
    print()
    print("下一步:")
    print("  1. 检查 git diff 确认修改")
    print("  2. 更新 Docker 镜像名 (data-api/data-web 等)")
    print("  3. 运行测试验证: cd api && uv run pytest")
    print("  4. 更新仓库远程地址")

if __name__ == "__main__":
    main()
