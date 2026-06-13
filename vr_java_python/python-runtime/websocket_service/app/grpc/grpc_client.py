"""
gRPC 客户端 — 与 Java 平台层通信

替代原有直连 DB 操作：
- 读取规则 → gRPC 调 Java RuleService
- 写入日志 → gRPC 调 Java MessageService
- 卡券匹配 → gRPC 调 Java DeliveryService
- 账号查询 → gRPC 调 Java AccountService
"""
import grpc
import os
import json
from loguru import logger

# gRPC 服务地址
GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = os.getenv("GRPC_PORT", "9090")

# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# 缓存 TTL（秒）
CACHE_TTL_RULES = 300      # 规则缓存 5 分钟
CACHE_TTL_SETTINGS = 600   # 设置缓存 10 分钟
CACHE_TTL_ACCOUNT = 180    # 账号缓存 3 分钟


class GrpcClient:
    """gRPC 客户端 — 与 Java 平台层通信"""

    _instance = None

    def __init__(self):
        self.channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
        self._redis = None

    @classmethod
    def get_instance(cls):
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def redis(self):
        """懒加载 Redis 连接"""
        if self._redis is None:
            import redis
            self._redis = redis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
            )
        return self._redis

    def _get_cache(self, key: str) -> str | None:
        """从 Redis 读取缓存"""
        try:
            return self.redis.get(key)
        except Exception as e:
            logger.warning(f"Redis 读取失败: {e}")
            return None

    def _set_cache(self, key: str, value: str, ttl: int):
        """写入 Redis 缓存"""
        try:
            self.redis.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Redis 写入失败: {e}")

    # ---- 账号服务 ----

    def get_account(self, account_id: str, owner_id: int) -> dict | None:
        """获取账号信息（优先走 Redis 缓存）"""
        cache_key = f"account:{account_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return json.loads(cached)

        try:
            from app.grpc import account_pb2, account_pb2_grpc
            stub = account_pb2_grpc.AccountServiceStub(self.channel)
            request = account_pb2.AccountRequest(account_id=account_id, owner_id=owner_id)
            response = stub.GetAccount(request)

            result = {
                "id": response.id,
                "account_id": response.account_id,
                "nickname": response.nickname,
                "status": response.status,
                "cookies": response.cookies,
            }
            self._set_cache(cache_key, json.dumps(result), CACHE_TTL_ACCOUNT)
            return result
        except Exception as e:
            logger.error(f"gRPC 获取账号失败: {e}")
            return None

    def update_account_status(self, account_id: str, status: str) -> bool:
        """更新账号状态"""
        try:
            from app.grpc import account_pb2, account_pb2_grpc
            stub = account_pb2_grpc.AccountServiceStub(self.channel)
            request = account_pb2.StatusRequest(account_id=account_id, status=status)
            response = stub.UpdateStatus(request)
            # 清除缓存
            self.redis.delete(f"account:{account_id}")
            return response.success
        except Exception as e:
            logger.error(f"gRPC 更新账号状态失败: {e}")
            return False

    # ---- 规则服务 ----

    def get_keyword_rules(self, account_id: str) -> list[dict]:
        """获取关键词规则（优先走 Redis 缓存）"""
        cache_key = f"keyword_rules:{account_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return json.loads(cached)

        try:
            from app.grpc import rule_pb2, rule_pb2_grpc
            stub = rule_pb2_grpc.RuleServiceStub(self.channel)
            request = rule_pb2.RuleRequest(account_id=account_id)
            response = stub.GetKeywordRules(request)

            rules = [
                {
                    "id": r.id,
                    "account_id": r.account_id,
                    "keyword": r.keyword,
                    "match_type": r.match_type,
                    "reply_content": r.reply_content,
                    "priority": r.priority,
                    "enabled": r.enabled,
                }
                for r in response.rules
            ]
            self._set_cache(cache_key, json.dumps(rules), CACHE_TTL_RULES)
            return rules
        except Exception as e:
            logger.error(f"gRPC 获取关键词规则失败: {e}")
            return []

    def get_delivery_rules(self, account_id: str) -> list[dict]:
        """获取发货规则"""
        cache_key = f"delivery_rules:{account_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return json.loads(cached)

        try:
            from app.grpc import rule_pb2, rule_pb2_grpc
            stub = rule_pb2_grpc.RuleServiceStub(self.channel)
            request = rule_pb2.RuleRequest(account_id=account_id)
            response = stub.GetDeliveryRules(request)

            rules = [
                {
                    "id": r.id,
                    "account_id": r.account_id,
                    "rule_code": r.rule_code,
                    "enabled": r.enabled,
                    "priority": r.priority,
                    "block_reason": r.block_reason,
                    "auto_close_order": r.auto_close_order,
                    "config": r.config,
                }
                for r in response.rules
            ]
            self._set_cache(cache_key, json.dumps(rules), CACHE_TTL_RULES)
            return rules
        except Exception as e:
            logger.error(f"gRPC 获取发货规则失败: {e}")
            return []

    def get_ai_settings(self, account_id: str) -> dict | None:
        """获取 AI 设置"""
        cache_key = f"ai_settings:{account_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return json.loads(cached)

        try:
            from app.grpc import rule_pb2, rule_pb2_grpc
            stub = rule_pb2_grpc.RuleServiceStub(self.channel)
            request = rule_pb2.AISettingRequest(account_id=account_id)
            response = stub.GetAISettings(request)

            result = {
                "enabled": response.enabled,
                "provider": response.provider,
                "model": response.model,
                "api_key": response.api_key,
                "base_url": response.base_url,
                "system_prompt": response.system_prompt,
            }
            self._set_cache(cache_key, json.dumps(result), CACHE_TTL_SETTINGS)
            return result
        except Exception as e:
            logger.error(f"gRPC 获取 AI 设置失败: {e}")
            return None

    def get_default_reply(self, account_id: str, item_id: str = "") -> dict | None:
        """获取默认回复"""
        try:
            from app.grpc import rule_pb2, rule_pb2_grpc
            stub = rule_pb2_grpc.RuleServiceStub(self.channel)
            request = rule_pb2.DefaultReplyRequest(account_id=account_id, item_id=item_id)
            response = stub.GetDefaultReply(request)
            return {
                "content": response.content,
                "reply_once": response.reply_once,
            }
        except Exception as e:
            logger.error(f"gRPC 获取默认回复失败: {e}")
            return None

    # ---- 消息服务 ----

    def write_reply_log(self, **kwargs):
        """写入回复日志"""
        try:
            from app.grpc import message_pb2, message_pb2_grpc
            stub = message_pb2_grpc.MessageServiceStub(self.channel)
            request = message_pb2.ReplyLogRequest(**kwargs)
            stub.WriteReplyLog(request)
        except Exception as e:
            logger.error(f"gRPC 写入回复日志失败: {e}")

    def write_ai_chat_message(self, **kwargs):
        """写入 AI 聊天消息"""
        try:
            from app.grpc import message_pb2, message_pb2_grpc
            stub = message_pb2_grpc.MessageServiceStub(self.channel)
            request = message_pb2.AIChatRequest(**kwargs)
            stub.WriteAIChatMessage(request)
        except Exception as e:
            logger.error(f"gRPC 写入 AI 聊天消息失败: {e}")

    def check_blacklist(self, account_id: str, buyer_id: str) -> tuple[bool, str]:
        """检查黑名单"""
        try:
            from app.grpc import message_pb2, message_pb2_grpc
            stub = message_pb2_grpc.MessageServiceStub(self.channel)
            request = message_pb2.BlacklistRequest(account_id=account_id, buyer_id=buyer_id)
            response = stub.CheckBlacklist(request)
            return response.is_blacklisted, response.reason
        except Exception as e:
            logger.error(f"gRPC 检查黑名单失败: {e}")
            return False, ""

    # ---- 发货服务 ----

    def match_card(self, account_id: str, item_id: str, quantity: int = 1) -> dict | None:
        """匹配卡券"""
        try:
            from app.grpc import delivery_pb2, delivery_pb2_grpc
            stub = delivery_pb2_grpc.DeliveryServiceStub(self.channel)
            request = delivery_pb2.MatchCardRequest(
                account_id=account_id, item_id=item_id, quantity=quantity
            )
            response = stub.MatchCard(request)
            if not response.matched:
                return None
            return {
                "card_id": response.card_id,
                "card_content": response.card_content,
                "card_type": response.card_type,
                "card_source": response.card_source,
            }
        except Exception as e:
            logger.error(f"gRPC 匹配卡券失败: {e}")
            return None

    def write_delivery_log(self, **kwargs):
        """写入发货日志"""
        try:
            from app.grpc import delivery_pb2, delivery_pb2_grpc
            stub = delivery_pb2_grpc.DeliveryServiceStub(self.channel)
            request = delivery_pb2.DeliveryLogRequest(**kwargs)
            stub.WriteDeliveryLog(request)
        except Exception as e:
            logger.error(f"gRPC 写入发货日志失败: {e}")

    def get_order_info(self, order_id: str) -> dict | None:
        """获取订单信息"""
        try:
            from app.grpc import delivery_pb2, delivery_pb2_grpc
            stub = delivery_pb2_grpc.DeliveryServiceStub(self.channel)
            request = delivery_pb2.OrderRequest(order_id=order_id)
            response = stub.GetOrderInfo(request)
            return {
                "order_id": response.order_id,
                "item_id": response.item_id,
                "buyer_id": response.buyer_id,
                "status": response.status,
                "amount": response.amount,
                "created_at": response.created_at,
            }
        except Exception as e:
            logger.error(f"gRPC 获取订单信息失败: {e}")
            return None


# 全局单例
grpc_client = GrpcClient.get_instance()
