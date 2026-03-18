#!/usr/bin/env bash
# SPQ 评测环境一键初始化
#
# 用法:
#   bash setup.sh           # 使用默认 python3
#   bash setup.sh 3.12      # 指定 Python 版本（需 uv）
#
# 做了什么:
#   1. 创建 .venv 虚拟环境（如已存在则跳过）
#   2. 安装框架核心 + skills 脚本依赖（editable mode）
#   3. 安装 Playwright chromium 浏览器（web-screenshot skill 需要）
#   4. 提示配置 .env

set -euo pipefail

VENV_DIR=".venv"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_VERSION="${1:-}"

# ─── 1. 创建虚拟环境 ───
if [ ! -d "$VENV_DIR" ]; then
    echo ">>> 创建虚拟环境 $VENV_DIR ..."
    if [ -n "$PYTHON_VERSION" ] && command -v uv &>/dev/null; then
        uv python install "$PYTHON_VERSION" 2>/dev/null || true
        uv venv --python "$PYTHON_VERSION" "$VENV_DIR"
    elif [ -n "$PYTHON_VERSION" ]; then
        "python${PYTHON_VERSION}" -m venv "$VENV_DIR"
    else
        python3 -m venv "$VENV_DIR"
    fi
    echo "    ✓ 虚拟环境已创建"
else
    echo ">>> $VENV_DIR 已存在，跳过创建"
fi

source "$VENV_DIR/bin/activate"
echo "    Python: $(python3 --version) ($(which python3))"

# ─── 2. 安装依赖 ───
echo ""
echo ">>> 安装框架核心 + skills 依赖 ..."
if command -v uv &>/dev/null; then
    uv pip install -e ".[skills]"
else
    pip install --upgrade pip
    pip install -e ".[skills]"
fi
echo "    ✓ Python 依赖安装完成"

# ─── 3. Playwright chromium ───
echo ""
echo ">>> 安装 Playwright Chromium 浏览器 ..."
python3 -m playwright install chromium
echo "    ✓ Chromium 安装完成"

# ─── 4. 系统工具检查 ───
echo ""
echo ">>> 检查系统工具 ..."
MISSING=""
for tool in curl dig gh jq tar; do
    if command -v "$tool" &>/dev/null; then
        printf "    ✓ %-10s %s\n" "$tool" "$(which "$tool")"
    else
        printf "    ✗ %-10s 未找到\n" "$tool"
        MISSING="$MISSING $tool"
    fi
done

if [ -n "$MISSING" ]; then
    echo ""
    echo "    ⚠ 缺少系统工具:$MISSING"
    echo "    部分 skills 的 shell 脚本依赖这些工具。"
    echo "    Ubuntu/Debian: sudo apt install$MISSING"
fi

# ─── 5. .env 提示 ───
echo ""
if [ -f .env ]; then
    echo ">>> .env 已存在 ✓"
else
    echo ">>> 未检测到 .env，请从模板创建:"
    echo "    cp .env.example .env"
    echo "    然后编辑 .env 填入 API key 等配置"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo " SPQ 环境准备完成！"
echo ""
echo " 激活环境:   source activate.sh"
echo " 运行评测:   python3 -m spq run -p openai -m catalog"
echo " 查看帮助:   python3 -m spq --help"
echo "═══════════════════════════════════════════════════"
