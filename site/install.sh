#!/usr/bin/env bash
# Dota Coach - macOS 一键安装
# Usage: curl -fsSL https://dota.bowie.top/install.sh | bash

set -e

ok()    { printf "\033[32m[OK]\033[0m %s\n" "$1"; }
warn()  { printf "\033[33m[WARN]\033[0m %s\n" "$1"; }
die()   { printf "\033[31m[ERR]\033[0m %s\n" "$1"; exit 1; }
sec()   { printf "\n\033[36m==> %s\033[0m\n" "$1"; }

DEST="$HOME/dota-coach"
sec "Dota Coach 安装开始（目标：$DEST）"

# --- 1. uv 检查 ---
sec "检查 uv"
if ! command -v uv >/dev/null 2>&1; then
    warn "uv 未安装，自动安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv >/dev/null 2>&1 || die "uv 安装失败"
ok "uv $(uv --version | awk '{print $2}')"

# --- 2. Python 检查（uv 会自己装，但提示一下） ---
sec "Python 由 uv 自动管理（>= 3.11）"

# --- 3. 克隆/更新 ---
sec "克隆 Dota Coach 仓库"
if [ -d "$DEST" ]; then
    warn "$DEST 已存在，更新到最新"
    git -C "$DEST" pull --ff-only
else
    git clone https://github.com/MajorTomLeee/dota-coach.git "$DEST"
fi
ok "源码就绪"

# --- 4. 装依赖 ---
sec "安装 Python 依赖（一两分钟）"
cd "$DEST"
uv venv
uv pip install -e ".[dev]"
ok "依赖装好"

# --- 5. 交互式配置 ---
sec "配置 Steam ID 和 API key"
uv run dotacoach init

# --- 6. GSI 配置 ---
sec "部署 Valve GSI 配置"
uv run dotacoach install-gsi

# --- 7. 收尾 ---
cat <<EOF

\033[35m================================================================\033[0m
\033[35m  ✅ 安装完成！还差最后一步（Steam 没开 API，必须手动）\033[0m
\033[35m================================================================\033[0m

在 Steam 库 → Dota 2 → 右键 → 属性 → 启动选项 中，加入：

    \033[33m-gamestateintegration -condebug\033[0m

然后启动实时层：

    \033[33mcd $DEST\033[0m
    \033[33muv run dotacoach run\033[0m

F8 = 全局静音切换。详细说明：https://dota.bowie.top

EOF
