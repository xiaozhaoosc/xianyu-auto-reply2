#!/usr/bin/env python3
"""采集功能自动化测试脚本

用法:
  python3 scripts/test_crawl.py                    # 使用默认凭据
  python3 scripts/test_crawl.py admin <password>   # 指定用户名密码

测试内容:
1. 登录获取 JWT
2. 获取有效闲鱼账号
3. 执行搜索采集
4. 检查结果（含滑块验证后 cookies 更新重试）
"""
import json
import os
import sys
import time

import requests

BASE = "http://localhost:8089"
API = f"{BASE}/api/v1"
TIMEOUT = 180


def login(user, pwd):
    r = requests.post(f"{API}/auth/login", json={"username": user, "password": pwd}, timeout=10)
    r.raise_for_status()
    d = r.json()
    if not d.get("success") or not d.get("token"):
        raise RuntimeError(d.get("message", "登录失败"))
    return d["token"]


def get_first_account(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API}/accounts/", headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    items = data if isinstance(data, list) else data.get("data", data.get("items", []))
    if isinstance(items, dict):
        items = items.get("items", [])
    for a in (items or []):
        if a.get("cookie") and a.get("enabled", True):
            return a.get("id") or a.get("account_id")
    return None


def test_search(token, account_id, keyword="手机"):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "keyword": keyword,
        "account_id": account_id,
        "start_page": 1,
        "pages": 1,
        "page_size": 5,
        "fetch_detail": False,
        "detail_limit": 0,
        "headless": True,
    }
    print(f"  关键词: {keyword}  账号ID: {account_id}")
    print(f"  等待响应 (最长 {TIMEOUT}s, 含滑块处理) ...")
    t0 = time.time()
    r = requests.post(f"{API}/compass/goofish/search", headers=headers, json=payload, timeout=TIMEOUT)
    elapsed = time.time() - t0
    print(f"  耗时: {elapsed:.1f}s  HTTP: {r.status_code}")
    return r.json()


def main():
    # 凭据: 命令行参数 > 环境变量 > 默认值
    user = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TEST_USER", "admin")
    pwd = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("TEST_PASS", "")

    if not pwd:
        print("[FAIL] 未提供密码。用法: python3 test_crawl.py <user> <password>")
        sys.exit(1)

    print("=" * 50)
    print("  采集功能自动化测试")
    print("=" * 50)

    # Step 1
    print("\n[Step 1] 登录 ...")
    try:
        token = login(user, pwd)
        print(f"  ✅ JWT: {token[:20]}...")
    except Exception as e:
        print(f"  ❌ {e}")
        sys.exit(1)

    # Step 2
    print("\n[Step 2] 获取账号 ...")
    account_id = get_first_account(token)
    if not account_id:
        print("  ❌ 未找到有效账号")
        sys.exit(1)
    print(f"  ✅ 账号ID: {account_id}")

    # Step 3
    print("\n[Step 3] 搜索采集 ...")
    result = test_search(token, account_id)

    # Step 4
    success = result.get("success", False)
    message = result.get("message", "")
    data = result.get("data", {})
    items = data.get("items", []) if isinstance(data, dict) else []
    error_detail = data.get("error", "") if isinstance(data, dict) else ""

    print("\n" + "=" * 50)
    print(f"  成功:     {success}")
    print(f"  消息:     {message}")
    if error_detail and error_detail != message:
        print(f"  错误详情: {error_detail}")
    print(f"  商品数量: {len(items)}")
    print("=" * 50)

    if success and items:
        print("\n✅ 测试通过!")
        for i, item in enumerate(items[:5]):
            print(f"  [{i+1}] {item.get('title','?')} | {item.get('price','?')}")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        print(f"  响应: {json.dumps(result, ensure_ascii=False)[:800]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
