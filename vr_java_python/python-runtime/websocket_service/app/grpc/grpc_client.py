"""
gRPC 客户端 — 与 Java 平台层通信

替代原有的直连 DB 操作：
- 读取规则 → gRPC 调 Java RuleService
- 写入日志 → gRPC 调 Java MessageService
- 卡券匹配 → gRPC 调 Java DeliveryService
"""
import grpc
import os
from loguru import logger

# gRPC 服务地址
GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = os.getenv("GRPC_PORT", "9090")


class GrpcClient:
    """gRPC 客户端单例"""

    _instance = None

    def __init__(self):
        self.channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_keyword_rules(self, account_id: str):
        """获取关键词规则"""
        # TODO: 实现 gRPC 调用
        pass

    def get_ai_settings(self, account_id: str):
        """获取 AI 设置"""
        # TODO: 实现 gRPC 调用
        pass

    def get_delivery_rules(self, account_id: str):
        """获取发货规则"""
        # TODO: 实现 gRPC 调用
        pass

    def match_card(self, account_id: str, item_id: str, quantity: int):
        """匹配卡券"""
        # TODO: 实现 gRPC 调用
        pass

    def write_reply_log(self, **kwargs):
        """写入回复日志"""
        # TODO: 实现 gRPC 调用
        pass

    def write_delivery_log(self, **kwargs):
        """写入发货日志"""
        # TODO: 实现 gRPC 调用
        pass


# 全局单例
grpc_client = GrpcClient.get_instance()