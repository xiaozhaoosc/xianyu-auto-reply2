# setup_ssh.ps1 - Auto configure SSH passwordless login from Windows to 192.168.1.21
# Usage: In PowerShell, run: .\scripts\setup_ssh.ps1

$ip = "192.168.1.21"
$user = "ken3zhao"
$port = 2216
$keyPath = "$env:USERPROFILE\.ssh\id_rsa.pub"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "         SSH Passwordless Setup Tool" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "Local Public Key: $keyPath" -ForegroundColor Gray
Write-Host "Target Server   : $user@$ip (Port: $port)" -ForegroundColor Gray
Write-Host "----------------------------------------------" -ForegroundColor Cyan

# 1. Check if local public key exists
if (-not (Test-Path $keyPath)) {
    Write-Host "Local public key not found. Generating a new SSH keypair..." -ForegroundColor Yellow
    ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\id_rsa" -N ""
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to generate SSH keypair. Please run 'ssh-keygen' manually and retry."
        exit 1
    }
    Write-Host "SSH keypair generated successfully!" -ForegroundColor Green
}

# 2. Read public key content
$pubKey = Get-Content -Path $keyPath -Raw
$pubKey = $pubKey.Trim()

# 3. Formulate the remote shell command
# We use single quotes to wrap the pubkey to prevent remote shell evaluation issues
$sshCmd = "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$pubKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

Write-Host "Sending public key to the target server..." -ForegroundColor Cyan
Write-Host "[INPUT REQUIRED] Please enter the password for $user@$ip below:" -ForegroundColor Yellow

# Execute the copy via ssh (disable host key checking for automation)
ssh -o StrictHostKeyChecking=no -p $port "${user}@${ip}" $sshCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS] Public key successfully transmitted and written!" -ForegroundColor Green
    Write-Host "Validating passwordless login..." -ForegroundColor Cyan
    
    # Test connection using BatchMode=yes to guarantee no password prompt is requested
    $testResult = ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 -p $port "${user}@${ip}" "echo 'SUCCESS'"
    if ($testResult.Trim() -eq "SUCCESS") {
        Write-Host "[SUCCESS] Validation passed! You can now log in without a password:" -ForegroundColor Green
        Write-Host "Command: ssh ${user}@${ip}" -ForegroundColor Yellow
    } else {
        Write-Warning "Key was copied, but passwordless login validation failed. Please check:"
        Write-Warning "1. If '/etc/ssh/sshd_config' on the server has 'PubkeyAuthentication yes'."
        Write-Warning "2. Ownership/permissions of the user's home directory or ~/.ssh directory on the server."
    }
} else {
    Write-Error "Failed to transmit public key. Please verify your password and network connectivity."
}
