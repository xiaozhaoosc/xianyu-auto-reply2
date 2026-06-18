# setup_ssh.ps1 - 自动配置 Windows 本地至 192.168.1.21 的 SSH 免密登录
# 使用方法：在 PowerShell 中执行: .\scripts\setup_ssh.ps1

$ip = "192.168.1.21"
$user = "ken3zhao"
$port = 22
$keyPath = "$env:USERPROFILE\.ssh\id_rsa.pub"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "         SSH 免密登录自动配置工具" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "本地公钥: $keyPath" -ForegroundColor Gray
Write-Host "目标服务器: $user@$ip (端口: $port)" -ForegroundColor Gray
Write-Host "----------------------------------------------" -ForegroundColor Cyan

# 1. 检查本地密钥是否存在
if (-not (Test-Path $keyPath)) {
    Write-Host "本地未检测到公钥，正在为您生成 SSH 密钥对..." -ForegroundColor Yellow
    # 自动生成密钥对（默认回车，无密码短语）
    ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\id_rsa" -N ""
    if ($LASTEXITCODE -ne 0) {
        Write-Error "SSH 密钥对生成失败，请手动运行 ssh-keygen 后重试。"
        exit 1
    }
    Write-Host "密钥对生成成功！" -ForegroundColor Green
}

# 2. 读取公钥内容
$pubKey = Get-Content -Path $keyPath -Raw
$pubKey = $pubKey.Trim()

# 3. 准备执行的远程指令
# 注意：使用单引号或者转义符包裹公钥，防止特殊字符（如邮件地址中的 @）被 Shell 错误解析
$sshCmd = "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$pubKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

Write-Host "正在传输公钥至目标服务器..." -ForegroundColor Cyan
Write-Host "👉 配合操作提示：请在下方输入 $user@$ip 的登录密码：" -ForegroundColor Yellow

# 执行拷贝
ssh -o StrictHostKeyChecking=no -p $port "${user}@${ip}" $sshCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[✓] 公钥传输并写入成功！" -ForegroundColor Green
    Write-Host "正在验证免密登录..." -ForegroundColor Cyan
    
    # 使用 BatchMode=yes 强制只进行公钥登录测试
    $testResult = ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 -p $port "${user}@${ip}" "echo 'SUCCESS'"
    if ($testResult.Trim() -eq "SUCCESS") {
        Write-Host "[✓] 验证通过！您现在可以使用以下命令直接免密登录了：" -ForegroundColor Green
        Write-Host "👉 ssh ${user}@${ip}" -ForegroundColor Yellow
    } else {
        Write-Warning "公钥已成功拷贝，但免密验证未通过。这通常是由于："
        Write-Warning "1. 目标服务器上的 SSH 配置（/etc/ssh/sshd_config）未开启公钥登录：PubkeyAuthentication yes"
        Write-Warning "2. 目标服务器上用户家目录或 ~/.ssh 目录的属主/权限不正确。"
    }
} else {
    Write-Error "公钥传输失败，请确认密码是否正确，或者网络与端口是否通畅。"
}
