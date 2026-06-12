#!/bin/bash
# 闲鱼自动回复与运营系统 - 本地一键开发调试启动脚本 (优先支持 Ubuntu)
# 用法: chmod +x 本地一键调试启动.sh && ./本地一键调试启动.sh

# 优雅的彩色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

write_header() {
    echo -e "${CYAN}\n=================================================="
    echo -e "  $1"
    echo -e "==================================================${NC}"
}

write_info() {
    echo -e "${NC}[*] $1"
}

write_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

write_warn() {
    echo -e "${YELLOW}[!] $1${NC}"
}

write_error() {
    echo -e "${RED}[x] $1${NC}"
}

write_header "闲鱼自动回复与运营系统 - 本地开发调试启动器 (Ubuntu)"

# 1. 检查 Docker 开发底座状态
write_info "正在检查 MySQL & Redis 容器底座状态..."
if ! command -v docker &> /dev/null; then
    write_error "未检测到 Docker 环境，请先安装 Docker！"
    exit 1
fi

containers=$(docker ps --format '{{.Names}}' 2>/dev/null)
mysqlRunning=$(echo "$containers" | grep -w "xianyu-dev-mysql")
redisRunning=$(echo "$containers" | grep -w "xianyu-dev-redis")

if [ -z "$mysqlRunning" ] || [ -z "$redisRunning" ]; then
    write_warn "检测到 MySQL 或 Redis 开发底座未启动，正在尝试为您启动..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        write_error "未检测到 docker compose 命令，请确认 Docker Compose 是否安装！"
        exit 1
    fi
    docker compose -f docker-compose.dev-db.yml up -d
    if [ $? -ne 0 ]; then
        write_error "启动 Docker 底座失败，请确保 Docker 正在后台运行！"
        exit 1
    fi
    write_success "Docker 底座 MySQL 和 Redis 容器启动成功！"
else
    write_success "MySQL & Redis 开发底座已在后台运行中。"
fi

# 2. 检查 Python 虚拟环境
venvPath="./venv"
if [ ! -d "$venvPath" ]; then
    write_warn "未检测到 venv 虚拟环境，请先等待依赖安装任务完成！"
    exit 1
fi

# 3. 检查前端依赖项是否已安装
if [ ! -d "frontend/node_modules" ]; then
    write_warn "未检测到主系统前端依赖 node_modules，正在尝试自动安装 (npm install)..."
    cd frontend && npm install --silent
    cd ..
    write_success "主系统前端依赖安装完成！"
fi

if [ ! -d "promotion/frontend/node_modules" ]; then
    write_warn "未检测到返佣系统前端依赖 node_modules，正在尝试自动安装 (npm install)..."
    cd promotion/frontend && npm install --silent
    cd ../..
    write_success "返佣系统前端依赖安装完成！"
fi

# 4. 同步根目录 .env 配置到各子服务中
write_info "正在同步环境变量配置文件 .env 到各后端子项目中..."
if [ -f ".env" ]; then
    cp -f .env backend-web/.env
    cp -f .env websocket/.env
    cp -f .env scheduler/.env
    cp -f .env promotion/backend/.env
    write_success "环境变量配置文件 .env 同步完成！"
else
    write_warn "未在根目录下检测到 .env 配置文件！"
fi

# 5. 清理占用端口 of 旧服务进程以防端口冲突，并关闭其宿主终端窗口 (Linux版)
write_info "正在清理可能占用调试端口的旧服务进程及关闭旧终端窗口..."
ports=(8089 8090 8091 8092 9000 9001)

# 确保 lsof 可用以寻找占用端口的 PID
if command -v lsof &> /dev/null; then
    for port in "${ports[@]}"; do
        pids=$(lsof -t -i:"$port" 2>/dev/null)
        if [ ! -z "$pids" ]; then
            for pid in $pids; do
                # 获取父进程（启动它的 shell 进程 bash/zsh）并关闭对应终端窗口
                ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
                if [ ! -z "$ppid" ] && [ "$ppid" -ne 1 ]; then
                    # 尝试杀掉直接父进程 shell
                    kill -9 "$ppid" 2>/dev/null
                fi
                # 强杀进程本身
                kill -9 "$pid" 2>/dev/null
            done
        fi
    done
    write_success "端口及旧终端窗口自动回收完成！"
else
    # 降级使用 fuser
    if command -v fuser &> /dev/null; then
        for port in "${ports[@]}"; do
            fuser -k -n tcp "$port" &> /dev/null
        done
        write_success "已通过 fuser 清理端口上的旧进程"
    else
        write_warn "未检测到 lsof 或 fuser，跳过端口自动查杀步骤，请确保端口未被占用！"
    fi
fi

# 6. 多终端窗口拉起各项子服务支持 (gnome-terminal 优先)
write_header "正在多终端窗口中拉起各项子服务..."

run_in_terminal() {
    title=$1
    dir=$2
    cmd=$3
    
    # 优先检测 gnome-terminal (Ubuntu 默认终端)
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" -- bash -c "cd $dir && $cmd; exec bash" &
    # 备选检测 xterm
    elif command -v xterm &> /dev/null; then
        xterm -T "$title" -e "bash -c 'cd $dir && $cmd; exec bash'" &
    else
        # 降级：无桌面环境或未安装图形终端时，直接在后台静默运行并输出日志到 logs/
        mkdir -p logs
        log_file="logs/${title// /_}.log"
        write_warn "未检测到图形终端，将在后台静默拉起 $title 并重定向输出至 $log_file"
        cd "$dir" && eval "$cmd" > "../$log_file" 2>&1 &
        cd - > /dev/null
    fi
}

# 启动各子模块
run_in_terminal "[Backend-Web :8089]" "backend-web" "../venv/bin/python main.py"
run_in_terminal "[WebSocket :8090]" "websocket" "../venv/bin/python main.py"
run_in_terminal "[Scheduler :8091]" "scheduler" "../venv/bin/python main.py"
run_in_terminal "[Promotion-Backend :8092]" "promotion/backend" "../../venv/bin/python main.py"
run_in_terminal "[Frontend :9000]" "frontend" "npm run dev"
run_in_terminal "[Promotion-Frontend :9001]" "promotion/frontend" "npm run dev"

write_success "\n所有 6 个服务已拉起完毕！"
write_info "提示：若运行在 Ubuntu 桌面环境，已为您弹出 6 个独立的日志查阅终端；"
write_info "若无桌面环境，可在 logs/ 目录下查阅各个服务的实时运行日志。"
write_info "管理端网址: http://localhost:9000 (默认账号: admin / admin123)"
write_info "返佣端网址: http://localhost:9001"
write_info "后端 Swagger 文档: http://localhost:8089/docs"
echo -e "${CYAN}==================================================${NC}"
