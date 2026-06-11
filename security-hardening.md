# 闲鱼自动回复系统 - 安全加固记录

## 加固时间
2026-06-11

## 已完成的加固措施

### 1. docker-compose.yml 密码脱敏
- 创建 .env 文件存储敏感信息
- docker-compose.yml 中的密码替换为环境变量引用
- .env 文件不提交 Git

### 2. chmod 777 → 755
- Dockerfile: chmod 777 → 755
- Dockerfile-cn: chmod 777 → 755
- entrypoint.sh: chmod 777 → 755

### 3. 外部 API 审计
- dy.zhinianboke.com/api/emailSend: 已禁用
- selfapi.zhinianboke.com/api/getItemDetail: 可配置禁用
- xy-update.zhinianboke.com: 只读，低风险
- xy.zhinianboke.com: 仅 launcher GUI，Docker 不涉及

### 4. exec() 危险调用审计
- secure_confirm_ultra.py: 混淆代码，无法审计
- secure_freeshipping_ultra.py: 混淆代码，无法审计
- launcher/service_runner.py: .pyc 加载，正常机制

### 5. 功能测试
- 登录 ✅
- 仪表盘 ✅
- 账号管理 ✅
- 自动回复 ✅
- 商品搜索/采集 ✅
- 定时采集 ✅
- 订单管理 ✅
- 卡券管理 ✅
- 系统设置 ✅
- 代理设置 ✅

## 待处理的安全问题
1. 默认密码硬编码（admin123, xianyu@2026）
2. 激活码签名盐暴露
3. JWT 弱密钥
4. 自动更新无签名验证
5. 极验 captcha_id/private_key 硬编码

## 访问地址
- 前端: http://192.168.50.160:9000
- 后端 API: http://localhost:8089
- WebSocket: http://localhost:8090
- 调度器: http://localhost:8091
