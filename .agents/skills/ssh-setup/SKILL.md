---
name: ssh-setup
description: "自动配置本地到目标主机的 SSH 免密登录，检测并生成本地密钥对，拷贝公钥到目标主机的 authorized_keys 并设置正确的权限。"
---

# SSH 免密登录配置 Skill

此 Skill 用于自动化配置从当前客户端到远程 Linux 服务器的 SSH 免密登录。

## 适用场景
当需要登录或部署项目到远程 Linux 主机（如 192.168.1.21），而本地尚未配置免密时，可调用此 Skill 快速建立信任关系。

## 自动化执行步骤

1. **确定目标配置**：
   默认目标为：
   - 目标主机 IP: `192.168.1.21`
   - 登录用户名: `ken3zhao`
   - SSH 端口: `2216`

2. **运行配置脚本**：
   在 PowerShell 终端中，切换至项目根目录，运行以下脚本：
   ```powershell
   .\scripts\setup_ssh.ps1
   ```

3. **用户配合操作**：
   - 脚本运行到“传输公钥至目标服务器”时，会输出提示 `👉 配合操作提示：请在下方输入 ken3zhao@192.168.1.21 的登录密码：`。
   - 用户此时**只需在终端中输入一次密码并回车**即可。

4. **自动完成校验**：
   - 脚本会自动关闭首次 Host Key 询问 (`StrictHostKeyChecking=no`)。
   - 写入公钥后，会自动通过 `BatchMode` 发起免密探测。验证通过后即告完成。

## 脚本设计逻辑 (可复用技术细节)

- **本地密钥自检**：
  检查 `$env:USERPROFILE\.ssh\id_rsa.pub` 是否存在。若不存在，自动执行：
  ```powershell
  ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\id_rsa" -N ""
  ```
- **权限安全对齐**：
  传输公钥时，在目标机自动建立 `.ssh` 目录并规范权限：
  ```bash
  mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '<公钥内容>' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
  ```
- **无密码自愈测试**：
  使用 `BatchMode=yes` 绕过密码键盘输入，测试单次连接。如果成功输出 `SUCCESS` 则配置完成：
  ```powershell
  ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 -p <端口> <用户名>@<IP> "echo 'SUCCESS'"
  ```
