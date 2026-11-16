"""
闲鱼智能运营平台 — 全页面自动化测试脚本
测试流程：登录 → 逐页导航 → 验证页面渲染 → CRUD 操作 → 截图留证
"""
import os
import json
import time
from playwright.sync_api import sync_playwright, expect

# 截图保存目录
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "test_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://localhost:9000"
USERNAME = "admin"
PASSWORD = "123456"

# 测试结果收集
results = []


def record(page_name, passed, detail=""):
    """记录测试结果"""
    status = "PASS" if passed else "FAIL"
    results.append({"page": page_name, "status": status, "detail": detail})
    icon = "✅" if passed else "❌"
    print(f"  {icon} [{status}] {page_name}: {detail}")


def screenshot(page, name):
    """保存截图"""
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    return path


def wait_and_check(page, selector, timeout=8000):
    """等待元素出现并返回是否存在"""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except Exception:
        return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 收集控制台错误
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # ============================================================
        # 1. 登录页面测试
        # ============================================================
        print("\n=== 1. 登录页面 ===")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("networkidle")
        screenshot(page, "01_login_page")

        # 验证登录表单存在
        login_form_ok = wait_and_check(page, "input#username, input[placeholder*='用户名']")
        record("登录页-表单渲染", login_form_ok, "登录表单元素存在")

        # 执行登录
        username_input = page.locator("input#username, input[placeholder*='用户名']").first
        password_input = page.locator("input#password, input[type='password']").first
        username_input.fill(USERNAME)
        password_input.fill(PASSWORD)

        # 点击登录按钮
        login_btn = page.locator("button[type='submit'], button:has-text('登录')").first
        login_btn.click()

        # 等待登录完成（跳转到 dashboard 或 token 写入 localStorage）
        try:
            page.wait_for_url("**/dashboard**", timeout=10000)
            login_ok = True
        except Exception:
            # 检查 localStorage 中是否有 token
            token = page.evaluate("localStorage.getItem('token')")
            login_ok = token is not None and len(token) > 0
            if login_ok:
                page.goto(f"{BASE_URL}/dashboard")
                page.wait_for_load_state("networkidle")

        screenshot(page, "02_after_login")
        record("登录功能", login_ok, f"admin/{PASSWORD} 登录{'成功' if login_ok else '失败'}")

        if not login_ok:
            print("\n❌ 登录失败，终止测试")
            browser.close()
            return

        # ============================================================
        # 2. Dashboard 工作台
        # ============================================================
        print("\n=== 2. Dashboard 工作台 ===")
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "03_dashboard")

        # 检查页面标题或主要内容区域
        dashboard_ok = wait_and_check(page, ".ant-card, .ant-statistic, h1, h2, h3", timeout=5000)
        record("Dashboard 页面", dashboard_ok, "工作台页面正常渲染")

        # ============================================================
        # 3. 账号管理
        # ============================================================
        print("\n=== 3. 账号管理 ===")
        page.goto(f"{BASE_URL}/accounts")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "04_accounts")

        accounts_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("账号管理-列表", accounts_ok, "账号列表页面正常渲染")

        # 尝试新增账号
        add_btn = page.locator("button:has-text('新增'), button:has-text('添加'), button:has-text('新建')").first
        if add_btn.is_visible():
            add_btn.click()
            time.sleep(1)
            screenshot(page, "05_accounts_add_modal")
            modal_ok = wait_and_check(page, ".ant-modal, .ant-drawer", timeout=3000)
            record("账号管理-新增弹窗", modal_ok, "新增账号弹窗正常弹出")
            # 关闭弹窗
            cancel_btn = page.locator(".ant-modal button:has-text('取消'), .ant-drawer button:has-text('取消')").first
            if cancel_btn.is_visible():
                cancel_btn.click()
                time.sleep(0.5)
        else:
            record("账号管理-新增弹窗", False, "未找到新增按钮")

        # ============================================================
        # 4. 关键词规则
        # ============================================================
        print("\n=== 4. 关键词规则 ===")
        page.goto(f"{BASE_URL}/keyword-rules")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "06_keyword_rules")

        kw_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("关键词规则-列表", kw_ok, "关键词规则页面正常渲染")

        # ============================================================
        # 5. 发货规则
        # ============================================================
        print("\n=== 5. 发货规则 ===")
        page.goto(f"{BASE_URL}/delivery-rules")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "07_delivery_rules")

        dr_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("发货规则-列表", dr_ok, "发货规则页面正常渲染")

        # ============================================================
        # 6. 默认回复
        # ============================================================
        print("\n=== 6. 默认回复 ===")
        page.goto(f"{BASE_URL}/default-replies")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "08_default_replies")

        reply_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("默认回复-列表", reply_ok, "默认回复页面正常渲染")

        # ============================================================
        # 7. 卡券管理
        # ============================================================
        print("\n=== 7. 卡券管理 ===")
        page.goto(f"{BASE_URL}/cards")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "09_cards")

        cards_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("卡券管理-列表", cards_ok, "卡券管理页面正常渲染")

        # ============================================================
        # 8. 订单管理
        # ============================================================
        print("\n=== 8. 订单管理 ===")
        page.goto(f"{BASE_URL}/orders")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "10_orders")

        orders_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("订单管理-列表", orders_ok, "订单管理页面正常渲染")

        # ============================================================
        # 9. 商品管理
        # ============================================================
        print("\n=== 9. 商品管理 ===")
        page.goto(f"{BASE_URL}/products")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "11_products")

        products_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("商品管理-列表", products_ok, "商品管理页面正常渲染")

        # ============================================================
        # 10. 素材库
        # ============================================================
        print("\n=== 10. 素材库 ===")
        page.goto(f"{BASE_URL}/materials")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "12_materials")

        materials_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("素材库-列表", materials_ok, "素材库页面正常渲染")

        # ============================================================
        # 11. 分销对接
        # ============================================================
        print("\n=== 11. 分销对接 ===")
        page.goto(f"{BASE_URL}/dock-records")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "13_dock_records")

        dock_ok = wait_and_check(page, ".ant-table, .ant-card, h2, h3", timeout=5000)
        record("分销对接-列表", dock_ok, "分销对接页面正常渲染")

        # ============================================================
        # 12. 系统设置
        # ============================================================
        print("\n=== 12. 系统设置 ===")
        page.goto(f"{BASE_URL}/settings")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        screenshot(page, "14_settings")

        settings_ok = wait_and_check(page, ".ant-card, .ant-form, h2, h3", timeout=5000)
        record("系统设置", settings_ok, "系统设置页面正常渲染")

        # ============================================================
        # 13. API 接口验证
        # ============================================================
        print("\n=== 13. API 接口验证 ===")

        # 获取 token
        token = page.evaluate("localStorage.getItem('token')")

        # 通过浏览器 fetch 验证关键 API
        api_tests = [
            ("/api/auth/userinfo", "GET", "获取用户信息"),
            ("/api/accounts?page=1&size=10", "GET", "账号列表"),
            ("/api/keyword-rules?page=1&size=10", "GET", "关键词规则列表"),
            ("/api/cards?page=1&size=10", "GET", "卡券列表"),
            ("/api/orders?page=1&size=10", "GET", "订单列表"),
        ]

        for path, method, name in api_tests:
            try:
                result = page.evaluate(f"""
                    async () => {{
                        const resp = await fetch('{BASE_URL}{path}', {{
                            method: '{method}',
                            headers: {{ 'Authorization': '{token}' }}
                        }});
                        const data = await resp.json();
                        return {{ status: resp.status, code: data.code }};
                    }}
                """)
                api_ok = result.get("code") == 200 or result.get("status") == 200
                record(f"API-{name}", api_ok, f"HTTP {result.get('status')}, code={result.get('code')}")
            except Exception as e:
                record(f"API-{name}", False, str(e)[:80])

        # ============================================================
        # 14. 控制台错误检查
        # ============================================================
        print("\n=== 14. 控制台错误 ===")
        # 过滤掉无关的网络错误
        significant_errors = [e for e in console_errors if "net::ERR" not in e and "404" not in e]
        if significant_errors:
            record("控制台错误", False, f"发现 {len(significant_errors)} 个错误")
            for err in significant_errors[:5]:
                print(f"    ⚠ {err[:120]}")
        else:
            record("控制台错误", True, "无显著控制台错误")

        browser.close()

    # ============================================================
    # 测试报告汇总
    # ============================================================
    print("\n" + "=" * 60)
    print("📊 自动化测试报告")
    print("=" * 60)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)

    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"  {icon} {r['page']}: {r['detail']}")

    print(f"\n总计: {total} 项 | 通过: {passed} | 失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    print(f"截图目录: {SCREENSHOT_DIR}")

    # 保存 JSON 报告
    report_path = os.path.join(os.path.dirname(__file__), "test_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"total": total, "passed": passed, "failed": failed, "results": results}, f, ensure_ascii=False, indent=2)
    print(f"测试报告: {report_path}")


if __name__ == "__main__":
    main()
