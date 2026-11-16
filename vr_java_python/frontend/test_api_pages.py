"""
闲鱼智能运营平台 — API + 页面自动化测试
通过 curl.exe 调用后端 API 验证所有功能
"""
import subprocess
import json
import sys

BASE = "http://localhost:8089"
FRONT = "http://localhost:9000"
results = []

def curl(method, url, data=None, token=None):
    """执行 curl 请求"""
    cmd = ["curl.exe", "-s", "-X", method, url, "-H", "Content-Type: application/json"]
    if token:
        cmd += ["-H", f"Authorization: {token}"]
    if data:
        # 写入临时文件避免 PowerShell JSON 转义问题
        tmp = "__curl_body.json"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        cmd += ["-d", f"@{tmp}"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception as e:
        return {"error": str(e)}

def record(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    icon = "✅" if passed else "❌"
    print(f"  {icon} [{status}] {name}: {detail}")

def check_frontend(path):
    """检查前端页面是否返回 200"""
    cmd = ["curl.exe", "-s", "-o", "nul", "-w", "%{http_code}", f"{FRONT}{path}"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() == "200"
    except:
        return False

# ============================================================
# 1. 基础设施检查
# ============================================================
print("\n=== 1. 基础设施 ===")
r = curl("GET", f"{BASE}/health")
record("后端健康检查", r.get("code") == 200, f"code={r.get('code')}")

r = curl("GET", f"{BASE}/scheduler/health")  # scheduler 在 8091
# scheduler 端口不同，单独测
cmd = ["curl.exe", "-s", "http://localhost:8091/scheduler/health"]
try:
    r2 = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    sched = json.loads(r2.stdout) if r2.stdout.strip() else {}
    record("Scheduler 健康检查", sched.get("code") == 200, f"code={sched.get('code')}")
except:
    record("Scheduler 健康检查", False, "连接失败")

# ============================================================
# 2. 登录测试
# ============================================================
print("\n=== 2. 登录 ===")
r = curl("POST", f"{BASE}/api/auth/login", {"username": "admin", "password": "123456"})
login_ok = r.get("code") == 200 and r.get("data", {}).get("token") is not None
token = r.get("data", {}).get("token", "")
record("登录 admin/123456", login_ok, f"token={'有' if token else '无'}")

# 错误密码
r = curl("POST", f"{BASE}/api/auth/login", {"username": "admin", "password": "wrong"})
record("错误密码拒绝", r.get("code") != 200, f"code={r.get('code')}")

# 空用户名
r = curl("POST", f"{BASE}/api/auth/login", {"username": "", "password": "123456"})
record("空用户名拒绝", r.get("code") != 200, f"code={r.get('code')}")

# ============================================================
# 3. 用户信息
# ============================================================
print("\n=== 3. 用户信息 ===")
r = curl("GET", f"{BASE}/api/auth/userinfo", token=token)
record("获取用户信息", r.get("code") == 200, f"username={r.get('data', {}).get('username', '?')}")

# 无 token 访问
r = curl("GET", f"{BASE}/api/auth/userinfo")
record("无Token访问拒绝", r.get("code") in [401, 500], f"code={r.get('code')}")

# ============================================================
# 4. 账号管理 CRUD
# ============================================================
print("\n=== 4. 账号管理 ===")
# 创建
r = curl("POST", f"{BASE}/api/accounts", {
    "accountId": "test_auto_001",
    "cookie": "auto_test_cookie",
    "loginMethod": "COOKIE",
    "status": "ACTIVE"
}, token=token)
record("创建账号", r.get("code") == 200, f"code={r.get('code')}")

# 列表
r = curl("GET", f"{BASE}/api/accounts?page=1&size=10", token=token)
record("账号列表", r.get("code") == 200, f"code={r.get('code')}")

# ============================================================
# 5. 关键词规则 CRUD
# ============================================================
print("\n=== 5. 关键词规则 ===")
r = curl("POST", f"{BASE}/api/keyword-rules", {
    "keyword": "auto_test_kw",
    "replyContent": "自动测试回复",
    "priority": 99,
    "isActive": True
}, token=token)
record("创建关键词规则", r.get("code") == 200, f"code={r.get('code')}")

r = curl("GET", f"{BASE}/api/keyword-rules?page=1&size=10", token=token)
record("关键词规则列表", r.get("code") == 200, f"code={r.get('code')}")

# ============================================================
# 6. 卡券管理 CRUD
# ============================================================
print("\n=== 6. 卡券管理 ===")
r = curl("POST", f"{BASE}/api/cards", {
    "name": "自动测试卡券",
    "type": "TEXT",
    "enabled": True
}, token=token)
record("创建卡券", r.get("code") == 200, f"code={r.get('code')}")

r = curl("GET", f"{BASE}/api/cards?page=1&size=10", token=token)
record("卡券列表", r.get("code") == 200, f"code={r.get('code')}")

# ============================================================
# 7. 订单管理
# ============================================================
print("\n=== 7. 订单管理 ===")
r = curl("GET", f"{BASE}/api/orders?page=1&size=10", token=token)
record("订单列表", r.get("code") == 200, f"code={r.get('code')}")

# ============================================================
# 8. 商品管理
# ============================================================
print("\n=== 8. 商品管理 ===")
r = curl("GET", f"{BASE}/api/products?page=1&size=10", token=token)
record("商品列表", r.get("code") == 200, f"code={r.get('code')}")

# ============================================================
# 9. 分销对接
# ============================================================
print("\n=== 9. 分销对接 ===")
r = curl("GET", f"{BASE}/api/dock-records?page=1&size=10", token=token)
record("分销对接列表", r.get("code") in [200, 404], f"code={r.get('code')}")

# ============================================================
# 10. 前端页面可达性
# ============================================================
print("\n=== 10. 前端页面可达性 ===")
pages = [
    ("/login", "登录页"),
    ("/dashboard", "工作台"),
    ("/accounts", "账号管理"),
    ("/keyword-rules", "关键词规则"),
    ("/delivery-rules", "发货规则"),
    ("/default-replies", "默认回复"),
    ("/cards", "卡券管理"),
    ("/orders", "订单管理"),
    ("/products", "商品管理"),
    ("/materials", "素材库"),
    ("/dock-records", "分销对接"),
    ("/settings", "系统设置"),
]
for path, name in pages:
    ok = check_frontend(path)
    record(f"前端-{name}", ok, f"{path} -> {'200' if ok else '非200'}")

# ============================================================
# 11. 前端代理验证（通过 9000 端口访问 API）
# ============================================================
print("\n=== 11. 前端代理验证 ===")
r = curl("POST", f"{FRONT}/api/auth/login", {"username": "admin", "password": "123456"})
proxy_ok = r.get("code") == 200 and r.get("data", {}).get("token") is not None
record("前端代理登录", proxy_ok, f"通过 9000 端口代理到后端")

# ============================================================
# 汇总
# ============================================================
print("\n" + "=" * 60)
print("📊 自动化测试报告")
print("=" * 60)

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
total = len(results)

for r in results:
    icon = "✅" if r["status"] == "PASS" else "❌"
    print(f"  {icon} {r['name']}: {r['detail']}")

print(f"\n总计: {total} 项 | 通过: {passed} | 失败: {failed}")
print(f"通过率: {passed/total*100:.1f}%")

# 保存报告
with open("test_report.json", "w", encoding="utf-8") as f:
    json.dump({"total": total, "passed": passed, "failed": failed, "results": results}, f, ensure_ascii=False, indent=2)

if failed > 0:
    print(f"\n⚠️  有 {failed} 项测试失败，需要修复")
    sys.exit(1)
else:
    print("\n🎉 全部测试通过！")
    sys.exit(0)
