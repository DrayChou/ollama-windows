# 设置输出编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# 删除旧的 ollama-latest.zip 文件
if (Test-Path "ollama-latest.zip") {
    Remove-Item -Force "ollama-latest.zip"
}

# 检查并停止正在运行的 Ollama 实例
$ollama_list_output = .\ollama.exe list 2>&1
if ($ollama_list_output -match "NAME\s+ID\s+SIZE\s+MODIFIED") {
    Write-Output "发现正在运行的 Ollama 实例，正在停止..."
    Stop-Process -Name "ollama" -Force
    Start-Sleep -Seconds 2 # 等待实例完全停止
}

# 检查是否存在 ollama.exe
$ollama_exists = Test-Path ".\ollama.exe"

# 获取最新版本信息
$json = Invoke-RestMethod -Uri "https://api.github.com/repos/ollama/ollama/releases/latest"
$latest_version = $json.tag_name -replace "^v", ""
$download_url = $json.assets | Where-Object { $_.name -eq "ollama-windows-amd64.zip" } | Select-Object -ExpandProperty browser_download_url

if (-Not $ollama_exists) {
    Write-Output "未找到 ollama.exe，正在下载最新版本..."
    $update_required = $true
} else {
    # 获取本地版本号
    $local_version_output = .\ollama.exe --version 2>&1
    $local_version = $local_version_output | Select-String -Pattern "ollama version is [0-9]*\.[0-9]*\.[0-9]*|client version is [0-9]*\.[0-9]*\.[0-9]*" | ForEach-Object { $_ -replace ".*version is ", "" }

    # 调试输出本地版本号
    Write-Output "本地版本号输出: $local_version_output"
    Write-Output "提取的本地版本号: $local_version"

    # 调试输出最新版本号
    Write-Output "最新版本号: $latest_version"

    # 比较版本号
    if ($local_version -eq $latest_version) {
        Write-Output "当前已经是最新版本: $local_version"
        $update_required = $false
    } else {
        Write-Output "发现新版本: $latest_version，当前版本: $local_version"
        $update_required = $true
    }
}

if ($update_required) {
    # 下载最新版本
    Invoke-WebRequest -Uri $download_url -OutFile "ollama-latest.zip"

    # 解压到临时目录
    Expand-Archive -Path "ollama-latest.zip" -DestinationPath ".\temp"

    # 替换现有的 ollama.exe
    Move-Item -Force ".\temp\ollama.exe" ".\ollama.exe"

    # 清理临时文件
    Remove-Item -Recurse -Force ".\temp"
    Remove-Item -Force "ollama-latest.zip"
}

# 设置环境变量： models 目录到当前目录下
$env:OLLAMA_MODELS = "$PWD\models"

# 设置环境变量： 设置 host 0.0.0.0
$env:OLLAMA_HOST = "0.0.0.0"

# 启动 ollama 服务
Start-Process -NoNewWindow -FilePath "cmd.exe" -ArgumentList "/c .\ollama.exe start"