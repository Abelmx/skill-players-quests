# SPQ 项目环境激活脚本
# 用法: source activate.sh
#
# 功能:
#   1. cd 到项目根目录
#   2. 激活 .venv 虚拟环境
#   3. 加载 .env 环境变量
#   4. 检查关键依赖是否就绪

SPQ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd "$SPQ_ROOT"

if [ ! -d .venv ]; then
    echo "spq: .venv 不存在，请先运行 bash setup.sh" >&2
    return 1 2>/dev/null || exit 1
fi

source .venv/bin/activate

if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# 快速检查 skills 关键依赖
_spq_ok=true
for _mod in httpx PIL qrcode reportlab playwright; do
    if ! python3 -c "import $_mod" 2>/dev/null; then
        echo "spq: 缺少依赖 $_mod，请运行 bash setup.sh 重新安装" >&2
        _spq_ok=false
    fi
done

if $_spq_ok; then
    echo "spq ready | python=$(python3 --version) | model=${SPQ_OPENAI_MODEL:-not set}"
else
    echo "spq: 部分依赖缺失，评测可能失败" >&2
fi

unset _spq_ok _mod SPQ_ROOT
