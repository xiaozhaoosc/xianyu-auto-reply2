#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书知识库 & 群机器人一键同步工具

功能：
1. 读取本地知识库 taobao_slider_bypass_solutions.md 内容
2. 支持同步到飞书知识库云文档 (使用飞书 Docx API)
3. 支持一键推送富文本卡片到飞书群群机器人 (使用 Webhook API)
"""
import os
import sys
import json
import time
import requests
from typing import Dict, Any, List

# 本地源文档路径
SOURCE_DOC = os.path.join(os.path.dirname(__file__), "..", "kendocs", "taobao_slider_bypass_solutions.md")

# ==========================================
# 飞书开发者凭证配置（如有知识库同步需求，请在此处配置）
# ==========================================
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "您的飞书自建应用_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "您的飞书自建应用_APP_SECRET")
# 知识库文件夹的 Token，或您想要创建文档的目标知识库 Token
FEISHU_SPACE_ID = os.getenv("FEISHU_SPACE_ID", "您的飞书知识库_SPACE_ID")

# ==========================================
# 飞书群机器人 Webhook 配置（如有群通知需求，请在此处配置）
# ==========================================
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")


def read_local_doc() -> str:
    """读取本地 Markdown 白皮书"""
    if not os.path.exists(SOURCE_DOC):
        print(f"[-] 错误：找不到源文档 {SOURCE_DOC}")
        sys.exit(1)
    with open(SOURCE_DOC, "r", encoding="utf-8") as f:
        return f.read()


def get_tenant_access_token() -> str:
    """获取飞书 Open API 访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        res_json = response.json()
        if res_json.get("code") == 0:
            token = res_json.get("tenant_access_token")
            print(f"[+] 成功获取 tenant_access_token: {token[:8]}******")
            return token
        else:
            print(f"[-] 获取 Token 失败: {res_json.get('msg')}")
            return ""
    except Exception as e:
        print(f"[-] 请求 Token 发生异常: {e}")
        return ""


def sync_to_feishu_docx(token: str, markdown_content: str):
    """将 Markdown 作为新文档上传到飞书云文档"""
    print("[*] 正在解析并同步到飞书知识库云文档 (Docx)...")
    if FEISHU_APP_ID == "您的飞书自建应用_APP_ID" or not token:
        print("[!] 提示：未配置有效的飞书 APP_ID/SECRET，跳过知识库同步。")
        return

    # 1. 创建一篇空的飞书云文档
    # 接口文档：https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 飞书新建文档参数，可指定所在的文件夹文件夹 (folder_token)
    payload = {
        "title": "淘宝与闲鱼滑块（x5sec）反爬绕过方案技术白皮书"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        res_json = response.json()
        if res_json.get("code") != 0:
            print(f"[-] 创建云文档失败: {res_json.get('msg')}")
            return
        
        doc_info = res_json.get("data", {}).get("document", {})
        doc_id = doc_info.get("document_id")
        print(f"[+] 飞书云文档创建成功！Document ID: {doc_id}")
        print(f"[+] 文档访问链接: https://bytedance.feishu.cn/docx/{doc_id}")
        
        # 2. 将本地 Markdown 的段落追加写入飞书文档中 (转换为飞书 block 块结构)
        # 飞书 Docx 使用结构化的 Block 树来管理文档，此处简易封装：把 Markdown 转换为纯文本段落块写入
        write_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/root/children"
        
        lines = markdown_content.split("\n")
        blocks = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            
            # 简单的 Markdown 解析
            block_type = 2 # text block
            text_element = {"content": line_str, "text_element_style": {}}
            
            if line_str.startswith("# "):
                block_type = 3 # h1
                text_element["content"] = line_str[2:]
            elif line_str.startswith("## "):
                block_type = 4 # h2
                text_element["content"] = line_str[3:]
            elif line_str.startswith("### "):
                block_type = 5 # h3
                text_element["content"] = line_str[4:]
            elif line_str.startswith("* ") or line_str.startswith("- "):
                block_type = 12 # bullet block
                text_element["content"] = line_str[2:]
                
            blocks.append({
                "block_type": block_type,
                block_type_name(block_type): {
                    "elements": [
                        {
                            "type": "text_run",
                            "text_run": text_element
                        }
                    ]
                }
            })
            
        # 飞书单次写入限制，每批最大 50 个 blocks
        batch_size = 40
        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i+batch_size]
            write_payload = {
                "children": batch,
                "index": -1 # 追加到文档末尾
            }
            write_res = requests.post(write_url, json=write_payload, headers=headers, timeout=10)
            if write_res.json().get("code") == 0:
                print(f"[+] 成功写入段落块 {i+1} 至 {i+len(batch)}")
            else:
                print(f"[-] 写入段落失败: {write_res.json().get('msg')}")
                
        print(f"[+] 知识库同步大功告成！您可以前往飞书查阅：https://bytedance.feishu.cn/docx/{doc_id}")
            
    except Exception as e:
        print(f"[-] 同步飞书知识库发生异常: {e}")


def block_type_name(b_type: int) -> str:
    """返回飞书 Block 块字段名"""
    mapping = {
        2: "page",
        3: "heading1",
        4: "heading2",
        5: "heading3",
        12: "bullet"
    }
    return mapping.get(b_type, "text")


def send_feishu_webhook(markdown_content: str):
    """通过飞书群机器人 Webhook 推送富文本通知"""
    print("[*] 正在准备发送群机器人 Webhook 通知...")
    if not FEISHU_WEBHOOK_URL or FEISHU_WEBHOOK_URL.startswith("http") is False:
        print("[!] 提示：未检测到有效飞书 WEBHOOK_URL，跳过机器人推送。")
        return
    
    # 构造富文本消息
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "🛡️ 淘宝/闲鱼滑块（x5sec）反爬绕过方案整理完毕",
                    "content": [
                        [
                            {"tag": "text", "text": "项目本地知识库已同步！内容包含：\n"},
                            {"tag": "text", "text": "1. 淘宝 acjs 与 x5sec 绕过的四大路线技术对比；\n"},
                            {"tag": "text", "text": "2. 滑块自动与人工双模自愈设计架构；\n"},
                            {"tag": "text", "text": "3. 本地开发与生产 Docker 部署的最优演进路径。\n\n"},
                            {"tag": "text", "text": "👉 详情请直接前往项目目录下的 kendocs/ 文件夹或 wiki 进行查阅！"}
                        ]
                    ]
                }
            }
        }
    }
    
    try:
        response = requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=10)
        res_json = response.json()
        if res_json.get("code") == 0:
            print("[+] 飞书群机器人通知推送成功！")
        else:
            print(f"[-] 飞书机器人推送失败: {res_json.get('msg')}")
    except Exception as e:
        print(f"[-] 推送 Webhook 发生网络异常: {e}")


def main():
    markdown_content = read_local_doc()
    print("[+] 读取本地白皮书成功，共计 %d 字符。" % len(markdown_content))
    
    # 1. 尝试飞书 Docx API 知识库同步
    token = get_tenant_access_token()
    if token:
        sync_to_feishu_docx(token, markdown_content)
        
    # 2. 尝试飞书群机器人 Webhook 消息通知
    send_feishu_webhook(markdown_content)


if __name__ == "__main__":
    main()
