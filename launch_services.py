import subprocess
import os
import time
import sys

def main():
    base_dir = r"D:\IdeaProjects\xianyu-auto-reply2"
    logs_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        
    # 同步 .env
    env_file = os.path.join(base_dir, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            env_content = f.read()
        for sub in ["backend-web", "websocket", "scheduler", "promotion/backend"]:
            sub_env = os.path.join(base_dir, sub, ".env")
            with open(sub_env, "w", encoding="utf-8") as f:
                f.write(env_content)
        print("[+] Sync'ed .env files successfully.")
        
    # 杀死旧端口进程
    print("[*] Cleaning up old processes...")
    cleanup_cmd = 'powershell -Command "foreach($port in @(8089, 8090, 8091, 8092, 9000, 9001)){$conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; if($conn){foreach($c in $conn){Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue}}}"'
    subprocess.run(cleanup_cmd, shell=True)
    time.sleep(2)
    
    # 定义要启动的服务
    services_def = [
        {
            "name": "backend-web",
            "cwd": os.path.join(base_dir, "backend-web"),
            "args": [os.path.join(base_dir, "venv", "Scripts", "python.exe"), "main.py"],
            "log": "backend-web.log"
        },
        {
            "name": "websocket",
            "cwd": os.path.join(base_dir, "websocket"),
            "args": [os.path.join(base_dir, "venv", "Scripts", "python.exe"), "main.py"],
            "log": "websocket.log"
        },
        {
            "name": "scheduler",
            "cwd": os.path.join(base_dir, "scheduler"),
            "args": [os.path.join(base_dir, "venv", "Scripts", "python.exe"), "main.py"],
            "log": "scheduler.log"
        },
        {
            "name": "promotion-backend",
            "cwd": os.path.join(base_dir, "promotion", "backend"),
            "args": [os.path.join(base_dir, "venv", "Scripts", "python.exe"), "main.py"],
            "log": "promotion-backend.log"
        },
        {
            "name": "frontend",
            "cwd": os.path.join(base_dir, "frontend"),
            "args": ["npm.cmd", "run", "dev"],
            "log": "frontend.log"
        },
        {
            "name": "promotion-frontend",
            "cwd": os.path.join(base_dir, "promotion", "frontend"),
            "args": ["npm.cmd", "run", "dev"],
            "log": "promotion-frontend.log"
        }
    ]
    
    running_processes = []
    print("[*] Starting all 6 services under supervisor...")
    
    for s in services_def:
        log_path = os.path.join(logs_dir, s["log"])
        log_file = open(log_path, "w", encoding="utf-8")
        
        # Popen 启动子进程，不带控制台窗口，并且将输出直接重定向到 log 文件
        p = subprocess.Popen(
            s["args"],
            cwd=s["cwd"],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        running_processes.append({"name": s["name"], "proc": p, "log_file": log_file})
        print(f"[+] Started {s['name']} (PID: {p.pid}), logging to logs/{s['log']}")
        
    print("[*] All services triggered. Supervisor loop entered.")
    
    # 保持守护进程运行，并且每 5 秒做一次基础健康检查
    try:
        while True:
            time.sleep(5)
            for item in running_processes:
                poll = item["proc"].poll()
                if poll is not None:
                    # 说明子进程退出了，我们尝试重新拉起它以实现自我修复！
                    print(f"[!] Warning: {item['name']} exited with code {poll}. Re-launching...")
                    s_def = next(x for x in services_def if x["name"] == item["name"])
                    log_path = os.path.join(logs_dir, s_def["log"])
                    log_file = open(log_path, "a", encoding="utf-8")
                    
                    p = subprocess.Popen(
                        s_def["args"],
                        cwd=s_def["cwd"],
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    item["proc"] = p
                    item["log_file"] = log_file
                    print(f"[+] Re-started {item['name']} (PID: {p.pid})")
    except KeyboardInterrupt:
        print("[*] Supervisor stopped. Killing all child processes...")
    finally:
        for item in running_processes:
            try:
                item["proc"].terminate()
                item["log_file"].close()
            except:
                pass

if __name__ == "__main__":
    main()
